import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS report_instance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                nombre VARCHAR(150) NOT NULL,
                data_json TEXT DEFAULT '{}',
                created_by_id INTEGER NOT NULL,
                assigned_to_id INTEGER,
                status VARCHAR(20) DEFAULT 'draft',
                fecha_actualizacion DATETIME,
                FOREIGN KEY (template_id) REFERENCES template (id),
                FOREIGN KEY (created_by_id) REFERENCES user (id),
                FOREIGN KEY (assigned_to_id) REFERENCES user (id)
            )
        ''')
        conn.commit()
        print("Table report_instance created successfully.")
    except sqlite3.OperationalError as e:
        print("Error creating table:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
