from app import create_app
from models import db
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    stmts = [
        # Create Organization table
        """CREATE TABLE IF NOT EXISTS organization (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(150) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        # User table updates
        """ALTER TABLE "user" ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organization(id)""",
        """ALTER TABLE "user" ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256)""",
        # Update references
        """ALTER TABLE template ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organization(id)""",
        """ALTER TABLE report_instance ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organization(id)""",
        """ALTER TABLE activity_log ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organization(id)"""
    ]
    
    for s in stmts:
        try:
            db.session.execute(db.text(s))
            print(f"OK: {s[:60]}...")
            db.session.commit()
        except Exception as e:
            print(f"SKIP ({e}): {s[:60]}...")
            db.session.rollback()
            
    # Default password hash for existing users
    try:
        default_hash = generate_password_hash('inova123')
        db.session.execute(db.text('UPDATE "user" SET password_hash = :hash WHERE password_hash IS NULL'), {'hash': default_hash})
        db.session.commit()
        print("Updated empty password hashes to 'inova123'")
    except Exception as e:
        print("Error updating password_hash:", e)
        db.session.rollback()
