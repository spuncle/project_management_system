from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    # ... 此模型无变化 ...
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    can_add = db.Column(db.Boolean, nullable=False, default=False)
    can_edit = db.Column(db.Boolean, nullable=False, default=False)
    can_delete = db.Column(db.Boolean, nullable=False, default=False)
    schedules = db.relationship('WorkSchedule', back_populates='author', lazy=True)
    logs = db.relationship('ActivityLog', back_populates='user', lazy=True)
    sent_invitations = db.relationship('InvitationCode', back_populates='creator', lazy=True)

class InvitationCode(db.Model):
    # ... 此模型无变化 ...
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', back_populates='sent_invitations')

class WorkSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    # personnel = db.Column(db.String(100), nullable=False) # <--- 【移除】旧的 personnel 字段
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    position = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=0)
    
    author = db.relationship('User', back_populates='schedules')
    # --- 【新增】一对多关系，指向任务分配表 ---
    assignments = db.relationship('TaskAssignment', backref='task', lazy='joined', cascade='all, delete-orphan')

class ActivityLog(db.Model):
    # ... 此模型无变化 ...
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='logs')

class Personnel(db.Model):
    # ... 此模型无变化 ...
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    def __repr__(self):
        return f'<Personnel {self.name}>'

# --- 【新增】任务分配模型 ---
class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('work_schedule.id'), nullable=False)
    personnel_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<TaskAssignment {self.personnel_name}>'