import json
from flask import Blueprint, jsonify, request, g
from models import db, Template, ReportInstance, ActivityLog, log_activity, Notification
from controllers.auth_middleware import require_auth
from services.report_service import save_report_logic

pwa_api_bp = Blueprint('pwa_api', __name__)

@pwa_api_bp.route('/api/templates', methods=['GET'])
@require_auth
def get_templates():
    templates = Template.query.filter_by(org_id=g.org_id).all()
    return jsonify({
        "templates": [{"id": t.id, "nombre": t.nombre} for t in templates]
    })

@pwa_api_bp.route('/api/customers', methods=['GET'])
@require_auth
def get_customers_for_selector():
    """Directorio de clientes accesible para todos los miembros de la org (para el selector al iniciar reporte)."""
    from models import Customer
    customers = Customer.query.filter_by(org_id=g.org_id).order_by(Customer.nombre_empresa).all()
    return jsonify({
        "customers": [{
            "id": c.id,
            "nombre_empresa": c.nombre_empresa,
            "rfc": c.rfc,
            "contacto_principal": c.contacto_principal,
            "erp_source": c.erp_source,
        } for c in customers]
    })


@pwa_api_bp.route('/api/reports', methods=['GET'])
@require_auth
def get_reports():
    if g.org_role in ['admin', 'supervisor']:
        reports = ReportInstance.query.filter_by(org_id=g.org_id).all()
    elif g.org_role == 'cliente':
        # Clients only see their own finished reports
        if not g.current_user.customer_id:
            reports = []
        else:
            reports = ReportInstance.query.filter_by(
                org_id=g.org_id, 
                customer_id=g.current_user.customer_id,
                status='terminado'
            ).all()
    else:
        # Tecnicos see their assigned or created reports
        reports = ReportInstance.query.filter_by(org_id=g.org_id).filter(
            (ReportInstance.assigned_to_id == g.current_user.id) | 
            (ReportInstance.created_by_id == g.current_user.id)
        ).all()
        
    return jsonify({
        "reports": [{
            "id": r.id,
            "nombre": r.nombre,
            "status": r.status,
            "porcentaje_avance": r.porcentaje_avance,
            "template_name": r.template.nombre if r.template else "Sin plantilla",
            "assigned_to_id": r.assigned_to_id,
            "created_by_id": r.created_by_id,
            "comentarios": r.comentarios,
            "archivo_compilado_path": r.archivo_compilado_path if r.status == 'terminado' else None,
            "fecha_actualizacion": r.fecha_actualizacion.strftime('%d %b %Y, %H:%M') if r.fecha_actualizacion else None
        } for r in reports]
    })

@pwa_api_bp.route('/api/report/start/<int:template_id>', methods=['POST'])
@require_auth
def start_report(template_id):
    from models import Customer
    template = db.session.get(Template, template_id)
    if not template or template.org_id != g.org_id:
        return jsonify({"error": "Plantilla no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    customer_id = data.get('customer_id')
    customer_data = {}

    # Validar que el cliente pertenece a esta org
    if customer_id:
        customer = Customer.query.filter_by(id=customer_id, org_id=g.org_id).first()
        if customer:
            customer_data = {
                "nombre_empresa": customer.nombre_empresa or '',
                "rfc": customer.rfc or '',
                "contacto_principal": customer.contacto_principal or '',
                "cliente": customer.nombre_empresa or '',      # alias comun en plantillas
                "empresa": customer.nombre_empresa or '',     # alias comun en plantillas
            }
        else:
            customer_id = None  # ignorar si no pertenece a la org

    report_nombre = f"Reporte de {template.nombre}"
    if customer_data.get('nombre_empresa'):
        report_nombre += f" — {customer_data['nombre_empresa']}"

    report = ReportInstance(
        org_id=g.org_id,
        template_id=template.id,
        nombre=report_nombre,
        created_by_id=g.current_user.id,
        assigned_to_id=g.current_user.id,
        customer_id=customer_id
    )
    db.session.add(report)
    db.session.commit()
    log_activity('REPORTE_INICIADO', f'Inició reporte desde PWA: {report.nombre}')
    return jsonify({"status": "success", "id": report.id, "customer_data": customer_data})

@pwa_api_bp.route('/api/report/sync_offline_create', methods=['POST'])
@require_auth
def sync_offline_create():
    """Crea un reporte que fue iniciado y guardado estando offline."""
    from models import Customer
    template_id = request.form.get('_template_id')
    customer_id = request.form.get('_customer_id')

    if not template_id:
        return jsonify({"error": "Falta el ID de plantilla"}), 400

    template = db.session.get(Template, int(template_id))
    if not template or template.org_id != g.org_id:
        return jsonify({"error": "Plantilla no encontrada"}), 404

    customer_data = {}
    if customer_id and customer_id != 'null':
        customer = Customer.query.filter_by(id=int(customer_id), org_id=g.org_id).first()
        if customer:
            customer_data = {"nombre_empresa": customer.nombre_empresa or ''}

    report_nombre = f"Reporte de {template.nombre}"
    if customer_data.get('nombre_empresa'):
        report_nombre += f" — {customer_data['nombre_empresa']}"

    report = ReportInstance(
        org_id=g.org_id,
        template_id=template.id,
        nombre=report_nombre,
        created_by_id=g.current_user.id,
        assigned_to_id=g.current_user.id,
        customer_id=int(customer_id) if customer_id and customer_id != 'null' else None
    )
    db.session.add(report)
    db.session.flush() # Obtener ID para save_report_logic

    # Ahora guardamos los datos (el payload incluía los datos del form igual que save)
    save_report_logic(report, request, g.current_user)
    
    db.session.commit()
    log_activity('REPORTE_SYNC_OFFLINE', f'Sincronizó reporte offline: {report.nombre} (ID: {report.id})')
    
    return jsonify({
        "status": "success",
        "id": report.id,
        "porcentaje_avance": report.porcentaje_avance,
        "status_actual": report.status
    })


@pwa_api_bp.route('/api/report/<int:instance_id>', methods=['GET'])
@require_auth
def get_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "Reporte no encontrado"}), 404

    # Verificar acceso: admin/supervisor ven todo; técnico solo los suyos
    if g.org_role not in ('admin', 'supervisor') and not g.current_user.is_admin:
        if report.created_by_id != g.current_user.id and report.assigned_to_id != g.current_user.id:
            return jsonify({"error": "No tienes acceso a este reporte"}), 403

    variables = json.loads(report.template.variables_json or '[]') if report.template else []
    saved_data = json.loads(report.data_json or '{}')

    from services.document_service import SmartDocxTemplate
    text_vars = [v for v in variables if not SmartDocxTemplate.is_image_var(v)]
    image_vars = [v for v in variables if SmartDocxTemplate.is_image_var(v)]

    return jsonify({
        "id": report.id,
        "nombre": report.nombre,
        "status": report.status,
        "template_name": report.template.nombre if report.template else "Sin plantilla",
        "text_vars": text_vars,
        "image_vars": image_vars,
        "saved_data": saved_data,
        "comentarios": report.comentarios,
        "porcentaje_avance": report.porcentaje_avance,
        "assigned_to_id": report.assigned_to_id,
    })


