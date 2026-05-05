import os
import psycopg2
from app import app
from models import db

def migrate():
    # Retrieve the exact database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL no encontrada en el entorno.")
        return

    # Handle postgres:// vs postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"Conectando a {db_url}...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        print("Creando tabla customer si no existe...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer (
                id SERIAL PRIMARY KEY,
                org_id INTEGER NOT NULL REFERENCES organization(id),
                nombre_empresa VARCHAR(150) NOT NULL,
                rfc VARCHAR(20),
                contacto_principal VARCHAR(150),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Añadiendo customer_id a la tabla user...")
        try:
            cursor.execute("ALTER TABLE \"user\" ADD COLUMN customer_id INTEGER REFERENCES customer(id)")
        except Exception as e:
            print(f"La columna user.customer_id probablemente ya existe o hubo un error: {e}")

        print("Añadiendo customer_id a la tabla report_instance...")
        try:
            cursor.execute("ALTER TABLE report_instance ADD COLUMN customer_id INTEGER REFERENCES customer(id)")
        except Exception as e:
            print(f"La columna report_instance.customer_id probablemente ya existe o hubo un error: {e}")

        print("¡Migración Customer completada exitosamente!")

    except Exception as e:
        print(f"Error durante la migración: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    with app.app_context():
        migrate()
