from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Remove deprecated columns
    db.session.execute(text('ALTER TABLE "user" DROP COLUMN IF EXISTS password_hash CASCADE;'))
    db.session.execute(text('ALTER TABLE "user" DROP COLUMN IF EXISTS mfa_secret CASCADE;'))
    db.session.execute(text('ALTER TABLE "user" DROP COLUMN IF EXISTS webauthn_id CASCADE;'))
    db.session.commit()
    print("Columnas deprecadas eliminadas con exito.")
