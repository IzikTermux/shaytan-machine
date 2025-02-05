from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import json
import os
import telebot
import logging
import sys
from datetime import datetime, timedelta
import tempfile

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Добавим глобальный конфиг в память
GLOBAL_CONFIG = {
    "special_mode": False,
    "special_students": {},
    "mode_expires_at": None,
    "salted_student": None
}

def save_config(config):
    try:
        logger.info(f"Сохраняем конфиг в память: {config}")
        global GLOBAL_CONFIG
        GLOBAL_CONFIG.update(config)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения конфига: {e}", exc_info=True)
        return False

def load_config():
    try:
        logger.info(f"Загружаем конфиг из памяти: {GLOBAL_CONFIG}")
        global GLOBAL_CONFIG
        
        # Проверяем, не истекло ли время действия режима
        if GLOBAL_CONFIG.get('mode_expires_at'):
            expires_at = datetime.fromisoformat(GLOBAL_CONFIG['mode_expires_at'])
            if datetime.now() > expires_at:
                GLOBAL_CONFIG['special_mode'] = False
                GLOBAL_CONFIG['mode_expires_at'] = None
                
        return GLOBAL_CONFIG
    except Exception as e:
        logger.error(f"Ошибка загрузки конфига: {e}", exc_info=True)
        return {
            "special_mode": False,
            "special_students": {},
            "mode_expires_at": None,
            "salted_student": None
        }

# Создаем бота
TOKEN = '7512260695:AAGRESRxQglZSb0mTFQri6ZFOha8PakUstA'
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)
CORS(app)

# Добавим обработку порта для Render
port = int(os.environ.get('PORT', 10000))

# Импортируем обработчики после создания бота
from bot import *

# Настраиваем вебхук при первом запросе
@app.before_first_request
def set_webhook():
    # Получаем URL из переменной окружения или используем тестовый
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://shaytan-web.onrender.com')
    url = f"{WEBHOOK_URL}/{TOKEN}"
    try:
        print("Начинаем настройку вебхука...")  # Добавляем логирование
        bot.remove_webhook()
        bot.set_webhook(url=url)
        print(f"Вебхук установлен на {url}")
        
        # Пробуем отправить тестовое сообщение
        try:
            bot.send_message(1228708306, f"🚀 Бот перезапущен\nWebhook URL: {url}")
            print("Тестовое сообщение отправлено")
        except Exception as e:
            print(f"Ошибка отправки тестового сообщения: {e}")
            
    except Exception as e:
        print(f"Ошибка установки вебхука: {e}")

# Обработчик вебхуков от Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            logger.info("Получен webhook запрос от Telegram")
            json_string = request.get_data().decode('utf-8')
            logger.info(f"Содержимое запроса: {json_string}")
            
            update = telebot.types.Update.de_json(json_string)
            
            # Добавляем логирование типа обновления
            if update.message:
                logger.info(f"Получено сообщение: {update.message.text}")
            elif update.callback_query:
                logger.info(f"Получен callback_query: {update.callback_query.data}")
            
            # Обрабатываем обновление синхронно
            bot.process_new_updates([update])
            logger.info("Обновление успешно обработано")
            return 'ok', 200
            
        except Exception as e:
            logger.error("Ошибка обработки вебхука", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return str(e), 500
    return 'error', 403

@app.route('/')
def serve_html():
    return send_file('main.html')

@app.route('/config.json')
def serve_config():
    config = load_config()
    logger.info(f"Отдаем конфиг: {config}")
    return jsonify(config)

@app.route('/update_config', methods=['POST'])
def update_config():
    try:
        config = request.json
        if save_config(config):
            return jsonify({"success": True, "config": load_config()})
        else:
            return jsonify({"success": False, "error": "Failed to save config"}), 500
    except Exception as e:
        logger.error(f"Ошибка обновления конфига: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

# Добавим тестовый роут
@app.route('/test')
def test():
    try:
        bot.send_message(1228708306, "🔄 Тест соединения")
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка теста: {e}", exc_info=True)
        return str(e), 500

# Добавим новый роут для проверки вебхука
@app.route('/check_webhook')
def check_webhook():
    try:
        webhook_info = bot.get_webhook_info()
        return jsonify({
            "webhook_url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Обновим тестовый роут
@app.route('/test_special')
def test_special():
    try:
        config = load_config()
        expires_at = datetime.now() + timedelta(minutes=5)
        
        config['special_mode'] = True
        config['mode_expires_at'] = expires_at.isoformat()
        
        if save_config(config):
            logger.info(f"Режим свои включен до {expires_at}")
            return jsonify({
                "status": "success",
                "message": "Режим свои включен на 5 минут",
                "expires_at": expires_at.isoformat(),
                "config": load_config()  # Перезагружаем конфиг для проверки
            })
        else:
            return jsonify({"status": "error", "message": "Failed to save config"}), 500
            
    except Exception as e:
        logger.error(f"Ошибка теста режима свои: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.before_first_request
def check_permissions():
    try:
        logger.info(f"Временная директория: {tempfile.gettempdir()}")
        logger.info(f"Текущая директория: {os.getcwd()}")
        logger.info(f"Содержимое текущей директории: {os.listdir()}")
        
        # Проверяем права на запись во временную директорию
        test_file = os.path.join(tempfile.gettempdir(), 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info("Права на запись во временную директорию есть")
        
    except Exception as e:
        logger.error(f"Проблема с правами доступа: {e}", exc_info=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
