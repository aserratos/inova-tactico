from app import create_app
from models import db, Notification
import os

app = create_app()

with app.app_context():
    # SQLite detecta automáticamente que la tabla no existe y la crea
    try:
        Notification.__table__.create(db.engine)
        print("✅ Tabla de Notificaciones creada con éxito.")
    except Exception as e:
        print("La tabla ya existía o hubo un error:", e)
