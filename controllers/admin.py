from flask import Blueprint, request, jsonify, g
from models import db, User, Organization
from controllers.auth_middleware import require_auth

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/organizations', methods=['GET'])
@require_auth
def get_organizations():
    if not getattr(g.current_user, 'is_admin', False):
        return jsonify({"error": "Unauthorized"}), 403
        
    orgs = Organization.query.all()
    return jsonify({
        "organizations": [{
            "id": o.id,
            "nombre": o.nombre,
            "created_at": o.created_at.strftime('%Y-%m-%d') if o.created_at else None
        } for o in orgs]
    })

@admin_bp.route('/api/admin/organizations', methods=['POST'])
@require_auth
def create_organization():
    if not getattr(g.current_user, 'is_admin', False):
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    nombre = data.get('nombre')
    
    if not nombre:
        return jsonify({"error": "El nombre es requerido"}), 400
        
    org = Organization(nombre=nombre)
    db.session.add(org)
    db.session.commit()
    
    return jsonify({"status": "success", "id": org.id})

@admin_bp.route('/api/admin/users', methods=['GET'])
@require_auth
def get_users():
    is_super_admin = getattr(g.current_user, 'is_admin', False)
    if not is_super_admin and g.org_role not in ['admin', 'supervisor']:
        return jsonify({"error": "Unauthorized"}), 403
        
    if is_super_admin:
        users = User.query.all()
    else:
        users = User.query.filter_by(org_id=g.org_id).all()
        
    return jsonify({
        "users": [{
            "id": u.id,
            "email": u.email,
            "nombre_completo": u.nombre_completo,
            "role": u.role,
            "org_id": u.org_id,
            "customer_id": u.customer_id,
            "is_active": u.is_active,
            "org_nombre": u.org.nombre if u.org else "N/A",
            "customer_nombre": u.customer.nombre_empresa if u.customer else "N/A"
        } for u in users]
    })

@admin_bp.route('/api/admin/customers', methods=['GET'])
@require_auth
def get_customers():
    is_super_admin = getattr(g.current_user, 'is_admin', False)
    if not is_super_admin and g.org_role not in ['admin', 'supervisor']:
        return jsonify({"error": "Unauthorized"}), 403
        
    if is_super_admin:
        customers = db.session.query(db.Model._decl_class_registry.get('Customer', None)).all() # Safe fallback if imported
        from models import Customer
        customers = Customer.query.all()
    else:
        from models import Customer
        customers = Customer.query.filter_by(org_id=g.org_id).all()
        
    return jsonify({
        "customers": [{
            "id": c.id,
            "nombre_empresa": c.nombre_empresa,
            "contacto_principal": c.contacto_principal,
            "rfc": c.rfc,
            "external_erp_id": c.external_erp_id,
            "erp_source": c.erp_source,
            "created_at": c.created_at.strftime('%Y-%m-%d') if c.created_at else None
        } for c in customers]
    })

@admin_bp.route('/api/admin/customers', methods=['POST'])
@require_auth
def create_customer():
    is_super_admin = getattr(g.current_user, 'is_admin', False)
    if not is_super_admin and g.org_role not in ['admin', 'supervisor']:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    nombre_empresa = data.get('nombre_empresa')
    
    if not nombre_empresa:
        return jsonify({"error": "El nombre de la empresa es requerido"}), 400
        
    from models import Customer
    # Fallback a g.org_id si is_super_admin es verdadero pero no se envio org_id
    org_id = data.get('org_id') or g.org_id if is_super_admin else g.org_id
    
    customer = Customer(
        org_id=org_id,
        nombre_empresa=nombre_empresa,
        contacto_principal=data.get('contacto_principal'),
        rfc=data.get('rfc')
    )
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({"status": "success", "id": customer.id})

@admin_bp.route('/api/admin/users', methods=['POST'])
@require_auth
def create_user():
    is_super_admin = getattr(g.current_user, 'is_admin', False)
    if not is_super_admin and g.org_role not in ['admin', 'supervisor']:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'tecnico')
    nombre_completo = data.get('nombre_completo', '')
    customer_id = data.get('customer_id')
    
    org_id = data.get('org_id') if is_super_admin else g.org_id
    if not org_id:
        return jsonify({"error": "org_id es requerido"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El correo ya existe"}), 400
        
    new_user = User(
        email=email,
        role=role,
        nombre_completo=nombre_completo,
        org_id=org_id,
        customer_id=customer_id if role == 'cliente' else None,
        is_active=True
    )
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    # Enviar correo de bienvenida con contraseña temporal
    from services.notification_service import send_welcome_email
    send_welcome_email(new_user, password)
    
    return jsonify({"status": "success", "id": new_user.id})

@admin_bp.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
@require_auth
def toggle_user(user_id):
    is_super_admin = getattr(g.current_user, 'is_admin', False)
    if not is_super_admin and g.org_role not in ['admin', 'supervisor']:
        return jsonify({"error": "Unauthorized"}), 403
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if not is_super_admin and user.org_id != g.org_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    # Prevent disabling yourself
    if user.id == g.current_user.id:
        return jsonify({"error": "No puedes desactivar tu propia cuenta"}), 400

    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({"status": "success", "is_active": user.is_active})
