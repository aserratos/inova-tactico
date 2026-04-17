from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash
import pyotp
import qrcode
import sys

app = create_app()

def init_db():
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("Base de datos inicializada.")

        # Verificar si ya existe un admin
        admin = User.query.filter_by(email='admin@inovasecurite.mx').first()
        if admin:
            print("El usuario admin ya existe.")
            return

        # Generar un secreto MFA
        secret = pyotp.random_base32()
        
        # Crear usuario
        admin = User(
            email='admin@inovasecurite.mx',
            password_hash=generate_password_hash('InovaSecurite2026!'),
            mfa_secret=secret,
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"\nUsuario admin configurado exitosamente.")
        print(f"Email: admin@inovasecurite.mx")
        print(f"Password: InovaSecurite2026!")
        print(f"\n--- CONFIGURACION DE MFA ---")
        print(f"Secreto MFA (Base32): {secret}")
        
        # Generar URL para Authenticator
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name='admin@inovasecurite.mx',
            issuer_name='Inova Securite Plantillas'
        )
        # Generar QR para el Autenticador
        print(f"Para configurar tu Authenticator ingresa manualmente la clave: {secret}\n")
        print(f"O puedes acceder al siguiente enlace en tu navegador para ver un QR temporal:")
        print(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={totp_uri}")
        
        try:
            # Intentar generar QR ASCII en consola
            import sys
            import io
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding='utf-8')
            print("\nCódigo QR Local:\n")
            qr = qrcode.QRCode()
            qr.add_data(totp_uri)
            qr.make(fit=True)
            qr.print_ascii()
        except:
            print("\n(El QR ASCII local no se pudo imprimir por la codificación de tu consola, usa el enlace arriba o copia el SECRETO manualmente)")
            
        print("\nGuarda esta información de forma segura. Sin embargo, no la necesitarás para el script de inicialización una vez agregada a tu dispositivo.")

if __name__ == "__main__":
    init_db()
