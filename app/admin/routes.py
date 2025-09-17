from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import admin_bp
from .forms import PersonnelForm
from app import db
from app.models import Personnel, User
from app.utils import log_activity
from app.decorators import admin_required

@admin_bp.route('/personnel', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_personnel():
    form = PersonnelForm()
    if form.validate_on_submit():
        person = Personnel(name=form.name.data)
        db.session.add(person)
        db.session.commit()
        log_activity('添加人员', f"添加了新人员: {person.name}")
        flash(f'人员 "{person.name}" 已成功添加。', 'success')
        return redirect(url_for('admin.manage_personnel'))
    
    personnel_list = Personnel.query.order_by(Personnel.name).all()
    return render_template('admin/personnel.html', title="人员管理", form=form, personnel_list=personnel_list)

@admin_bp.route('/personnel/delete/<int:person_id>', methods=['POST'])
@login_required
@admin_required
def delete_personnel(person_id):
    person = Personnel.query.get_or_404(person_id)
    log_activity('删除人员', f"删除了人员: {person.name}")
    db.session.delete(person)
    db.session.commit()
    flash(f'人员 "{person.name}" 已被删除。', 'success')
    return redirect(url_for('admin.manage_personnel'))

# --- 新增用户管理路由 ---
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.id).all()
    return render_template('admin/users.html', title="用户管理", users=users)

@admin_bp.route('/api/user/<int:user_id>/permissions', methods=['POST'])
@login_required
@admin_required
def update_user_permissions(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': '不能修改自己的权限。'}), 400
        
    data = request.get_json()
    permission_name = data.get('permission')
    value = data.get('value')

    if permission_name in ['is_admin', 'can_add', 'can_edit', 'can_delete']:
        setattr(user, permission_name, value)
        db.session.commit()
        log_activity('更新用户权限', f"更新了用户 {user.username} 的权限 '{permission_name}' 为 {value}")
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': '无效的权限名称。'}), 400