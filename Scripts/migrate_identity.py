import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Add Identifier Columns
        try: cur.execute("ALTER TABLE user ADD COLUMN nombre_completo TEXT")
        except: pass
        try: cur.execute("ALTER TABLE user ADD COLUMN puesto TEXT")
        except: pass
        
        conn.commit()
        print("Database migrated with Identity columns.")
    except Exception as e:
        print("Error during identity migration:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
