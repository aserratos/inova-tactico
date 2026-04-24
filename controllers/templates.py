import os
import io
import re
import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, send_file
from controllers.auth_middleware import require_auth as login_required
from flask import g
from werkzeug.utils import secure_filename
import psutil
import platform
from models import db, Template, User, ReportInstance, ActivityLog, log_activity, Notification
from functools import wraps
from extensions import executor
from services.document_service import SmartDocxTemplate, background_compile_task
from services.report_service import save_report_logic

templates_bp = Blueprint('templates', __name__)

def mfa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('mfa_verified'):
            return redirect(url_for('auth.mfa'))
        return f(*args, **kwargs)
    return decorated_function

@templates_bp.route('/dashboard')
@login_required
@mfa_required
def dashboard():
    # 1. Show my templates AND public templates
    templates = Template.query.filter(
        (Template.uploader_id == g.current_user.id) | (Template.is_public == True)
    ).order_by(Template.is_favorite.desc(), Template.fecha_subida.desc()).all()
    
    # 2. Get Users if Admin
    users = []
    if g.current_user.is_admin:
        users = User.query.all()
        
    # 3. Get Collaborative Reports (Drafts)
    # If admin/supervisor: see all. If user: see assigned or created.
    if g.current_user.is_admin or g.current_user.role == 'supervisor':
        draft_reports = ReportInstance.query.order_by(ReportInstance.fecha_actualizacion.desc()).all()
    else:
        draft_reports = ReportInstance.query.filter(
            (ReportInstance.assigned_to_id == g.current_user.id) | (ReportInstance.created_by_id == g.current_user.id)
        ).order_by(ReportInstance.fecha_actualizacion.desc()).all()
        
    # 4. Get Activity Logs for Bitacora
    logs = []
    if g.current_user.is_admin:
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(150).all()
        
    return render_template('dashboard/index.html', 
                          templates=templates, 
                          users=users, 
                          draft_reports=draft_reports,
                          logs=logs)

# --- 🔌 API DE REACT PWA ---

@templates_bp.route('/api/reports')
@login_required
@mfa_required
def get_reports_api():
    if g.current_user.is_admin or g.current_user.role == 'supervisor':
        draft_reports = ReportInstance.query.order_by(ReportInstance.fecha_actualizacion.desc()).all()
    else:
        draft_reports = ReportInstance.query.filter(
            (ReportInstance.assigned_to_id == g.current_user.id) | (ReportInstance.created_by_id == g.current_user.id)
        ).order_by(ReportInstance.fecha_actualizacion.desc()).all()
        
    reports_data = []
    for r in draft_reports:
        template = r.template
        variables_list = json.loads(template.variables_json or '[]') if template else []
        text_vars = [v for v in variables_list if not SmartDocxTemplate.is_image_var(v)]
        image_vars = [v for v in variables_list if SmartDocxTemplate.is_image_var(v)]
        
        reports_data.append({
            'id': r.id,
            'nombre': r.nombre,
            'status': r.status,
            'porcentaje_avance': r.porcentaje_avance,
            'fecha_actualizacion': r.fecha_actualizacion.strftime('%d %b'),
            'asignado': r.assigned_to.nombre_completo if r.assigned_to and r.assigned_to.nombre_completo else 'Sin Asignar',
            'asignado_iniciales': ''.join([n[0] for n in (r.assigned_to.nombre_completo or '').split()[:2]]) if r.assigned_to and r.assigned_to.nombre_completo else '??',
            'has_compiled_file': bool(r.archivo_compilado_path and (os.path.exists(r.archivo_compilado_path) or 'templates/' in r.archivo_compilado_path)),
            'template_name': template.nombre if template else '',
            'text_vars': text_vars,
            'image_vars': image_vars,
            'data_json': r.data_json or '{}'
        })
        
    return {"reports": reports_data}

@templates_bp.route('/api/templates')
@login_required
def api_get_templates():
    templates = Template.query.filter(
        (Template.uploader_id == g.current_user.id) | (Template.is_public == True)
    ).order_by(Template.is_favorite.desc(), Template.fecha_subida.desc()).all()
    return {"templates": [{"id": t.id, "nombre": t.nombre} for t in templates]}

