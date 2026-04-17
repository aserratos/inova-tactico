import os
import sys

# Asegurar que importamos del directorio raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, User, Template, ReportInstance, ActivityLog, Notification
from app import create_app

def migrate():
    # 1. Cargar aplicación (carga el .env)
    app = create_app()
    
    neon_url = os.environ.get('DATABASE_URL', '')
    if not neon_url or "TU_ENLACE_AQUI" in neon_url:
        print("❌ ERROR: Aún no has pegado tu enlace de Neon en el archivo .env")
        return
        
    if neon_url.startswith("postgres://"):
        neon_url = neon_url.replace("postgres://", "postgresql://", 1)
        
    if neon_url.startswith("sqlite"):
        print("❌ ERROR: El DATABASE_URL sigue configurado como sqlite.")
        return

    print("Conectando a SQLite local...")
    # Asegúrate de la ruta correcta para SQLite
    sqlite_db_path = os.path.join(app.root_path, 'instance', 'app.db')
    sqlite_engine = create_engine(f'sqlite:///{sqlite_db_path}')
    SessionLocal = sessionmaker(bind=sqlite_engine)
    sqlite_session = SessionLocal()
    
    print("Extrayendo datos locales...")
    users = sqlite_session.query(User).all()
    templates = sqlite_session.query(Template).all()
    reports = sqlite_session.query(ReportInstance).all()
    logs = sqlite_session.query(ActivityLog).all()
    notifs = sqlite_session.query(Notification).all()

    sqlite_session.expunge_all()
    sqlite_session.close()

    print("Conectando a Neon PostgreSQL...")
    app.config['SQLALCHEMY_DATABASE_URI'] = neon_url
    neon_engine = create_engine(neon_url)
    
    with app.app_context():
        print("Creando tablas en Neon...")
        db.create_all()
        
    SessionRemote = sessionmaker(bind=neon_engine)
    neon_session = SessionRemote()
    
    print("Migrando datos (esto puede tomar unos segundos)...")
    
    try:
        # Usamos merge para preservar los IDs (Primary Keys)
        for u in users: neon_session.merge(u)
        neon_session.flush()
        
        for t in templates: neon_session.merge(t)
        neon_session.flush()
        
        for r in reports: neon_session.merge(r)
        neon_session.flush()
        
        for l in logs: neon_session.merge(l)
        for n in notifs: neon_session.merge(n)
        
        neon_session.commit()
        
        # PostgreSQL necesita que se actualicen las secuencias de IDs
        # porque insertamos IDs manualmente
        print("Ajustando secuencias en PostgreSQL...")
        neon_session.execute(db.text("SELECT setval('user_id_seq', COALESCE((SELECT MAX(id)+1 FROM \"user\"), 1), false);"))
        neon_session.execute(db.text("SELECT setval('template_id_seq', COALESCE((SELECT MAX(id)+1 FROM template), 1), false);"))
        neon_session.execute(db.text("SELECT setval('report_instance_id_seq', COALESCE((SELECT MAX(id)+1 FROM report_instance), 1), false);"))
        neon_session.execute(db.text("SELECT setval('activity_log_id_seq', COALESCE((SELECT MAX(id)+1 FROM activity_log), 1), false);"))
        neon_session.execute(db.text("SELECT setval('notification_id_seq', COALESCE((SELECT MAX(id)+1 FROM notification), 1), false);"))
        neon_session.commit()
        
        print("[EXITO] Migracion completada exitosamente!")
        print("Tu aplicación ya está lista para operar en Neon.")
        
    except Exception as e:
        neon_session.rollback()
        print(f"[ERROR] Error durante la migracion: {str(e)}")
    finally:
        neon_session.close()

if __name__ == "__main__":
    migrate()
