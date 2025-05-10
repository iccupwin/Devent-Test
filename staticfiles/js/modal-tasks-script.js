// Enhanced Task Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing enhanced task modal');
    
    // Set up modal functionality
    setupTaskModal();
    
    // Add theme toggle button
    addThemeToggle();
    
    // Check and apply current theme
    applyCurrentTheme();
});

// Function to set up modal functionality
function setupTaskModal() {
    const taskModal = document.getElementById('taskModal');
    if (!taskModal) {
        console.error('Task modal element not found');
        return;
    }
    
    console.log('Setting up task modal');
    
    // Get modal elements
    const modalClose = taskModal.querySelector('.apple-modal-close');
    const modalTaskTitle = document.getElementById('modalTaskTitle');
    const modalTaskId = document.getElementById('modalTaskId');
    const modalTaskProject = document.getElementById('modalTaskProject');
    const modalTaskAssignee = document.getElementById('modalTaskAssignee');
    const modalTaskPriority = document.getElementById('modalTaskPriority');
    const modalTaskStatus = document.getElementById('modalTaskStatus');
    const modalTaskDateStart = document.getElementById('modalTaskDateStart');
    const modalTaskDateEnd = document.getElementById('modalTaskDateEnd');
    const modalTaskDescription = document.getElementById('modalTaskDescription');
    const modalIntegrateButton = document.getElementById('modalIntegrateButton');
    
    // Close modal when clicking the close button
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            closeTaskModal();
        });
    }
    
    // Close modal when clicking outside the content
    taskModal.addEventListener('click', function(event) {
        if (event.target === taskModal) {
            closeTaskModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && taskModal.classList.contains('show')) {
            closeTaskModal();
        }
    });
    
    // Setup task name link click to open modal
    document.querySelectorAll('.task-name-link, .btn-view').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const taskId = this.getAttribute('data-task-id');
            if (taskId) {
                openTaskModal(taskId);
            }
        });
    });
    
    // Setup integrate button in modal
    if (modalIntegrateButton) {
        modalIntegrateButton.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            if (!taskId) return;
            
            integrateTaskWithClaude(taskId, this);
        });
    }
}

