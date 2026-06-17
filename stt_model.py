import numpy as np
from faster_whisper import WhisperModel
import os
import logging
import tempfile
import soundfile as sf

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechToText:
    """Распознавание речи без PyTorch (только CPU оптимизации)"""
    
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        logger.info(f"Инициализация модели распознавания речи: {model_size}")
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.num_threads = 8
        
        # faster-whisper использует CTranslate2 (не требует PyTorch!)
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            cpu_threads=self.num_threads,
            num_workers=1
        )
        logger.info(f"Модель {model_size} успешно загружена")
    
    def recognize(self, audio_path, language="ru"):
        """Распознавание речи из аудиофайла"""
        try:
            logger.info(f"Распознавание файла: {audio_path}")
            
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Файл {audio_path} не найден")
            
            # Транскрипция (без PyTorch!)
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                best_of=5,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "threshold": 0.5
                }
            )
            
            # Сбор текста из сегментов
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
                logger.debug(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
            result_text = " ".join(text_parts).strip()
            
            if not result_text:
                result_text = "Не удалось распознать речь. Попробуйте говорить четче."
            
            logger.info(f"Распознанный текст: {result_text[:100]}...")
            return result_text
            
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            return f"Ошибка распознавания: {str(e)}"

# Пример использования
if __name__ == "__main__":
    stt = SpeechToText()
    print("Модель готова к работе (без PyTorch!)")