@templates_bp.route('/api/report/<int:instance_id>', methods=['GET'])
@login_required
def api_get_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report:
        return {"error": "No encontrado"}, 404
        
    template = report.template
    variables_list = json.loads(template.variables_json or '[]')
    
    text_vars = [v for v in variables_list if not SmartDocxTemplate.is_image_var(v)]
    image_vars = [v for v in variables_list if SmartDocxTemplate.is_image_var(v)]
    
    saved_data = json.loads(report.data_json or '{}')
    
    return {
        "id": report.id,
        "nombre": report.nombre,
        "status": report.status,
        "template_name": template.nombre,
        "text_vars": text_vars,
        "image_vars": image_vars,
        "saved_data": saved_data
    }

@templates_bp.route('/api/report/save/<int:instance_id>', methods=['POST'])
@login_required
def api_save_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report: 
        return {"error": "No encontrado"}, 404
    
    # Use centralized logic (it reads request.form and request.files)
    save_report_logic(report, request, g.current_user)
    
    db.session.commit()
    return {"status": "success"}

@templates_bp.route('/api/report/start/<int:template_id>', methods=['POST'])
@login_required
def api_start_report(template_id):
    template = db.session.get(Template, template_id)
    if not template:
        return {"error": "Plantilla no encontrada"}, 404
        
    if template.variables_json:
        variables_list = json.loads(template.variables_json)
        total = len(variables_list)
    else:
        try:
            doc = SmartDocxTemplate(template.ruta_archivo_docx)
            variables_list = list(doc.get_undeclared_template_variables())
            template.variables_json = json.dumps(variables_list)
            db.session.commit()
            total = len(variables_list)
        except Exception:
            total = 0

    new_report = ReportInstance(
        template_id=template.id,
        nombre=f"{template.nombre} - {datetime.now().strftime('%d/%m %H:%M')}",
        created_by_id=g.current_user.id,
        assigned_to_id=g.current_user.id,
        total_campos=total,
        porcentaje_avance=0
    )
    db.session.add(new_report)
    db.session.commit()
    log_activity('REPORTE_INICIADO_API', f'Inició nuevo levantamiento: {template.nombre}')
    
    return {"status": "success", "id": new_report.id}

@templates_bp.route('/api/report/compile/<int:instance_id>', methods=['POST'])
@login_required
def api_compile_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report: return {"error": "No encontrado"}, 404
    
    if report.porcentaje_avance < 100:
        return {"error": f"Incompleto (Avance: {report.porcentaje_avance}%)"}, 400
    
    app = current_app._get_current_object()
    executor.submit(background_compile_task, app, report.id, g.current_user.id)
    
    return {"status": "success"}

