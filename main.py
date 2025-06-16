import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    message = f"💸 New transaction:{data}"
    send_message(message)
    return 'ok', 200

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, json=payload)

@app.route('/', methods=['GET'])
def home():
    return 'Bot is running!', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
