import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Convert old statuses to new ones
        cur.execute("UPDATE report_instance SET status = 'en_ejecucion' WHERE status = 'draft'")
        cur.execute("UPDATE report_instance SET status = 'terminado' WHERE status = 'completed'")
        conn.commit()
        print("Existing statuses modernized.")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()
