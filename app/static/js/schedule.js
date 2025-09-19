document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const taskModalElement = document.getElementById('taskModal');
    const conflictModalElement = document.getElementById('conflictResolutionModal');
    if (!taskModalElement || !conflictModalElement) {
        console.error("关键的模态框HTML元素未找到，脚本无法执行。");
        return;
    }
    const taskModal = new bootstrap.Modal(taskModalElement);
    const conflictModal = new bootstrap.Modal(conflictModalElement);
    const taskForm = document.getElementById('taskForm');
    const taskModalLabel = document.getElementById('taskModalLabel');
    const formTaskId = document.getElementById('taskFormTaskId');
    const formAction = document.getElementById('taskFormAction');
    const formVersion = document.getElementById('taskFormVersion');
    const formContent = document.getElementById('taskFormContent');
    const formPersonnel = document.getElementById('taskFormPersonnel');
    const formStartDate = document.getElementById('taskFormStartDate');
    const formEndDate = document.getElementById('taskFormEndDate');

    if (typeof USER_CAN_EDIT !== 'undefined' && USER_CAN_EDIT) {
        document.querySelectorAll('.task-list-container').forEach(container => {
            new Sortable(container, {
                animation: 150,
                group: 'shared',
                ghostClass: 'blue-background-class',
                onEnd: function (evt) {
                    const taskId = evt.item.dataset.taskId;
                    const taskVersion = evt.item.dataset.taskVersion;
                    
                    if (evt.from !== evt.to) {
                        const newDate = evt.to.dataset.date;
                        updateTaskDate(taskId, newDate, taskVersion);
                    }
                    
                    updateOrder(evt.from);
                    if (evt.from !== evt.to) {
                        updateOrder(evt.to);
                    }
                    
                    checkAndToggleEmptyPlaceholder(evt.from);
                    checkAndToggleEmptyPlaceholder(evt.to);
                }
            });
        });
    }

    function checkAndToggleEmptyPlaceholder(container) {
        if (!container) return;
        const placeholder = container.querySelector('.empty-day-placeholder');
        const taskCards = container.querySelectorAll('.task-card');
        if (taskCards.length === 0 && !placeholder) {
            const p = document.createElement('p');
            p.className = 'empty-day-placeholder';
            p.textContent = '(空)';
            container.appendChild(p);
        } else if (taskCards.length > 0 && placeholder) {
            placeholder.remove();
        }
    }

    async function updateOrder(container) {
        const tasks = Array.from(container.querySelectorAll('.task-card'))
            .map(card => ({
                id: parseInt(card.dataset.taskId),
                version: parseInt(card.dataset.taskVersion)
            }));
        
        if (tasks.length === 0) return;

        try {
            const response = await fetch('/api/update_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ tasks: tasks })
            });
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.error || "顺序更新失败，页面将刷新。");
                location.reload();
            } else {
                 // 成功后刷新，以获取后端生成的新版本号
                 location.reload();
            }
        } catch (error) {
            alert("网络错误，顺序更新失败。");
            location.reload();
        }
    }

    async function updateTaskDate(taskId, newDate, taskVersion) {
        try {
            const response = await fetch(`/api/update_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ 
                    task_date: newDate,
                    version: parseInt(taskVersion)
                })
            });
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.error || "移动任务失败，页面将刷新。");
                location.reload();
            }
        } catch (error) {
            alert("网络错误，移动任务失败。");
            location.reload();
        }
    }

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
            try {
                const response = await fetch(`/api/get_task/${taskId}`);
                if (response.ok) {
                    const task = await response.json();
                    formTaskId.value = task.id;
                    formContent.value = task.content;
                    formPersonnel.value = task.personnel;
                    formStartDate.value = task.task_date;
                    formVersion.value = task.version;
                    formEndDate.parentElement.parentElement.style.display = 'none';
                } else {
                    alert('无法加载任务详情，请刷新页面后重试。');
                    taskModal.hide();
                }
            } catch (error) {
                console.error("加载任务详情失败:", error);
                alert('网络错误，无法加载任务详情。');
            }
        }
    });

    taskForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const action = formAction.value;
        let response;
        
        try {
            if (action === 'add') {
                const formData = new FormData(taskForm);
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
                    task_date: formStartDate.value,
                    version: parseInt(formVersion.value)
                };
                response = await fetch(`/api/update_task/${taskId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify(data)
                });
            }

            if (response.ok) {
                location.reload();
            } else if (response.status === 409) {
                const errorData = await response.json();
                handleConflict(errorData.current_data, {
                    content: formContent.value,
                    personnel: formPersonnel.value,
                });
            } else {
                const errorData = await response.json().catch(() => ({ error: '服务器返回了一个未知错误。' }));
                alert(errorData.error || `操作失败 (状态码: ${response.status})`);
            }
        } catch (error) {
            console.error('表单提交时发生错误:', error);
            alert('发生网络错误或无法解析服务器响应。');
        }
    });

    function handleConflict(currentData, yourData) {
        taskModal.hide();
        document.getElementById('conflictCurrentContent').textContent = `内容: ${currentData.content}\n人员: ${currentData.personnel}`;
        document.getElementById('conflictYourContent').textContent = `内容: ${yourData.content}\n人员: ${yourData.personnel}`;
        conflictModal.show();

        const overwriteBtn = document.getElementById('conflictOverwriteBtn');
        const newOverwriteBtn = overwriteBtn.cloneNode(true);
        overwriteBtn.parentNode.replaceChild(newOverwriteBtn, overwriteBtn);

        newOverwriteBtn.addEventListener('click', async () => {
            const taskId = formTaskId.value;
            const data = {
                content: yourData.content,
                personnel: yourData.personnel,
                task_date: formStartDate.value,
                version: currentData.version
            };

            const response = await fetch(`/api/update_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(data)
            });

            if(response.ok) {
                location.reload();
            } else {
                alert('覆盖失败，可能发生了新的冲突。请刷新页面。');
                conflictModal.hide();
            }
        });

        document.getElementById('conflictDiscardBtn').onclick = () => {
            conflictModal.hide();
        };
    }

    formStartDate.addEventListener('change', function() {
        if (!formEndDate.value || formEndDate.value < this.value) {
            formEndDate.value = this.value;
        }
        formEndDate.min = this.value;
    });
});