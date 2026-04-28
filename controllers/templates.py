import os
import io
import re
import json
from datetime import datetime, timezone
from flask import Blueprint, request, g, current_app, send_file, redirect, url_for
from controllers.auth_middleware import require_auth as login_required, require_permission
from werkzeug.utils import secure_filename
import psutil
import platform
from models import db, Template, User, ReportInstance, ActivityLog, log_activity, Notification
from extensions import executor
from services.document_service import SmartDocxTemplate, background_compile_task
from services.report_service import save_report_logic

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/dashboard')
@login_required
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

# --- OCR: Vision IA ---

@templates_bp.route('/api/ocr/extract', methods=['POST'])
@login_required
def api_ocr_extract():
    if 'image' not in request.files:
        return {"error": "No se recibio imagen"}, 400

    image_file = request.files['image']
    mime_type = image_file.mimetype or 'image/jpeg'

    if not mime_type.startswith('image/'):
        return {"error": "Solo se aceptan imagenes (JPG, PNG). Los PDFs no son compatibles."}, 400

    campos_raw = request.form.get('campos', '[]')
    try:
        campos = json.loads(campos_raw)
    except Exception:
        campos = []

    image_bytes = image_file.read()
    raw_text = ''

    try:
        import google.generativeai as genai

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada en el servidor"}, 500

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Estrategia inteligente: extraer TODO el texto del documento
        # y luego mapear al formulario con criterio semantico
        campos_str = ', '.join(campos) if campos else 'todos los datos relevantes'
        prompt = f"""Eres un asistente experto en documentos oficiales mexicanos.

PASO 1: Lee TODO el texto visible en la imagen.
PASO 2: Identifica que tipo de documento es (INE, Constancia Fiscal SAT, Acta Constitutiva, Comprobante de Domicilio, etc.)
PASO 3: Los campos del formulario son: {campos_str}

Para cada campo del formulario, busca el valor mas adecuado en el documento usando criterio semantico:
- Si el campo se llama 'nombre', 'nombre_completo', 'razon_social', 'denominacion' -> busca el nombre de la persona o empresa
- Si el campo se llama 'rfc' -> busca el RFC con homoclave
- Si el campo se llama 'domicilio', 'direccion', 'calle', 'domicilio_fiscal' -> busca la direccion completa
- Si el campo se llama 'curp' -> busca el CURP
- Si el campo se llama 'fecha', 'fecha_nacimiento', 'vigencia' -> busca la fecha relevante en DD/MM/YYYY
- Si el campo se llama 'folio', 'numero', 'id' -> busca cualquier numero de identificacion
- Para cualquier otro campo, intenta inferir el valor mas logico del documento

IMPORTANTE: Responde SOLO con un JSON valido. Usa null SOLO si es absolutamente imposible inferir el valor.
Ejemplo: {{"nombre_completo": "EMPRESA EJEMPLO SA DE CV", "rfc": "EEJ850312AB3", "domicilio": "AV REFORMA 123 COL CENTRO CDMX"}}

JSON:"""

        img_part = genai.types.Part(
            inline_data=genai.types.Blob(mime_type=mime_type, data=image_bytes)
        )

        response = model.generate_content([img_part, prompt])
        raw_text = response.text.strip()

        # Limpiar markdown si viene con ```json ... ```
        if '```' in raw_text:
            parts = raw_text.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                try:
                    json.loads(part)
                    raw_text = part
                    break
                except Exception:
                    continue

        extracted = json.loads(raw_text)
        result = {k: v for k, v in extracted.items() if v is not None and str(v).strip() != ''}

        log_activity('OCR_EJECUTADO', f'Extraccion IA: {len(result)} campo(s)')
        return {"status": "success", "data": result}

    except json.JSONDecodeError:
        print(f'OCR parse error. Raw: {raw_text[:300]}')
        return {"status": "partial", "data": {}, "error": "La IA respondio en formato inesperado"}
    except Exception as e:
        print(f'OCR Error: {e}')
        return {"error": f"Error IA: {str(e)}"}, 500


# --- 🔔 API DE NOTIFICACIONES (Relocalizado) ---

@templates_bp.route('/api/notifications/unread')
@login_required
def get_unread_notifications():
    if not g.current_user:
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
    if not g.current_user:
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


# --- ⚙️ ADMIN API: SISTEMA ---

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
def toggle_favorite(template_id):
    template = db.session.get(Template, template_id)
    if template:
        template.is_favorite = not template.is_favorite
        db.session.commit()
    return redirect(url_for('templates.dashboard'))

@templates_bp.route('/public/<int:template_id>', methods=['POST'])
@login_required
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

# --- 👑 ADMIN API ENDPOINTS ---
from models import ActivityLog

@templates_bp.route('/auth/api/admin/logs', methods=['GET'])
@login_required
def api_admin_logs():
    if not getattr(g.current_user, 'is_admin', False):
        return {"error": "Unauthorized"}, 403
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return {"logs": [{
        "id": l.id,
        "action": l.action,
        "details": l.details,
        "timestamp": getattr(l, 'timestamp').strftime('%Y-%m-%d %H:%M:%S'),
        "user": l.user.email if l.user else 'System'
    } for l in logs]}

