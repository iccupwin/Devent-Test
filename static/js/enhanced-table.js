// Скрипт для исправления проблем с таблицей и добавления переключателя темы

document.addEventListener('DOMContentLoaded', function() {
    // Добавление кнопки переключения темы
    addThemeToggle();
    
    // Исправление колонок таблицы
    fixTableColumns();
    
    // Обработка события выбора колонок
    setupColumnToggle();
    
    // Проверка и установка темы
    setupTheme();
});

function addThemeToggle() {
    // Проверяем, нет ли уже кнопки переключения темы
    if (document.querySelector('.theme-toggle')) return;
    
    // Создаем кнопку переключения темы
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
    
    // Добавляем элемент в документ
    document.body.appendChild(themeToggle);
    
    // Добавляем обработчик события для переключения темы
    themeToggle.addEventListener('click', function() {
        toggleTheme();
    });
}

function setupTheme() {
    // Проверяем сохраненную тему или используем системные настройки
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-theme');
        updateThemeIcon(true);
    } else {
        document.body.classList.remove('dark-theme');
        updateThemeIcon(false);
    }
}

function toggleTheme() {
    if (document.body.classList.contains('dark-theme')) {
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
        if (isDark) {
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'block';
        } else {
            lightIcon.style.display = 'block';
            darkIcon.style.display = 'none';
        }
    }
}

function fixTableColumns() {
    // Получаем таблицу
    const table = document.querySelector('.tasks-table');
    
    if (!table) return;
    
    // Устанавливаем фиксированную ширину для таблицы
    table.style.width = '100%';
    table.style.tableLayout = 'fixed';
    
    // Устанавливаем ширину для каждой колонки
    const columnWidths = {
        'id': '60px',
        'name': '25%',
        'status': '120px',
        'project': '15%',
        'dates': '120px',
        'assignee': '120px',
        'actions': '100px'
    };
    
    // Получаем все заголовки таблицы
    const headers = table.querySelectorAll('th');
    
    // Устанавливаем ширину для каждого заголовка
    headers.forEach(header => {
        // Получаем класс колонки (column-id, column-name и т.д.)
        const classNames = Array.from(header.classList);
        const columnClass = classNames.find(className => className.startsWith('column-'));
        
        if (columnClass) {
            const column = columnClass.replace('column-', '');
            if (columnWidths[column]) {
                header.style.width = columnWidths[column];
            }
        }
    });
    
    // Устанавливаем свойства для ячеек
    const cells = table.querySelectorAll('td');
    cells.forEach(cell => {
        cell.style.overflow = 'hidden';
        cell.style.textOverflow = 'ellipsis';
        cell.style.whiteSpace = 'nowrap';
        cell.style.padding = '12px 16px';
        cell.style.position = 'relative';
    });
    
    // Добавляем интерактивность для названий задач
    const taskNameCells = table.querySelectorAll('.column-name');
    taskNameCells.forEach(cell => {
        const link = cell.querySelector('.task-name-link');
        if (link) {
            // Устанавливаем базовые стили для ссылки
            link.style.display = 'inline-block';
            link.style.maxWidth = '100%';
            link.style.overflow = 'hidden';
            link.style.textOverflow = 'ellipsis';
            link.style.whiteSpace = 'nowrap';
            link.style.transition = 'all 0.2s ease';
            
            // Добавляем обработчики событий
            link.addEventListener('mouseenter', function() {
                this.style.overflow = 'visible';
                this.style.whiteSpace = 'normal';
                this.style.backgroundColor = 'var(--apple-hover, #f8f9fa)';
                this.style.position = 'absolute';
                this.style.zIndex = '100';
                this.style.padding = '8px';
                this.style.border = '1px solid var(--apple-border, rgba(0, 0, 0, 0.1))';
                this.style.borderRadius = '8px';
                this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
                this.style.maxWidth = '300px';
                this.style.left = '0';
            });
            
            link.addEventListener('mouseleave', function() {
                this.style.overflow = 'hidden';
                this.style.whiteSpace = 'nowrap';
                this.style.backgroundColor = '';
                this.style.position = 'relative';
                this.style.zIndex = '';
                this.style.padding = '';
                this.style.border = '';
                this.style.borderRadius = '';
                this.style.boxShadow = '';
                this.style.maxWidth = '100%';
                this.style.left = '';
            });
        }
    });
    
    // Оптимизируем столбец статуса
    const statusCells = table.querySelectorAll('.column-status');
    statusCells.forEach(cell => {
        const statusBadge = cell.querySelector('.task-status');
        if (statusBadge) {
            statusBadge.style.display = 'inline-block';
            statusBadge.style.maxWidth = '100%';
            statusBadge.style.overflow = 'hidden';
            statusBadge.style.textOverflow = 'ellipsis';
        }
    });
    
    // Оптимизируем столбец проекта
    const projectCells = table.querySelectorAll('.column-project');
    projectCells.forEach(cell => {
        const projectName = cell.querySelector('.project-name');
        if (projectName) {
            projectName.style.overflow = 'hidden';
            projectName.style.textOverflow = 'ellipsis';
            projectName.style.whiteSpace = 'nowrap';
            projectName.style.maxWidth = 'calc(100% - 40px)';
            projectName.style.display = 'inline-block';
            projectName.style.verticalAlign = 'middle';
        }
    });
    
    // Оптимизируем столбец исполнителя
    const assigneeCells = table.querySelectorAll('.column-assignee');
    assigneeCells.forEach(cell => {
        const assigneeName = cell.querySelector('.assignee-name');
        if (assigneeName) {
            assigneeName.style.overflow = 'hidden';
            assigneeName.style.textOverflow = 'ellipsis';
            assigneeName.style.whiteSpace = 'nowrap';
            assigneeName.style.maxWidth = 'calc(100% - 40px)';
            assigneeName.style.display = 'inline-block';
            assigneeName.style.verticalAlign = 'middle';
        }
    });
}

