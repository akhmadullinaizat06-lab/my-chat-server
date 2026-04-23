from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import random

app = Flask(__name__)
CORS(app)

# Хранилища
public_messages = []
private_messages = {}
user_profiles = {}
online_users = {}
verification_codes = {}

def get_chat_key(user1, user2):
    return ":".join(sorted([user1, user2]))

# ========== РЕГИСТРАЦИЯ ==========

@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    if not phone:
        return jsonify({"status": "error", "message": "Номер обязателен"}), 400
    
    code = str(random.randint(1000, 9999))
    verification_codes[phone] = code
    print(f"***** КОД ДЛЯ {phone}: {code} *****")
    return jsonify({"status": "success", "message": "Код отправлен"})

@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    
    if not phone or not name or not code:
        return jsonify({"status": "error"}), 400
    
    if phone not in verification_codes or verification_codes[phone] != code:
        return jsonify({"status": "error", "message": "Неверный код"}), 400
    
    del verification_codes[phone]
    user_profiles[phone] = {
        'phone': phone,
        'name': name,
        'registered_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    online_users[phone] = datetime.datetime.now()
    
    return jsonify({"status": "success", "profile": user_profiles[phone]})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    name = data.get('name', '').strip()
    
    if not phone or not name:
        return jsonify({"status": "error"}), 400
    
    user_profiles[phone] = {
        'phone': phone,
        'name': name,
        'registered_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    online_users[phone] = datetime.datetime.now()
    
    return jsonify({"status": "success", "profile": user_profiles[phone]})

# ========== ПРОФИЛИ ==========

@app.route('/get_profile')
def get_profile():
    phone = request.args.get('phone', '')
    if phone in user_profiles:
        return jsonify(user_profiles[phone])
    return jsonify(None)

@app.route('/get_all_profiles')
def get_all_profiles():
    profiles = []
    now = datetime.datetime.now()
    
    for phone, profile in user_profiles.items():
        last_seen = online_users.get(phone)
        is_online = False
        if last_seen:
            diff = (now - last_seen).total_seconds()
            is_online = diff < 300
        
        profiles.append({
            'phone': phone,
            'name': profile['name'],
            'online': is_online,
            'registered_at': profile.get('registered_at', '')
        })
    
    return jsonify(sorted(profiles, key=lambda x: (not x['online'], x['name'])))

@app.route('/get_users')
def get_users():
    """Совместимость со старым клиентом."""
    return get_all_profiles()

@app.route('/ping')
def ping():
    phone = request.args.get('phone', '')
    if phone and phone in user_profiles:
        online_users[phone] = datetime.datetime.now()
    return jsonify({"status": "ok"})

# ========== СООБЩЕНИЯ ==========

@app.route('/get_public_messages')
def get_public_messages():
    return jsonify(public_messages)

@app.route('/send_public_message', methods=['POST'])
def send_public_message():
    data = request.get_json()
    phone = data.get('phone', '')
    text = data.get('text', '')
    
    if not text or not phone:
        return jsonify({"status": "error"}), 400
    
    if phone not in user_profiles:
        return jsonify({"status": "error", "message": "Пользователь не найден"}), 404
    
    online_users[phone] = datetime.datetime.now()
    
    new_message = {
        "phone": phone,
        "name": user_profiles[phone]['name'],
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }
    
    public_messages.append(new_message)
    if len(public_messages) > 100:
        public_messages.pop(0)
    
    return jsonify({"status": "success"})

@app.route('/send_private_message', methods=['POST'])
def send_private_message():
    data = request.get_json()
    from_phone = data.get('from', '')
    to_phone = data.get('to', '')
    text = data.get('text', '')
    
    if not text or not from_phone or not to_phone:
        return jsonify({"status": "error"}), 400
    
    if from_phone not in user_profiles:
        return jsonify({"status": "error"}), 404
    
    online_users[from_phone] = datetime.datetime.now()
    
    chat_key = get_chat_key(from_phone, to_phone)
    
    if chat_key not in private_messages:
        private_messages[chat_key] = []
    
    new_message = {
        "from_phone": from_phone,
        "from_name": user_profiles[from_phone]['name'],
        "to_phone": to_phone,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }
    
    private_messages[chat_key].append(new_message)
    if len(private_messages[chat_key]) > 200:
        private_messages[chat_key].pop(0)
    
    return jsonify({"status": "success"})

@app.route('/get_private_messages')
def get_private_messages():
    phone1 = request.args.get('phone1', '')
    phone2 = request.args.get('phone2', '')
    
    if not phone1 or not phone2:
        return jsonify([])
    
    chat_key = get_chat_key(phone1, phone2)
    return jsonify(private_messages.get(chat_key, []))

@app.route('/get_chats')
def get_chats():
    phone = request.args.get('phone', '')
    if not phone:
        return jsonify([])
    
    chats = []
    for key in private_messages.keys():
        phones = key.split(':')
        if phone in phones:
            other_phone = phones[0] if phones[1] == phone else phones[1]
            if other_phone in user_profiles:
                last_msg = private_messages[key][-1] if private_messages[key] else None
                last_seen = online_users.get(other_phone)
                is_online = False
                if last_seen:
                    diff = (datetime.datetime.now() - last_seen).total_seconds()
                    is_online = diff < 300
                
                chats.append({
                    "phone": other_phone,
                    "name": user_profiles[other_phone]['name'],
                    "last_message": (last_msg['text'][:30] + "...") if last_msg and len(last_msg['text']) > 30 else (last_msg['text'] if last_msg else ""),
                    "last_time": last_msg['time'] if last_msg else "",
                    "online": is_online
                })
    
    return jsonify(sorted(chats, key=lambda x: x['last_time'], reverse=True))

@app.route('/version.json')
def version():
    return jsonify({
        "version": 2,
        "version_name": "1.1",
        "download_url": "https://github.com/akhmadullinaizat06-lab/my-chat-server/releases/download/v1.1/onlinechat.apk"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
