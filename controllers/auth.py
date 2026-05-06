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
        'sub': str(user.id),
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
    u = g.current_user
    return jsonify({
        'user': {
            'id': u.id,
            'email': u.email,
            'nombre_completo': u.nombre_completo,
            'puesto': u.puesto,
            'telefono': u.telefono,
            'role': u.role,
            'org_id': u.org_id
        }
    })

@auth_bp.route('/api/auth/profile', methods=['POST'])
@require_auth
def update_profile():
    data = request.json or {}
    u = g.current_user
    if 'nombre_completo' in data:
        u.nombre_completo = data['nombre_completo'].strip()
    if 'puesto' in data:
        u.puesto = data['puesto'].strip()
    if 'telefono' in data:
        u.telefono = data['telefono'].strip()
    db.session.commit()
    return jsonify({
        'status': 'success',
        'user': {
            'id': u.id,
            'email': u.email,
            'nombre_completo': u.nombre_completo,
            'puesto': u.puesto,
            'telefono': u.telefono,
            'role': u.role,
            'org_id': u.org_id
        }
    })

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    data = request.json or {}
    current_pwd = data.get('current_password', '')
    new_pwd = data.get('new_password', '')

    if not current_pwd or not new_pwd:
        return jsonify({'error': 'Se requieren la contraseña actual y la nueva.'}), 400

    u = g.current_user
    if not u.check_password(current_pwd):
        return jsonify({'error': 'La contraseña actual es incorrecta.'}), 401

    if len(new_pwd) < 8:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 8 caracteres.'}), 400

    u.set_password(new_pwd)
    db.session.commit()
    return jsonify({'status': 'success'})


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