// Function to open task modal with task data
function openTaskModal(taskId) {
    const taskModal = document.getElementById('taskModal');
    if (!taskModal) return;
    
    // Show loading state in modal
    const modalTaskTitle = document.getElementById('modalTaskTitle');
    const modalTaskId = document.getElementById('modalTaskId');
    const modalTaskProject = document.getElementById('modalTaskProject');
    const modalTaskAssignee = document.getElementById('modalTaskAssignee');
    const modalTaskPriority = document.getElementById('modalTaskPriority');
    const modalTaskStatus = document.getElementById('modalTaskStatus');
    const modalTaskDateStart = document.getElementById('modalTaskDateStart');
    const modalTaskDateEnd = document.getElementById('modalTaskDateEnd');
    const modalTaskDescription = document.getElementById('modalTaskDescription');
    const modalIntegrateButton = document.getElementById('modalIntegrateButton');
    
    // Set loading state
    if (modalTaskTitle) modalTaskTitle.textContent = 'Загрузка...';
    if (modalTaskId) modalTaskId.textContent = `ID: ${taskId}`;
    if (modalTaskProject) modalTaskProject.textContent = '-';
    if (modalTaskAssignee) modalTaskAssignee.textContent = '-';
    if (modalTaskPriority) modalTaskPriority.textContent = '-';
    if (modalTaskStatus) {
        modalTaskStatus.className = 'apple-status-badge';
        modalTaskStatus.textContent = '-';
    }
    if (modalTaskDateStart) modalTaskDateStart.textContent = '-';
    if (modalTaskDateEnd) modalTaskDateEnd.textContent = '-';
    if (modalTaskDescription) modalTaskDescription.textContent = 'Загрузка данных задачи...';
    if (modalIntegrateButton) modalIntegrateButton.setAttribute('data-task-id', taskId);
    
    // Show modal and prevent body scrolling
    taskModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Trigger animation
    setTimeout(() => {
        taskModal.classList.add('show');
    }, 10);
    
    // Fetch task data
    fetch(`/api/task/${taskId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при загрузке задачи');
            }
            return response.json();
        })
        .then(task => {
            console.log('Task data loaded:', task);
            
            if (modalTaskTitle) modalTaskTitle.textContent = task.name || 'Без названия';
            if (modalTaskId) modalTaskId.textContent = `ID: ${task.id}`;
            
            // Project
            if (modalTaskProject) {
                modalTaskProject.textContent = task.project && task.project.name 
                    ? task.project.name 
                    : 'Не указан';
            }
            
            // Assignee
            if (modalTaskAssignee) {
                if (task.assignees && task.assignees.users && task.assignees.users.length > 0) {
                    const assigneeNames = task.assignees.users.map(assignee => {
                        const nameHash = (assignee.name.length + assignee.name.charCodeAt(0)) % 10;
                        return `<div class="assignee-wrapper">
                            <div class="assignee-avatar" data-color="${nameHash}">
                                ${assignee.name.charAt(0).toUpperCase()}
                            </div>
                            <span class="assignee-name">${assignee.name}</span>
                        </div>`;
                    }).join('  ');
                    modalTaskAssignee.innerHTML = assigneeNames;
                } else {
                    modalTaskAssignee.textContent = 'Не назначен';
                }
            }
            
            // Assigner
            const modalTaskAssigner = document.getElementById('modalTaskAssigner');
            if (modalTaskAssigner) {
                modalTaskAssigner.textContent = task.assigner && task.assigner.name 
                    ? task.assigner.name 
                    : 'Не указан';
            }
            
            // Priority
            if (modalTaskPriority) {
                modalTaskPriority.textContent = task.priority && task.priority.name 
                    ? task.priority.name 
                    : 'Обычный';
            }
            
            // Status
            if (modalTaskStatus) {
                if (task.status && task.status.name) {
                    const statusName = task.status.name.toLowerCase().replace(/\s+/g, '');
                    modalTaskStatus.className = 'apple-status-badge ' + statusName;
                    modalTaskStatus.textContent = task.status.name;
                    
                    // Disable integrate button if task is completed
                    if (modalIntegrateButton && 
                        (statusName === 'завершена' || statusName === 'завершенная' || 
                         statusName === 'выполненная' || task.status.id === 3)) {
                        modalIntegrateButton.disabled = true;
                    } else if (modalIntegrateButton) {
                        modalIntegrateButton.disabled = false;
                    }
                } else {
                    modalTaskStatus.className = 'apple-status-badge';
                    modalTaskStatus.textContent = 'Не указан';
                    if (modalIntegrateButton) modalIntegrateButton.disabled = false;
                }
            }
            
            // Dates
            if (modalTaskDateStart) {
                modalTaskDateStart.textContent = task.startDateTime 
                    ? formatDate(task.startDateTime) 
                    : 'Не указана';
            }
            
            if (modalTaskDateEnd) {
                modalTaskDateEnd.textContent = task.endDateTime 
                    ? formatDate(task.endDateTime) 
                    : 'Не указана';
            }
            
            // Description
            if (modalTaskDescription) {
                if (task.description) {
                    modalTaskDescription.innerHTML = task.description;
                } else {
                    modalTaskDescription.textContent = 'Описание отсутствует';
                }
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            if (modalTaskTitle) modalTaskTitle.textContent = 'Ошибка загрузки';
            if (modalTaskDescription) {
                modalTaskDescription.textContent = 'Не удалось загрузить данные задачи. Пожалуйста, попробуйте еще раз.';
            }
        });
}

// Function to close task modal
function closeTaskModal() {
    const taskModal = document.getElementById('taskModal');
    if (!taskModal) return;
    
    // Remove show class for animation
    taskModal.classList.remove('show');
    
    // Hide modal after animation
    setTimeout(() => {
        taskModal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }, 300);
}

// Function to integrate a task with Claude
function integrateTaskWithClaude(taskId, button) {
    // Save original button content
    const originalText = button.querySelector('.button-text');
    const spinner = button.querySelector('.loading-spinner');
    
    if (originalText && spinner) {
        // Show loading state
        originalText.style.display = 'none';
        spinner.style.display = 'inline-block';
        button.disabled = true;
    } else {
        // Fallback if button doesn't have the expected structure
        button.innerHTML = '<div class="loading-spinner"></div> Обработка...';
        button.disabled = true;
    }
    
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
        console.error('Integration error:', error);
        
        // Restore button state
        if (originalText && spinner) {
            originalText.style.display = 'inline';
            spinner.style.display = 'none';
            button.disabled = false;
        } else {
            button.innerHTML = 'Обсудить с Claude';
            button.disabled = false;
        }
        
        // Show error notification
        showNotification('error', 'Ошибка!', error.message);
    });
}

// Helper function to format date
function formatDate(dateInput) {
    if (!dateInput) return '';
    
    try {
        let date;
        
        if (typeof dateInput === 'object') {
            // Try to find a date property
            if (dateInput.dateFrom) {
                date = new Date(dateInput.dateFrom);
            } else if (dateInput.dateTo) {
                date = new Date(dateInput.dateTo);
            } else {
                // Try other properties
                for (let key in dateInput) {
                    if (typeof dateInput[key] === 'string' && dateInput[key].includes('-')) {
                        date = new Date(dateInput[key]);
                        if (!isNaN(date.getTime())) break;
                    }
                }
            }
        } else if (typeof dateInput === 'string') {
            date = new Date(dateInput);
        }
        
        if (!date || isNaN(date.getTime())) {
            console.warn('Invalid date:', dateInput);
            return 'Неверная дата';
        }
        
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        console.error('Error formatting date:', e);
        return 'Ошибка форматирования';
    }
}

// Function to show notification
function showNotification(type, title, message) {
    let notification = document.getElementById('notification');
    
    if (!notification) {
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
    } else {
        notification.className = 'apple-notification';
    }
    
    const notificationIcon = document.getElementById('notification-icon');
    const notificationTitle = document.getElementById('notification-title');
    const notificationMessage = document.getElementById('notification-message');
    const notificationClose = document.getElementById('notification-close');
    
    // Set content
    if (type === 'success') {
        notificationIcon.innerHTML = '✓';
        notification.classList.add('success');
    } else if (type === 'error') {
        notificationIcon.innerHTML = '✗';
        notification.classList.add('error');
    } else {
        notificationIcon.innerHTML = 'ℹ';
        notification.classList.add('info');
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

// Functions for theme switching
function addThemeToggle() {
    // Check if theme toggle already exists
    if (document.querySelector('.theme-toggle')) return;
    
    // Create theme toggle button
    const themeToggle = document.createElement('div');
    themeToggle.className = 'theme-toggle';
    themeToggle.innerHTML = `
        <svg id="light-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
        <svg id="dark-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
        </svg>
    `;
    
    // Add to document
    document.body.appendChild(themeToggle);
    
    // Add click event to toggle theme
    themeToggle.addEventListener('click', function() {
        toggleTheme();
    });
}

function applyCurrentTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Apply theme based on saved preference or system preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-theme');
        updateThemeIcon(true);
    } else {
        document.body.classList.remove('dark-theme');
        updateThemeIcon(false);
    }
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    
    if (isDark) {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        updateThemeIcon(false);
    } else {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        updateThemeIcon(true);
    }
}

function updateThemeIcon(isDark) {
    const lightIcon = document.getElementById('light-icon');
    const darkIcon = document.getElementById('dark-icon');
    
    if (lightIcon && darkIcon) {
        lightIcon.style.display = isDark ? 'none' : 'block';
        darkIcon.style.display = isDark ? 'block' : 'none';
    }
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