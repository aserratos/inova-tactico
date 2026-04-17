import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'tecnico'")
        conn.commit()
        print("Column 'role' added to 'user' table.")
    except Exception as e:
        print("Error (maybe column already exists):", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
