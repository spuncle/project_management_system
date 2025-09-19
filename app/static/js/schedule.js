// --- 【修改】Toast 函数，统一使用灰色系 ---
function showToast(message, type = 'info') {
    const toastElement = document.getElementById('appToast');
    if (!toastElement) return;

    const toastBody = toastElement.querySelector('.toast-body');
    const closeButton = toastElement.querySelector('.btn-close');
    const toast = new bootstrap.Toast(toastElement);

    // 移除所有可能的颜色类
    toastElement.classList.remove('text-bg-success', 'text-bg-danger', 'text-bg-info', 'text-bg-warning', 'text-bg-secondary');
    
    // 统一设置为灰色系，并确保关闭按钮可见
    toastElement.classList.add('text-bg-secondary'); // Bootstrap 的标准灰色
    closeButton.classList.add('btn-close-white'); // 在深色背景上使用白色关闭按钮

    toastBody.textContent = message;
    toast.show();
}


document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const taskModalElement = document.getElementById('taskModal');
    const conflictModalElement = document.getElementById('conflictResolutionModal');
    if (!taskModalElement || !conflictModalElement) {
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

    const personnelInput = document.getElementById('taskFormPersonnel');
    const tagify = new Tagify(personnelInput, {
        whitelist: typeof PERSONNEL_WHITELIST !== 'undefined' ? PERSONNEL_WHITELIST : [],
        dropdown: {
            maxItems: 20,
            enabled: 0,
            closeOnSelect: false
        }
    });

    if (typeof USER_CAN_EDIT !== 'undefined' && USER_CAN_EDIT) {
        document.querySelectorAll('.task-list-container').forEach(container => {
            new Sortable(container, {
                animation: 150,
                group: 'shared',
                ghostClass: 'blue-background-class',
                onEnd: async function (evt) {
                    const movedTaskElement = evt.item;
                    const fromContainer = evt.from;
                    const toContainer = evt.to;
                    
                    const payload = {
                        moved_task: {
                            id: parseInt(movedTaskElement.dataset.taskId),
                            version: parseInt(movedTaskElement.dataset.taskVersion)
                        },
                        target_list: {
                            date: toContainer.dataset.date,
                            task_ids: Array.from(toContainer.querySelectorAll('.task-card')).map(card => card.dataset.taskId)
                        }
                    };

                    if (fromContainer !== toContainer) {
                        payload.source_list = {
                            date: fromContainer.dataset.date,
                            task_ids: Array.from(fromContainer.querySelectorAll('.task-card')).map(card => card.dataset.taskId)
                        };
                    }
                    
                    try {
                        const response = await fetch('/api/reorder_tasks', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                            body: JSON.stringify(payload)
                        });

                        if (!response.ok) {
                            const errorData = await response.json();
                            showToast(errorData.error || "操作失败，页面将刷新以同步最新状态。", 'danger');
                            setTimeout(() => location.reload(), 2000);
                        } else {
                             location.reload();
                        }
                    } catch (error) {
                        showToast("网络错误，操作失败。页面将刷新。", 'danger');
                        setTimeout(() => location.reload(), 2000);
                    }
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

    document.body.addEventListener('click', async function(event) {
        const addBtn = event.target.closest('.add-task-btn');
        const editBtn = event.target.closest('.edit-task-btn');
        const deleteBtn = event.target.closest('.delete-task-btn');

        if (addBtn) {
            taskModalLabel.textContent = '添加新任务';
            formAction.value = 'add';
            taskForm.reset();
            tagify.removeAllTags();
            formTaskId.value = '';
            const date = addBtn.dataset.date;
            formStartDate.value = date;
            formEndDate.value = date;
            formEndDate.min = date;
            formEndDate.parentElement.parentElement.style.display = 'flex';
        }

        if (editBtn) {
            event.preventDefault();
            taskModalLabel.textContent = '编辑任务';
            formAction.value = 'edit';
            taskForm.reset();
            tagify.removeAllTags();
            const taskId = editBtn.dataset.taskId;
            try {
                const response = await fetch(`/api/get_task/${taskId}`);
                if (response.ok) {
                    const task = await response.json();
                    formTaskId.value = task.id;
                    formContent.value = task.content;
                    tagify.addTags(task.personnel);
                    formStartDate.value = task.task_date;
                    formVersion.value = task.version;
                    formEndDate.parentElement.parentElement.style.display = 'none';
                } else {
                    showToast('无法加载任务详情，请刷新页面后重试。', 'danger');
                    taskModal.hide();
                }
            } catch (error) {
                console.error("加载任务详情失败:", error);
                showToast('网络错误，无法加载任务详情。', 'danger');
            }
        }

        if (deleteBtn) {
            event.preventDefault();
            const taskId = deleteBtn.dataset.taskId;
            deleteTask(taskId, deleteBtn);
        }
    });

    async function deleteTask(taskId, buttonElement) {
        try {
            const response = await fetch(`/api/delete_task/${taskId}`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json();
            if (data.success) {
                showToast(data.message || '任务已删除。', 'success');
                const card = buttonElement.closest('.task-card');
                const container = card.parentElement;
                card.remove();
                checkAndToggleEmptyPlaceholder(container);
            } else {
                showToast(data.error || '删除失败。', 'danger');
            }
        } catch (error) {
            showToast('网络错误，删除失败。', 'danger');
        }
    }

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
                    personnel: tagify.value,
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
                    personnel: tagify.value.map(tag => tag.value),
                });
            } else {
                const errorData = await response.json().catch(() => ({ error: '服务器返回了一个未知错误。' }));
                showToast(errorData.error || `操作失败 (状态码: ${response.status})`, 'danger');
            }
        } catch (error) {
            console.error('表单提交时发生错误:', error);
            showToast('发生网络错误或无法解析服务器响应。', 'danger');
        }
    });

    function handleConflict(currentData, yourData) {
        taskModal.hide();
        const currentPersonnelStr = Array.isArray(currentData.personnel) ? currentData.personnel.join(', ') : currentData.personnel;
        const yourPersonnelStr = Array.isArray(yourData.personnel) ? yourData.personnel.join(', ') : yourData.personnel;

        document.getElementById('conflictCurrentContent').textContent = `内容: ${currentData.content}\n人员: ${currentPersonnelStr}`;
        document.getElementById('conflictYourContent').textContent = `内容: ${yourData.content}\n人员: ${yourPersonnelStr}`;
        conflictModal.show();

        const overwriteBtn = document.getElementById('conflictOverwriteBtn');
        const newOverwriteBtn = overwriteBtn.cloneNode(true);
        overwriteBtn.parentNode.replaceChild(newOverwriteBtn, overwriteBtn);

        newOverwriteBtn.addEventListener('click', async () => {
            const taskId = formTaskId.value;
            const data = {
                content: formContent.value,
                personnel: tagify.value,
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
                showToast('覆盖失败，可能发生了新的冲突。请刷新页面。', 'danger');
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