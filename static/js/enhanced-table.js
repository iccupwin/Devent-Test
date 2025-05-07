// Enhanced Table Functionality for Planfix Tasks
document.addEventListener('DOMContentLoaded', function() {
    // Add theme toggle button to all pages
    addThemeToggle();
    
    // Fix table columns and text overflow
    fixTableColumns();
    
    // Handle column visibility toggle
    setupColumnToggle();
    
    // Check and apply current theme
    applyCurrentTheme();
    
    // Setup modal functionality
    setupTaskModal();

    // Setup filters
    setupFilters();

    // Setup global search
    setupGlobalSearch();
});

// Function to add theme toggle button
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

// Function to fix table columns and text overflow
function fixTableColumns() {
    // Get all tables with tasks-table class
    const tables = document.querySelectorAll('.tasks-table');
    
    tables.forEach(table => {
        // Ensure table has fixed layout
        table.style.width = '100%';
        table.style.tableLayout = 'fixed';
        
        // Define column widths
        const columnWidths = {
            'id': '60px',
            'name': '25%',
            'status': '120px',
            'project': '15%',
            'dates': '120px',
            'assignee': '120px',
            'actions': '100px'
        };
        
        // Set header widths and styles
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            const classNames = Array.from(header.classList);
            const columnClass = classNames.find(className => className.startsWith('column-'));
            
            if (columnClass) {
                const column = columnClass.replace('column-', '');
                if (columnWidths[column]) {
                    header.style.width = columnWidths[column];
                }
            }
            
            // Ensure text doesn't overflow in headers
            header.style.overflow = 'hidden';
            header.style.textOverflow = 'ellipsis';
            header.style.whiteSpace = 'nowrap';
            header.style.position = 'sticky';
            header.style.top = '0';
            header.style.zIndex = '10';
        });
        
        // Fix cell text overflow
        const cells = table.querySelectorAll('td');
        cells.forEach(cell => {
            cell.style.overflow = 'hidden';
            cell.style.textOverflow = 'ellipsis';
            cell.style.whiteSpace = 'nowrap';
            cell.style.maxWidth = '0'; // Forces ellipsis to work correctly
        });
        
        // Add hover effect for task names
        const taskNameCells = table.querySelectorAll('.column-name');
        taskNameCells.forEach(cell => {
            const link = cell.querySelector('.task-name-link');
            if (link) {
                // Add hover effect
                link.addEventListener('mouseenter', function() {
                    const rect = this.getBoundingClientRect();
                    
                    // Create tooltip
                    const tooltip = document.createElement('div');
                    tooltip.className = 'task-name-hover';
                    tooltip.textContent = this.textContent.trim();
                    tooltip.style.position = 'absolute';
                    tooltip.style.top = (rect.bottom + window.scrollY) + 'px';
                    tooltip.style.left = (rect.left) + 'px';
                    tooltip.style.zIndex = '1000';
                    tooltip.style.background = 'white';
                    tooltip.style.padding = '8px 12px';
                    tooltip.style.borderRadius = '8px';
                    tooltip.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                    tooltip.style.maxWidth = '300px';
                    tooltip.style.display = 'block';
                    
                    // Add to document
                    document.body.appendChild(tooltip);
                    
                    // Store tooltip reference
                    this._tooltip = tooltip;
                });
                
                link.addEventListener('mouseleave', function() {
                    // Remove tooltip
                    if (this._tooltip) {
                        this._tooltip.remove();
                        this._tooltip = null;
                    }
                });
            }
        });
    });
}

// Function to set up column visibility toggle
function setupColumnToggle() {
    const toggleButton = document.getElementById('toggle-columns');
    if (!toggleButton) return;
    
    const columnsDropdown = document.getElementById('columns-dropdown');
    if (!columnsDropdown) return;
    
    // Make sure dropdown is hidden initially
    columnsDropdown.style.display = 'none';
    
    // Toggle dropdown visibility
    toggleButton.addEventListener('click', function(event) {
        event.stopPropagation();
        
        const isVisible = columnsDropdown.style.display === 'block';
        columnsDropdown.style.display = isVisible ? 'none' : 'block';
        
        // Position dropdown
        if (!isVisible) {
            const rect = toggleButton.getBoundingClientRect();
            columnsDropdown.style.top = (rect.bottom + window.scrollY) + 'px';
            columnsDropdown.style.right = (window.innerWidth - rect.right) + 'px';
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (columnsDropdown.style.display === 'block' && 
            !columnsDropdown.contains(event.target) && 
            !toggleButton.contains(event.target)) {
            columnsDropdown.style.display = 'none';
        }
    });
    
    // Handle column visibility toggles
    const checkboxes = columnsDropdown.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const column = this.dataset.column;
            const visible = this.checked;
            
            // Toggle column visibility
            document.querySelectorAll(`.column-${column}`).forEach(cell => {
                cell.style.display = visible ? '' : 'none';
            });
            
            // Save settings
            saveColumnSettings();
        });
    });
    
    // Load saved column settings
    loadColumnSettings();
}


