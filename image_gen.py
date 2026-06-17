import os
from datetime import datetime
import logging
import torch
from diffusers import StableDiffusionPipeline
from deep_translator import GoogleTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGenerator:
    """Генерация изображений с автоматическим переводом на английский"""
    
    def __init__(self, model_id="runwayml/stable-diffusion-v1-5"):
        self.output_dir = "static/generated"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Загружаем переводчик
        try:
            self.translator = GoogleTranslator(source='ru', target='en')
            logger.info("✅ Переводчик (русский -> английский) загружен")
        except Exception as e:
            logger.warning(f"⚠️ Переводчик не загружен: {e}")
            self.translator = None

        # Загружаем модель генерации
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Загрузка модели {model_id} на {self.device}...")
        
        # Убираем problematic параметры
        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # Убираем variant! Используем float32
            safety_checker=None,
            requires_safety_checker=False
        )
        
        if self.device == "cpu":
            self.pipe.enable_attention_slicing()
        else:
            self.pipe = self.pipe.to(self.device)
            self.pipe.enable_attention_slicing()
        
        logger.info("✅ Модель генерации загружена и готова к работе")
    
    def generate(self, prompt, steps=25, guidance_scale=7.5):
        """Генерация изображения с автоматическим переводом промпта"""
        logger.info(f"Оригинальный промпт: {prompt}")
        
        # Переводим промпт на английский если есть переводчик
        translated_prompt = prompt
        if self.translator and prompt.strip():
            try:
                translated_prompt = self.translator.translate(prompt)
                logger.info(f"Переведённый промпт: {translated_prompt}")
            except Exception as e:
                logger.error(f"Ошибка перевода: {e}")
        
        # Генерация изображения
        try:
            with torch.no_grad():
                result = self.pipe(
                    translated_prompt,
                    num_inference_steps=steps,
                    guidance_scale=guidance_scale
                )
            image = result.images[0]
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            raise Exception(f"Ошибка генерации: {str(e)}")
        
        # Сохраняем результат
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"generated_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        image.save(filepath)
        
        logger.info(f"✅ Изображение сохранено: {filepath}")
        return f"/static/generated/{filename}"
    
    def generate_fast(self, prompt):
        """Быстрая генерация"""
        return self.generate(prompt, steps=15)