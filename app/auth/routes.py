import secrets
from flask import render_template, url_for, flash, redirect, request
from . import auth_bp
from .forms import RegistrationForm, LoginForm, InvitationForm
from app.models import User, InvitationCode
from app import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from app.utils import log_activity
from app.decorators import admin_required

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(user)
        
        invitation = InvitationCode.query.filter_by(code=form.invitation_code.data).first()
        invitation.is_used = True
        
        db.session.commit()
        
        flash('您的账户已创建！现在可以登录了。', 'success')
        log_activity('用户注册', f"用户 {user.username} 使用邀请码 {invitation.code} 注册成功。")
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='注册', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            log_activity('用户登录')
            flash('登录成功！', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('登录失败，请检查用户名和密码。', 'danger')
    return render_template('auth/login.html', title='登录', form=form)

@auth_bp.route('/logout')
def logout():
    log_activity('用户登出')
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/invite', methods=['GET', 'POST'])
@login_required
@admin_required
def invite():
    form = InvitationForm()
    if form.validate_on_submit():
        code_str = secrets.token_urlsafe(16)
        new_code = InvitationCode(code=code_str, created_by_id=current_user.id)
        db.session.add(new_code)
        db.session.commit()
        
        flash(f'已生成新邀请码: {code_str}', 'success')
        log_activity('生成邀请码', f"生成了邀请码 {code_str}")
        return redirect(url_for('auth.invite'))
    
    codes = InvitationCode.query.filter_by(is_used=False).order_by(InvitationCode.created_at.desc()).all()
    return render_template('auth/invite.html', title='生成邀请码', form=form, codes=codes)