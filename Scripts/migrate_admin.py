import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL")
        cur.execute("UPDATE user SET is_admin = 1 WHERE email = 'admin@inovasecurite.mx'")
        conn.commit()
        print("Column is_admin added and admin user updated.")
    except sqlite3.OperationalError as e:
        print("Extension notice:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
