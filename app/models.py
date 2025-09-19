from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
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
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    position = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=0)
    
    author = db.relationship('User', back_populates='schedules')
    
    # --- 【修改】增加了 order_by，让人员始终按顺序排列 ---
    assignments = db.relationship(
        'TaskAssignment', 
        backref='task', 
        lazy='joined', 
        cascade='all, delete-orphan',
        order_by='TaskAssignment.position'
    )
    # ----------------------------------------------------

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='logs')

class Personnel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    def __repr__(self):
        return f'<Personnel {self.name}>'

class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('work_schedule.id'), nullable=False)
    personnel_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, nullable=False) # <--- 【新增】用于排序的字段

    def __repr__(self):
        return f'<TaskAssignment {self.personnel_name}>'