document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing');
    const voiceBtn = document.getElementById('voice-btn');
    const ttsToggle = document.getElementById('tts-toggle');

    const toggleBtns = document.querySelectorAll('.toggle-btn');

    let isTtsEnabled = true;
    let currentProvider = 'ollama';

    // Handle Toggle
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            toggleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentProvider = btn.dataset.provider;
        });
    });

    // Scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    scrollToBottom();

    // Text to Speech
    const speak = (text) => {
        if (!isTtsEnabled) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
    };

    ttsToggle.addEventListener('click', () => {
        isTtsEnabled = !isTtsEnabled;
        ttsToggle.classList.toggle('active', !isTtsEnabled);
        if (!isTtsEnabled) window.speechSynthesis.cancel();
    });

    // Speech to Text
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        voiceBtn.addEventListener('click', () => {
            recognition.start();
            voiceBtn.style.color = '#ef4444';
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            voiceBtn.style.color = '';
            chatForm.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = () => {
            voiceBtn.style.color = '';
        };

        recognition.onend = () => {
            voiceBtn.style.color = '';
        };
    } else {
        voiceBtn.style.display = 'none';
    }

    // Handle Form Submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        const userDiv = document.createElement('div');
        userDiv.className = 'message user';
        userDiv.textContent = message;
        chatMessages.appendChild(userDiv);
        userInput.value = '';
        scrollToBottom();

        // Show typing
        typingIndicator.style.display = 'block';

        try {
            const formData = new FormData();
            formData.append('message', message);
            formData.append('provider', currentProvider);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            const response = await fetch('/chat/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            typingIndicator.style.display = 'none';

            if (data.response) {
                const botDiv = document.createElement('div');
                botDiv.className = 'message bot';
                botDiv.textContent = data.response;

                if (data.image_url) {
                    const img = document.createElement('img');
                    img.src = data.image_url;
                    img.className = 'bot-image';
                    botDiv.appendChild(img);
                }

                chatMessages.appendChild(botDiv);
                speak(data.response);
            } else if (data.error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'message bot';
                errorDiv.style.color = '#ef4444';
                errorDiv.textContent = 'Error: ' + data.error;
                chatMessages.appendChild(errorDiv);
            }

            scrollToBottom();
        } catch (error) {
            typingIndicator.style.display = 'none';
            console.error(error);
        }
    });
});
