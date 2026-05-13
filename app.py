import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta
from flask import Flask
from models import db
from flask_cors import CORS
from extensions import executor

def datetime_format(value):
    if isinstance(value, datetime):
        return value.strftime('%d %b %Y, %H:%M:%S')
    return value

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'inova_dev_secret_key_12345')
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)

    # CORS: flask-cors como base (maneja el preflight OPTIONS)
    CORS(app, supports_credentials=True, origins="*")

    # Hook manual que garantiza headers CORS en TODAS las respuestas
    # (incluyendo errores 500 y cualquier URL de preview de Vercel)
    import re as _re
    _static_origins = set(
        os.environ.get(
            'CORS_ORIGINS',
            'https://inova-tactico.vercel.app,http://localhost:5173,http://localhost:3000,https://ovniflow.vercel.app'
        ).split(',')
    )

    @app.after_request
    def ensure_cors_headers(response):
        from flask import request as _req
        origin = _req.headers.get('Origin', '')
        if not origin:
            return response

        is_allowed = (
            origin in _static_origins
            or bool(_re.match(r'^https://[a-zA-Z0-9._-]+\.vercel\.app$', origin))
            or bool(_re.match(r'^http://localhost:\d+$', origin))
        )

        if is_allowed:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
            response.headers['Vary'] = 'Origin, Accept-Encoding'

        return response

    # Manejador global de preflight OPTIONS para todas las rutas
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_preflight_global(path=''):
        response = app.make_response('')
        response.status_code = 200
        return response

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'plantillas')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.jinja_env.filters['datetime_format'] = datetime_format

    db.init_app(app)
    executor.init_app(app)

    from controllers.templates import templates_bp
    from controllers.auth import auth_bp
    from controllers.pwa_api import pwa_api_bp
    from controllers.admin import admin_bp
    from controllers.integrations import integrations_bp
    
    app.register_blueprint(templates_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pwa_api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(integrations_bp)

    return app


app = create_app()
with app.app_context():
    db.create_all()
    # Ejecutamos la migracion automaticamente
    try:
        from migrate_customer import migrate as migrate_cust
        migrate_cust()
        from migrate_erp import migrate as migrate_erp_func
        migrate_erp_func()
    except Exception as e:
        print("Error en migracion automatica:", e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True, use_reloader=False)
