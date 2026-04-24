from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import pyotp
import secrets
from datetime import datetime, timedelta, timezone
from models import User, ActivityLog, db, log_activity

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if session.get('mfa_verified'):
            return redirect(url_for('templates.dashboard'))
        else:
            return redirect(url_for('auth.mfa'))
            
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Credenciales incorrectas.', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.is_active:
            flash('Cuenta desactivada. Contacte al administrador.', 'error')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        session['mfa_verified'] = False
        log_activity('LOGIN', 'Inicio de sesión temporal previo a MFA')
        
        return redirect(url_for('auth.mfa'))
            
    return render_template('auth/login.html')

@auth_bp.route('/mfa', methods=['GET', 'POST'])
@login_required
def mfa():
    if session.get('mfa_verified'):
        return redirect(url_for('templates.dashboard'))
        
    if request.method == 'POST':
        token = request.form.get('token')
        
        if not current_user.mfa_secret:
            flash('Seguridad MFA no configurada para este usuario.', 'error')
            return redirect(url_for('auth.login'))
            
        totp = pyotp.TOTP(current_user.mfa_secret)
        if totp.verify(token):
            session['mfa_verified'] = True
            log_activity('LOGIN_MFA', 'Superó verificación MFA 2FA')
            return redirect(url_for('templates.dashboard'))
        else:
            flash('Código MFA inválido. Inténtalo de nuevo.', 'error')
            
    return render_template('auth/mfa.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity('LOGOUT', 'Cierre de sesión manual')
    logout_user()
    session.pop('mfa_verified', None)
    return redirect(url_for('auth.login'))

# --- 🔌 API DE AUTENTICACIÓN PWA ---

@auth_bp.route('/api/session', methods=['GET'])
def api_check_session():
    if current_user.is_authenticated:
        return {
            "authenticated": True,
            "mfa_verified": session.get('mfa_verified', False),
            "user": {
                "email": current_user.email,
                "nombre": current_user.nombre_completo or current_user.email,
                "rol": current_user.role,
                "is_admin": current_user.is_admin
            }
        }
    return {"authenticated": False}, 401

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return {"status": "error", "message": "Credenciales incorrectas"}, 401
        
    if not user.is_active:
        return {"status": "error", "message": "Cuenta desactivada. Contacte al administrador."}, 403
        
    login_user(user)
    session['mfa_verified'] = False
    log_activity('LOGIN_API', 'Inicio de sesión temporal previo a MFA (PWA)')
    
    return {"status": "success", "requires_mfa": True}

@auth_bp.route('/api/mfa', methods=['POST'])
@login_required
def api_mfa():
    data = request.json or {}
    token = data.get('token')
    
    if not current_user.mfa_secret:
        # Si no tiene MFA configurado, lo dejamos pasar por ahora (o forzar configuración, pero PWA asume login simple)
        session['mfa_verified'] = True
        session.permanent = True
        return {"status": "success"}
        
    totp = pyotp.TOTP(current_user.mfa_secret)
    if totp.verify(token):
        session['mfa_verified'] = True
        session.permanent = True
        log_activity('LOGIN_MFA_API', 'Superó verificación MFA 2FA (PWA)')
        return {"status": "success", "user": {"email": current_user.email, "nombre": current_user.nombre_completo}}
    else:
        return {"status": "error", "message": "Código MFA inválido"}, 401

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    log_activity('LOGOUT_API', 'Cierre de sesión manual (PWA)')
    logout_user()
    session.pop('mfa_verified', None)
    return {"status": "success"}

@auth_bp.route('/api/admin/logs', methods=['GET'])
@login_required
def api_admin_logs():
    if not current_user.is_admin:
        return {"error": "Acceso denegado"}, 403
    
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": log.user.email if log.user else 'Sistema',
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return {"logs": logs_data}

# --- USER MANAGEMENT (ADMIN ONLY) ---

@auth_bp.route('/api/admin/users', methods=['GET'])
@login_required
def api_admin_users():
    if not current_user.is_admin:
        return {"error": "Acceso denegado"}, 403
    
    users = User.query.all()
    users_data = []
    for u in users:
        users_data.append({
            "id": u.id,
            "email": u.email,
            "nombre_completo": u.nombre_completo,
            "puesto": u.puesto,
            "role": u.role,
            "is_active": u.is_active,
            "telefono": u.telefono
        })
    return {"users": users_data}

@auth_bp.route('/api/admin/users/create', methods=['POST'])
@login_required
def api_create_user():
    if not current_user.is_admin:
        return {"error": "Acceso denegado"}, 403
        
    data = request.json or {}
    email = data.get('email')
    nombre_completo = data.get('nombre_completo')
    puesto = data.get('puesto')
    password = data.get('password')
    telefono = data.get('telefono')
    role = data.get('role', 'tecnico')
    
    if not email: return {"error": "Email requerido"}, 400
    if User.query.filter_by(email=email).first():
        return {"error": "El correo ya está registrado"}, 400
        
    invite_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    mfa_secret = pyotp.random_base32()
    temp_pass = password or secrets.token_hex(16)
    
    new_user = User(
        email=email,
        nombre_completo=nombre_completo,
        puesto=puesto,
        password_hash=generate_password_hash(temp_pass),
        mfa_secret=mfa_secret,
        role=role,
        is_admin=(role == 'admin'),
        telefono=telefono,
        invite_token=invite_token,
        invite_token_expiry=expiry
    )
    db.session.add(new_user)
    db.session.commit()
    log_activity('USER_CREATE_API', f'Registró nuevo elemento: {email}')
    
    return {"status": "success", "invite_token": invite_token}

@auth_bp.route('/api/admin/users/reset/<int:user_id>', methods=['POST'])
@login_required
def api_reset_password(user_id):
    if not current_user.is_admin: return {"error": "Acceso denegado"}, 403
    
    user = db.session.get(User, user_id)
    if not user: return {"error": "No encontrado"}, 404
    
    data = request.json or {}
    new_password = data.get('new_password')
    if not new_password or len(new_password) < 8:
        return {"error": "La clave debe tener al menos 8 caracteres"}, 400
        
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    log_activity('ADMIN_PASSWORD_RESET_API', f'Forzó cambio de clave para: {user.email}')
    return {"status": "success"}

@auth_bp.route('/api/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def api_delete_user(user_id):
    if not current_user.is_admin: return {"error": "Acceso denegado"}, 403
    if user_id == current_user.id: return {"error": "No te puedes eliminar a ti mismo"}, 400
        
    user = db.session.get(User, user_id)
    if user:
        email = user.email
        db.session.delete(user)
        db.session.commit()
        log_activity('USER_DELETE_API', f'Baja definitiva de: {email}')
        
    return {"status": "success"}

@auth_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
        return redirect(url_for('templates.dashboard'))
    
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@auth_bp.route('/admin/users/create', methods=['POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        return redirect(url_for('templates.dashboard'))
        
    email = request.form.get('email')
    nombre_completo = request.form.get('nombre_completo')
    puesto = request.form.get('puesto')
    password = request.form.get('password') # Still here for manual/fallback, but we'll prioritize Token
    telefono = request.form.get('telefono')
    role = request.form.get('role', 'tecnico')
    
    if not email:
        flash('Email es requerido.', 'error')
        return redirect(url_for('templates.dashboard'))
    
    if User.query.filter_by(email=email).first():
        flash('El correo ya está registrado.', 'error')
        return redirect(url_for('templates.dashboard'))
        
    # Security: Generate 24h setup token
    invite_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    mfa_secret = pyotp.random_base32()
    
    # If no password provided (normal for Invite), use a random one temporarily
    temp_pass = password or secrets.token_hex(16)
    
    new_user = User(
        email=email,
        nombre_completo=nombre_completo,
        puesto=puesto,
        password_hash=generate_password_hash(temp_pass),
        mfa_secret=mfa_secret,
        role=role,
        is_admin=(role == 'admin'),
        telefono=telefono,
        invite_token=invite_token,
        invite_token_expiry=expiry
    )
    
    db.session.add(new_user)
    db.session.commit()
    log_activity('USER_CREATE', f'Registró nuevo elemento: {email}')
    
    flash(f'Colaborador {email} registrado. Listo para enviar invitación por WhatsApp.', 'success')
    return redirect(url_for('templates.dashboard'))

@auth_bp.route('/admin/users/reset/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if not current_user.is_admin:
        return redirect(url_for('templates.dashboard'))
    
    user = db.session.get(User, user_id)
    new_password = request.form.get('new_password')
    
    if user and new_password:
        if len(new_password) < 8 or not any(c.isdigit() for c in new_password):
            flash('La nueva contraseña debe tener 8 caracteres y un número.', 'error')
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            log_activity('ADMIN_PASSWORD_RESET', f'Forzó cambio de clave para: {user.email}')
            flash(f'La contraseña para {user.email} fue restablecida con éxito.', 'success')
            
    # Always send them back to the user tab
    return redirect(url_for('templates.dashboard') + "?tab=users")

@auth_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('templates.dashboard'))
        
    if user_id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'error')
        return redirect(url_for('auth.admin_users'))
        
    user = db.session.get(User, user_id)
    if user:
        email = user.email
        db.session.delete(user)
        db.session.commit()
        log_activity('USER_DELETE', f'Baja definitiva de: {email}')
        flash('Usuario eliminado del sistema.', 'success')
        
    return redirect(url_for('templates.dashboard'))



@auth_bp.route('/setup/<token>', methods=['GET', 'POST'])
def setup_account(token):
    # Search for user with this active token
    user = User.query.filter_by(invite_token=token).first()
    
    # Validation: Exists and NOT expired
    now = datetime.now(timezone.utc)
    if not user or (user.invite_token_expiry and user.invite_token_expiry.replace(tzinfo=timezone.utc) < now):
        return render_template('auth/setup.html', error="Enlace expirado o inválido. Solicite uno nuevo.")
        
    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password or len(new_password) < 8 or not any(char.isdigit() for char in new_password):
            flash('La contraseña debe tener al menos 8 caracteres y contener al menos un número.', 'error')
            return render_template('auth/setup.html', user=user, token=token)
            
        # Success: Update and Burn Token
        user.password_hash = generate_password_hash(new_password)
        user.invite_token = None
        user.invite_token_expiry = None
        user.is_active = True
        db.session.commit()
        log_activity('SETUP_CUENTA', 'Finalizó configuración inicial.', user_id=user.id)
        
        flash('Cuenta configurada con éxito. Ya puedes entrar con tu nueva clave.', 'success')
        return redirect(url_for('auth.login'))
    
    # Generate provisioning URI for QR scan
    totp = pyotp.TOTP(user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="Inova Securite")
        
    return render_template('auth/setup.html', user=user, token=token, provisioning_uri=provisioning_uri)
