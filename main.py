from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)

@app.post("/")
async def webhook_handler(request: Request):
    data = await request.json()
    print("✅ Webhook received:", data)

    # Send a message with basic TX info (you can customize this later)
    message = f"🔔 New TX:\n{data}"
    send_message(message)

    return {"status": "ok"}
