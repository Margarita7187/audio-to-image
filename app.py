from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from stt_model import SpeechToText
from image_gen import ImageGenerator
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['SECRET_KEY'] = 'voice2image-secret-key'

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'webm'}

# Создание папок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/generated', exist_ok=True)

print("=" * 60)
print("Voice to Image Generator")
print("=" * 60)

# Инициализация моделей
print("✓ Загрузка модели распознавания речи...")
try:
    stt = SpeechToText(model_size="base")
    print("  Распознавание речи готово")
except Exception as e:
    print(f"✗ Ошибка загрузки STT: {e}")
    stt = None

print("✓ Загрузка модели генерации изображений (rudalle-Malevich)...")
try:
    image_gen = ImageGenerator()
    print("  Генератор изображений готов")
except Exception as e:
    print(f"✗ Ошибка загрузки генератора: {e}")
    image_gen = None

print("=" * 60)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/generated/<filename>')
def generated_file(filename):
    return send_from_directory('static/generated', filename)

@app.route('/recognize_microphone', methods=['POST'])
def recognize_microphone():
    if stt is None:
        return jsonify({'error': 'Модель распознавания не загружена'}), 503
    
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Аудио файл не найден'}), 400
        
        audio_file = request.files['audio']
        filename = secure_filename(f"mic_{uuid.uuid4().hex}.webm")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        text = stt.recognize(filepath)
        
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': True,
            'text': text,
            'message': 'Речь успешно распознана'
        })
        
    except Exception as e:
        logger.error(f"Ошибка распознавания: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/recognize_file', methods=['POST'])
def recognize_file():
    if stt is None:
        return jsonify({'error': 'Модель распознавания не загружена'}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400
        
        filename = secure_filename(f"upload_{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        text = stt.recognize(filepath)
        
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': True,
            'text': text,
            'message': 'Файл успешно обработан'
        })
        
    except Exception as e:
        logger.error(f"Ошибка обработки файла: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_image', methods=['POST'])
def generate_image():
    if image_gen is None:
        return jsonify({'error': 'Генератор изображений не загружен'}), 503
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        is_fast = data.get('fast', False)  # Получаем параметр fast из запроса
        
        if not prompt:
            return jsonify({'error': 'Текст не может быть пустым'}), 400
        
        logger.info(f"Запрос на генерацию: {prompt} (fast={is_fast})")
        
        # Выбираем метод в зависимости от параметра
        if is_fast:
            image_url = image_gen.generate_fast(prompt)
        else:
            image_url = image_gen.generate(prompt)
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'prompt': prompt,
            'message': 'Изображение успешно сгенерировано'
        })
        
    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🌐 Запуск сервера на http://localhost:8080")
    print("📝 Откройте браузер и перейдите по адресу выше")
    print("🛑 Нажмите Ctrl+C для остановки\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080, threaded=True)