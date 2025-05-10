document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    
    // Получаем ID беседы из data-атрибута
    let currentConversationId = null;
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer && chatContainer.getAttribute('data-conversation-id')) {
        currentConversationId = chatContainer.getAttribute('data-conversation-id');
    }
    
    console.log('Текущий ID беседы:', currentConversationId);
    
    // Автоматически регулируем высоту текстового поля
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Прокручиваем чат вниз при загрузке
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    scrollToBottom();
    
    // Обработчик отправки формы
    if (messageForm) {
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
                    
                    // Если это новая беседа, обновляем ID и URL
                    if (response.conversation_id && !currentConversationId) {
                        currentConversationId = response.conversation_id;
                        
                        // Обновляем URL без перезагрузки страницы
                        const newUrl = `/conversation/${currentConversationId}/`;
                        window.history.pushState({}, '', newUrl);
                        
                        // Обновляем боковую панель
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                    
                    // Прокручиваем чат вниз
                    scrollToBottom();
                })
                .catch(error => {
                    console.error('Ошибка:', error);
                    
                    // Удаляем индикатор набора текста
                    if (typingIndicator) {
                        typingIndicator.remove();
                    }
                    
                    // Показываем сообщение об ошибке
                    addMessageToChat('assistant', 'Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.');
                    scrollToBottom();
                });
        });
    }
    
    // Функция для добавления сообщения в чат
    function addMessageToChat(role, content) {
        // Удаляем приветственное сообщение, если оно есть
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Создаем элемент сообщения
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', role);
        
        // Разная структура HTML в зависимости от роли
        if (role === 'assistant') {
            messageElement.innerHTML = `
                <div class="assistant-avatar">C</div>
                <div class="message-content-wrapper">
                    <div class="message-role">Claude</div>
                    <div class="message-content">${formatMessageContent(content)}</div>
                </div>
            `;
        } else {
            messageElement.innerHTML = `
                <div class="message-role">Вы</div>
                <div class="message-content">${formatMessageContent(content)}</div>
            `;
        }
        
        // Добавляем в DOM
        chatMessages.appendChild(messageElement);
        
        // Прокручиваем в видимую область
        scrollToBottom();
        
        return messageElement;
    }
    
    // Функция форматирования содержимого сообщения
    function formatMessageContent(content) {
        // Проверяем, что content является строкой
        if (typeof content !== 'string') {
            // Если это объект, пытаемся преобразовать его в строку
            if (typeof content === 'object') {
                try {
                    content = JSON.stringify(content);
                } catch (e) {
                    content = String(content);
                }
            } else {
                // Для других типов просто преобразуем в строку
                content = String(content);
            }
        }
        
        // Экранируем HTML и сохраняем переносы строк
        const escaped = escapeHtml(content);
        return escaped.replace(/\n/g, '<br>');
    }
    
    // Функция добавления индикатора набора текста
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.classList.add('typing-indicator');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.classList.add('typing-dot');
            indicator.appendChild(dot);
        }
        
        chatMessages.appendChild(indicator);
        scrollToBottom();
        
        return indicator;
    }
    
    // Функция отправки сообщения на сервер
    async function sendMessageToServer(message) {
        try {
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
            
            const data = await response.json();
            
            if (!response.ok) {
                // Если есть сообщение об ошибке в ответе, используем его
                const errorMessage = data.error || 'Произошла неизвестная ошибка';
                throw new Error(errorMessage);
            }
            
            return data;
        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);
            throw new Error(error.message || 'Произошла ошибка при отправке сообщения');
        }
    }
    
    // Вспомогательная функция для экранирования HTML
    function escapeHtml(unsafe) {
        // Проверяем, что unsafe является строкой
        if (typeof unsafe !== 'string') {
            if (unsafe === null || unsafe === undefined) {
                return '';
            }
            try {
                unsafe = String(unsafe);
            } catch (e) {
                console.error('Error converting to string:', e);
                return '';
            }
        }
        
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Получение CSRF токена из cookies
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