import datetime
import jwt
from flask import Blueprint, request, jsonify, current_app, g
from models import db, User, Organization
from controllers.auth_middleware import require_auth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciales inválidas'}), 401
        
    if not user.is_active:
        return jsonify({'error': 'Cuenta inactiva'}), 401

    payload = {
        'sub': user.id,
        'email': user.email,
        'org_id': user.org_id,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'nombre_completo': user.nombre_completo,
            'role': user.role,
            'org_id': user.org_id
        }
    })

@auth_bp.route('/api/auth/me', methods=['GET'])
@require_auth
def me():
    return jsonify({
        'user': {
            'id': g.current_user.id,
            'email': g.current_user.email,
            'nombre_completo': g.current_user.nombre_completo,
            'role': g.current_user.role,
            'org_id': g.current_user.org_id
        }
    })

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    # Solo para crear el primer superadmin o si permitimos auto-registro.
    # En un SaaS real, podrías limitar esto o requerir invitación.
    data = request.json
    email = data.get('email')
    password = data.get('password')
    org_name = data.get('org_name')
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'El correo ya está registrado'}), 400
        
    # Crear Organización
    org = Organization(nombre=org_name or "Mi Organización")
    db.session.add(org)
    db.session.flush() # Para obtener org.id
    
    # Crear Usuario Admin de la org
    user = User(
        email=email,
        org_id=org.id,
        role='admin',
        is_admin=True # Primer usuario puede ser superadmin del sistema
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Cuenta creada. Por favor inicia sesión.'})