@templates_bp.route('/api/report/download/<int:instance_id>')
@login_required
def api_download_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or not report.archivo_compilado_path:
        return {"error": "Archivo no encontrado"}, 404
        
    if os.path.exists(report.archivo_compilado_path):
        return send_file(
            report.archivo_compilado_path,
            as_attachment=True,
            download_name=f"{report.nombre}.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        from services.storage_service import get_presigned_url
        url = get_presigned_url(report.archivo_compilado_path)
        if url:
            return {"url": url} # Send URL for PWA to redirect/download
        else:
            return {"error": "Enlace caducado"}, 404

# --- 🔔 API DE NOTIFICACIONES (Relocalizado) ---

@templates_bp.route('/api/notifications/unread')
@login_required
def get_unread_notifications():
    if not g.current_user.is_authenticated:
        return {"notifications": [], "count": 0}, 401
        
    notifs = Notification.query.filter_by(user_id=g.current_user.id, is_read=False).order_by(Notification.timestamp.desc()).limit(10).all()
    return {
        "count": Notification.query.filter_by(user_id=g.current_user.id, is_read=False).count(),
        "notifications": [{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "link": n.link,
            "time": n.timestamp.strftime('%H:%M')
        } for n in notifs]
    }

@templates_bp.route('/api/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    if not g.current_user.is_authenticated:
        return {"status": "error"}, 401
        
    n = db.session.get(Notification, notif_id)
    if n and n.user_id == g.current_user.id:
        n.is_read = True
        db.session.commit()
        return {"status": "success"}
    return {"status": "error"}, 404

# --- 🎯 API DE TABLERO KANBAN ---
@templates_bp.route('/api/report/update_status/<int:instance_id>', methods=['POST'])
@login_required
@mfa_required
def update_report_status(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report:
        return {"status": "error", "message": "Reporte no encontrado"}, 404
        
    if report.assigned_to_id != g.current_user.id and not g.current_user.is_admin:
        return {"status": "error", "message": "No tienes permiso para mover este reporte."}, 403
        
    new_status = request.json.get('status')
    valid_statuses = ['por_hacer', 'en_ejecucion', 'pendiente', 'terminado']
    
    if new_status not in valid_statuses:
        return {"status": "error", "message": "Estatus inválido."}, 400
        
    # Validación Gatekeeper: No puede ir a "terminado" si no es el 100%
    if new_status == 'terminado' and report.porcentaje_avance < 100:
        return {
            "status": "error", 
            "message": f"El reporte solo tiene un avance del {report.porcentaje_avance}%. Debes capturar todos los datos para completarlo."
        }, 400
        
    old_status = report.status
    report.status = new_status
    
    db.session.commit()
    log_activity('OPERACION_ACTUALIZADA', f'Movió ID-{report.id} a la columna "{new_status}" vía Kanban.')
    
    # Enviar Notificación In-App si el usuario que movió NO es el creador original
    if new_status == 'terminado' and report.created_by_id != g.current_user.id:
        notif = Notification(
            user_id=report.created_by_id,
            title='Reporte Concluido en Sitio',
            message=f"{g.current_user.nombre_completo or g.current_user.email} completó el levantamiento {report.nombre}.",
            type='success',
            link=url_for('templates.edit_report', instance_id=report.id)
        )
        db.session.add(notif)
        db.session.commit()
    
    return {"status": "success", "new_status": report.status}


@templates_bp.route('/report/start/<int:template_id>', methods=['GET'])
@login_required
@mfa_required
def start_report(template_id):
    template = db.session.get(Template, template_id)
    if not template:
        flash('Plantilla no encontrada.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    # Create initial instance from Cache if possible
    if template.variables_json:
        variables_list = json.loads(template.variables_json)
        total = len(variables_list)
    else:
        # Fallback to reading Word once and updating cache
        try:
            doc = SmartDocxTemplate(template.ruta_archivo_docx)
            variables_list = list(doc.get_undeclared_template_variables())
            template.variables_json = json.dumps(variables_list)
            db.session.commit()
            total = len(variables_list)
        except Exception as e:
            total = 0

    new_report = ReportInstance(
        template_id=template.id,
        nombre=f"{template.nombre} - {datetime.now().strftime('%d/%m %H:%M')}",
        created_by_id=g.current_user.id,
        assigned_to_id=g.current_user.id,
        total_campos=total,
        porcentaje_avance=0
    )
    db.session.add(new_report)
    db.session.commit()
    log_activity('REPORTE_INICIADO', f'Inició nuevo levantamiento basado en {template.nombre}')
    
    return redirect(url_for('templates.edit_report', instance_id=new_report.id))

@templates_bp.route('/report/edit/<int:instance_id>', methods=['GET'])
@login_required
@mfa_required
def edit_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report:
        flash('Reporte no encontrado.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    # Check access
    if not g.current_user.is_admin and report.created_by_id != g.current_user.id and report.assigned_to_id != g.current_user.id:
        flash('No tienes permiso para ver este reporte.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    template = report.template
    if template.variables_json:
        variables_list = sorted(json.loads(template.variables_json))
    else:
        doc = SmartDocxTemplate(template.ruta_archivo_docx)
        try:
            variables = doc.get_undeclared_template_variables()
            variables_list = sorted(list(variables))
            template.variables_json = json.dumps(variables_list)
            db.session.commit()
        except Exception as e:
            flash(f'Error al procesar plantilla: {str(e)}', 'error')
            return redirect(url_for('templates.dashboard'))
            
    text_vars = [v for v in variables_list if not SmartDocxTemplate.is_image_var(v)]
    image_vars = [v for v in variables_list if SmartDocxTemplate.is_image_var(v)]
    
    saved_data = json.loads(report.data_json or '{}')
    
    # Get all users for assignment dropdown
    all_users = User.query.all()
    
    return render_template('dashboard/fill.html', 
                          template=report.template, 
                          report=report,
                          text_vars=text_vars, 
                          image_vars=image_vars,
                          saved_data=saved_data,
                          all_users=all_users)

@templates_bp.route('/report/save/<int:instance_id>', methods=['POST'])
@login_required
@mfa_required
def save_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report: 
        flash('Reporte no encontrado.', 'error')
        return redirect(url_for('templates.dashboard'))
    
    # Use centralized logic
    save_report_logic(report, request, g.current_user)
    
    db.session.commit()
    flash('Progreso guardado exitosamente.', 'success')
    return redirect(url_for('templates.edit_report', instance_id=report.id))

@templates_bp.route('/report/compile/<int:instance_id>', methods=['POST'])
@login_required
@mfa_required
def compile_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report: return redirect(url_for('templates.dashboard'))
    
    # First, save current state
    save_report_logic(report, request, g.current_user)
    
    # Gatekeeper Security: Only compile if 100%
    if report.porcentaje_avance < 100:
        db.session.commit() # Save progress anyway
        variables_list = json.loads(report.template.variables_json or '[]')
        data = json.loads(report.data_json or '{}')
        faltantes = [v.upper() for v in variables_list if not data.get(v) or str(data.get(v)).strip() == '']
        msg_faltantes = ", ".join(faltantes)
        flash(f'¡Incompleto! (Avance: {report.porcentaje_avance}%). Faltan estos campos: {msg_faltantes}', 'error')
        return redirect(url_for('templates.edit_report', instance_id=report.id))
    
    db.session.commit()
    app = current_app._get_current_object()
    executor.submit(background_compile_task, app, report.id, g.current_user.id)
    
    flash('Tu reporte se está compilando en segundo plano. Te enviaremos una notificación cuando esté listo.', 'success')
    return redirect(url_for('templates.dashboard'))


@templates_bp.route('/report/download_compiled/<int:instance_id>')
@login_required
@mfa_required
def download_compiled_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report:
        flash('Reporte no encontrado.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    if report.created_by_id != g.current_user.id and report.assigned_to_id != g.current_user.id and not g.current_user.is_admin:
        flash('No tienes permiso para descargar este reporte.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    if not report.archivo_compilado_path:
        flash('El archivo compilado no existe o aún se está generando.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    if os.path.exists(report.archivo_compilado_path):
        return send_file(
            report.archivo_compilado_path,
            as_attachment=True,
            download_name=f"{report.nombre}.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        from services.storage_service import get_presigned_url
        url = get_presigned_url(report.archivo_compilado_path)
        if url:
            return redirect(url)
        else:
            flash('Error al acceder al archivo o enlace caducado.', 'error')
            return redirect(url_for('templates.dashboard'))

@templates_bp.route('/api/system_stats', methods=['GET'])
@login_required
@mfa_required
def system_stats():
    if not g.current_user.is_admin:
        return {"error": "Unauthorized"}, 403
        
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    
    try:
        disk = psutil.disk_usage(os.path.abspath(current_app.config.get('UPLOAD_FOLDER', current_app.root_path)))
    except:
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cores": psutil.cpu_count(logical=True),
        "cpu": cpu,
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "percent": mem.percent
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    }

@templates_bp.route('/upload', methods=['POST'])
@login_required
@mfa_required
def upload():
    if not g.current_user.is_admin:
        flash('Solo los administradores pueden subir nuevas plantillas.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    if 'document' not in request.files:
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    file = request.files['document']
    
    if file.filename == '':
        flash('El archivo no tiene nombre.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'docx':
        filename = secure_filename(file.filename)
        from services.storage_service import upload_file_to_r2
        object_key = f"templates/{int(datetime.now().timestamp())}_{filename}"
        upload_file_to_r2(file, object_key)
        
        nombre = request.form.get('nombre')
        if not nombre:
            nombre = filename.rsplit('.', 1)[0]
            
        is_public = True if request.form.get('public') == 'on' else False
        
        # Cache variables on upload
        try:
            file.seek(0)
            doc = SmartDocxTemplate(file)
            vars = list(doc.get_undeclared_template_variables())
            vars_json = json.dumps(vars)
        except:
            vars_json = "[]"

        new_template = Template(
            nombre=nombre,
            ruta_archivo_docx=object_key,
            uploader_id=g.current_user.id,
            is_public=is_public,
            variables_json=vars_json
        )
        db.session.add(new_template)
        db.session.commit()
        log_activity('PLANTILLA_CREADA', f'Subió nuevo formato matriz: {nombre}')
        
        flash('Plantilla subida exitosamente.', 'success')
    else:
        flash('Formato no válido. Solo se permiten archivos .docx.', 'error')
        
    return redirect(url_for('templates.dashboard'))

@templates_bp.route('/api/admin/templates/upload', methods=['POST'])
@login_required
def api_upload_template():
    if not g.current_user.is_admin:
        return {"error": "Acceso denegado"}, 403
        
    if 'document' not in request.files:
        return {"error": "No se seleccionó ningún archivo"}, 400
        
    file = request.files['document']
    
    if file.filename == '':
        return {"error": "Archivo sin nombre"}, 400
        
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'docx':
        filename = secure_filename(file.filename)
        from services.storage_service import upload_file_to_r2
        object_key = f"templates/{int(datetime.now().timestamp())}_{filename}"
        upload_file_to_r2(file, object_key)
        
        nombre = request.form.get('nombre')
        if not nombre: nombre = filename.rsplit('.', 1)[0]
        
        try:
            file.seek(0)
            doc = SmartDocxTemplate(file)
            vars = list(doc.get_undeclared_template_variables())
            vars_json = json.dumps(vars)
        except:
            vars_json = "[]"

        new_template = Template(
            nombre=nombre,
            ruta_archivo_docx=object_key,
            uploader_id=g.current_user.id,
            is_public=True,
            variables_json=vars_json
        )
        db.session.add(new_template)
        db.session.commit()
        log_activity('PLANTILLA_CREADA_API', f'Subió nuevo formato matriz: {nombre}')
        
        return {"status": "success", "id": new_template.id}
    else:
        return {"error": "Formato inválido. Solo .docx"}, 400

@templates_bp.route('/favorite/<int:template_id>', methods=['POST'])
@login_required
@mfa_required
def toggle_favorite(template_id):
    template = db.session.get(Template, template_id)
    if template:
        template.is_favorite = not template.is_favorite
        db.session.commit()
    return redirect(url_for('templates.dashboard'))

@templates_bp.route('/public/<int:template_id>', methods=['POST'])
@login_required
@mfa_required
def toggle_public(template_id):
    template = db.session.get(Template, template_id)
    # Only the uploader can change visibility
    if template and template.uploader_id == g.current_user.id:
        template.is_public = not template.is_public
        db.session.commit()
        flash('Visibilidad de la plantilla actualizada.', 'success')
    return redirect(url_for('templates.dashboard'))

@templates_bp.route('/delete/<int:template_id>', methods=['POST'])
@login_required
@mfa_required
def delete_template(template_id):
    template = db.session.get(Template, template_id)
    if not template:
        return redirect(url_for('templates.dashboard'))
        
    if not g.current_user.is_admin and template.uploader_id != g.current_user.id:
        flash('Acceso denegado. No tienes permiso para eliminar esta plantilla.', 'error')
        return redirect(url_for('templates.dashboard'))

    same_path_count = Template.query.filter(Template.ruta_archivo_docx == template.ruta_archivo_docx, Template.id != template.id).count()
    if same_path_count == 0 and os.path.exists(template.ruta_archivo_docx):
        try:
            os.remove(template.ruta_archivo_docx)
        except OSError:
            pass
    # For R2, we will just delete the DB record to keep it simple and preserve history if needed.
    db.session.delete(template)
    nombre = template.nombre
    db.session.commit()
    log_activity('PLANTILLA_ELIMINADA', f'Eliminó formato matriz: {nombre}')
    flash('Plantilla eliminada exitosamente.', 'success')
    return redirect(url_for('templates.dashboard'))

@templates_bp.route('/api/admin/templates/delete/<int:template_id>', methods=['POST'])
@login_required
def api_delete_template(template_id):
    if not g.current_user.is_admin:
        return {"error": "Acceso denegado"}, 403
        
    template = db.session.get(Template, template_id)
    if not template: return {"error": "No encontrado"}, 404
        
    db.session.delete(template)
    db.session.commit()
    log_activity('PLANTILLA_ELIMINADA_API', f'Eliminó formato matriz: {template.nombre}')
    return {"status": "success"}

@templates_bp.route('/report/delete/<int:instance_id>', methods=['POST'])
@login_required
@mfa_required
def delete_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report:
        flash('Reporte no encontrado.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    # Security: Only owner or admin
    if not g.current_user.is_admin and report.created_by_id != g.current_user.id:
        flash('No tienes permiso para eliminar este reporte.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    db.session.delete(report)
    nombre = report.nombre
    db.session.commit()
    log_activity('REPORTE_ELIMINADO', f'Eliminó levantamiento de campo: {nombre}')
    flash('Reporte eliminado exitosamente.', 'success')
    return redirect(url_for('templates.dashboard'))



@templates_bp.route('/report/media/<int:instance_id>/<var_name>')
@login_required
@mfa_required
def report_media(instance_id, var_name):
    report = db.session.get(ReportInstance, instance_id)
    if not report: return 'Not found', 404
    data = json.loads(report.data_json or '{}')
    if not path: return 'Not found', 404
    
    if os.path.exists(path):
        return send_file(path)
    else:
        from services.storage_service import get_presigned_url
        url = get_presigned_url(path)
        if url:
            return redirect(url)
        return 'Not found', 404
