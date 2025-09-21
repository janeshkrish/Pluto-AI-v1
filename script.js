document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const conversationLog = document.getElementById('conversation-log');
    const statusText = document.getElementById('status-text');
    const commandItems = document.querySelectorAll('.command-item');
    const langButtons = document.querySelectorAll('.lang-button');

    // --- WebSocket Event Handlers ---
    socket.on('connect', () => { statusText.textContent = 'Connected. Initializing...'; });
    socket.on('status_update', (msg) => { statusText.textContent = msg.data; });
    socket.on('log_message', (msg) => { addMessage(msg.data, `${msg.type}-message`); });
    socket.on('ai_speak', (msg) => { console.log(`AI Speech Triggered in ${msg.lang}:`, msg.data); });

    // --- Functions ---
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            socket.emit('user_message', { data: message });
            messageInput.value = '';
        }
    }

    function addMessage(text, type) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', type);
        messageElement.innerHTML = text.replace(/\n/g, '<br>');
        conversationLog.appendChild(messageElement);
        conversationLog.scrollTop = conversationLog.scrollHeight;
    }

    // --- Event Listeners ---
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (event) => { if (event.key === 'Enter') sendMessage(); });

    commandItems.forEach(item => {
        item.addEventListener('click', (event) => {
            event.preventDefault();
            const command = item.dataset.command;
            socket.emit('user_message', { data: command });
        });
    });

    // Language switcher logic
    langButtons.forEach(button => {
        button.addEventListener('click', () => {
            langButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const lang = button.dataset.lang;
            socket.emit('change_language', { lang: lang });
        });
    });
});

