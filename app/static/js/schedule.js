document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
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
        // 点击“添加”按钮
        if (event.target.closest('.add-task-btn')) {
            const button = event.target.closest('.add-task-btn');
            taskModalLabel.textContent = '添加新任务';
            formAction.value = 'add';
            taskForm.reset();
            formTaskId.value = '';
            
            const date = button.dataset.date;
            formStartDate.value = date;
            formEndDate.value = date; // 默认为当天
            formEndDate.min = date;
            
            // 显示结束日期输入框
            formEndDate.parentElement.style.display = 'block';
        }

        // 点击“编辑”按钮
        if (event.target.closest('.edit-task-btn')) {
            const button = event.target.closest('.edit-task-btn');
            taskModalLabel.textContent = '编辑任务';
            formAction.value = 'edit';
            taskForm.reset();
            
            const taskId = button.dataset.taskId;
            const response = await fetch(`/api/get_task/${taskId}`);
            if (response.ok) {
                const task = await response.json();
                formTaskId.value = task.id;
                formContent.value = task.content;
                formPersonnel.value = task.personnel;
                formStartDate.value = task.task_date;
                
                // 编辑时隐藏结束日期，因为只修改单条记录
                formEndDate.parentElement.style.display = 'none';
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
        
        if (action === 'add') {
            // 添加新任务，使用传统的表单提交
            const formData = new FormData(taskForm);
            formData.append('csrf_token', csrfToken);

            fetch("{{ url_for('main.add_task') }}", {
                method: 'POST',
                body: formData
            }).then(response => {
                if(response.ok) location.reload();
                else alert('添加失败。');
            });

        } else if (action === 'edit') {
            // 编辑任务，使用API
            const taskId = formTaskId.value;
            const data = {
                content: formContent.value,
                personnel: formPersonnel.value,
                task_date: formStartDate.value
            };

            const response = await fetch(`/api/update_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                location.reload(); 
            } else {
                alert('更新失败。');
            }
        }
        taskModal.hide();
    });

    // 联动开始和结束日期
    formStartDate.addEventListener('change', function() {
        if (!formEndDate.value || formEndDate.value < this.value) {
            formEndDate.value = this.value;
        }
        formEndDate.min = this.value;
    });
});