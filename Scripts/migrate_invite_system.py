import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Add Columns to User
        try: cur.execute("ALTER TABLE user ADD COLUMN telefono TEXT")
        except: pass
        try: cur.execute("ALTER TABLE user ADD COLUMN invite_token TEXT")
        except: pass
        try: cur.execute("ALTER TABLE user ADD COLUMN invite_token_expiry DATETIME")
        except: pass
        
        conn.commit()
        print("Database migrated with Invite System columns.")
    except Exception as e:
        print("Error during migration:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
