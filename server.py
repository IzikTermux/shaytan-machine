from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import json
import os
import telebot
from bot import bot, TOKEN

app = Flask(__name__)
CORS(app)

# Добавим обработку порта для Render
port = int(os.environ.get('PORT', 5000))

# Настраиваем вебхук при первом запросе
@app.before_first_request
def set_webhook():
    # Получаем URL из переменной окружения или используем тестовый
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://shaytan-web.onrender.com')
    url = f"{WEBHOOK_URL}/{TOKEN}"
    try:
        bot.remove_webhook()
        bot.set_webhook(url=url)
        # Отправляем сообщение о запуске
        bot.send_message(1228708306, f"🚀 Бот перезапущен\nWebhook URL: {url}")
        print(f"Вебхук установлен на {url}")
    except Exception as e:
        print(f"Ошибка установки вебхука: {e}")

# Обработчик вебхуков от Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            print(f"Получено обновление: {json_string}")  # Добавляем логирование
            return 'ok', 200
        except Exception as e:
            print(f"Ошибка обработки вебхука: {e}")  # Добавляем логирование ошибок
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
