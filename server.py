from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import json
import os
import telebot
from bot import bot, TOKEN

app = Flask(__name__)
CORS(app)

# Добавим обработку порта для Render
port = int(os.environ.get('PORT', 10000))

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
            print("Получен webhook запрос от Telegram")  # Добавляем логирование
            json_string = request.get_data().decode('utf-8')
            print(f"Содержимое запроса: {json_string}")  # Логируем содержимое
            
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            
            print("Обновление успешно обработано")
            return 'ok', 200
        except Exception as e:
            print(f"Ошибка обработки вебхука: {e}")
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
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
