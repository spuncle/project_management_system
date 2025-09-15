import secrets
from flask import render_template, url_for, flash, redirect, request
from . import auth_bp
from .forms import RegistrationForm, LoginForm, InvitationForm
from app.models import User, Invitation
from app import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from app.utils import log_activity

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    invite_code = request.args.get('invite')
    if not invite_code:
        flash('注册需要一个有效的邀请码。', 'danger')
        return redirect(url_for('auth.login'))

    invitation = Invitation.query.filter_by(code=invite_code, is_used=False).first()
    if not invitation:
        flash('邀请码无效或已被使用。', 'danger')
        return redirect(url_for('auth.login'))

    form = RegistrationForm()
    # 预填充邀请的邮箱地址
    if request.method == 'GET':
        form.email.data = invitation.email

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)

        invitation.is_used = True
        db.session.commit()

        flash('您的账户已创建！现在可以登录了。', 'success')
        log_activity('用户注册', f"用户 {user.username} 使用邀请码 {invite_code} 注册成功。")
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
def invite():
    form = InvitationForm()
    if form.validate_on_submit():
        email = form.email.data
        code = secrets.token_urlsafe(16)
        invitation = Invitation(code=code, email=email, created_by_id=current_user.id)
        db.session.add(invitation)
        db.session.commit()

        invite_link = url_for('auth.register', invite=code, _external=True)
        flash(f'已为 {email} 生成邀请链接:', 'success')
        flash(invite_link, 'info')
        log_activity('生成邀请码', f"为邮箱 {email} 生成邀请码。")
        return redirect(url_for('auth.invite'))

    invitations = Invitation.query.filter_by(created_by_id=current_user.id).order_by(Invitation.created_at.desc()).all()
    return render_template('auth/invite.html', title='邀请新用户', form=form, invitations=invitations)
