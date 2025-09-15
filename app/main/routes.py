import pandas as pd
from io import BytesIO
from openpyxl.utils import get_column_letter
import openpyxl
from flask import (render_template, request, jsonify, redirect, 
                   url_for, flash, Response, make_response)
from flask_login import login_required, current_user
from datetime import date, timedelta, datetime
from sqlalchemy import and_

from . import main_bp
from app import db
from app.models import WorkSchedule, ActivityLog
from app.utils import log_activity


def get_week_dates(start_date_str=None):
    """获取指定日期所在周的周一到周日日期列表。"""
    if start_date_str:
        base_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        base_date = date.today()

    start_of_week = base_date - timedelta(days=base_date.weekday())
    return [start_of_week + timedelta(days=i) for i in range(7)]

@main_bp.route('/')
@login_required
def index():
    start_date_str = request.args.get('start_date')
    week_dates = get_week_dates(start_date_str)
    start_of_week = week_dates[0]
    end_of_week = week_dates[-1]

    # SQLAlchemy查询
    tasks = WorkSchedule.query.filter(
        and_(
            WorkSchedule.task_date >= start_of_week,
            WorkSchedule.task_date <= end_of_week
        )
    ).order_by(WorkSchedule.task_date).all()

    # 按日期分组任务
    schedule_by_day = {day: [] for day in week_dates}
    for task in tasks:
        schedule_by_day[task.task_date].append(task)

    prev_week_start = start_of_week - timedelta(days=7)
    next_week_start = start_of_week + timedelta(days=7)

    return render_template(
        'main/index.html', 
        schedule_by_day=schedule_by_day,
        week_dates=week_dates,
        prev_week=prev_week_start.strftime('%Y-%m-%d'),
        next_week=next_week_start.strftime('%Y-%m-%d'),
        page_title=f"周工作计划 ({start_of_week.strftime('%Y/%m/%d')} - {end_of_week.strftime('%Y/%m/%d')})"
    )

@main_bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task_date_str = request.form.get('task_date')
    content = request.form.get('content')
    personnel = request.form.get('personnel')

    if not all([task_date_str, content, personnel]):
        flash('所有字段都是必填项。', 'danger')
    else:
        task_date = datetime.strptime(task_date_str, '%Y-%m-%d').date()
        new_task = WorkSchedule(
            task_date=task_date,
            content=content,
            personnel=personnel,
            author_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
        log_activity('创建任务', f"内容: {content}, 日期: {task_date_str}")
        flash('新任务已添加。', 'success')

    return redirect(url_for('main.index', start_date=task_date_str))

@main_bp.route('/api/update_task', methods=['POST'])
@login_required
def update_task():
    data = request.get_json()
    task_id = data.get('id')
    field = data.get('field')
    value = data.get('value')

    task = WorkSchedule.query.get_or_404(task_id)

    # 简单的权限检查 (可选，例如只允许作者编辑)
    # if task.author_id != current_user.id:
    #     return jsonify({'success': False, 'error': 'Permission denied'}), 403

    if hasattr(task, field):
        setattr(task, field, value)
        db.session.commit()
        log_activity('更新任务', f"更新任务ID {task_id} 的字段 '{field}' 为 '{value}'")
        return jsonify({'success': True, 'message': '任务已更新。'})

    return jsonify({'success': False, 'error': 'Invalid field'}), 400

@main_bp.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = WorkSchedule.query.get_or_404(task_id)
    start_date = task.task_date - timedelta(days=task.task_date.weekday())

    # 权限检查
    # if task.author_id != current_user.id:
    #     flash('您没有权限删除此任务。', 'danger')
    #     return redirect(url_for('main.index', start_date=start_date.strftime('%Y-%m-%d')))

    log_activity('删除任务', f"删除任务ID {task_id}, 内容: '{task.content}'")
    db.session.delete(task)
    db.session.commit()
    flash('任务已删除。', 'success')
    return redirect(url_for('main.index', start_date=start_date.strftime('%Y-%m-%d')))

@main_bp.route('/export_excel', methods=['POST'])
@login_required
def export_excel():
    start_date_str = request.form.get('start_date')

    week_dates = get_week_dates(start_date_str)
    start_of_week = week_dates[0]
    end_of_week = week_dates[-1]

    tasks = WorkSchedule.query.filter(
        WorkSchedule.task_date.between(start_of_week, end_of_week)
    ).order_by(WorkSchedule.task_date).all()

    if not tasks:
        flash('该周没有可导出的数据。', 'warning')
        return redirect(url_for('main.index', start_date=start_date_str))

    data = {
        '日期': [t.task_date.strftime('%Y-%m-%d') for t in tasks],
        '工作内容': [t.content for t in tasks],
        '负责人': [t.personnel for t in tasks],
        '创建人': [t.author.username for t in tasks]
    }
    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='周工作计划')
        workbook = writer.book
        worksheet = writer.sheets['周工作计划']

        # 调整列宽
        for i, col in enumerate(df.columns, 1):
            column_letter = get_column_letter(i)
            max_length = max(df[col].astype(str).map(len).max(), len(col))
            worksheet.column_dimensions[column_letter].width = max_length + 2

        # 加粗表头
        for cell in worksheet["1:1"]:
            cell.font = openpyxl.styles.Font(bold=True)

    output.seek(0)

    log_activity('导出Excel', f"导出了 {start_of_week} 到 {end_of_week} 的工作计划。")

    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename=work_schedule_{start_of_week}_to_{end_of_week}.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response

@main_bp.route('/logs')
@login_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=20)
    return render_template('main/logs.html', logs=logs, title="操作日志")
