import os
import resend
from flask import render_template_string

def get_resend_api_key():
    return os.environ.get('RESEND_API_KEY')

def send_email(to_email, subject, html_content):
    """
    Función genérica para enviar correos electrónicos vía Resend.
    """
    api_key = get_resend_api_key()
    if not api_key:
        print("ERROR: RESEND_API_KEY no está configurada.")
        return False
        
    resend.api_key = api_key

    # En pruebas con cuentas gratis de Resend, el "from" debe ser un correo verificado
    # o usar el de prueba "onboarding@resend.dev" si estás probando con tu propio email.
    # Recomendación para producción: "notificaciones@tu-dominio.com"
    sender = "onboarding@resend.dev"
    
    try:
        r = resend.Emails.send({
            "from": f"OmniFlow <{sender}>",
            "to": to_email,
            "subject": subject,
            "html": html_content
        })
        print(f"Correo enviado a {to_email}. ID: {r.get('id')}")
        return True
    except Exception as e:
        print(f"Error al enviar correo vía Resend: {e}")
        return False

def send_welcome_email(user, temp_password):
    """
    Envia correo de bienvenida con credenciales iniciales.
    """
    subject = "¡Bienvenido a OmniFlow!"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #4F46E5;">Bienvenido a OmniFlow</h2>
        <p>Hola <strong>{user.nombre_completo or 'Usuario'}</strong>,</p>
        <p>Tu cuenta ha sido creada exitosamente. A continuación, tus credenciales de acceso:</p>
        <div style="background: #f4f4f5; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
            <p><strong>Usuario:</strong> {user.email}</p>
            <p><strong>Contraseña Temporal:</strong> <span style="color: #e11d48; font-family: monospace; font-size: 16px;">{temp_password}</span></p>
        </div>
        <p>Por motivos de seguridad, te recomendamos iniciar sesión e ir a la sección de Ajustes para cambiar tu contraseña lo antes posible.</p>
        <br/>
        <a href="https://inova-tactico.vercel.app/login" style="background: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Iniciar Sesión</a>
        <br/><br/>
        <p style="font-size: 12px; color: #888;">El equipo de OmniFlow</p>
    </div>
    """
    return send_email(user.email, subject, html)

def send_report_completed_notification(report):
    """
    Notifica a los involucrados cuando un documento/reporte ha sido completado.
    (Ejemplo básico, puede expandirse para avisar al supervisor).
    """
    # Determinar destinatario (ej. supervisor o creador)
    destinatario = report.creator.email
    
    subject = f"Documento Finalizado: {report.nombre}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #10B981;">Documento Completado</h2>
        <p>El documento <strong>{report.nombre}</strong> ha sido completado exitosamente y su archivo compilado está listo para descargarse.</p>
        <br/>
        <a href="https://inova-tactico.vercel.app/dashboard" style="background: #10B981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Ver Tablero</a>
    </div>
    """
    return send_email(destinatario, subject, html)
