// DOM элементы
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const recordBtn = document.getElementById('recordBtn');
const stopRecordBtn = document.getElementById('stopRecordBtn');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const fileUploadLabel = document.getElementById('fileUploadLabel');
const recognizedText = document.getElementById('recognizedText');
const promptText = document.getElementById('promptText');
const generateBtn = document.getElementById('generateBtn');
const generateFastBtn = document.getElementById('generateFastBtn');
const clearTextBtn = document.getElementById('clearTextBtn');
const downloadBtn = document.getElementById('downloadBtn');
const recordingStatus = document.getElementById('recordingStatus');
const uploadStatus = document.getElementById('uploadStatus');
const generationStatus = document.getElementById('generationStatus');
const imageContainer = document.getElementById('imageContainer');

// Toast уведомления
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    let icon = '';
    switch(type) {
        case 'success': icon = '<i class="fas fa-check-circle"></i>'; break;
        case 'error': icon = '<i class="fas fa-exclamation-circle"></i>'; break;
        default: icon = '<i class="fas fa-info-circle"></i>';
    }
    toast.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Обновление статуса
function updateStatus(element, message, isError = false) {
    if (!element) return;
    element.textContent = message;
    element.style.color = isError ? '#ff4757' : '#00d68f';
}

// Синхронизация текста
recognizedText.addEventListener('input', () => {
    promptText.value = recognizedText.value;
});

clearTextBtn.addEventListener('click', () => {
    recognizedText.value = '';
    promptText.value = '';
    showToast('Текст очищен', 'info');
});

// Запись с микрофона
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });;
            await sendAudioToServer(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        recordBtn.disabled = true;
        stopRecordBtn.disabled = false;
        updateStatus(recordingStatus, '🔴 Запись... Говорите чётко');
        showToast('Запись началась', 'info');
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('Нет доступа к микрофону', 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.disabled = false;
        stopRecordBtn.disabled = true;
        updateStatus(recordingStatus, '⏹️ Обработка...');
    }
}

async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    try {
        const response = await fetch('/recognize_microphone', { method: 'POST', body: formData });
        const data = await response.json();
        
        if (data.success) {
            recognizedText.value = data.text;
            promptText.value = data.text;
            updateStatus(recordingStatus, '✅ Распознано!');
            showToast('Речь успешно распознана', 'success');
        } else {
            updateStatus(recordingStatus, '❌ Ошибка', true);
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('Ошибка соединения', 'error');
    }
}

// Загрузка файла (drag & drop)
fileUploadLabel?.addEventListener('click', () => fileInput.click());

fileUploadLabel?.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadLabel.style.borderColor = '#6c63ff';
});

fileUploadLabel?.addEventListener('dragleave', (e) => {
    e.preventDefault();
    fileUploadLabel.style.borderColor = 'rgba(108, 99, 255, 0.3)';
});

fileUploadLabel?.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadLabel.style.borderColor = 'rgba(108, 99, 255, 0.3)';
    const files = e.dataTransfer.files;
    if (files.length) {
        fileInput.files = files;
        uploadFile();
    }
});

fileInput?.addEventListener('change', () => { if (fileInput.files.length) uploadFile(); });

async function uploadFile() {
    const file = fileInput.files[0];
    if (!file) { showToast('Выберите файл', 'warning'); return; }
    
    const formData = new FormData();
    formData.append('file', file);
    updateStatus(uploadStatus, '⏳ Загрузка...');
    
    try {
        const response = await fetch('/recognize_file', { method: 'POST', body: formData });
        const data = await response.json();
        
        if (data.success) {
            recognizedText.value = data.text;
            promptText.value = data.text;
            updateStatus(uploadStatus, '✅ Файл обработан!');
            showToast('Файл успешно распознан', 'success');
        } else {
            updateStatus(uploadStatus, '❌ ' + data.error, true);
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('Ошибка соединения', 'error');
    }
}

// Генерация изображения
async function generateImage(isFast = false) {
    const prompt = promptText.value.trim();
    if (!prompt) { showToast('Введите текст для генерации', 'warning'); return; }
    
    imageContainer.innerHTML = `
        <div class="placeholder">
            <div class="placeholder-icon loading-pulse">
                <i class="fas fa-magic"></i>
                <i class="fas fa-spinner fa-pulse"></i>
                <i class="fas fa-image"></i>
            </div>
            <p>🎨 Генерация изображения${isFast ? ' (быстрый режим)' : ''}...</p>
            <span>${isFast ? 'Обычно занимает 5-10 секунд' : 'Обычно занимает 15-30 секунд'}</span>
        </div>
    `;
    
    updateStatus(generationStatus, '⏳ Генерация...');
    generateBtn.disabled = true;
    generateFastBtn.disabled = true;
    downloadBtn.style.display = 'none';
    
    try {
        const response = await fetch('/generate_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                prompt: prompt,
                fast: isFast  // <-- ПЕРЕДАЕМ параметр fast
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            imageContainer.innerHTML = `<img src="${data.image_url}?t=${Date.now()}" alt="Generated image">`;
            updateStatus(generationStatus, '✅ Изображение сгенерировано!');
            downloadBtn.style.display = 'flex';
            showToast('Изображение готово!', 'success');
            
            downloadBtn.onclick = () => {
                const link = document.createElement('a');
                link.href = data.image_url;
                link.download = `generated_${Date.now()}.png`;
                link.click();
                showToast('Скачивание началось', 'success');
            };
        } else {
            imageContainer.innerHTML = `
                <div class="placeholder">
                    <div class="placeholder-icon"><i class="fas fa-exclamation-triangle"></i></div>
                    <p>❌ Ошибка генерации</p>
                    <span>${data.error || 'Попробуйте другой промпт'}</span>
                </div>
            `;
            updateStatus(generationStatus, '❌ Ошибка', true);
            showToast(data.error || 'Ошибка генерации', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        imageContainer.innerHTML = `
            <div class="placeholder">
                <div class="placeholder-icon"><i class="fas fa-plug"></i></div>
                <p>❌ Ошибка соединения</p>
                <span>Проверьте интернет</span>
            </div>
        `;
        updateStatus(generationStatus, '❌ Ошибка', true);
        showToast('Ошибка соединения', 'error');
    } finally {
        generateBtn.disabled = false;
        generateFastBtn.disabled = false;
    }
}

// Обработчики
recordBtn.addEventListener('click', startRecording);
stopRecordBtn.addEventListener('click', stopRecording);
uploadBtn.addEventListener('click', uploadFile);
generateBtn.addEventListener('click', () => generateImage(false));
generateFastBtn.addEventListener('click', () => generateImage(true));

// Проверка микрофона
if (!navigator.mediaDevices?.getUserMedia) {
    recordBtn.disabled = true;
    showToast('Микрофон не поддерживается', 'error');
}

console.log('🎤 Voice to Image Generator готов!');