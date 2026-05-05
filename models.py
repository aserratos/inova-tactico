from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    erp_api_key = db.Column(db.String(255), unique=False, nullable=True)
    erp_url = db.Column(db.String(255), nullable=True)
    erp_db = db.Column(db.String(100), nullable=True)
    erp_username = db.Column(db.String(150), nullable=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    nombre_empresa = db.Column(db.String(150), nullable=False)
    rfc = db.Column(db.String(20), nullable=True)
    contacto_principal = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    external_erp_id = db.Column(db.String(100), nullable=True)
    erp_source = db.Column(db.String(50), nullable=True)
    
    org = db.relationship('Organization', backref=db.backref('customers', lazy=True))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False) # Admin del sistema (super admin)
    role = db.Column(db.String(50), default='tecnico') # tecnico, supervisor, admin (de la organización), cliente
    
    # Identidad Táctica
    nombre_completo = db.Column(db.String(200), nullable=True)
    puesto = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)

    org = db.relationship('Organization', backref=db.backref('users', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    ruta_archivo_docx = db.Column(db.String(300), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    variables_json = db.Column(db.Text, default='[]')
    
    uploader = db.relationship('User', backref=db.backref('templates', lazy=True))
    org = db.relationship('Organization', backref=db.backref('templates', lazy=True))

class ReportInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    external_erp_id = db.Column(db.String(100), nullable=True)
    data_json = db.Column(db.Text, default='{}')
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='por_hacer')
    fecha_actualizacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    comentarios = db.Column(db.Text, default='')
    porcentaje_avance = db.Column(db.Integer, default=0)
    total_campos = db.Column(db.Integer, default=0)
    campos_llenados = db.Column(db.Integer, default=0)
    archivo_compilado_path = db.Column(db.String(300), nullable=True)
    
    template = db.relationship('Template', backref=db.backref('instances', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by_id], backref=db.backref('created_reports', lazy=True))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref=db.backref('assigned_reports', lazy=True))
    org = db.relationship('Organization', backref=db.backref('reports', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('reports', lazy=True))

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('activities', lazy='dynamic'))
    org = db.relationship('Organization', backref=db.backref('activities', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')
    link = db.Column(db.String(300), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

def log_activity(action, details=None, user_id=None):
    from flask import g
    uid = user_id if user_id else (g.current_user.id if hasattr(g, 'current_user') and g.current_user else None)
    if uid:
        user = db.session.get(User, uid)
        org_id = user.org_id if user else None
        log = ActivityLog(user_id=uid, org_id=org_id, action=action, details=details)
        db.session.add(log)
        try:
            db.session.commit()
        except:
            db.session.rollback()
