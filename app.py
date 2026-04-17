import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone
from flask import Flask, redirect, url_for, send_from_directory
from models import db, User
from flask_login import LoginManager
from flask_cors import CORS

def datetime_format(value):
    if isinstance(value, datetime):
        return value.strftime('%d %b %Y, %H:%M:%S')
    return value

import secrets
from flask_executor import Executor

executor = Executor()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'inova_dev_secret_key_12345')
    
    # Habilitar CORS para que la PWA (React) pueda comunicarse con la API
    CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.1.72:5173", "http://192.168.1.72:5174", "*"])

    @app.route('/sw.js')
    def serve_sw():
        # Servir con header explícito para permitir el scope total
        response = send_from_directory(os.path.join(app.root_path, 'static'), 'sw.js')
        response.headers['Service-Worker-Allowed'] = '/'
        response.headers['Content-Type'] = 'application/javascript'
        return response

    @app.route('/manifest.json')
    def serve_manifest():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json', mimetype='application/json')

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'plantillas')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register filter explicitly
    app.jinja_env.filters['datetime_format'] = datetime_format

    db.init_app(app)
    executor.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
        
    from controllers.auth import auth_bp
    from controllers.templates import templates_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(templates_bp)

    
    @app.route('/')
    def index():
        return redirect(url_for('templates.dashboard'))
        
    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8001, debug=True, use_reloader=False)