function setupColumnToggle() {
    // Получаем кнопку переключения столбцов
    const toggleButton = document.querySelector('.toggle-columns-btn');
    if (!toggleButton) return;
    
    // Получаем или создаем выпадающий список колонок
    let columnsDropdown = document.getElementById('columns-dropdown');
    
    if (!columnsDropdown) {
        columnsDropdown = document.createElement('div');
        columnsDropdown.id = 'columns-dropdown';
        columnsDropdown.className = 'columns-dropdown';
        columnsDropdown.style.display = 'none';
        
        // Заголовок
        const header = document.createElement('div');
        header.className = 'columns-dropdown-header';
        header.textContent = 'Выбор столбцов';
        columnsDropdown.appendChild(header);
        
        // Контейнер для чекбоксов
        const optionsContainer = document.createElement('div');
        
        // Создаем опции для каждой колонки
        const columnNames = {
            'id': 'ID',
            'name': 'Название',
            'status': 'Статус',
            'project': 'Проект',
            'dates': 'Даты',
            'assignee': 'Исполнитель',
            'actions': 'Действия'
        };
        
        for (const column in columnNames) {
            const option = document.createElement('label');
            option.className = 'column-option';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = true;
            checkbox.dataset.column = column;
            
            // Проверяем сохраненные настройки
            const savedSettings = JSON.parse(localStorage.getItem('columnSettings')) || {};
            if (savedSettings[column] !== undefined) {
                checkbox.checked = savedSettings[column];
            }
            
            checkbox.addEventListener('change', function() {
                toggleColumn(column, this.checked);
            });
            
            option.appendChild(checkbox);
            option.appendChild(document.createTextNode(columnNames[column]));
            optionsContainer.appendChild(option);
        }
        
        columnsDropdown.appendChild(optionsContainer);
        
        // Добавляем выпадающий список в документ
        document.body.appendChild(columnsDropdown);
    }
    
    // Отображаем/скрываем выпадающий список при клике на кнопку
    toggleButton.addEventListener('click', function(event) {
        event.stopPropagation();
        
        // Позиционируем выпадающий список относительно кнопки
        const rect = toggleButton.getBoundingClientRect();
        columnsDropdown.style.top = (rect.bottom + window.scrollY) + 'px';
        columnsDropdown.style.right = (window.innerWidth - rect.right) + 'px';
        
        // Отображаем или скрываем выпадающий список
        if (columnsDropdown.style.display === 'block') {
            columnsDropdown.style.display = 'none';
        } else {
            columnsDropdown.style.display = 'block';
        }
    });
    
    // Скрываем выпадающий список при клике вне его
    document.addEventListener('click', function(event) {
        if (!columnsDropdown.contains(event.target) && event.target !== toggleButton) {
            columnsDropdown.style.display = 'none';
        }
    });
    
    // Загружаем сохраненные настройки отображения колонок
    loadColumnSettings();
}

function toggleColumn(column, show) {
    // Получаем все элементы с классом для данной колонки
    const elements = document.querySelectorAll(`.column-${column}`);
    
    // Отображаем или скрываем элементы
    elements.forEach(element => {
        element.style.display = show ? '' : 'none';
    });
    
    // Сохраняем настройки отображения колонок
    saveColumnSettings();
}

function saveColumnSettings() {
    const settings = {};
    
    // Получаем все чекбоксы
    const checkboxes = document.querySelectorAll('#columns-dropdown input[type="checkbox"]');
    
    // Сохраняем состояние каждого чекбокса
    checkboxes.forEach(checkbox => {
        settings[checkbox.dataset.column] = checkbox.checked;
    });
    
    // Сохраняем настройки в localStorage
    localStorage.setItem('columnSettings', JSON.stringify(settings));
}

function loadColumnSettings() {
    // Получаем сохраненные настройки из localStorage
    const settings = JSON.parse(localStorage.getItem('columnSettings'));
    
    if (!settings) return;
    
    // Применяем настройки к чекбоксам и колонкам
    Object.keys(settings).forEach(column => {
        const checkbox = document.querySelector(`#columns-dropdown input[data-column="${column}"]`);
        
        if (checkbox) {
            checkbox.checked = settings[column];
            toggleColumn(column, settings[column]);
        }
    });
}