from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    # Clerk identifier (opcional, pero útil si Clerk usa su propio ID)
    clerk_id = db.Column(db.String(100), unique=True, nullable=True) 
    
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.String(50), default='tecnico') # tecnico, supervisor, admin
    
    # Identidad Táctica
    nombre_completo = db.Column(db.String(200), nullable=True) # Nombre real
    puesto = db.Column(db.String(100), nullable=True) # Cargo o Posición
    telefono = db.Column(db.String(20), nullable=True) # Para envío de WhatsApp

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    ruta_archivo_docx = db.Column(db.String(300), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    variables_json = db.Column(db.Text, default='[]') # Lista de qué campos tiene el Word
    clerk_org_id = db.Column(db.String(100), nullable=True)  # Multi-tenant: organización dueña
    
    # Relationship with User
    uploader = db.relationship('User', backref=db.backref('templates', lazy=True))

class ReportInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False) # Nombre específico de este levantamiento
    data_json = db.Column(db.Text, default='{}') # Datos de texto en formato JSON
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='por_hacer') # por_hacer, en_ejecucion, pendiente, terminado
    fecha_actualizacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # [NUEVO] Para Kanban e Inteligencia de Negocio
    comentarios = db.Column(db.Text, default='') # Que se quedó pendiente
    porcentaje_avance = db.Column(db.Integer, default=0) # Cálculo automático 0-100
    total_campos = db.Column(db.Integer, default=0) # Cuantos campos tiene la plantilla
    campos_llenados = db.Column(db.Integer, default=0) # Cuantos campos han sido contestados
    archivo_compilado_path = db.Column(db.String(300), nullable=True) # Ruta del Word generado
    clerk_org_id = db.Column(db.String(100), nullable=True)  # Multi-tenant: organización dueña
    
    template = db.relationship('Template', backref=db.backref('instances', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by_id], backref=db.backref('created_reports', lazy=True))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref=db.backref('assigned_reports', lazy=True))

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    clerk_org_id = db.Column(db.String(100), nullable=True)  # Multi-tenant: organización dueña
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('activities', lazy='dynamic'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info') # info, assignment, success, warning
    link = db.Column(db.String(300), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

def log_activity(action, details=None, user_id=None):
    from flask import g
    uid = user_id if user_id else (g.current_user.id if hasattr(g, 'current_user') and g.current_user else None)
    if uid:
        log = ActivityLog(user_id=uid, action=action, details=details)
        db.session.add(log)
        try:
            db.session.commit()
        except:
            db.session.rollback()
