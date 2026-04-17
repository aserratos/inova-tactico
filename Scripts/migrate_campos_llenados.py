import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE report_instance ADD COLUMN campos_llenados INTEGER DEFAULT 0")
        conn.commit()
        print("Database migrated with campos_llenados column.")
    except Exception as e:
        print("Error during migration (might already exist):", e)
    finally:
        conn.close()
