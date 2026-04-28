from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    # Make all users admin for now, or just the newly created one
    users = User.query.all()
    for user in users:
        user.is_admin = True
        user.role = 'admin'
    db.session.commit()
    print("Usuarios actualizados a admin.")
