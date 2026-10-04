(function() {
    const BASE_URL = "https://vertebra-perfume-ai.onrender.com";

    const styles = `
        #vertebra-chat-widget { position: fixed; bottom: 20px; right: 20px; z-index: 999999; display: flex; flex-direction: column; align-items: flex-end; font-family: 'Tajawal', sans-serif; }
        #vertebra-chat-window { width: 380px; height: 600px; background: white; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); overflow: hidden; display: none; margin-bottom: 15px; border: 1px solid #EAEAEA; transition: all 0.3s ease; }
        #vertebra-chat-window iframe { width: 100%; height: 100%; border: none; }
        #vertebra-chat-btn { width: 60px; height: 60px; background: #9B26B6; border-radius: 50%; cursor: pointer; box-shadow: 0 4px 12px rgba(155,38,182,0.3); display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
        #vertebra-chat-btn:hover { transform: scale(1.05); }
        #vertebra-chat-btn svg { width: 30px; height: 30px; fill: white; }
    `;

    const styleSheet = document.createElement("style");
    styleSheet.innerText = styles;
    document.head.appendChild(styleSheet);

    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'vertebra-chat-widget';

    widgetContainer.innerHTML = `
        <div id="vertebra-chat-window">
            <iframe src="${BASE_URL}/"></iframe>
        </div>
        <div id="vertebra-chat-btn" onclick="toggleVertebraChat()">
            <!-- اللوغو ديالك -->
            <img src="${BASE_URL}/static/logo.png" alt="Chat" style="width: 35px; height: 35px; object-fit: contain;">
        </div>
    `;
    document.body.appendChild(widgetContainer);

    window.toggleVertebraChat = function() {
        const chatWindow = document.getElementById('vertebra-chat-window');
        if (chatWindow.style.display === 'none' || chatWindow.style.display === '') {
            chatWindow.style.display = 'block';
        } else {
            chatWindow.style.display = 'none';
        }
    };

    window.addEventListener('message', function(event) {
        if (event.data === 'closeChatWidget') {
            const chatWindow = document.getElementById('vertebra-chat-window');
            if (chatWindow) {
                chatWindow.style.display = 'none';
            }
        }
    });

})();