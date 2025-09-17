document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const taskModalElement = document.getElementById('taskModal');
    if (!taskModalElement) return;

    const taskModal = new bootstrap.Modal(taskModalElement);
    const taskForm = document.getElementById('taskForm');
    const taskModalLabel = document.getElementById('taskModalLabel');

    const formTaskId = document.getElementById('taskFormTaskId');
    const formAction = document.getElementById('taskFormAction');
    const formContent = document.getElementById('taskFormContent');
    const formPersonnel = document.getElementById('taskFormPersonnel');
    const formStartDate = document.getElementById('taskFormStartDate');
    const formEndDate = document.getElementById('taskFormEndDate');

    // --- 初始化拖拽排序 ---
    document.querySelectorAll('.task-list-container').forEach(container => {
        new Sortable(container, {
            animation: 150,
            group: 'shared',
            ghostClass: 'blue-background-class',
            onEnd: function (evt) {
                const taskId = evt.item.dataset.taskId;
                if (evt.from !== evt.to) {
                    const newDate = evt.to.dataset.date;
                    updateTaskDate(taskId, newDate);
                }
                updateOrder(evt.from);
                if (evt.from !== evt.to) {
                    updateOrder(evt.to);
                }
            }
        });
    });

    async function updateOrder(container) {
        const taskIds = Array.from(container.children).map(card => card.dataset.taskId);
        fetch('/api/update_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ task_ids: taskIds })
        });
    }

    async function updateTaskDate(taskId, newDate) {
        fetch(`/api/update_task/${taskId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ task_date: newDate })
        });
    }

    // --- 统一处理模态框的打开事件 ---
    document.body.addEventListener('click', async function(event) {
        const addBtn = event.target.closest('.add-task-btn');
        const editBtn = event.target.closest('.edit-task-btn');

        if (addBtn) {
            taskModalLabel.textContent = '添加新任务';
            formAction.value = 'add';
            taskForm.reset();
            formTaskId.value = '';
            
            const date = addBtn.dataset.date;
            formStartDate.value = date;
            formEndDate.value = date;
            formEndDate.min = date;
            
            formEndDate.parentElement.parentElement.style.display = 'flex';
        }

        if (editBtn) {
            taskModalLabel.textContent = '编辑任务';
            formAction.value = 'edit';
            taskForm.reset();
            
            const taskId = editBtn.dataset.taskId;
            const response = await fetch(`/api/get_task/${taskId}`);
            if (response.ok) {
                const task = await response.json();
                formTaskId.value = task.id;
                formContent.value = task.content;
                formPersonnel.value = task.personnel;
                formStartDate.value = task.task_date;
                
                formEndDate.parentElement.parentElement.style.display = 'none';
            } else {
                alert('无法加载任务详情。');
                taskModal.hide();
            }
        }
    });

    // --- 统一处理模态框的表单提交事件 ---
    taskForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const action = formAction.value;
        let response;
        
        try {
            if (action === 'add') {
                const formData = new FormData(taskForm);
                
                // 【关键修正】这里使用标准的相对路径 /add_task
                response = await fetch("/add_task", {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-CSRFToken': csrfToken }
                });
            } else if (action === 'edit') {
                const taskId = formTaskId.value;
                const data = {
                    content: formContent.value,
                    personnel: formPersonnel.value,
                    task_date: formStartDate.value
                };
                response = await fetch(`/api/update_task/${taskId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify(data)
                });
            }

            if (response.ok) {
                location.reload();
            } else {
                const errorData = await response.json();
                alert(errorData.error || `操作失败 (状态码: ${response.status})`);
            }
        } catch (error) {
            console.error('An error occurred:', error);
            alert('发生网络错误或无法解析服务器响应。');
        } finally {
            taskModal.hide();
        }
    });

    // 联动开始和结束日期
    formStartDate.addEventListener('change', function() {
        if (!formEndDate.value || formEndDate.value < this.value) {
            formEndDate.value = this.value;
        }
        formEndDate.min = this.value;
    });
});