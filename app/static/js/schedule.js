document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const editTaskModal = new bootstrap.Modal(document.getElementById('editTaskModal'));
    const editTaskForm = document.getElementById('editTaskForm');
    const editTaskIdField = document.getElementById('editTaskId');
    const editTaskDateField = document.getElementById('editTaskDate');
    const editTaskContentField = document.getElementById('editTaskContent');
    const editTaskPersonnelField = document.getElementById('editTaskPersonnel');

    // --- 功能1: 初始化拖拽排序 ---
    document.querySelectorAll('.task-list-container').forEach(container => {
        new Sortable(container, {
            animation: 150,
            group: 'shared', // 可以在不同日期之间拖拽
            ghostClass: 'blue-background-class',
            onEnd: function (evt) {
                const targetContainer = evt.to;
                const taskIds = Array.from(targetContainer.children).map(card => card.dataset.taskId);
                const newDate = targetContainer.dataset.date;
                const taskId = evt.item.dataset.taskId;

                // 如果任务被拖拽到了新的日期
                if (evt.from !== evt.to) {
                    updateTaskDate(taskId, newDate);
                }
                
                // 更新源列表和目标列表的顺序
                updateOrder(evt.from);
                if (evt.from !== evt.to) {
                    updateOrder(evt.to);
                }
            }
        });
    });

    async function updateOrder(container) {
        const taskIds = Array.from(container.children).map(card => card.dataset.taskId);
        await fetch('/api/update_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ task_ids: taskIds })
        });
    }

    async function updateTaskDate(taskId, newDate) {
        // 这是一个简化的更新，仅更新日期
        // 注意：这会触发两次数据库更新（一次日期，一次顺序），可以优化
        await fetch(`/api/update_task/${taskId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ task_date: newDate })
        });
    }

    // --- 功能2: 处理任务编辑模态框 ---
    document.body.addEventListener('click', async function(event) {
        if (event.target.closest('.edit-task-btn')) {
            const button = event.target.closest('.edit-task-btn');
            const taskId = button.dataset.taskId;
            
            // 获取任务详情并填充表单
            const response = await fetch(`/api/get_task/${taskId}`);
            if (response.ok) {
                const task = await response.json();
                editTaskIdField.value = task.id;
                editTaskDateField.value = task.task_date;
                editTaskContentField.value = task.content;
                editTaskPersonnelField.value = task.personnel;
            } else {
                alert('无法加载任务详情。');
            }
        }
    });

    // 提交编辑表单
    editTaskForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const taskId = editTaskIdField.value;
        const data = {
            task_date: editTaskDateField.value,
            content: editTaskContentField.value,
            personnel: editTaskPersonnelField.value
        };

        const response = await fetch(`/api/update_task/${taskId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            editTaskModal.hide();
            // 简单地刷新页面来显示更新
            location.reload(); 
        } else {
            alert('更新失败。');
        }
    });

    // --- 功能3: 添加多日任务的日期逻辑 (可选) ---
    const addTaskStartDate = document.getElementById('addTaskStartDate');
    const addTaskEndDate = document.getElementById('addTaskEndDate');
    if(addTaskStartDate && addTaskEndDate) {
        addTaskStartDate.addEventListener('change', function() {
            // 确保结束日期不早于开始日期
            if (!addTaskEndDate.value || addTaskEndDate.value < this.value) {
                addTaskEndDate.value = this.value;
            }
            addTaskEndDate.min = this.value;
        });
    }
});