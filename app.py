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

    # Habilitar CORS para que la PWA (React/Vercel) pueda comunicarse con la API
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

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
    app.register_blueprint(templates_bp)

    return app


app = create_app()
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True, use_reloader=False)