// Setup task modal functionality
function setupTaskModal() {
    const taskModal = document.getElementById('taskModal');
    console.log('Task Modal Element:', taskModal);
    
    if (!taskModal) {
        console.error('Task Modal element not found!');
        return;
    }
    
    const modalClose = taskModal.querySelector('.apple-modal-close');
    console.log('Modal Close Button:', modalClose)
    
    // Close modal when clicking the close button
    if (modalClose) {
        modalClose.addEventListener('click', closeTaskModal);
    }
    
    // Close modal when clicking outside the content
    taskModal.addEventListener('click', function(event) {
        if (event.target === taskModal) {
            closeTaskModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && taskModal && taskModal.classList.contains('show')) {
            closeTaskModal();
        }
    });
    
    // Setup task name link click to open modal
    document.querySelectorAll('.task-name-link').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const taskId = this.getAttribute('data-task-id');
            if (taskId) {
                openTaskModal(taskId);
            }
        });
    });
    
    // Setup view buttons to open modal
    document.querySelectorAll('.btn-view').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const taskId = this.getAttribute('data-task-id');
            if (taskId) {
                openTaskModal(taskId);
            }
        });
    });
    
    // Setup integrate button in modal
    const modalIntegrateButton = document.getElementById('modalIntegrateButton');
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
    const modalTaskAssigner = document.getElementById('modalTaskAssigner');
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
    if (modalTaskAssigner) modalTaskAssigner.textContent = '-';
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
            console.log('Task data:', task); // Для отладки
            console.log('Task assigner:', task.assigner); // Для отладки
            console.log('Task assignees:', task.assignees); // Для отладки
            
            if (modalTaskTitle) modalTaskTitle.textContent = task.name || 'Без названия';
            if (modalTaskId) modalTaskId.textContent = `ID: ${task.id}`;
            
            // Project
            if (modalTaskProject) {
                modalTaskProject.textContent = task.project && task.project.name 
                    ? task.project.name 
                    : 'Не указан';
            }
            
            // Assigner
            if (modalTaskAssigner) {
                if (task.assigner && task.assigner.name) {
                    modalTaskAssigner.textContent = task.assigner.name;
                } else {
                    modalTaskAssigner.textContent = 'Не указан';
                }
            }
            
            // Assignee
            if (modalTaskAssignee) {
                console.log('Task assignees:', task.assignees); // Для отладки
                if (task.assignees && task.assignees.users && Array.isArray(task.assignees.users) && task.assignees.users.length > 0) {
                    modalTaskAssignee.textContent = task.assignees.users.map(a => a.name).join(', ');
                } else {
                    modalTaskAssignee.textContent = 'Не назначен';
                }
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
            if (dateInput.date) {
                date = new Date(dateInput.date);
            } else if (dateInput.dateFrom) {
                date = new Date(dateInput.dateFrom);
            } else if (dateInput.dateTo) {
                date = new Date(dateInput.dateTo);
            } else if (dateInput.datetime) {
                date = new Date(dateInput.datetime);
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
            return 'Не указана';
        }
        
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        console.error('Error formatting date:', e);
        return 'Не указана';
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

// Function to save column visibility settings
function saveColumnSettings() {
    const settings = {};
    document.querySelectorAll('#columns-dropdown input[type="checkbox"]').forEach(checkbox => {
        settings[checkbox.dataset.column] = checkbox.checked;
    });
    
    localStorage.setItem('columnSettings', JSON.stringify(settings));
}

// Function to load column visibility settings
function loadColumnSettings() {
    const settings = JSON.parse(localStorage.getItem('columnSettings'));
    if (!settings) return;
    
    Object.keys(settings).forEach(column => {
        // Update checkbox state
        const checkbox = document.querySelector(`#columns-dropdown input[data-column="${column}"]`);
        if (checkbox) {
            checkbox.checked = settings[column];
        }
        
        // Update column visibility
        document.querySelectorAll(`.column-${column}`).forEach(cell => {
            cell.style.display = settings[column] ? '' : 'none';
        });
    });
}

// Functions for theme switching
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

// Function to setup filters
function setupFilters() {
    const statusFilter = document.getElementById('status-filter');
    const projectFilter = document.getElementById('project-filter');
    const assignerFilter = document.getElementById('assigner-filter');
    const searchInput = document.getElementById('task-search');
    const searchButton = document.querySelector('.search-button');

    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }

    if (projectFilter) {
        projectFilter.addEventListener('change', applyFilters);
    }

    if (assignerFilter) {
        assignerFilter.addEventListener('change', applyFilters);
    }

    if (searchInput) {
        // Поиск при вводе
        searchInput.addEventListener('input', applyFilters);
        
        // Поиск при нажатии Enter
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilters();
            }
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }

    // Load assigners
    loadAssigners();
}

