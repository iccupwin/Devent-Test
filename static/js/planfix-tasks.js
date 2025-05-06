// JavaScript для работы с задачами Planfix
document.addEventListener('DOMContentLoaded', function() {
    // Элементы страницы
    const refreshButton = document.getElementById('refresh-button');
    const statusFilter = document.getElementById('status-filter');
    const projectFilter = document.getElementById('project-filter');
    const taskSearch = document.getElementById('task-search');
    const pageSize = document.getElementById('page-size');
    const tasksTableBody = document.getElementById('tasks-table-body');
    const paginationPages = document.getElementById('pagination-pages');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    const toggleColumnsButton = document.getElementById('toggle-columns');
    const columnsDropdown = document.getElementById('columns-dropdown');
    const dropdownClose = document.querySelector('.dropdown-close');
    const columnOptions = document.querySelectorAll('.column-option input');
    const resetFiltersButton = document.getElementById('reset-filters');
    
    // Переменные для состояния
    let currentPage = 1; // По умолчанию первая страница
    let currentStatusFilter = 'all'; // По умолчанию все статусы
    let currentSearch = '';
    let currentProjectFilter = 'all';
    let currentSortColumn = 'id';
    let currentSortDirection = 'asc';
    let currentPageSize = 25; // По умолчанию 25 задач на странице
    
    // Инициализируем с учетом параметров URL
    initFromURL();
    
    // Инициализация проектов
    loadProjects();
    
    // Инициализация задач
    updateTasksTable();
    
    // Обработчики событий
    refreshButton.addEventListener('click', function() {
        showNotification('info', 'Обновление...', 'Загрузка актуальных данных...');
        forceUpdateCache()
            .then(() => {
                updateTasksTable();
                showNotification('success', 'Готово!', 'Данные успешно обновлены');
            })
            .catch(error => {
                showNotification('error', 'Ошибка!', error.message);
            });
    });
    
    statusFilter.addEventListener('change', function() {
        currentStatusFilter = this.value;
        console.log(`Фильтр статуса: ${currentStatusFilter}`);
        updateTasksTable();
    });
    
    projectFilter.addEventListener('change', function() {
        currentProjectFilter = this.value;
        console.log(`Фильтр проекта: ${currentProjectFilter}`);
        updateTasksTable();
    });
    
    // Обработчик для поиска с задержкой
    taskSearch.addEventListener('input', debounce(function() {
        currentSearch = this.value.trim();
        console.log(`Поиск: ${currentSearch}`);
        updateTasksTable();
    }, 300));
    
    pageSize.addEventListener('change', function() {
        currentPageSize = parseInt(this.value);
        updateTasksTable();
    });
    
    prevPageButton.addEventListener('click', function() {
        if (currentPage > 1) {
            currentPage--;
            updateURL();
            updateTasksTable();
        }
    });
    
    nextPageButton.addEventListener('click', function() {
        currentPage++;
        updateURL();
        updateTasksTable();
    });
    
    // Обработчик для сортировки по столбцам
    document.querySelectorAll('.sortable').forEach(headerCell => {
        headerCell.addEventListener('click', function() {
            const sortColumn = this.dataset.sort;
            console.log('Сортировка по столбцу:', sortColumn);
            
            // Если клик по текущему столбцу сортировки, меняем направление
            if (sortColumn === currentSortColumn) {
                currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortColumn = sortColumn;
                currentSortDirection = 'asc';
            }
            
            console.log(`Установлена сортировка: ${currentSortColumn} ${currentSortDirection}`);
            
            // Обновляем визуальное отображение сортировки
            document.querySelectorAll('.sort-indicator').forEach(indicator => {
                indicator.remove();
            });
            
            const indicator = document.createElement('span');
            indicator.classList.add('sort-indicator');
            indicator.textContent = currentSortDirection === 'asc' ? ' ↑' : ' ↓';
            this.appendChild(indicator);
            
            // Обновляем таблицу с учетом сортировки
            updateTasksTable();
        });
    });
    
    // Обработчик для выпадающего меню столбцов
    toggleColumnsButton.addEventListener('click', function() {
        columnsDropdown.classList.toggle('active');
    });
    
    dropdownClose.addEventListener('click', function() {
        columnsDropdown.classList.remove('active');
    });
    
    document.addEventListener('click', function(event) {
        if (!columnsDropdown.contains(event.target) && !toggleColumnsButton.contains(event.target)) {
            columnsDropdown.classList.remove('active');
        }
    });
    
    columnOptions.forEach(option => {
        option.addEventListener('change', function() {
            const columnClass = '.column-' + this.dataset.column;
            const isVisible = this.checked;
            
            document.querySelectorAll(columnClass).forEach(cell => {
                cell.style.display = isVisible ? '' : 'none';
            });
        });
    });
    
    if (resetFiltersButton) {
        resetFiltersButton.addEventListener('click', function() {
            statusFilter.value = 'all';
            projectFilter.value = 'all';
            taskSearch.value = '';
            currentStatusFilter = 'all';
            currentProjectFilter = 'all';
            currentSearch = '';
            currentPage = 1;
            updateURL();
            updateTasksTable();
        });
    }
    
    // Обработчик для кнопок интеграции с Claude
    document.addEventListener('click', function(event) {
        if (event.target.closest('.btn-integrate')) {
            const button = event.target.closest('.btn-integrate');
            const taskId = button.dataset.taskId;
            
            // Заменяем содержимое кнопки на спиннер
            const originalContent = button.innerHTML;
            button.innerHTML = '<div class="loading-spinner"></div>';
            button.disabled = true;
            
            // Отправляем запрос на интеграцию
            integrateTaskWithClaude(taskId)
                .then(response => {
                    if (response.success) {
                        showNotification('success', 'Успешно!', 'Задача добавлена в чат с Claude');
                        // Перенаправляем на страницу чата
                        window.location.href = `/conversation/${response.conversation_id}/`;
                    } else {
                        throw new Error(response.error || 'Ошибка при интеграции с Claude');
                    }
                })
                .catch(error => {
                    button.innerHTML = originalContent;
                    button.disabled = false;
                    showNotification('error', 'Ошибка!', error.message);
                });
        }
    });
    
    // Функции для работы с модальным окном задачи
    const taskModal = document.getElementById('taskModal');
    const modalClose = document.querySelector('.task-modal-close');
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
    
    // Обработчик для открытия модального окна при клике на название задачи
    document.addEventListener('click', function(event) {
        const taskLink = event.target.closest('.task-name-link');
        if (taskLink) {
            event.preventDefault();
            const taskId = taskLink.getAttribute('href').split('/').filter(Boolean).pop();
            openTaskModal(taskId);
        }
    });
    
    // Закрытие модального окна при клике на крестик
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            closeTaskModal();
        });
    }
    
    // Закрытие модального окна при клике вне его содержимого
    if (taskModal) {
        taskModal.addEventListener('click', function(event) {
            if (event.target === taskModal) {
                closeTaskModal();
            }
        });
    }
    
    // Закрытие модального окна по клавише Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && taskModal && taskModal.style.display === 'block') {
            closeTaskModal();
        }
    });
    
    // Функция открытия модального окна с данными задачи
    function openTaskModal(taskId) {
        // Показываем индикатор загрузки в модальном окне
        modalTaskTitle.textContent = 'Загрузка...';
        modalTaskId.textContent = taskId;
        modalTaskProject.textContent = '-';
        modalTaskAssignee.textContent = '-';
        modalTaskPriority.textContent = '-';
        modalTaskStatus.className = 'task-status';
        modalTaskStatus.textContent = '-';
        modalTaskDateStart.textContent = '-';
        modalTaskDateEnd.textContent = '-';
        modalTaskDescription.textContent = 'Загрузка данных задачи...';
        modalIntegrateButton.setAttribute('data-task-id', taskId);
        
        // Открываем модальное окно
        taskModal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Блокируем прокрутку страницы
        
        // Запрашиваем данные задачи
        fetch(`/api/task/${taskId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка при загрузке задачи');
                }
                return response.json();
            })
            .then(task => {
                // Заполняем модальное окно данными
                modalTaskTitle.textContent = task.name || 'Без названия';
                modalTaskId.textContent = task.id;
                
                // Проект
                if (task.project && task.project.name) {
                    modalTaskProject.textContent = task.project.name;
                } else {
                    modalTaskProject.textContent = 'Не указан';
                }
                
                // Исполнители
                if (task.assignees && task.assignees.length > 0) {
                    modalTaskAssignee.textContent = task.assignees.map(a => a.name).join(', ');
                } else {
                    modalTaskAssignee.textContent = 'Не назначен';
                }
                
                // Приоритет
                if (task.priority && task.priority.name) {
                    modalTaskPriority.textContent = task.priority.name;
                } else {
                    modalTaskPriority.textContent = 'Обычный';
                }
                
                // Статус
                if (task.status && task.status.name) {
                    const statusClass = getStatusClass(task.status.name);
                    modalTaskStatus.className = 'task-status ' + statusClass;
                    modalTaskStatus.textContent = task.status.name;
                    
                    // Если задача завершена, отключаем кнопку интеграции
                    if (statusClass === 'завершена' || statusClass === 'завершенная' || statusClass === 'выполненная' || task.status.id === 3) {
                        modalIntegrateButton.disabled = true;
                    } else {
                        modalIntegrateButton.disabled = false;
                    }
                } else {
                    modalTaskStatus.className = 'task-status';
                    modalTaskStatus.textContent = 'Не указан';
                    modalIntegrateButton.disabled = false;
                }
                
                // Даты
                if (task.startDateTime) {
                    modalTaskDateStart.textContent = formatDate(task.startDateTime);
                } else {
                    modalTaskDateStart.textContent = 'Не указана';
                }
                
                if (task.endDateTime) {
                    modalTaskDateEnd.textContent = formatDate(task.endDateTime);
                } else {
                    modalTaskDateEnd.textContent = 'Не указана';
                }
                
                // Описание
                if (task.description) {
                    modalTaskDescription.innerHTML = task.description;
                } else {
                    modalTaskDescription.textContent = 'Описание отсутствует';
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                modalTaskTitle.textContent = 'Ошибка загрузки';
                modalTaskDescription.textContent = 'Не удалось загрузить данные задачи. Пожалуйста, попробуйте еще раз.';
            });
    }
    
    // Функция закрытия модального окна
    function closeTaskModal() {
        taskModal.style.display = 'none';
        document.body.style.overflow = ''; // Восстанавливаем прокрутку страницы
    }
    
    // Обработчик для кнопки интеграции в модальном окне
    if (modalIntegrateButton) {
        modalIntegrateButton.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            if (!taskId) return;
            
            // Заменяем содержимое кнопки на спиннер
            const originalContent = this.innerHTML;
            this.innerHTML = '<div class="loading-spinner"></div> Обработка...';
            this.disabled = true;
            
            // Отправляем запрос на интеграцию
            integrateTaskWithClaude(taskId)
                .then(response => {
                    if (response.success) {
                        showNotification('success', 'Успешно!', 'Задача добавлена в чат с Claude');
                        // Перенаправляем на страницу чата
                        window.location.href = `/conversation/${response.conversation_id}/`;
                    } else {
                        throw new Error(response.error || 'Ошибка при интеграции с Claude');
                    }
                })
                .catch(error => {
                    this.innerHTML = originalContent;
                    this.disabled = false;
                    showNotification('error', 'Ошибка!', error.message);
                });
        });
    }
    
    // Функция для инициализации из URL
    function initFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Получаем параметры из URL
        if (urlParams.has('page')) {
            currentPage = parseInt(urlParams.get('page')) || 1;
        }
        
        if (urlParams.has('status')) {
            currentStatusFilter = urlParams.get('status');
            if (statusFilter) {
                statusFilter.value = currentStatusFilter;
            }
        }
        
        if (urlParams.has('project')) {
            currentProjectFilter = urlParams.get('project');
            console.log('URL содержит параметр project:', currentProjectFilter);
        }
    }
    
    // Функция для загрузки проектов
    function loadProjects() {
        fetch('/api/projects/')
            .then(response => response.json())
            .then(data => {
                const projects = data.projects || [];
                console.log('Загружены проекты:', projects);
                
                // Очищаем текущие опции, кроме "Все проекты"
                while (projectFilter.options.length > 1) {
                    projectFilter.remove(1);
                }
                
                // Сортируем проекты по имени для удобства
                projects.sort((a, b) => {
                    const nameA = (a.name || '').toLowerCase();
                    const nameB = (b.name || '').toLowerCase();
                    if (nameA < nameB) return -1;
                    if (nameA > nameB) return 1;
                    return 0;
                });
                
                // Добавляем новые проекты
                projects.forEach(project => {
                    if (project && project.name) {
                        const option = document.createElement('option');
                        option.value = project.id;
                        option.textContent = project.name;
                        projectFilter.appendChild(option);
                    }
                });
                
                // Если был выбран проект из URL, устанавливаем его
                if (currentProjectFilter !== 'all') {
                    projectFilter.value = currentProjectFilter;
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке проектов:', error);
                showNotification('error', 'Ошибка!', 'Не удалось загрузить проекты');
            });
    }
    
    // Функция для обновления таблицы задач
    function updateTasksTable() {
        const tasksTableBody = document.getElementById('tasks-table-body');
        
        // Показываем индикатор загрузки
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center; padding: 2rem;">
                    <div style="display: flex; justify-content: center; align-items: center;">
                        <div class="loading-spinner"></div>
                        <span style="margin-left: 1rem;">Загрузка задач...</span>
                    </div>
                </td>
            </tr>
        `;

        // Цветовая палитра для постановщиков
        const assignerColors = {
            'default': '#2E294E', // Основной цвет
            'colors': [
                '#E74C3C', // тёмно-красный
                '#2980B9', // тёмно-синий
                '#27AE60', // тёмно-зелёный
                '#8E44AD', // тёмно-фиолетовый
                '#D35400', // тёмно-оранжевый
                '#16A085', // тёмно-бирюзовый
                '#2C3E50', // тёмно-серый
                '#7D3C98'  // тёмно-пурпурный
            ]
        };

        // Функция для получения цвета постановщика
        function getAssignerColor(assignerName) {
            if (!assignerName) return assignerColors.default;
            
            // Создаем хэш имени для стабильного распределения цветов
            let hash = 0;
            for (let i = 0; i < assignerName.length; i++) {
                hash = assignerName.charCodeAt(i) + ((hash << 5) - hash);
            }
            
            // Используем хэш для выбора цвета из палитры
            const colorIndex = Math.abs(hash) % assignerColors.colors.length;
            return assignerColors.colors[colorIndex];
        }

        // Формируем URL для запроса
        const apiUrl = `/api/tasks/`;
        console.log('API URL:', apiUrl);
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка при загрузке задач');
                }
                return response.json();
            })
            .then(data => {
                console.log('Получены данные от API:', data);
                const tasks = data.tasks || [];
                
                // Логируем первую задачу для проверки формата дат
                if (tasks.length > 0) {
                    console.log('Пример задачи:', {
                        id: tasks[0].id,
                        name: tasks[0].name,
                        dateBegin: tasks[0].dateBegin,
                        dateEnd: tasks[0].dateEnd,
                        rawTask: tasks[0]
                    });
                }
                
                // Применяем фильтр по статусу (клиентская фильтрация)
                let filteredTasks = tasks.slice(); // Копируем массив
                
                if (currentStatusFilter === 'active') {
                    filteredTasks = filteredTasks.filter(task => {
                        const status = task.status && task.status.name ? task.status.name.toLowerCase() : '';
                        return !(status.includes('завершен') || status.includes('выполнен') || 
                                 status.includes('completed') || (task.status && task.status.id === 3));
                    });
                } else if (currentStatusFilter === 'completed') {
                    filteredTasks = filteredTasks.filter(task => {
                        const status = task.status && task.status.name ? task.status.name.toLowerCase() : '';
                        return status.includes('завершен') || status.includes('выполнен') || 
                               status.includes('completed') || (task.status && task.status.id === 3);
                    });
                }
                
                // Применяем фильтр по проекту
                if (currentProjectFilter !== 'all') {
                    filteredTasks = filteredTasks.filter(task => {
                        return task.project && String(task.project.id) === String(currentProjectFilter);
                    });
                }
                
                // Применяем поиск
                if (currentSearch) {
                    const searchLower = currentSearch.toLowerCase();
                    filteredTasks = filteredTasks.filter(task => {
                        return (task.name && task.name.toLowerCase().includes(searchLower)) ||
                               (task.description && task.description.toLowerCase().includes(searchLower)) ||
                               (task.project && task.project.name && task.project.name.toLowerCase().includes(searchLower)) ||
                               (task.assignees && task.assignees.some(a => a.name && a.name.toLowerCase().includes(searchLower)));
                    });
                }
                
                // Применяем сортировку
                filteredTasks.sort((a, b) => {
                    let valA, valB;
                    
                    switch (currentSortColumn) {
                        case 'id':
                            valA = parseInt(a.id) || 0;
                            valB = parseInt(b.id) || 0;
                            break;
                        case 'name':
                            valA = (a.name || '').toLowerCase();
                            valB = (b.name || '').toLowerCase();
                            break;
                        case 'status':
                            valA = (a.status && a.status.name ? a.status.name : '').toLowerCase();
                            valB = (b.status && b.status.name ? b.status.name : '').toLowerCase();
                            break;
                        case 'project':
                            valA = (a.project && a.project.name ? a.project.name : '').toLowerCase();
                            valB = (b.project && b.project.name ? b.project.name : '').toLowerCase();
                            break;
                        case 'dates':
                            valA = a.dateEnd || a.dateBegin || '';
                            valB = b.dateEnd || b.dateBegin || '';
                            break;
                        case 'assignee':
                            valA = (a.assignees && a.assignees[0] && a.assignees[0].name ? a.assignees[0].name : '').toLowerCase();
                            valB = (b.assignees && b.assignees[0] && b.assignees[0].name ? b.assignees[0].name : '').toLowerCase();
                            break;
                        default:
                            valA = parseInt(a.id) || 0;
                            valB = parseInt(b.id) || 0;
                    }
                    
                    // Проверяем направление сортировки
                    if (currentSortDirection === 'asc') {
                        if (valA < valB) return -1;
                        if (valA > valB) return 1;
                        return 0;
                    } else {
                        if (valA > valB) return -1;
                        if (valA < valB) return 1;
                        return 0;
                    }
                });
                
                // Отображаем индикатор сортировки в заголовке таблицы
                document.querySelectorAll('.sort-indicator').forEach(indicator => {
                    indicator.remove();
                });
                
                const currentSortHeader = document.querySelector(`.sortable[data-sort="${currentSortColumn}"]`);
                if (currentSortHeader) {
                    const indicator = document.createElement('span');
                    indicator.classList.add('sort-indicator');
                    indicator.textContent = currentSortDirection === 'asc' ? ' ↑' : ' ↓';
                    currentSortHeader.appendChild(indicator);
                }
                
                // Очищаем текущее содержимое таблицы
                tasksTableBody.innerHTML = '';
                
                if (filteredTasks.length === 0) {
                    // Показываем сообщение "Нет задач"
                    const noTasksRow = document.createElement('tr');
                    noTasksRow.innerHTML = `
                        <td colspan="7" class="no-tasks-cell">
                            <div class="no-tasks">
                                <div class="no-tasks-icon">📋</div>
                                <h3>Задачи не найдены</h3>
                                <p>Попробуйте изменить параметры поиска или обновить список задач.</p>
                                <button id="reset-filters" class="btn btn-primary">Сбросить фильтры</button>
                            </div>
                        </td>
                    `;
                    tasksTableBody.appendChild(noTasksRow);
                    
                    // Добавляем обработчик для кнопки сброса фильтров
                    const resetBtn = noTasksRow.querySelector('#reset-filters');
                    if (resetBtn) {
                        resetBtn.addEventListener('click', function() {
                            statusFilter.value = 'all';
                            projectFilter.value = 'all';
                            taskSearch.value = '';
                            currentStatusFilter = 'all';
                            currentProjectFilter = 'all';
                            currentSearch = '';
                            currentPage = 1;
                            updateTasksTable();
                        });
                    }
                } else {
                    // Добавляем задачи в таблицу
                    filteredTasks.forEach(task => {
                        const row = document.createElement('tr');
                        
                        // Определяем, является ли задача завершенной
                        const isCompleted = task.status && 
                            (task.status.id === 3 || 
                             (task.status.name && task.status.name.toLowerCase().includes('завершен')) || 
                             (task.status.name && task.status.name.toLowerCase().includes('completed')));
                        
                        // Форматируем даты
                        const dateBegin = task.startDateTime ? formatDate(task.startDateTime) : '';
                        const dateEnd = task.endDateTime ? formatDate(task.endDateTime) : '';
                        
                        // Проект и его цвет
                        const projectColors = [
                            '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', 
                            '#f59e0b', '#10b981', '#06b6d4', '#3b82f6'
                        ];
                        
                        const projectColor = task.project && task.project.id ? 
                            projectColors[task.project.id % projectColors.length] : 
                            '#9ca3af';
                        
                        row.innerHTML = `
                            <td class="column-id">${task.id}</td>
                            <td class="column-name">
                                <a href="/planfix/task/${task.id}/" class="task-name-link">
                                    ${escapeHtml(task.name || 'Без названия')}
                                    ${task.description ? '<span class="has-description" title="Есть описание">📝</span>' : ''}
                                </a>
                            </td>
                            <td class="column-status">
                                <span class="task-status ${getStatusClass(task.status ? task.status.name : '')}">
                                    ${task.status ? escapeHtml(task.status.name) : 'Без статуса'}
                                </span>
                            </td>
                            <td class="column-project">
                                ${task.project && task.project.name ? 
                                    `<div class="project-badge" style="background-color: ${projectColor}">
                                        ${task.project.name.charAt(0).toUpperCase()}
                                    </div>
                                    <span class="project-name">${escapeHtml(task.project.name)}</span>` : 
                                    '<span class="empty-value">Не указан</span>'}
                            </td>
                            <td class="column-dates">
                                <div class="task-dates">
                                    ${dateBegin ? 
                                        `<div class="date-start">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                                <line x1="3" y1="10" x2="21" y2="10"></line>
                                            </svg>
                                            ${dateBegin}
                                        </div>` : ''}
                                    ${dateEnd ? 
                                        `<div class="date-end">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                                <line x1="3" y1="10" x2="21" y2="10"></line>
                                            </svg>
                                            ${dateEnd}
                                        </div>` : ''}
                                    ${!dateBegin && !dateEnd ? 
                                        '<span class="empty-value">Не указаны</span>' : ''}
                                </div>
                            </td>
                            <td class="column-assignee">
                                ${task.assigner ? 
                                    `<div class="assignee-wrapper">
                                        <div class="assignee-avatar" style="background-color: ${getAssignerColor(task.assigner.name)}">
                                            ${task.assigner.name ? task.assigner.name.charAt(0).toUpperCase() : '?'}
                                        </div>
                                        <span class="assignee-name">${escapeHtml(task.assigner.name)}</span>
                                    </div>` : 
                                    '<span class="empty-value">Не указан</span>'}
                            </td>
                            <td class="column-actions">
                                <div class="table-actions">
                                    <a href="/planfix/task/${task.id}/" class="btn-icon btn-view" title="Просмотр задачи">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                            <circle cx="12" cy="12" r="3"></circle>
                                        </svg>
                                    </a>
                                    <button 
                                        class="btn-icon btn-integrate"
                                        data-task-id="${task.id}"
                                        title="Обсудить с Claude"
                                        ${isCompleted ? 'disabled' : ''}
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        `;
                        
                        tasksTableBody.appendChild(row);
                    });
                }
                
                // Обновляем информацию о количестве задач
                document.getElementById('shown-from').textContent = filteredTasks.length > 0 ? '1' : '0';
                document.getElementById('shown-to').textContent = filteredTasks.length.toString();
                document.getElementById('total-count').textContent = tasks.length.toString();
            })
            .catch(error => {
                console.error('Ошибка при загрузке задач:', error);
                tasksTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="no-tasks-cell">
                            <div class="no-tasks">
                                <div class="no-tasks-icon" style="color: #ef4444;">❌</div>
                                <h3>Ошибка загрузки</h3>
                                <p>Не удалось загрузить задачи. Пожалуйста, проверьте подключение и попробуйте снова.</p>
                                <button id="retry-button" class="btn btn-primary">Повторить</button>
                            </div>
                        </td>
                    </tr>
                `;
                
                // Добавляем обработчик для кнопки повтора
                const retryBtn = tasksTableBody.querySelector('#retry-button');
                if (retryBtn) {
                    retryBtn.addEventListener('click', function() {
                        updateTasksTable();
                    });
                }
            });
    }
    
    // Функция для принудительного обновления кэша
    function forceUpdateCache() {
        return fetch('/api/tasks/update/?force=true', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при обновлении кэша');
            }
            return response.json();
        });
    }
    
    // Функция для интеграции задачи с Claude
    function integrateTaskWithClaude(taskId) {
        return fetch(`/planfix/task/${taskId}/integrate/`, {
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
        });
    }
    
    // Функция для обновления URL
    function updateURL() {
        const url = new URL(window.location);
        url.searchParams.set('page', currentPage);
        url.searchParams.set('status', currentStatusFilter);
        
        // Добавляем или удаляем параметр проекта
        if (currentProjectFilter !== 'all') {
            url.searchParams.set('project', currentProjectFilter);
        } else {
            url.searchParams.delete('project');
        }
        
        window.history.replaceState({}, '', url);
        console.log('URL обновлен:', url.toString());
    }
    
    // Функция для обновления пагинации
    function updatePagination(currentPage, totalPages, totalCount) {
        // Очищаем текущие кнопки страниц
        paginationPages.innerHTML = '';
        
        // Определяем, какие страницы показывать
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        // Корректировка, если мы находимся в конце списка
        if (endPage === totalPages) {
            startPage = Math.max(1, endPage - 4);
        }
        
        // Добавляем кнопку для первой страницы, если она не включена
        if (startPage > 1) {
            const firstPageButton = document.createElement('button');
            firstPageButton.classList.add('pagination-page');
            firstPageButton.textContent = '1';
            firstPageButton.addEventListener('click', function() {
                currentPage = 1;
                updateURL();
                updateTasksTable();
            });
            paginationPages.appendChild(firstPageButton);
            
            // Добавляем многоточие, если нужно
            if (startPage > 2) {
                const ellipsis = document.createElement('span');
                ellipsis.classList.add('pagination-ellipsis');
                ellipsis.textContent = '...';
                paginationPages.appendChild(ellipsis);
            }
        }
        
        // Добавляем кнопки для страниц
        for (let i = startPage; i <= endPage; i++) {
            const pageButton = document.createElement('button');
            pageButton.classList.add('pagination-page');
            if (i === currentPage) {
                pageButton.classList.add('active');
            }
            pageButton.textContent = i;
            
            pageButton.addEventListener('click', function() {
                currentPage = i;
                updateURL();
                updateTasksTable();
            });
            
            paginationPages.appendChild(pageButton);
        }
        
        // Добавляем многоточие и последнюю страницу, если нужно
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement('span');
                ellipsis.classList.add('pagination-ellipsis');
                ellipsis.textContent = '...';
                paginationPages.appendChild(ellipsis);
            }
            
            const lastPageButton = document.createElement('button');
            lastPageButton.classList.add('pagination-page');
            lastPageButton.textContent = totalPages;
            lastPageButton.addEventListener('click', function() {
                currentPage = totalPages;
                updateURL();
                updateTasksTable();
            });
            paginationPages.appendChild(lastPageButton);
        }
        
        // Обновляем состояние кнопок пагинации
        prevPageButton.disabled = currentPage <= 1;
        nextPageButton.disabled = currentPage >= totalPages;
    }
    
    // Вспомогательные функции
    function getStatusClass(statusName) {
        if (!statusName) return '';
        
        // Преобразуем в нижний регистр для сравнения
        const statusLower = statusName.toLowerCase();
        
        // Расширенные проверки для различных статусов
        if (statusLower.includes('черновик')) return 'черновик';
        if (statusLower.includes('нов')) return 'новая';
        if (statusLower.includes('работ')) return 'вработе';
        if (statusLower.includes('выполн') || 
            statusLower.includes('заверш') || 
            statusLower.includes('готов') || 
            statusLower.includes('compl')) return 'завершена';
        if (statusLower.includes('отлож') || 
            statusLower.includes('приост')) return 'отложена';
        
        // Возвращаем сам статус в нижнем регистре как запасной вариант
        return statusLower.replace(/\s+/g, '');
    }
    
    function formatDate(dateInput) {
        if (!dateInput) return '';
        
        console.log('Received date input:', dateInput, 'Type:', typeof dateInput);
        
        try {
            let date;
            
            // Если это объект, проверяем его структуру
            if (typeof dateInput === 'object') {
                // Если это объект с dateFrom/dateTo
                if (dateInput.dateFrom) {
                    date = parsePlanfixDate(dateInput.dateFrom);
                } else if (dateInput.dateTo) {
                    date = parsePlanfixDate(dateInput.dateTo);
                } else {
                    // Пробуем найти дату в других свойствах
                    for (let key in dateInput) {
                        if (typeof dateInput[key] === 'string' && dateInput[key].includes('-')) {
                            date = parsePlanfixDate(dateInput[key]);
                            if (!isNaN(date.getTime())) break;
                        }
                    }
                }
            } else if (typeof dateInput === 'string') {
                date = parsePlanfixDate(dateInput);
            }
            
            if (!date || isNaN(date.getTime())) {
                console.log('Invalid date:', dateInput);
                return 'Неверная дата';
            }
            
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            console.error('Error formatting date:', e);
            return 'Ошибка форматирования';
        }
    }
    
    // Вспомогательная функция для парсинга даты в формате Planfix
    function parsePlanfixDate(dateStr) {
        if (!dateStr) return null;
        
        // Формат: DD-MM-YYYY HH:mm
        const match = dateStr.match(/(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?/);
        if (!match) return null;
        
        const [_, day, month, year, hours = '00', minutes = '00'] = match;
        return new Date(year, month - 1, day, hours, minutes);
    }
    
    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Функция для отображения уведомлений
    function showNotification(type, title, message) {
        const notification = document.getElementById('notification');
        const notificationIcon = document.getElementById('notification-icon');
        const notificationTitle = document.getElementById('notification-title');
        const notificationMessage = document.getElementById('notification-message');
        const notificationClose = document.getElementById('notification-close');
        
        // Создаем элементы, если они не существуют
        if (!notification) {
            // Создаем элемент уведомления
            const newNotification = document.createElement('div');
            newNotification.id = 'notification';
            newNotification.className = 'notification ' + type;
            newNotification.style.display = 'none';
            
            // Создаем иконку
            const newIcon = document.createElement('div');
            newIcon.id = 'notification-icon';
            newIcon.className = 'notification-icon';
            
            // Создаем контент
            const newContent = document.createElement('div');
            newContent.className = 'notification-content';
            
            // Создаем заголовок и сообщение
            const newTitle = document.createElement('div');
            newTitle.id = 'notification-title';
            newTitle.className = 'notification-title';
            
            const newMessage = document.createElement('div');
            newMessage.id = 'notification-message';
            newMessage.className = 'notification-message';
            
            // Создаем кнопку закрытия
            const newClose = document.createElement('button');
            newClose.id = 'notification-close';
            newClose.className = 'notification-close';
            newClose.innerHTML = '&times;';
            
            // Собираем структуру
            newContent.appendChild(newTitle);
            newContent.appendChild(newMessage);
            newNotification.appendChild(newIcon);
            newNotification.appendChild(newContent);
            newNotification.appendChild(newClose);
            
            // Добавляем в документ
            document.body.appendChild(newNotification);
            
            // Обновляем ссылки на элементы
            return showNotification(type, title, message);
        }
        
        // Устанавливаем тип уведомления
        notification.className = 'notification ' + type;
        
        // Устанавливаем иконку
        if (type === 'success') {
            notificationIcon.innerHTML = '✓';
        } else if (type === 'error') {
            notificationIcon.innerHTML = '✗';
        } else {
            notificationIcon.innerHTML = 'ℹ';
        }
        
        // Устанавливаем заголовок и сообщение
        notificationTitle.textContent = title;
        notificationMessage.textContent = message;
        
        // Показываем уведомление
        notification.style.display = 'flex';
        
        // Скрываем уведомление через 5 секунд
        const timeoutId = setTimeout(function() {
            notification.classList.add('hiding');
            setTimeout(function() {
                notification.style.display = 'none';
                notification.classList.remove('hiding');
            }, 300);
        }, 5000);
        
        // Обработчик для кнопки закрытия
        notificationClose.addEventListener('click', function() {
            clearTimeout(timeoutId);
            notification.classList.add('hiding');
            setTimeout(function() {
                notification.style.display = 'none';
                notification.classList.remove('hiding');
            }, 300);
        });
    }
    
    // Функция для отложенного выполнения
    function debounce(func, delay) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                func.apply(context, args);
            }, delay);
        };
    }
    
    // Функция для получения CSRF токена из cookies
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
    
    // Обновляем заголовок колонки в HTML
    document.querySelector('.column-assignee').textContent = 'Постановщик';
});