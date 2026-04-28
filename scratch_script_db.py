from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS clerk_id VARCHAR(120) UNIQUE;'))
    db.session.commit()
    print("Columna clerk_id agregada con exito.")
