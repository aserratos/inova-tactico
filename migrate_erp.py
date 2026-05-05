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
        print("Añadiendo erp_api_key a organization...")
        try:
            cursor.execute("ALTER TABLE organization ADD COLUMN erp_api_key VARCHAR(255) UNIQUE")
        except Exception as e:
            print(f"La columna ya existe o error: {e}")
            
        print("Añadiendo external_erp_id a customer...")
        try:
            cursor.execute("ALTER TABLE customer ADD COLUMN external_erp_id VARCHAR(100)")
        except Exception as e:
            print(f"La columna ya existe o error: {e}")
            
        print("Añadiendo erp_source a customer...")
        try:
            cursor.execute("ALTER TABLE customer ADD COLUMN erp_source VARCHAR(50)")
        except Exception as e:
            print(f"La columna ya existe o error: {e}")
            
        print("Añadiendo external_erp_id a report_instance...")
        try:
            cursor.execute("ALTER TABLE report_instance ADD COLUMN external_erp_id VARCHAR(100)")
        except Exception as e:
            print(f"La columna ya existe o error: {e}")

        print("¡Migración ERP completada exitosamente!")

    except Exception as e:
        print(f"Error durante la migración: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    with app.app_context():
        migrate()
