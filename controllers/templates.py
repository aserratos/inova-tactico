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
    # 1. Show my templates AND public templates (filtered by org)
    templates = Template.query.filter(Template.org_id == g.org_id).order_by(Template.is_favorite.desc(), Template.fecha_subida.desc()).all()
    
    # 2. Get Users if Admin
    users = []
    if g.current_user.is_admin or g.org_role == 'supervisor':
        users = User.query.filter_by(org_id=g.org_id).all()
        
    # 3. Get Collaborative Reports (Drafts)
    if g.current_user.is_admin or g.org_role == 'supervisor':
        draft_reports = ReportInstance.query.filter_by(org_id=g.org_id).order_by(ReportInstance.fecha_actualizacion.desc()).all()
    else:
        draft_reports = ReportInstance.query.filter_by(org_id=g.org_id).filter(
            (ReportInstance.assigned_to_id == g.current_user.id) | (ReportInstance.created_by_id == g.current_user.id)
        ).order_by(ReportInstance.fecha_actualizacion.desc()).all()
        
    # 4. Get Activity Logs for Bitacora
    logs = []
    if g.current_user.is_admin or g.org_role == 'supervisor':
        logs = ActivityLog.query.filter_by(org_id=g.org_id).order_by(ActivityLog.timestamp.desc()).limit(150).all()
        
    return render_template('dashboard/index.html', 
                          templates=templates, 
                          users=users, 
                          draft_reports=draft_reports,
                          logs=logs)

# --- OCR: Vision IA (Extraccion + Mapeo Semantico) ---