// Function to load assigners
function loadAssigners() {
    const assignerFilter = document.getElementById('assigner-filter');
    if (!assignerFilter) return;
    
    // Get unique assigners from the table
    const assigners = new Set();
    document.querySelectorAll('.column-assignee .assignee-name').forEach(element => {
        const assignerName = element.textContent.trim();
        if (assignerName && assignerName !== 'Не указан') {
            assigners.add(assignerName);
        }
    });
    
    // Sort assigners alphabetically
    const sortedAssigners = Array.from(assigners).sort();
    
    // Add options to select
    sortedAssigners.forEach(assigner => {
        const option = document.createElement('option');
        option.value = assigner;
        option.textContent = assigner;
        assignerFilter.appendChild(option);
    });
}

// Function to apply filters
function applyFilters() {
    const statusFilter = document.getElementById('status-filter');
    const projectFilter = document.getElementById('project-filter');
    const assignerFilter = document.getElementById('assigner-filter');
    const searchInput = document.getElementById('task-search');

    const statusValue = statusFilter ? statusFilter.value : 'all';
    const projectValue = projectFilter ? projectFilter.value : 'all';
    const assignerValue = assignerFilter ? assignerFilter.value : 'all';
    const searchValue = searchInput ? searchInput.value.trim().toLowerCase() : '';

    let visibleCount = 0;
    const totalRows = document.querySelectorAll('.tasks-table tbody tr').length;

    document.querySelectorAll('.tasks-table tbody tr').forEach(row => {
        const status = row.querySelector('.column-status .task-status')?.textContent.trim() || '';
        const project = row.querySelector('.column-project .project-name')?.textContent.trim() || 'Не указан';
        const assigner = row.querySelector('.column-assignee .assignee-name')?.textContent.trim() || 'Не указан';
        const id = row.querySelector('.column-id')?.textContent.trim() || '';
        const name = row.querySelector('.column-name .task-name-link')?.textContent.trim() || '';
        const dates = row.querySelector('.column-dates')?.textContent.trim() || '';

        const statusMatch = statusValue === 'all' || 
            (statusValue === 'active' && !status.toLowerCase().includes('завершена')) ||
            (statusValue === 'completed' && status.toLowerCase().includes('завершена'));
        const projectMatch = projectValue === 'all' || project === projectValue;
        const assignerMatch = assignerValue === 'all' || assigner === assignerValue;

        // Поиск по всем основным колонкам
        const rowText = [id, name, status, project, dates, assigner].join(' ').toLowerCase();
        const searchMatch = !searchValue || rowText.includes(searchValue);

        const isVisible = statusMatch && projectMatch && assignerMatch && searchMatch;
        row.style.display = isVisible ? '' : 'none';
        
        if (isVisible) {
            visibleCount++;
        }
    });

    // Обновляем информацию о пагинации
    const shownFrom = document.getElementById('shown-from');
    const shownTo = document.getElementById('shown-to');
    const totalCount = document.getElementById('total-count');

    if (shownFrom) shownFrom.textContent = visibleCount > 0 ? '1' : '0';
    if (shownTo) shownTo.textContent = visibleCount;
    if (totalCount) totalCount.textContent = totalRows;

    // Показываем сообщение, если ничего не найдено
    const noTasksRow = document.querySelector('.no-tasks-cell');
    if (noTasksRow) {
        noTasksRow.style.display = visibleCount === 0 ? '' : 'none';
    }
}

// Function to setup global search
function setupGlobalSearch() {
    const searchInput = document.getElementById('task-search');
    if (!searchInput) return;

    // Обработчик Ctrl+F
    document.addEventListener('keydown', function(e) {
        // Проверяем нажатие Ctrl+F
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault(); // Предотвращаем стандартное поведение браузера
            searchInput.focus();
        }
    });

    // Обработчик Enter в любом месте страницы
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.target.matches('textarea, input[type="text"]')) {
            e.preventDefault();
            searchInput.focus();
            applyFilters();
        }
    });

    // Обработчик клика на иконку поиска в шапке
    const searchButton = document.querySelector('.search-button');
    if (searchButton) {
        searchButton.addEventListener('click', function(e) {
            e.preventDefault();
            searchInput.focus();
            applyFilters();
        });
    }
}