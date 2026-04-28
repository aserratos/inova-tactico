import os
import jwt
import requests
from functools import wraps
from flask import request, jsonify, g
from models import db, User

CLERK_JWKS_URL = "https://saved-spaniel-72.clerk.accounts.dev/.well-known/jwks.json"
CLERK_ISSUER = "https://saved-spaniel-72.clerk.accounts.dev"

# Cache para las llaves públicas
_jwks = None

def get_jwks():
    global _jwks
    if not _jwks:
        response = requests.get(CLERK_JWKS_URL)
        response.raise_for_status()
        _jwks = response.json()
    return _jwks

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': 'No token provided'}), 401

        token = auth_header.split(' ')[1]
        
        try:
            # Obtener el key id (kid) del token
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            if not kid:
                raise ValueError("No kid found in token header")
                
            # Buscar la llave publica correspondiente en el JWKS
            jwks = get_jwks()
            rsa_key = {}
            for key in jwks['keys']:
                if key['kid'] == kid:
                    rsa_key = {
                        'kty': key['kty'],
                        'kid': key['kid'],
                        'use': key['use'],
                        'n': key['n'],
                        'e': key['e']
                    }
                    break
                    
            if not rsa_key:
                raise ValueError("Public key not found in JWKS")
                
            # Convertir el JWK a formato PEM usando pyjwt
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key)
            
            # Verificar el token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={"verify_signature": True, "verify_aud": False},
                issuer=CLERK_ISSUER
            )
            
            # --- Identidad del Usuario ---
            clerk_id = payload.get('sub')

            # --- Organizacion Activa (Multi-tenant) ---
            # Clerk incrusta 'org_id' y 'org_role' en el JWT cuando el usuario
            # tiene una organizacion activa en la sesion.
            g.org_id   = payload.get('org_id')    # ej: "org_2abc123..."
            g.org_role = payload.get('org_role')   # ej: "org:admin", "supervisor", "tecnico"

            # Normalizar el rol quitando el prefijo "org:" si existe
            if g.org_role and g.org_role.startswith('org:'):
                g.org_role = g.org_role.replace('org:', '')

            # Permisos del usuario en la organizacion (lista de strings)
            g.org_permissions = payload.get('org_permissions', [])

            # Buscar o crear al usuario en nuestra base de datos local
            user = User.query.filter_by(clerk_id=clerk_id).first()
            if not user:
                email = None
                clerk_secret = os.environ.get('CLERK_SECRET_KEY')
                if clerk_secret:
                    from clerk_backend_api import Clerk
                    try:
                        clerk_client = Clerk(bearer_auth=clerk_secret)
                        clerk_user = clerk_client.users.get(clerk_id)
                        if clerk_user.email_addresses:
                            email = clerk_user.email_addresses[0].email_address
                    except Exception as e:
                        print("Error fetch clerk user:", e)
                
                if not email:
                    email = payload.get('email') or f"{clerk_id}@clerk.dev"
                
                user = User.query.filter_by(email=email).first()
                if user:
                    user.clerk_id = clerk_id
                    db.session.commit()
                else:
                    user = User(
                        email=email,
                        clerk_id=clerk_id,
                        role='tecnico'
                    )
                    db.session.add(user)
                    db.session.commit()
                
            g.current_user = user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired'}), 401
        except Exception as e:
            print(f"Token verification error: {e}")
            return jsonify({'status': 'error', 'message': f'Invalid token: {e}'}), 401
            
        return f(*args, **kwargs)
        
    return decorated


def require_permission(permission):
    """Decorador adicional para validar permisos especificos de Clerk.

    Uso:
        @require_auth
        @require_permission('manage_plantillas')
        def mi_endpoint(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            org_perms = getattr(g, 'org_permissions', [])
            org_role  = getattr(g, 'org_role', '')
            # El admin de la org siempre tiene acceso total
            if org_role == 'admin':
                return f(*args, **kwargs)
            if permission not in org_perms:
                return jsonify({
                    'status': 'error',
                    'message': f'Permiso requerido: {permission}'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
