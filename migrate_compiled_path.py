import sqlite3

def migrate():
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE report_instance ADD COLUMN archivo_compilado_path VARCHAR(300)')
        conn.commit()
        print("Migración exitosa.")
    except sqlite3.OperationalError as e:
        print(f"Error o ya migrado: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
