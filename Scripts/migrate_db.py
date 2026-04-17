import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE template ADD COLUMN is_favorite BOOLEAN DEFAULT 0 NOT NULL")
        conn.commit()
        print("Column is_favorite added successfully.")
    except sqlite3.OperationalError as e:
        print("Expected error (already exists or other):", e)
    finally:
        conn.close()
else:
    print("Database not found.")
