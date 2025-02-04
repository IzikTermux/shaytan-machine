from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import json
import os
import telebot
import logging
import sys
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Функции для работы с конфигурацией
def load_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            # Проверяем, не истекло ли время действия режима
            if config['mode_expires_at']:
                expires_at = datetime.fromisoformat(config['mode_expires_at'])
                if datetime.now() > expires_at:
                    config['special_mode'] = False
                    config['mode_expires_at'] = None
                    save_config(config)
            return config
    except:
        return {"special_mode": False, "special_students": {}, "mode_expires_at": None}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

# Создаем бота
TOKEN = '7512260695:AAGRESRxQglZSb0mTFQri6ZFOha8PakUstA'
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)
CORS(app)

# Добавим обработку порта для Render
port = int(os.environ.get('PORT', 10000))

# Импортируем обработчики после создания бота
from bot import *

# Инициализируем config.json если его нет
if not os.path.exists('config.json'):
    save_config({"special_mode": False, "special_students": {}, "mode_expires_at": None})

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
    return send_file('config.json')

@app.route('/update_config', methods=['POST'])
def update_config():
    config = request.json
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    return jsonify({"success": True})

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

# Добавьте новый роут
@app.route('/test_special')
def test_special():
    try:
        config = load_config()
        expires_at = datetime.now() + timedelta(minutes=5)
        config['special_mode'] = True
        config['mode_expires_at'] = expires_at.isoformat()
        save_config(config)
        logger.info(f"Режим свои включен до {expires_at}")
        
        # Проверяем, что конфиг сохранился
        saved_config = load_config()
        logger.info(f"Сохраненный конфиг: {saved_config}")
        
        return jsonify({
            "status": "success",
            "message": "Режим свои включен на 5 минут",
            "expires_at": expires_at.isoformat(),
            "config": saved_config
        })
    except Exception as e:
        logger.error(f"Ошибка теста режима свои: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
