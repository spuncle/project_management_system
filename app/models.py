from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    schedules = db.relationship('WorkSchedule', backref='author', lazy=True)
    logs = db.relationship('ActivityLog', backref='user', lazy=True)
    sent_invitations = db.relationship('Invitation', backref='creator', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Invitation {self.code}>'

class WorkSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    personnel = db.Column(db.String(100), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<WorkSchedule {self.id} on {self.task_date}>'

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Log: {self.user.username} - {self.action}>'
