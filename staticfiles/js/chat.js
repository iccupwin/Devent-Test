document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const newChatButton = document.getElementById('newChatButton');
    
    // Получаем ID разговора из шаблона или устанавливаем null для нового чата
    let currentConversationId = typeof currentConversationId !== 'undefined' ? currentConversationId : null;
    
    // Автоматическое увеличение высоты textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Прокрутка чата вниз при загрузке страницы
    if (chatMessages.lastElementChild) {
        chatMessages.lastElementChild.scrollIntoView();
    }
    
    // Обработчик кнопки "Новый чат"
    if (newChatButton) {
        newChatButton.addEventListener('click', function() {
            window.location.href = '/';
        });
    }
    
    // Обработчик отправки формы
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Добавляем сообщение пользователя в чат
        addMessageToChat('user', message);
        
        // Очищаем поле ввода
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Показываем индикатор набора текста
        const typingIndicator = addTypingIndicator();
        
        // Отправляем сообщение на сервер
        sendMessageToServer(message)
            .then(response => {
                // Удаляем индикатор набора текста
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                
                // Добавляем ответ от Claude в чат
                addMessageToChat('assistant', response.message);
                
                // Сохраняем ID разговора и обновляем URL, если это новый чат
                if (response.conversation_id && !currentConversationId) {
                    currentConversationId = response.conversation_id;
                    // Обновляем URL без перезагрузки страницы
                    window.history.pushState(
                        {}, 
                        '', 
                        `/conversation/${currentConversationId}/`
                    );
                    
                    // Обновляем список чатов
                    updateConversationsList();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Удаляем индикатор набора текста
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                
                // Показываем сообщение об ошибке
                addMessageToChat('assistant', 'Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.');
            });
    });
    
    // Функция для добавления сообщения в чат
    function addMessageToChat(role, content) {
        // Удаляем приветственное сообщение, если оно есть
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', role);
        
        const roleElement = document.createElement('div');
        roleElement.classList.add('message-role');
        roleElement.textContent = role === 'user' ? 'Вы' : 'Claude';
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        contentElement.textContent = content;
        
        messageElement.appendChild(roleElement);
        messageElement.appendChild(contentElement);
        
        chatMessages.appendChild(messageElement);
        
        // Прокручиваем чат до последнего сообщения
        messageElement.scrollIntoView({ behavior: 'smooth' });
        
        return messageElement;
    }
    
    // Функция для обновления списка чатов (для AJAX)
    function updateConversationsList() {
        // Эта функция будет использоваться в будущем для динамического обновления списка
        // Пока просто перезагружаем страницу после определенного времени
        if (typeof conversationsListElement !== 'undefined') {
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }
    
    // Функция для добавления индикатора набора текста
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.classList.add('typing-indicator');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.classList.add('typing-dot');
            indicator.appendChild(dot);
        }
        
        chatMessages.appendChild(indicator);
        indicator.scrollIntoView({ behavior: 'smooth' });
        
        return indicator;
    }
    
    // Функция для отправки сообщения на сервер
    async function sendMessageToServer(message) {
        const response = await fetch('/api/message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return response.json();
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
});