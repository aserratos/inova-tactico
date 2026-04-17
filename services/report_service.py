import os
import json
from werkzeug.utils import secure_filename
from flask import current_app, url_for
from models import db, Notification, log_activity
from services.document_service import SmartDocxTemplate

def save_report_logic(report, req, current_user):
    new_nombre = req.form.get('_report_name')
    if new_nombre: report.nombre = new_nombre
    
    new_comentarios = req.form.get('_comentarios')
    if new_comentarios is not None:
        report.comentarios = new_comentarios

    current_data = json.loads(report.data_json or '{}')
    
    if report.template.variables_json:
        variables = json.loads(report.template.variables_json)
    else:
        doc = SmartDocxTemplate(report.template.ruta_archivo_docx)
        try:
            variables = list(doc.get_undeclared_template_variables())
            report.template.variables_json = json.dumps(variables)
            db.session.commit()
        except Exception as e:
            variables = []
        
    filled_count = 0
    for var in variables:
        if not SmartDocxTemplate.is_image_var(var):
            val = req.form.get(var, '')
            current_data[var] = val
            if val and str(val).strip(): filled_count += 1
        else:
            file = req.files.get(var)
            if file and file.filename != '':
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext not in ['jpg', 'jpeg', 'png', 'heic', 'gif']:
                    continue
                filename = secure_filename(f"inst_{report.id}_{var}_{file.filename}")
                from services.storage_service import upload_file_to_r2
                object_key = f"media/inst_{report.id}/{filename}"
                upload_file_to_r2(file, object_key)
                current_data[var] = object_key # Guardamos la llave de R2
                filled_count += 1
            elif current_data.get(var):
                filled_count += 1
                
    report.data_json = json.dumps(current_data)
    
    report.campos_llenados = filled_count
    if len(variables) > 0:
        report.porcentaje_avance = int((filled_count / len(variables)) * 100)
    else:
        report.porcentaje_avance = 0
    report.total_campos = len(variables)
    
    if report.status == 'por_hacer' and report.porcentaje_avance > 0 and report.porcentaje_avance < 100:
        report.status = 'en_ejecucion'
        log_activity('OPERACION_ACTUALIZADA', f'El reporte avanzó automáticamente a "En Ejecución" ({report.porcentaje_avance}%)')

    if report.status in ['por_hacer', 'en_ejecucion', 'pendiente'] and report.porcentaje_avance == 100:
        report.status = 'terminado'
        log_activity('OPERACION_ACTUALIZADA', f'El reporte avanzó automáticamente a "Completados" ({report.porcentaje_avance}%)')

    new_assignee = req.form.get('_assigned_to')
    if new_assignee: 
        new_assignee_id = int(new_assignee)
        if report.assigned_to_id != new_assignee_id:
            notif = Notification(
                user_id=new_assignee_id,
                title="Nueva Asignación",
                message=f"Se te ha asignado el levantamiento: {report.nombre}",
                type="assignment",
                link=url_for('templates.edit_report', instance_id=report.id)
            )
            db.session.add(notif)
            report.assigned_to_id = new_assignee_id
    
    new_status = req.form.get('_status')
    if new_status: 
        if report.status != new_status and new_status == 'terminado':
            if report.created_by_id != current_user.id:
                notif = Notification(
                    user_id=report.created_by_id,
                    title="Misión Completada",
                    message=f"El reporte '{report.nombre}' ha sido marcado como terminado.",
                    type="success",
                    link=url_for('templates.edit_report', instance_id=report.id)
                )
                db.session.add(notif)
        report.status = new_status
