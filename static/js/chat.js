document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const newChatButton = document.getElementById('newChatButton');
    
    // Объявляем переменную для ID разговора
    let currentConversationId;
    
    // Проверяем, существует ли переменная в глобальном контексте (установленная в шаблоне)
    if (typeof window.conversationId !== 'undefined') {
        currentConversationId = window.conversationId;
    } else {
        currentConversationId = null;
    }
    
    console.log('Chat.js loaded, currentConversationId:', currentConversationId);
    
    // Автоматическое увеличение высоты textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Устанавливаем фокус на поле ввода
    messageInput.focus();
    
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
        
        console.log('Sending message:', message);
        
        // Добавляем сообщение пользователя в чат
        addMessageToChat('user', message);
        
        // Очищаем поле ввода
        messageInput.value = '';
        messageInput.style.height = 'auto';
        messageInput.focus();
        
        // Показываем индикатор набора текста
        const typingIndicator = addTypingIndicator();
        
        // Отправляем сообщение на сервер
        sendMessageToServer(message)
            .then(response => {
                console.log('Received response:', response);
                
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
                console.error('Error sending message:', error);
                
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
        console.log('Adding message to chat:', role, content);
        
        // Удаляем приветственное сообщение, если оно есть
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', role);
        
        if (role === 'assistant') {
            const avatarElement = document.createElement('div');
            avatarElement.classList.add('assistant-avatar');
            avatarElement.textContent = 'C';
            
            const contentWrapperElement = document.createElement('div');
            contentWrapperElement.classList.add('message-content-wrapper');
            
            const roleElement = document.createElement('div');
            roleElement.classList.add('message-role');
            roleElement.textContent = 'Claude';
            
            const contentElement = document.createElement('div');
            contentElement.classList.add('message-content');
            contentElement.textContent = content;
            
            contentWrapperElement.appendChild(roleElement);
            contentWrapperElement.appendChild(contentElement);
            
            messageElement.appendChild(avatarElement);
            messageElement.appendChild(contentWrapperElement);
        } else {
            const roleElement = document.createElement('div');
            roleElement.classList.add('message-role');
            roleElement.textContent = 'Вы';
            
            const contentElement = document.createElement('div');
            contentElement.classList.add('message-content');
            contentElement.textContent = content;
            
            messageElement.appendChild(roleElement);
            messageElement.appendChild(contentElement);
        }
        
        chatMessages.appendChild(messageElement);
        
        // Прокручиваем чат до последнего сообщения
        messageElement.scrollIntoView({ behavior: 'smooth' });
        
        return messageElement;
    }
    
    // Функция для обновления списка чатов (для AJAX)
    function updateConversationsList() {
        console.log('Updating conversations list');
        // Эта функция будет использоваться в будущем для динамического обновления списка
        // Пока просто перезагружаем страницу после определенного времени
        if (document.querySelector('.conversations-list')) {
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
        console.log('Sending message to server:', message);
        
        try {
            // Получаем CSRF-токен
            const csrftoken = getCookie('csrftoken');
            console.log('CSRF token:', csrftoken);
            
            // Формируем данные для отправки
            const data = {
                message: message,
                conversation_id: currentConversationId
            };
            console.log('Request data:', data);
            
            // Отправляем запрос
            const response = await fetch('/api/message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            });
            
            console.log('Server response status:', response.status);
            
            // Если ответ не OK, выбрасываем ошибку
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Server error response:', errorData);
                throw new Error(errorData.error || 'Ошибка сервера');
            }
            
            // Парсим JSON и возвращаем результат
            const result = await response.json();
            console.log('Server response data:', result);
            return result;
        } catch (error) {
            console.error('Error in sendMessageToServer:', error);
            throw error;
        }
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