from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from . import admin_bp
from .forms import PersonnelForm
from app import db
from app.models import Personnel
from app.utils import log_activity

@admin_bp.route('/personnel', methods=['GET', 'POST'])
@login_required
def manage_personnel():
    form = PersonnelForm()
    if form.validate_on_submit():
        person = Personnel(name=form.name.data)
        db.session.add(person)
        db.session.commit()
        log_activity('添加负责人', f"添加了新负责人: {person.name}")
        flash(f'负责人 "{person.name}" 已成功添加。', 'success')
        return redirect(url_for('admin.manage_personnel'))
    
    personnel_list = Personnel.query.order_by(Personnel.name).all()
    return render_template('admin/personnel.html', title="负责人管理", form=form, personnel_list=personnel_list)

@admin_bp.route('/personnel/delete/<int:person_id>', methods=['POST'])
@login_required
def delete_personnel(person_id):
    person = Personnel.query.get_or_404(person_id)
    log_activity('删除负责人', f"删除了负责人: {person.name}")
    db.session.delete(person)
    db.session.commit()
    flash(f'负责人 "{person.name}" 已被删除。', 'success')
    return redirect(url_for('admin.manage_personnel'))