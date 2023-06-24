from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import openai

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    api_key = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('conversations', lazy=True))
    prompt = db.Column(db.String(1000), nullable=False)
    response = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Conversation('{self.user_id}', '{self.prompt}', '{self.response}', '{self.timestamp}')"
    
class SystemPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return f"SystemPrompt('{self.prompt}')"