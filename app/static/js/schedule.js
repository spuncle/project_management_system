document.addEventListener('DOMContentLoaded', function () {
    // --- 1. 变量定义与初始化 ---
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // 模态框 DOM 元素与 Bootstrap 实例
    const taskModalElement = document.getElementById('taskModal');
    const conflictModalElement = document.getElementById('conflictResolutionModal');
    if (!taskModalElement || !conflictModalElement) {
        console.error("关键的模态框HTML元素未找到，脚本无法执行。");
        return; // 如果关键元素不存在，则终止脚本执行
    }
    const taskModal = new bootstrap.Modal(taskModalElement);
    const conflictModal = new bootstrap.Modal(conflictModalElement);

    // 任务表单相关的 DOM 元素
    const taskForm = document.getElementById('taskForm');
    const taskModalLabel = document.getElementById('taskModalLabel');
    const formTaskId = document.getElementById('taskFormTaskId');
    const formAction = document.getElementById('taskFormAction');
    const formVersion = document.getElementById('taskFormVersion');
    const formContent = document.getElementById('taskFormContent');
    const formPersonnel = document.getElementById('taskFormPersonnel');
    const formStartDate = document.getElementById('taskFormStartDate');
    const formEndDate = document.getElementById('taskFormEndDate');

    // --- 2. 拖拽排序功能 (带权限检查) ---
    
    // USER_CAN_EDIT 这个全局变量由 index.html 模板通过 <script> 标签提供
    if (typeof USER_CAN_EDIT !== 'undefined' && USER_CAN_EDIT) {
        document.querySelectorAll('.task-list-container').forEach(container => {
            new Sortable(container, {
                animation: 150,
                group: 'shared', // 允许在不同日期列之间拖拽
                ghostClass: 'blue-background-class',
                onEnd: function (evt) {
                    const taskId = evt.item.dataset.taskId;

                    // 如果任务被拖拽到了新的日期列
                    if (evt.from !== evt.to) {
                        const newDate = evt.to.dataset.date;
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
    }

    async function updateOrder(container) {
        const taskIds = Array.from(container.children).map(card => card.dataset.taskId);
        fetch('/api/update_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ task_ids: taskIds })
        });
    }

    async function updateTaskDate(taskId, newDate) {
        // 这个API调用只更新日期，顺序由 updateOrder 处理
        fetch(`/api/update_task/${taskId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ task_date: newDate })
        });
    }

    // --- 3. 统一的模态框打开事件处理 ---
    document.body.addEventListener('click', async function(event) {
        const addBtn = event.target.closest('.add-task-btn');
        const editBtn = event.target.closest('.edit-task-btn');

        // 处理“添加”按钮点击
        if (addBtn) {
            taskModalLabel.textContent = '添加新任务';
            formAction.value = 'add';
            taskForm.reset();
            formTaskId.value = '';
            
            const date = addBtn.dataset.date;
            formStartDate.value = date;
            formEndDate.value = date; // 默认开始和结束日期是同一天
            formEndDate.min = date;
            
            // 确保结束日期输入框可见
            formEndDate.parentElement.parentElement.style.display = 'flex';
        }

        // 处理“编辑”按钮点击
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
                    
                    // 编辑时隐藏结束日期输入框
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

    // --- 4. 统一的模态框表单提交事件处理 ---
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
                    task_date: formStartDate.value,
                    version: parseInt(formVersion.value)
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

    // --- 5. 冲突解决逻辑 ---
    function handleConflict(currentData, yourData) {
        taskModal.hide();
        
        // 填充冲突模态框的内容
        document.getElementById('conflictCurrentContent').textContent = `内容: ${currentData.content}\n人员: ${currentData.personnel}`;
        document.getElementById('conflictYourContent').textContent = `内容: ${yourData.content}\n人员: ${yourData.personnel}`;
        
        conflictModal.show();

        // 为“强制覆盖”按钮绑定一次性点击事件
        const overwriteBtn = document.getElementById('conflictOverwriteBtn');
        const newOverwriteBtn = overwriteBtn.cloneNode(true); // 复制按钮以移除旧的监听器
        overwriteBtn.parentNode.replaceChild(newOverwriteBtn, overwriteBtn);

        newOverwriteBtn.addEventListener('click', async () => {
            yourData.version = currentData.version; // 使用从服务器获取的最新版本号
            const taskId = formTaskId.value;

            const response = await fetch(`/api/update_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(yourData)
            });

            if(response.ok) {
                location.reload();
            } else {
                alert('覆盖失败，可能发生了新的冲突。请刷新页面。');
                conflictModal.hide();
            }
        });

        // “放弃修改”按钮的逻辑
        document.getElementById('conflictDiscardBtn').onclick = () => {
            conflictModal.hide();
        };
    }

    // --- 6. 辅助逻辑：联动开始和结束日期 ---
    formStartDate.addEventListener('change', function() {
        if (!formEndDate.value || formEndDate.value < this.value) {
            formEndDate.value = this.value;
        }
        formEndDate.min = this.value;
    });
});