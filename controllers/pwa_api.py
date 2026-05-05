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

@pwa_api_bp.route('/api/reports', methods=['GET'])
@require_auth
def get_reports():
    if g.org_role in ['admin', 'supervisor']:
        reports = ReportInstance.query.filter_by(org_id=g.org_id).all()
    else:
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
            "comentarios": r.comentarios
        } for r in reports]
    })

@pwa_api_bp.route('/api/report/start/<int:template_id>', methods=['POST'])
@require_auth
def start_report(template_id):
    template = db.session.get(Template, template_id)
    if not template or template.org_id != g.org_id:
        return jsonify({"error": "Plantilla no encontrada"}), 404
        
    report = ReportInstance(
        org_id=g.org_id,
        template_id=template.id,
        nombre=f"Reporte de {template.nombre} - Nuevo",
        created_by_id=g.current_user.id,
        assigned_to_id=g.current_user.id
    )
    db.session.add(report)
    db.session.commit()
    log_activity('REPORTE_INICIADO', f'Inició reporte desde PWA: {report.nombre}')
    return jsonify({"status": "success", "id": report.id})

@pwa_api_bp.route('/api/report/<int:instance_id>', methods=['GET'])
@require_auth
def get_report(instance_id):
    report = db.session.get(ReportInstance, instance_id)
    if not report or report.org_id != g.org_id:
        return jsonify({"error": "Reporte no encontrado"}), 404
        
    variables = json.loads(report.template.variables_json) if report.template.variables_json else []
    data_json = json.loads(report.data_json) if report.data_json else {}
    
    return jsonify({
        "report": {
            "id": report.id,
            "nombre": report.nombre,
            "status": report.status,
            "comentarios": report.comentarios,
            "assigned_to_id": report.assigned_to_id
        },
        "template": {
            "id": report.template.id,
            "nombre": report.template.nombre,
            "variables": variables
        },
        "data": data_json
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
    return jsonify({"status": "success"})
