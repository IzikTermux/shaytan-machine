from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import json
import os
import threading
import telebot
from bot import bot, TOKEN  # Импортируем также TOKEN

app = Flask(__name__)
CORS(app)

# Добавим обработку порта для Render
port = int(os.environ.get('PORT', 5000))

# Глобальная переменная для отслеживания статуса бота
bot_thread = None
bot_started = False

def start_bot():
    global bot_started
    if not bot_started:
        try:
            print("Запускаем бота...")
            bot.infinity_polling()
        except Exception as e:
            print(f"Ошибка запуска бота: {e}")

@app.before_first_request
def init_bot():
    global bot_thread, bot_started
    if not bot_started:
        print("Инициализация бота...")
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()
        bot_started = True
        
        # Отправляем сообщение о запуске
        try:
            bot.send_message(1228708306, "🚀 Бот перезапущен и готов к работе!")
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")

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
