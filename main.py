import requests
from flask import Flask, request
import os

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_token_info(token_address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{token_address}"
        res = requests.get(url)
        data = res.json()

        if "pairs" in data and len(data["pairs"]) > 0:
            pair = data["pairs"][0]
            name = pair.get("baseToken", {}).get("name", "Unknown Token")
            symbol = pair.get("baseToken", {}).get("symbol", "")
            price = pair.get("priceUsd", "N/A")
            market_cap = pair.get("fdv", "N/A")

            return {
                "name": name,
                "symbol": symbol,
                "price": price,
                "market_cap": market_cap
            }
        else:
            return {"name": "Unknown", "symbol": "", "price": "N/A", "market_cap": "N/A"}
    except Exception as e:
        print("Error fetching token info:", e)
        return {"name": "Unknown", "symbol": "", "price": "N/A", "market_cap": "N/A"}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.json

    try:
        for txn in data.get("transactions", []):
            description = txn.get("description", "")
            signature = txn.get("signature", "")
            amount = txn.get("amount", "")
            token_address = txn.get("tokenAddress", "")

            token_info = get_token_info(token_address)

            msg = f"🔔 *New Transaction*\n"
            msg += f"*Token:* {token_info['name']} ({token_info['symbol']})\n"
            msg += f"*Price:* ${token_info['price']}\n"
            msg += f"*Market Cap:* ${token_info['market_cap']}\n"
            msg += f"*Amount:* {amount}\n"
            msg += f"[View on Solscan](https://solscan.io/tx/{signature})"

            send_telegram_message(msg)
    except Exception as e:
        print("Error processing webhook:", e)

    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True, port=3000)
