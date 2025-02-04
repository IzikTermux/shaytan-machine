from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import json
import os
import telebot
from bot import bot, TOKEN, handle_message  # Импортируем обработчик сообщений

app = Flask(__name__)
CORS(app)

# Добавим обработку порта для Render
port = int(os.environ.get('PORT', 5000))

# Настраиваем вебхук при первом запросе
@app.before_first_request
def set_webhook():
    url = f"https://shaytan-web.onrender.com/{TOKEN}"  # Замените на ваш URL
    try:
        bot.remove_webhook()
        bot.set_webhook(url=url)
        print(f"Вебхук установлен на {url}")
    except Exception as e:
        print(f"Ошибка установки вебхука: {e}")

# Обработчик вебхуков от Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'ok', 200
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

# Добавим роут для проверки статуса бота
@app.route('/bot_status')
def bot_status():
    global bot_started
    try:
        # Пробуем отправить тестовое сообщение
        bot.send_message(1228708306, "✅ Бот работает")
        return jsonify({"status": "running", "bot_started": bot_started})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "bot_started": bot_started})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
