import os
import re
import json
from datetime import datetime
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from flask import url_for
from models import db, ReportInstance, ActivityLog, log_activity, Notification

class SmartDocxTemplate(DocxTemplate):
    def patch_xml(self, src_xml):
        patched = super().patch_xml(src_xml)
        def replace_spaces(match):
            inner_content = match.group(1).strip().lower()
            fixed_content = re.sub(r'\W+', '_', inner_content).strip('_')
            fixed_content = re.sub(r'_+', '_', fixed_content)
            return '{{ ' + fixed_content + ' }}'
        patched = re.sub(r'\{\{(.*?)\}\}', replace_spaces, patched, flags=re.DOTALL)
        return patched

    @staticmethod
    def is_image_var(name):
        norm_name = name.lower().strip('_')
        prefixes = ('foto_', 'imagen_', 'img_', 'pic_')
        suffixes = ('_foto', '_imagen', '_img', '_pic')
        return any(norm_name.startswith(p) for p in prefixes) or any(norm_name.endswith(s) for s in suffixes)

def format_date_spanish(date_str):
    if not date_str: return ""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except:
        return date_str

def background_compile_task(app, instance_id, user_id):
    with app.app_context():
        report = db.session.get(ReportInstance, instance_id)
        if not report: return
        
        try:
            from services.storage_service import download_file_from_r2, upload_file_to_r2
            import io
            
            # 1. Obtener la plantilla (Local o R2)
            template_path = report.template.ruta_archivo_docx
            if os.path.exists(template_path):
                doc = SmartDocxTemplate(template_path)
            else:
                template_stream = download_file_from_r2(template_path)
                if not template_stream:
                    raise Exception(f"Plantilla no encontrada en R2: {template_path}")
                doc = SmartDocxTemplate(template_stream)
            
            data = json.loads(report.data_json or '{}')
            context = {}
            
            for var, value in data.items():
                if SmartDocxTemplate.is_image_var(var):
                    if value:
                        # 2. Obtener la imagen (Local o R2)
                        if os.path.exists(value):
                            upload_dir = os.path.abspath(os.path.join(app.root_path, 'plantillas', 'borradores'))
                            if os.path.abspath(value).startswith(upload_dir):
                                context[var] = InlineImage(doc, value, width=Mm(160))
                            else:
                                context[var] = ""
                        else:
                            # Try R2
                            image_stream = download_file_from_r2(value)
                            if image_stream:
                                context[var] = InlineImage(doc, image_stream, width=Mm(160))
                            else:
                                context[var] = ""
                    else:
                        context[var] = ""
                else:
                    if "FECHA" in var.upper() or "DATE" in var.upper():
                        context[var] = format_date_spanish(value)
                    else:
                        context[var] = value
                    
            doc.render(context)
            
            # 3. Guardar el DOCX final en memoria RAM y subir a R2
            doc_stream = io.BytesIO()
            doc.save(doc_stream)
            
            filename = f"Reporte_{report.id}_{int(datetime.now().timestamp())}.docx"
            object_key = f"compilados/{filename}"
            
            upload_file_to_r2(doc_stream, object_key)
            
            report.archivo_compilado_path = object_key
            
            log_activity('REPORTE_COMPILADO', f'Generó DOCX Final de: {report.nombre}', user_id=user_id)
            
            notif = Notification(
                user_id=user_id,
                title="Reporte Listo",
                message=f"El documento '{report.nombre}' ha terminado de compilarse.",
                type="success",
                link=url_for('templates.download_compiled_report', instance_id=report.id)
            )
            db.session.add(notif)
            db.session.commit()
            
        except Exception as e:
            notif = Notification(
                user_id=user_id,
                title="Error de Compilación",
                message=f"Error al compilar '{report.nombre}': {str(e)}",
                type="error"
            )
            db.session.add(notif)
            db.session.commit()
