import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone, timedelta
from flask import Flask, redirect, url_for, send_from_directory
from models import db, User
from flask_cors import CORS
from flask_cors import CORS

def datetime_format(value):
    if isinstance(value, datetime):
        return value.strftime('%d %b %Y, %H:%M:%S')
    return value

import secrets
from extensions import executor

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'inova_dev_secret_key_12345')
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365) # Sesiones persistentes (1 año)
    
    # Habilitar CORS para que la PWA (React) pueda comunicarse con la API
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

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
    
    # Flask-Login ha sido reemplazado por autenticación JWT con Clerk
    # Se usa @require_auth de auth_middleware en las rutas
        
    from controllers.templates import templates_bp
    
    app.register_blueprint(templates_bp)

    
    @app.route('/')
    def index():
        return redirect(url_for('templates.dashboard'))
        
    return app


app = create_app()
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True, use_reloader=False)
