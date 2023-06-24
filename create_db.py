from app import app
from models import db, User

with app.app_context():
    db.create_all()