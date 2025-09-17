import pandas as pd
from io import BytesIO
from openpyxl.utils import get_column_letter
from flask import (render_template, request, jsonify, redirect, 
                   url_for, flash, Response, make_response)
from flask_login import login_required, current_user
from datetime import date, timedelta, datetime
from sqlalchemy import and_, func

from . import main_bp
from app import db
from app.models import WorkSchedule, ActivityLog, Personnel
from app.utils import log_activity

def get_week_dates(start_date_str=None):
    if start_date_str:
        try:
            base_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            base_date = date.today()
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

    # 判断当前是否为当前周，用于UI显示
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    is_current_week = (start_of_week == current_week_start)

    tasks = WorkSchedule.query.filter(
        WorkSchedule.task_date.between(start_of_week, end_of_week)
    ).order_by(WorkSchedule.task_date, WorkSchedule.position).all()
    
    personnel_list = Personnel.query.order_by(Personnel.name).all()
    
    schedule_by_day = {day: [] for day in week_dates}
    for task in tasks:
        if task.task_date in schedule_by_day:
            schedule_by_day[task.task_date].append(task)
        
    prev_week_start = start_of_week - timedelta(days=7)
    next_week_start = start_of_week + timedelta(days=7)

    return render_template(
        'main/index.html', 
        schedule_by_day=schedule_by_day,
        week_dates=week_dates,
        personnel_list=personnel_list,
        prev_week=prev_week_start.strftime('%Y-%m-%d'),
        next_week=next_week_start.strftime('%Y-%m-%d'),
        is_current_week=is_current_week,
        page_title=f"周工作计划 ({start_of_week.strftime('%Y/%m/%d')} - {end_of_week.strftime('%Y/%m/%d')})"
    )

@main_bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date') or start_date_str
    content = request.form.get('content')
    personnel = request.form.get('personnel')

    if not all([start_date_str, content, personnel]):
        flash('开始日期、工作内容和负责人均为必填项。', 'danger')
        return redirect(url_for('main.index'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('日期格式不正确。', 'danger')
        return redirect(url_for('main.index', start_date=start_date_str))

    current_date = start_date
    while current_date <= end_date:
        max_pos = db.session.query(func.max(WorkSchedule.position)).filter_by(task_date=current_date).scalar() or -1
        new_task = WorkSchedule(
            task_date=current_date,
            content=content,
            personnel=personnel,
            author_id=current_user.id,
            position=max_pos + 1
        )
        db.session.add(new_task)
        current_date += timedelta(days=1)
    
    db.session.commit()
    log_activity('创建任务', f"为日期 {start_date_str} 到 {end_date_str} 添加了任务: {content}")
    flash('新任务已添加。', 'success')
        
    return redirect(url_for('main.index', start_date=start_date_str))

@main_bp.route('/api/get_task/<int:task_id>')
@login_required
def get_task_details(task_id):
    task = WorkSchedule.query.get_or_404(task_id)
    return jsonify({
        'id': task.id,
        'task_date': task.task_date.strftime('%Y-%m-%d'),
        'content': task.content,
        'personnel': task.personnel
    })

@main_bp.route('/api/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = WorkSchedule.query.get_or_404(task_id)
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    task.content = data.get('content', task.content)
    task.personnel = data.get('personnel', task.personnel)
    
    new_date_str = data.get('task_date')
    if new_date_str:
        try:
            task.task_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    db.session.commit()
    log_activity('更新任务', f"更新了任务ID {task_id}")
    return jsonify({'success': True, 'message': '任务已更新。'})

@main_bp.route('/api/update_order', methods=['POST'])
@login_required
def update_order():
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if task_ids:
        case_statement = db.case(
            {task_id: index for index, task_id in enumerate(task_ids)},
            value=WorkSchedule.id
        )
        db.session.query(WorkSchedule).filter(WorkSchedule.id.in_(task_ids)).update(
            {'position': case_statement}, synchronize_session=False
        )
        db.session.commit()
        log_activity('调整任务顺序', f"更新了 {len(task_ids)} 个任务的顺序")
    
    return jsonify({'success': True})

@main_bp.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = WorkSchedule.query.get_or_404(task_id)
    start_date = task.task_date - timedelta(days=task.task_date.weekday())
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
    ).order_by(WorkSchedule.task_date, WorkSchedule.position).all()
    
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
        for i, col in enumerate(df.columns, 1):
            column_letter = get_column_letter(i)
            max_length = max(df[col].astype(str).map(len).max(), len(col))
            worksheet.column_dimensions[column_letter].width = max_length + 2
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