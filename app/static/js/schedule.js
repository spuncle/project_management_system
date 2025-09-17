document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
    const conflictModal = new bootstrap.Modal(document.getElementById('conflictResolutionModal'));
    const taskForm = document.getElementById('taskForm');
    const taskModalLabel = document.getElementById('taskModalLabel');

    const formTaskId = document.getElementById('taskFormTaskId');
    const formAction = document.getElementById('taskFormAction');
    const formVersion = document.getElementById('taskFormVersion');
    const formContent = document.getElementById('taskFormContent');
    const formPersonnel = document.getElementById('taskFormPersonnel');
    const formStartDate = document.getElementById('taskFormStartDate');
    const formEndDate = document.getElementById('taskFormEndDate');

    // ... 拖拽排序的逻辑无变化 ...
    if (typeof USER_CAN_EDIT !== 'undefined' && USER_CAN_EDIT) {
        // ... SortableJS 初始化代码 ...
    }
    async function updateOrder(container) { /* ... */ }
    async function updateTaskDate(taskId, newDate) { /* ... */ }


    // --- 统一处理模态框的打开事件 (增加了 version 字段) ---
    document.body.addEventListener('click', async function(event) {
        const addBtn = event.target.closest('.add-task-btn');
        const editBtn = event.target.closest('.edit-task-btn');

        if (addBtn) {
            // ... 添加逻辑无变化 ...
        }

        if (editBtn) {
            taskModalLabel.textContent = '编辑任务';
            formAction.value = 'edit';
            taskForm.action = '';
            taskForm.reset();
            
            const taskId = editBtn.dataset.taskId;
            const response = await fetch(`/api/get_task/${taskId}`);
            if (response.ok) {
                const task = await response.json();
                formTaskId.value = task.id;
                formContent.value = task.content;
                formPersonnel.value = task.personnel;
                formStartDate.value = task.task_date;
                formVersion.value = task.version; // <--- 【修改】填充版本号
                
                formEndDate.parentElement.parentElement.style.display = 'none';
            } else {
                alert('无法加载任务详情。');
                taskModal.hide();
            }
        }
    });

    // --- 统一处理模态框的表单提交事件 (重写) ---
    taskForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const action = formAction.value;
        
        if (action === 'add') {
            taskForm.method = 'POST';
            taskForm.action = '/add_task';
            const hiddenToken = document.createElement('input');
            hiddenToken.type = 'hidden';
            hiddenToken.name = 'csrf_token';
            hiddenToken.value = csrfToken;
            taskForm.appendChild(hiddenToken);
            taskForm.submit();
            return;
        } 
        
        if (action === 'edit') {
            const taskId = formTaskId.value;
            const data = {
                content: formContent.value,
                personnel: formPersonnel.value,
                task_date: formStartDate.value,
                version: parseInt(formVersion.value) // 发送版本号
            };

            try {
                const response = await fetch(`/api/update_task/${taskId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    location.reload();
                } else if (response.status === 409) { // --- 【修改】处理冲突 ---
                    const errorData = await response.json();
                    handleConflict(errorData.current_data, data);
                } else {
                    const errorData = await response.json();
                    alert(errorData.error || `操作失败 (状态码: ${response.status})`);
                }
            } catch (error) {
                console.error('An error occurred:', error);
                alert('发生网络错误。');
            }
        }
    });

    // --- 【新增】处理冲突的函数 ---
    function handleConflict(currentData, yourData) {
        taskModal.hide();
        
        document.getElementById('conflictCurrentContent').textContent = `内容: ${currentData.content}\n人员: ${currentData.personnel}`;
        document.getElementById('conflictYourContent').textContent = `内容: ${yourData.content}\n人员: ${yourData.personnel}`;
        
        conflictModal.show();

        document.getElementById('conflictOverwriteBtn').onclick = async () => {
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
        };

        document.getElementById('conflictDiscardBtn').onclick = () => {
            conflictModal.hide();
            // 不做任何操作，让用户停留在当前页面，可以重新点击编辑以获取最新数据
        };
    }

    // 联动开始和结束日期
    formStartDate.addEventListener('change', function() {
        if (!formEndDate.value || formEndDate.value < this.value) {
            formEndDate.value = this.value;
        }
        formEndDate.min = this.value;
    });
});