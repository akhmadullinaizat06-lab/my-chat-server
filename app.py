from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os

app = Flask(__name__)
CORS(app)

messages = []

@app.route("/get_messages")
def get_messages():
    return jsonify(messages)

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    username = data.get("username", "Аноним")
    text = data.get("text", "")
    if not text:
        return jsonify({"status": "error", "message": "Текст не может быть пустым"}), 400
    new_message = {
        "username": username,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }
    messages.append(new_message)
    if len(messages) > 50:
        messages.pop(0)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
