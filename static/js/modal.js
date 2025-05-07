// Simple Modal Implementation
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking for modal');
    
    // Check if modal exists 
    const modal = document.getElementById('taskModal');
    console.log('Modal element:', modal);
    
    if (modal) {
        console.log('Modal found, setting up event listeners');
        
        // Get all task name links and view buttons
        const taskLinks = document.querySelectorAll('.task-name-link, .btn-view');
        console.log('Task links found:', taskLinks.length);
        
        // Add click event to all task links
        taskLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Link clicked', this);
                
                const taskId = this.getAttribute('data-task-id');
                console.log('Task ID:', taskId);
                
                // Update modal content
                document.getElementById('modalTaskTitle').textContent = 'Задача #' + taskId;
                document.getElementById('modalTaskId').textContent = 'ID: ' + taskId;
                
                // Show modal
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
                
                // Add show class after small delay for animation
                setTimeout(() => {
                    modal.classList.add('show');
                }, 10);
                
                // Fetch task data from API
                fetch(`/api/task/${taskId}/`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Ошибка при загрузке задачи');
                        }
                        return response.json();
                    })
                    .then(task => {
                        console.log('Task data:', task);
                        
                        // Update modal content with task data
                        document.getElementById('modalTaskTitle').textContent = task.name || 'Без названия';
                        document.getElementById('modalTaskId').textContent = `ID: ${task.id}`;
                        
                        // Update other fields
                        if (document.getElementById('modalTaskProject')) {
                            document.getElementById('modalTaskProject').textContent = 
                                task.project && task.project.name ? task.project.name : 'Не указан';
                        }
                        
                        if (document.getElementById('modalTaskAssignee')) {
                            if (task.assignees && task.assignees.length > 0) {
                                document.getElementById('modalTaskAssignee').textContent = 
                                    task.assignees.map(a => a.name).join(', ');
                            } else {
                                document.getElementById('modalTaskAssignee').textContent = 'Не назначен';
                            }
                        }
                        
                        if (document.getElementById('modalTaskPriority')) {
                            document.getElementById('modalTaskPriority').textContent = 
                                task.priority && task.priority.name ? task.priority.name : 'Обычный';
                        }
                        
                        if (document.getElementById('modalTaskStatus')) {
                            if (task.status && task.status.name) {
                                const statusElem = document.getElementById('modalTaskStatus');
                                const statusName = task.status.name.toLowerCase().replace(/\s+/g, '');
                                
                                statusElem.className = 'apple-status-badge ' + statusName;
                                statusElem.textContent = task.status.name;
                            } else {
                                document.getElementById('modalTaskStatus').textContent = 'Не указан';
                            }
                        }
                        
                        if (document.getElementById('modalTaskDateStart')) {
                            document.getElementById('modalTaskDateStart').textContent = 
                                task.startDateTime ? formatDate(task.startDateTime) : 'Не указана';
                        }
                        
                        if (document.getElementById('modalTaskDateEnd')) {
                            document.getElementById('modalTaskDateEnd').textContent = 
                                task.endDateTime ? formatDate(task.endDateTime) : 'Не указана';
                        }
                        
                        if (document.getElementById('modalTaskDescription')) {
                            if (task.description) {
                                document.getElementById('modalTaskDescription').innerHTML = task.description;
                            } else {
                                document.getElementById('modalTaskDescription').textContent = 'Описание отсутствует';
                            }
                        }
                        
                        // Set task ID for integrate button
                        if (document.getElementById('modalIntegrateButton')) {
                            document.getElementById('modalIntegrateButton').setAttribute('data-task-id', task.id);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching task data:', error);
                    });
            });
        });
        
        // Close modal when clicking the close button
        const closeBtn = modal.querySelector('.apple-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                console.log('Close button clicked');
                
                // Remove show class
                modal.classList.remove('show');
                
                // Hide modal after animation completes
                setTimeout(() => {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }, 300);
            });
        }
        
        // Close modal when clicking outside the content
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                console.log('Clicked outside modal content');
                
                // Remove show class
                modal.classList.remove('show');
                
                // Hide modal after animation completes
                setTimeout(() => {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }, 300);
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && modal.style.display === 'block') {
                console.log('Escape key pressed');
                
                // Remove show class
                modal.classList.remove('show');
                
                // Hide modal after animation completes
                setTimeout(() => {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }, 300);
            }
        });
        
        // Handle integrate button click
        const modalIntegrateButton = document.getElementById('modalIntegrateButton');
        if (modalIntegrateButton) {
            modalIntegrateButton.addEventListener('click', function() {
                const taskId = this.getAttribute('data-task-id');
                if (!taskId) return;
                
                // Get button elements
                const buttonText = this.querySelector('.button-text');
                const spinner = this.querySelector('.loading-spinner');
                
                // Show loading state
                if (buttonText && spinner) {
                    buttonText.style.display = 'none';
                    spinner.style.display = 'inline-block';
                }
                this.disabled = true;
                
                // Send request to integrate task
                fetch(`/planfix/task/${taskId}/integrate/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Ошибка при интеграции с Claude');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        showNotification('success', 'Успешно!', 'Задача добавлена в чат с Claude');
                        
                        // Redirect to conversation
                        window.location.href = `/conversation/${data.conversation_id}/`;
                    } else {
                        throw new Error(data.error || 'Произошла ошибка');
                    }
                })
                .catch(error => {
                    // Restore button state
                    if (buttonText && spinner) {
                        buttonText.style.display = '';
                        spinner.style.display = 'none';
                    }
                    this.disabled = false;
                    
                    // Show error notification
                    showNotification('error', 'Ошибка!', error.message);
                });
            });
        }
    }
});

// Helper function to format date
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'Некорректная дата';
    
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Helper function to show notification
function showNotification(type, title, message) {
    let notification = document.getElementById('notification');
    
    if (!notification) {
        // Create notification element if it doesn't exist
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.className = 'apple-notification';
        notification.innerHTML = `
            <div class="apple-notification-content">
                <div id="notification-icon" class="apple-notification-icon"></div>
                <div class="apple-notification-text">
                    <div id="notification-title" class="apple-notification-title"></div>
                    <div id="notification-message" class="apple-notification-message"></div>
                </div>
                <button id="notification-close" class="apple-notification-close">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;
        document.body.appendChild(notification);
    }
    
    // Set notification class based on type
    notification.className = 'apple-notification ' + type;
    
    // Get notification elements
    const notificationIcon = document.getElementById('notification-icon');
    const notificationTitle = document.getElementById('notification-title');
    const notificationMessage = document.getElementById('notification-message');
    const notificationClose = document.getElementById('notification-close');
    
    // Set content based on type
    if (type === 'success') {
        notificationIcon.innerHTML = '✓';
    } else if (type === 'error') {
        notificationIcon.innerHTML = '✗';
    } else {
        notificationIcon.innerHTML = 'ℹ';
    }
    
    notificationTitle.textContent = title;
    notificationMessage.textContent = message;
    
    // Show notification
    notification.style.display = 'block';
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto hide after 5 seconds
    const timeoutId = setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.style.display = 'none';
        }, 300);
    }, 5000);
    
    // Close on button click
    notificationClose.addEventListener('click', () => {
        clearTimeout(timeoutId);
        notification.classList.remove('show');
        setTimeout(() => {
            notification.style.display = 'none';
        }, 300);
    });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}