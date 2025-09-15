document.addEventListener('DOMContentLoaded', function() {
    const editableFields = document.querySelectorAll('.editable');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    editableFields.forEach(field => {
        field.addEventListener('click', function(event) {
            // 防止在input内部点击时再次触发
            if (event.target.tagName.toLowerCase() === 'input') {
                return;
            }

            const currentText = this.innerText;
            const originalHtml = this.innerHTML;
            const taskId = this.dataset.taskId;
            const fieldName = this.dataset.field;

            // 创建输入框
            const input = document.createElement('input');
            input.type = 'text';
            input.value = currentText;
            input.className = 'form-control input-edit';

            this.innerHTML = '';
            this.appendChild(input);
            input.focus();

            // 保存或取消的逻辑
            const handleBlur = async () => {
                const newValue = input.value.trim();

                // 如果值没有改变，则恢复原状
                if (newValue === currentText) {
                    this.innerHTML = originalHtml;
                    return;
                }

                // 发送Fetch请求
                try {
                    const response = await fetch('/api/update_task', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken 
                        },
                        body: JSON.stringify({
                            id: taskId,
                            field: fieldName,
                            value: newValue
                        })
                    });

                    const data = await response.json();

                    if (data.success) {
                        this.innerText = newValue; // 更新成功，显示新文本
                    } else {
                        console.error('Update failed:', data.error);
                        this.innerHTML = originalHtml; // 更新失败，恢复原状
                        alert('更新失败: ' + (data.error || '未知错误'));
                    }
                } catch (error) {
                    console.error('Fetch error:', error);
                    this.innerHTML = originalHtml; // 网络错误，恢复原状
                    alert('网络请求失败。');
                }
            };

            // 当输入框失去焦点时触发保存
            input.addEventListener('blur', handleBlur);

            // 按下Enter键也触发保存
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    input.blur();
                }
                if (e.key === 'Escape') {
                    // 按下Escape键取消编辑
                    this.innerHTML = originalHtml;
                    input.removeEventListener('blur', handleBlur); // 移除监听以防重复触发
                }
            });
        });
    });
});
