from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import random

app = Flask(__name__)
CORS(app)

public_messages = []# Общие сообщения
private_messages = {} # Приватные сообщения
user_profiles = {} # Профили пользователей (ключ - номер телефона)
online_users = {} # Онлайн статусы (ключ - номер телефона)
verification_codes = {} # Временное хранилище кодов подтверждения

def get_chat_key(user1, user2):
    return ":".join(sorted([user1, user2]))

# 1. Отправка кода подтверждения
@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    if not phone:
        return jsonify({"status": "error", "message": "Номер телефона обязателен"}), 400

    # Генерируем 4-значный код
    code = str(random.randint(1000, 9999))
    verification_codes[phone] = code
    
    # В реальном приложении здесь будет отправка SMS
    print(f"***** КОД ДЛЯ {phone}: {code} *****")
    
    return jsonify({"status": "success", "message": "Код отправлен"})

# 2. Подтверждение кода и регистрация
@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()

    if not phone or not name or not code:
        return jsonify({"status": "error", "message": "Все поля обязательны"}), 400

    # Проверяем код
    if phone not in verification_codes or verification_codes[phone] != code:
        return jsonify({"status": "error", "message": "Неверный код"}), 400

    # Удаляем использованный код
    del verification_codes[phone]

    # Создаем или обновляем профиль
    user_profiles[phone] = {
        'phone': phone,
        'name': name,
        'registered_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # Отмечаем онлайн
    online_users[phone] = datetime.datetime.now()

    return jsonify({
        "status": "success",
        "profile": user_profiles[phone]
    })

# ... (все остальные маршруты: /get_profile, /get_all_profiles, /ping,
#      /get_public_messages, /send_public_message, /get_private_messages,
#      /send_private_message, /get_chats, /version.json остаются без изменений)