@pwa_api_bp.route('/api/report/save/<int:instance_id>', methods=['POST'])
@require_auth
def save_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "Reporte no encontrado"}), 404
        
    save_report_logic(report, request, g.current_user)
    db.session.commit()
    log_activity('REPORTE_GUARDADO', f'Guardó progreso de reporte ID-{report.id}')
    return jsonify({
        "status": "success",
        "porcentaje_avance": report.porcentaje_avance,
        "status_actual": report.status
    })

@pwa_api_bp.route('/api/report/<int:instance_id>/media/<path:var_name>', methods=['GET'])
@require_auth
def get_report_media(instance_id, var_name):
    """Devuelve una URL pre-firmada de R2 para una imagen de un reporte."""
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "No encontrado"}), 404

    saved = json.loads(report.data_json or '{}')
    object_key = saved.get(var_name)
    if not object_key:
        return jsonify({"error": "Imagen no encontrada"}), 404

    from services.storage_service import get_presigned_url
    url = get_presigned_url(object_key, expiration=600)  # 10 minutos
    if not url:
        return jsonify({"error": "No se pudo generar URL"}), 500

    from flask import redirect
    return redirect(url)

@pwa_api_bp.route('/api/report/clone/<int:instance_id>', methods=['POST'])
@require_auth
def clone_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "Reporte no encontrado"}), 404

    new_report = ReportInstance(
        org_id=g.org_id,
        template_id=report.template_id,
        nombre=f"{report.nombre} (Clon)",
        created_by_id=g.current_user.id,
        assigned_to_id=g.current_user.id,
        customer_id=report.customer_id,
        data_json=report.data_json,
        porcentaje_avance=report.porcentaje_avance,
        status='por_hacer'
    )
    
    db.session.add(new_report)
    db.session.commit()
    
    log_activity('REPORTE_CLONADO', f'Reporte original ID-{report.id} clonado como ID-{new_report.id}')
    
    return jsonify({
        "status": "success",
        "new_id": new_report.id
    })

@pwa_api_bp.route('/api/report/compile/<int:instance_id>', methods=['POST'])
@require_auth
def compile_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "Reporte no encontrado"}), 404

    if report.status != 'terminado':
        return jsonify({"error": "El reporte debe estar terminado para compilarlo."}), 400

    from services.document_service import background_compile_task
    from extensions import executor
    
    # Run in background to avoid blocking
    executor.submit(background_compile_task, current_app._get_current_object(), instance_id, g.current_user.id)
    
    return jsonify({"status": "success", "message": "Compilación iniciada en segundo plano"})

@pwa_api_bp.route('/api/report/download/<int:instance_id>', methods=['GET'])
@require_auth
def download_compiled_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "Reporte no encontrado"}), 404
        
    if not report.archivo_compilado_path:
        return jsonify({"error": "El documento aún no ha sido compilado."}), 400
        
    from services.storage_service import get_presigned_url
    url = get_presigned_url(report.archivo_compilado_path, expiration=3600)
    
    if not url:
        return jsonify({"error": "Error al generar link de descarga."}), 500
        
    return jsonify({"url": url})
