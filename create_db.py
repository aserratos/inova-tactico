from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN webauthn_id VARCHAR(100) UNIQUE;"))
        db.session.commit()
        print("Column webauthn_id added successfully.")
    except Exception as e:
        print("Error adding column (maybe already exists):", e)
        db.session.rollback()
        
    db.create_all()
    print("New tables created successfully.")
