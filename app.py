from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os

app = Flask(__name__)
CORS(app)

# Общие сообщения (как раньше)
public_messages = []

# Приватные сообщения: ключ - "user1:user2" (отсортированные имена)
private_messages = {}

# Список всех пользователей, которые когда-либо заходили
all_users = set()

# Кто сейчас онлайн (упрощённо - кто отправлял сообщения в последние 5 минут)
online_users = {}

def get_chat_key(user1, user2):
    """Создаёт уникальный ключ для чата двух пользователей."""
    return ":".join(sorted([user1, user2]))

@app.route('/get_public_messages')
def get_public_messages():
    return jsonify(public_messages)

@app.route('/send_public_message', methods=['POST'])
def send_public_message():
    data = request.get_json()
    username = data.get('username', 'Аноним')
    text = data.get('text', '')

    if not text:
        return jsonify({"status": "error"}), 400

    # Обновляем онлайн-статус
    online_users[username] = datetime.datetime.now()
    all_users.add(username)

    new_message = {
        "username": username,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": "public"
    }

    public_messages.append(new_message)
    if len(public_messages) > 50:
        public_messages.pop(0)

    return jsonify({"status": "success"})

@app.route('/get_users')
def get_users():
    """Возвращает список всех пользователей с онлайн-статусом."""
    users_list = []
    now = datetime.datetime.now()
    
    for user in all_users:
        last_seen = online_users.get(user)
        is_online = False
        if last_seen:
            diff = (now - last_seen).total_seconds()
            is_online = diff < 300  # Онлайн если активен в последние 5 минут
        
        users_list.append({
            "username": user,
            "online": is_online
        })
    
    return jsonify(sorted(users_list, key=lambda x: (not x['online'], x['username'])))

@app.route('/send_private_message', methods=['POST'])
def send_private_message():
    data = request.get_json()
    from_user = data.get('from', '')
    to_user = data.get('to', '')
    text = data.get('text', '')

    if not text or not from_user or not to_user:
        return jsonify({"status": "error"}), 400

    # Обновляем онлайн-статус
    online_users[from_user] = datetime.datetime.now()
    all_users.add(from_user)
    all_users.add(to_user)

    chat_key = get_chat_key(from_user, to_user)
    
    if chat_key not in private_messages:
        private_messages[chat_key] = []
    
    new_message = {
        "from": from_user,
        "to": to_user,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": "private"
    }
    
    private_messages[chat_key].append(new_message)
    if len(private_messages[chat_key]) > 100:
        private_messages[chat_key].pop(0)

    return jsonify({"status": "success"})

@app.route('/get_private_messages')
def get_private_messages():
    user1 = request.args.get('user1', '')
    user2 = request.args.get('user2', '')
    
    if not user1 or not user2:
        return jsonify([])
    
    chat_key = get_chat_key(user1, user2)
    return jsonify(private_messages.get(chat_key, []))

@app.route('/get_chats')
def get_chats():
    """Возвращает список чатов для пользователя."""
    username = request.args.get('username', '')
    if not username:
        return jsonify([])
    
    chats = []
    for key in private_messages.keys():
        users = key.split(':')
        if username in users:
            other_user = users[0] if users[1] == username else users[1]
            last_msg = private_messages[key][-1] if private_messages[key] else None
            chats.append({
                "with": other_user,
                "last_message": last_msg['text'][:30] + "..." if last_msg and len(last_msg['text']) > 30 else (last_msg['text'] if last_msg else ""),
                "last_time": last_msg['time'] if last_msg else "",
                "online": other_user in online_users and (datetime.datetime.now() - online_users[other_user]).total_seconds() < 300
            })
    
    return jsonify(sorted(chats, key=lambda x: x['last_time'], reverse=True))

@app.route('/ping')
def ping():
    """Обновляет онлайн-статус пользователя."""
    username = request.args.get('username', '')
    if username:
        online_users[username] = datetime.datetime.now()
        all_users.add(username)
    return jsonify({"status": "ok"})
@app.route('/version.json')
def version():
    """Возвращает информацию о последней версии приложения."""
    return jsonify({
        "version": 2,                    # Увеличивайте при каждом обновлении
        "version_name": "1.1",           # Версия для отображения
        "download_url": "https://github.com/akhmadullinaizat06-lab/my-chat-server/releases/download/v1.1/onlinechat.apk"
    })
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
