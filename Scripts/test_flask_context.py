from app import create_app
from models import db, Template

app = create_app()
app.config['TESTING'] = True

with app.app_context():
    # Encuentra la plantilla que está fallando
    t = Template.query.filter_by(nombre='PIPC_MACHOTE_2026').first()
    if t:
        print("Encontrada plantilla:", t.id, t.ruta_archivo_docx)
        client = app.test_client()
        # Para evadir login_required, le hacemos un hack a session o algo, pero flask_login tira redirect a auth.login
        # Vamos a llamar la función internamente
        from controllers.templates import SmartDocxTemplate
        doc = SmartDocxTemplate(t.ruta_archivo_docx)
        try:
            vars = doc.get_undeclared_template_variables()
            print("Variables parsed via Flask controllers successfully!")
            print(list(vars)[:5])
        except Exception as e:
            print("ERROR IN FLASK CONTEXT:", e)
    else:
        print("No template found.")
