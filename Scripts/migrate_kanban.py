import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Update User table
        try:
            cur.execute("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'tecnico'")
            cur.execute("UPDATE user SET role = 'admin' WHERE email = 'admin@inovasecurite.mx'")
        except: pass

        # Update ReportInstance table
        try: cur.execute("ALTER TABLE report_instance ADD COLUMN comentarios TEXT DEFAULT ''")
        except: pass
        try: cur.execute("ALTER TABLE report_instance ADD COLUMN porcentaje_avance INTEGER DEFAULT 0")
        except: pass
        try: cur.execute("ALTER TABLE report_instance ADD COLUMN total_campos INTEGER DEFAULT 0")
        except: pass
        
        conn.commit()
        print("Database schema updated for Kanban and Roles.")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
