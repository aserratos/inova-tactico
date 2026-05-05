import os
import jwt
from functools import wraps
from flask import request, jsonify, g, current_app
from models import db, User

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': 'No token provided'}), 401

        token = auth_header.split(' ')[1]
        secret_key = current_app.config['SECRET_KEY']
        
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            user_id = payload.get('sub')
            
            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                return jsonify({'status': 'error', 'message': 'User not found or inactive'}), 401
                
            g.current_user = user
            g.org_id = user.org_id
            g.org_role = user.role # 'admin', 'supervisor', 'tecnico'
            
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'status': 'error', 'message': f'Invalid token: {e}'}), 401
            
        return f(*args, **kwargs)
        
    return decorated

def require_permission(permission):
    """
    Simula los permisos de Clerk basados en el role local.
    Roles:
      - admin: todo
      - supervisor: manage_plantillas, manage_users, etc
      - tecnico: create_reportes
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            org_role = getattr(g, 'org_role', '')
            
            # El admin de la org siempre tiene acceso total
            if org_role == 'admin' or g.current_user.is_admin:
                return f(*args, **kwargs)
                
            # Mapeo simple de permisos
            role_permissions = {
                'supervisor': ['manage_plantillas', 'view_reports', 'create_reportes'],
                'tecnico': ['create_reportes']
            }
            
            user_perms = role_permissions.get(org_role, [])
            
            if permission not in user_perms:
                return jsonify({
                    'status': 'error',
                    'message': f'Permiso requerido: {permission}'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
