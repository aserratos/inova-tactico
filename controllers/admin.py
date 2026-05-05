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
            "is_active": u.is_active,
            "org_nombre": u.org.nombre if u.org else "N/A"
        } for u in users]
    })

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
        is_active=True
    )
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
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
