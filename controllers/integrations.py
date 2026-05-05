import xmlrpc.client
import socket
from flask import Blueprint, jsonify, request, g
from models import db, Organization, Customer
from controllers.auth_middleware import require_auth

ODOO_TIMEOUT = 15  # segundos

def _odoo_proxy(url, path):
    """Crea un ServerProxy con timeout configurado."""
    transport = xmlrpc.client.SafeTransport()
    transport._connection = (None, None)
    full_url = '{}/{}'.format(url.rstrip('/'), path)
    # Usar context para SSL y timeout manual via socket
    import http.client
    class TimeoutSafeTransport(xmlrpc.client.SafeTransport):
        def make_connection(self, host):
            conn = xmlrpc.client.SafeTransport.make_connection(self, host)
            conn.timeout = ODOO_TIMEOUT
            return conn
    return xmlrpc.client.ServerProxy(full_url, transport=TimeoutSafeTransport())

integrations_bp = Blueprint('integrations', __name__)

@integrations_bp.route('/api/admin/integrations/odoo', methods=['GET', 'POST'])
@require_auth
def manage_odoo_config():
    if not getattr(g.current_user, 'is_admin', False) and g.org_role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    org = Organization.query.get(g.org_id)
    if not org:
        return jsonify({"error": "Organización no encontrada"}), 404

    if request.method == 'GET':
        return jsonify({
            "config": {
                "erp_url": org.erp_url,
                "erp_db": org.erp_db,
                "erp_username": org.erp_username,
                "erp_api_key": "exists" if org.erp_api_key else ""
            }
        })
        
    if request.method == 'POST':
        data = request.json
        org.erp_url = data.get('erp_url', org.erp_url)
        org.erp_db = data.get('erp_db', org.erp_db)
        org.erp_username = data.get('erp_username', org.erp_username)
        # Only update password/API key if a new one is provided and not masked
        new_key = data.get('erp_api_key')
        if new_key and new_key != '********':
            org.erp_api_key = new_key
            
        db.session.commit()
        return jsonify({"status": "success"})

@integrations_bp.route('/api/admin/integrations/odoo/test', methods=['POST'])
@require_auth
def test_odoo_connection():
    if not getattr(g.current_user, 'is_admin', False) and g.org_role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    org = Organization.query.get(g.org_id)
    if not org:
        return jsonify({"error": "Organización no encontrada"}), 404

    if not org.erp_url or not org.erp_db or not org.erp_username or not org.erp_api_key:
        return jsonify({"error": "Faltan credenciales. Guarda la configuración primero."}), 400

    try:
        common = _odoo_proxy(org.erp_url, 'xmlrpc/2/common')
        # Primero verificar que el servidor responde
        try:
            version = common.version()
            odoo_version = version.get('server_version', 'unknown')
        except socket.timeout:
            return jsonify({"error": "Timeout: Odoo tardó demasiado en responder (>15s). Verifica la URL."}), 504
        except Exception as ve:
            return jsonify({"error": f"El servidor Odoo no responde: {str(ve)}"}), 502

        # Autenticar
        try:
            uid = common.authenticate(org.erp_db, org.erp_username, org.erp_api_key, {})
        except socket.timeout:
            return jsonify({"error": "Timeout durante autenticación."}), 504
        except Exception as ae:
            return jsonify({"error": f"Error en autenticación: {str(ae)}"}), 502

        if not uid:
            return jsonify({"error": "Credenciales incorrectas. Verifica el email de usuario y la API Key."}), 401

        return jsonify({"status": "connected", "uid": uid, "odoo_version": odoo_version})
    except Exception as e:
        import traceback
        print('Odoo Test Error:', traceback.format_exc())
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

@integrations_bp.route('/api/integrations/odoo/sync', methods=['POST'])
@require_auth
def sync_odoo_customers():
    # Solo administradores de la organizacion o super admins
    if not getattr(g.current_user, 'is_admin', False) and g.org_role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    # Obtener el org_id
    org_id = request.json.get('org_id')
    if not org_id:
        org_id = g.org_id
        
    org = Organization.query.get(org_id)
    if not org:
        return jsonify({"error": "Organización no encontrada"}), 404
        
    if not org.erp_url or not org.erp_db or not org.erp_username or not org.erp_api_key:
        return jsonify({"error": "La configuración de Odoo está incompleta para esta organización. Revisa los ajustes."}), 400

    try:
        # Autenticar
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(org.erp_url))
        uid = common.authenticate(org.erp_db, org.erp_username, org.erp_api_key, {})
        
        if not uid:
            return jsonify({"error": "Error de autenticación con Odoo. Verifica credenciales."}), 401
            
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(org.erp_url))
        
        # Buscar "partners" que son empresas y clientes
        partners = models.execute_kw(org.erp_db, uid, org.erp_api_key,
            'res.partner', 'search_read',
            [[('is_company', '=', True)]],
            {'fields': ['name', 'vat', 'email', 'phone']}
        )
        
        sync_count = 0
        for p in partners:
            external_id = str(p.get('id'))
            name = p.get('name')
            vat = p.get('vat') or ''
            email = p.get('email') or ''
            
            # Revisar si ya existe este cliente
            existing = Customer.query.filter_by(org_id=org.id, external_erp_id=external_id).first()
            if not existing:
                # Intentar buscar por RFC si no hay external ID (evitar duplicados manuales)
                if vat:
                    existing = Customer.query.filter_by(org_id=org.id, rfc=vat).first()
            
            if existing:
                # Actualizar datos
                existing.nombre_empresa = name
                if vat:
                    existing.rfc = vat
                existing.contacto_principal = email
                existing.external_erp_id = external_id
                existing.erp_source = 'odoo'
            else:
                # Crear nuevo
                new_cust = Customer(
                    org_id=org.id,
                    nombre_empresa=name,
                    rfc=vat,
                    contacto_principal=email,
                    external_erp_id=external_id,
                    erp_source='odoo'
                )
                db.session.add(new_cust)
                
            sync_count += 1
            
        db.session.commit()
        return jsonify({"status": "success", "synced_count": sync_count, "message": f"Se sincronizaron {sync_count} clientes de Odoo exitosamente."})
        
    except Exception as e:
        db.session.rollback()
        print("Error Odoo Sync:", str(e))
        return jsonify({"error": f"Error al conectar con Odoo: {str(e)}"}), 500
