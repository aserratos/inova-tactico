import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE template ADD COLUMN is_public BOOLEAN DEFAULT 0 NOT NULL")
        conn.commit()
        print("Column is_public added successfully.")
    except sqlite3.OperationalError as e:
        print("Extension notice:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