@templates_bp.route('/api/ocr/extract', methods=['POST'])
@login_required
def api_ocr_extract():
    """
    Pipeline de 2 pasos:
    1. Gemini lee el documento y extrae TODOS los datos que encuentra (libre)
    2. Gemini mapea semanticamente esos datos a los campos del formulario
    Resultado: el formulario se llena aunque los nombres de campo sean distintos al documento.
    La inspeccion humana corrige despues si es necesario.
    """
    if 'image' not in request.files:
        return {"error": "No se recibio imagen"}, 400

    image_file = request.files['image']
    mime_type = image_file.mimetype or 'image/jpeg'

    if not mime_type.startswith('image/'):
        return {"error": "Solo se aceptan imagenes JPG/PNG. Convierte el PDF a imagen primero."}, 400

    campos_raw = request.form.get('campos', '[]')
    try:
        campos = json.loads(campos_raw)
    except Exception:
        campos = []

    image_bytes = image_file.read()
    raw_text = ''

    try:
        import requests as http_requests
        import base64

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada en el servidor"}, 500

        campos_str = ', '.join(campos) if campos else 'nombre, rfc, domicilio, fecha, razon_social'

        prompt_text = (
            "Eres un sistema experto en extraccion de datos de documentos oficiales mexicanos "
            "(SAT, INE, Actas Constitutivas, Comprobantes de Domicilio, etc). "
            "Sigue estos 2 pasos:\n\n"
            "PASO 1: Lee TODO el texto visible en la imagen del documento.\n"
            "PASO 2: Mapea los datos al siguiente formulario usando sinonimos e inferencia semantica.\n\n"
            f"CAMPOS DEL FORMULARIO: {campos_str}\n\n"
            "REGLAS DE MAPEO (el nombre del campo varia pero el significado es el mismo):\n"
            "- empresa, nombre, razon_social, denominacion, contribuyente, nombre_empresa -> nombre de persona o empresa\n"
            "- rfc, clave_rfc, r_f_c -> clave RFC con homoclave (ej: PMT231030T82)\n"
            "- cp, codigo_postal, zip, c_p -> codigo postal de 5 digitos\n"
            "- estado, estatus, status, estado_padron -> estatus SAT (ACTIVO) o entidad federativa\n"
            "- domicilio, direccion, calle, domicilio_fiscal -> direccion completa\n"
            "- municipio, ciudad, localidad, delegacion, alcaldia -> municipio o ciudad\n"
            "- fecha, vigencia, fecha_inicio, fecha_expedicion -> fecha relevante en DD/MM/YYYY\n"
            "- regimen, tipo_empresa, tipo_sociedad -> tipo de sociedad o regimen fiscal\n"
            "- tecnico, responsable, usuario, asesor -> null (no viene en documentos oficiales)\n"
            "- CUALQUIER OTRO CAMPO: usa inferencia semantica para encontrar el valor mas logico\n\n"
            "IMPORTANTE:\n"
            "- Responde SOLO con un JSON valido, sin texto adicional\n"
            "- Copia el texto EXACTAMENTE como aparece en el documento\n"
            "- Usa null solo si el dato genuinamente no existe en la imagen\n"
            "- NO inventes datos\n\n"
            "JSON:"
        )

        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                    {"text": prompt_text}
                ]
            }],
            "generationConfig": {"temperature": 0.1}
        }

        # Cadena de modelos: si uno falla por cuota (429) o saturacion (503), intenta el siguiente
        MODELS = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.0-flash-lite']
        http_resp = None
        used_model = None

        for model in MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            print(f'OCR intentando modelo: {model}')
            http_resp = http_requests.post(url, json=payload, timeout=30)
            print(f'OCR HTTP Status ({model}): {http_resp.status_code}')

            if http_resp.status_code == 200:
                used_model = model
                break  # Exito, salir del loop
            elif http_resp.status_code in (429, 503):
                print(f'OCR {http_resp.status_code} en {model}, intentando siguiente...')
                continue  # Intentar el siguiente modelo
            else:
                # Error diferente (400, 401, etc) — no tiene sentido reintentar
                safe_error = http_resp.text[:300].replace(api_key, '***')
                return {"error": f"Gemini error {http_resp.status_code}: {safe_error}"}, 500

        if not used_model:
            return {"error": "Todos los modelos de Gemini estan saturados. Intenta en 1-2 minutos."}, 503

        print(f'OCR usando modelo: {used_model}')

        gemini_data = http_resp.json()
        if 'error' in gemini_data:
            err = gemini_data['error']
            return {"error": f"Gemini: {err.get('message', str(err))}"}, 500

        raw_text = gemini_data['candidates'][0]['content']['parts'][0]['text'].strip()
        print(f'OCR raw_text preview: {raw_text[:200]}')

        # Limpiar markdown si viene con ```json ... ```
        if '```' in raw_text:
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
            if json_match:
                raw_text = json_match.group(1).strip()

        extracted = json.loads(raw_text)
        result = {k: v for k, v in extracted.items() if v is not None and str(v).strip() not in ('', 'null', 'N/A', 'NA')}

        log_activity('OCR_EJECUTADO', f'Extraccion IA: {len(result)}/{len(campos)} campo(s)')
        return {"status": "success", "data": result}

    except json.JSONDecodeError as e:
        print(f'OCR JSON parse error: {e}. Raw: {raw_text[:400]}')
        return {"error": f"La IA respondio texto no-JSON: {raw_text[:150]}"}, 500
    except Exception as e:
        print(f'OCR Exception: {type(e).__name__}: {e}')
        return {"error": f"{type(e).__name__}: {str(e)}"}, 500



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
    if not report or report.org_id != g.org_id:
        return {"status": "error", "message": "Reporte no encontrado"}, 404
        
    if report.assigned_to_id != g.current_user.id and not g.current_user.is_admin and g.org_role != 'supervisor':
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
    is_super_admin = getattr(g.current_user, 'is_admin', False)
    if not is_super_admin and g.org_role not in ('admin', 'supervisor'):
        return {"error": "Acceso denegado. Solo administradores pueden subir plantillas."}, 403
        
    if 'document' not in request.files:
        return {"error": "No se seleccionó ningún archivo"}, 400
        
    file = request.files['document']
    
    if file.filename == '':
        return {"error": "Archivo sin nombre"}, 400
        
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'docx':
        filename = secure_filename(file.filename)
        from services.storage_service import upload_file_to_r2
        object_key = f"templates/{int(datetime.now().timestamp())}_{filename}"
        ok = upload_file_to_r2(file, object_key)
        if not ok:
            return {"error": "Error al subir el archivo a almacenamiento. Verifica las credenciales de R2."}, 500
        
        nombre = request.form.get('nombre')
        if not nombre: nombre = filename.rsplit('.', 1)[0]
        
        try:
            file.seek(0)
            doc = SmartDocxTemplate(file)
            vars = list(doc.get_undeclared_template_variables())
            vars_json = json.dumps(vars)
        except Exception as ve:
            print(f'Error extrayendo variables de plantilla: {ve}')
            vars_json = "[]"

        new_template = Template(
            nombre=nombre,
            ruta_archivo_docx=object_key,
            uploader_id=g.current_user.id,
            is_public=True,
            variables_json=vars_json,
            org_id=g.org_id
        )
        db.session.add(new_template)
        db.session.commit()
        log_activity('PLANTILLA_CREADA_API', f'Subíó nuevo formato matriz: {nombre}')
        
        return {"status": "success", "id": new_template.id, "nombre": nombre, "variables": json.loads(vars_json)}
    else:
        return {"error": "Formato inválido. Solo se permiten archivos .docx"}, 400

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
    if not g.current_user.is_admin and g.org_role != 'supervisor':
        return {"error": "Acceso denegado"}, 403
        
    template = db.session.get(Template, template_id)
    if not template or template.org_id != g.org_id: return {"error": "No encontrado"}, 404
        
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
    if not getattr(g.current_user, 'is_admin', False) and g.org_role != 'supervisor':
        return {"error": "Unauthorized"}, 403
    logs = ActivityLog.query.filter_by(org_id=g.org_id).order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return {"logs": [{
        "id": l.id,
        "action": l.action,
        "details": l.details,
        "timestamp": getattr(l, 'timestamp').strftime('%Y-%m-%d %H:%M:%S'),
        "user": l.user.email if l.user else 'System'
    } for l in logs]}

