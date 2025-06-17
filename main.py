import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MIN_AMOUNT = float(os.getenv("MIN_TRANSACTION_AMOUNT", 0.1))  # Default 0.1 SOL

LABELS_FILE = "wallet_labels.json"

# Load or initialize wallet labels
if os.path.exists(LABELS_FILE):
    with open(LABELS_FILE, "r") as f:
        wallet_labels = json.load(f)
else:
    wallet_labels = {}

def save_labels():
    with open(LABELS_FILE, "w") as f:
        json.dump(wallet_labels, f, indent=2)

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

def send_telegram_message(message, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.json

    try:
        for txn in data.get("transactions", []):
            amount = float(txn.get("amount", 0))
            if amount < MIN_AMOUNT:
                continue  # Filter small transactions

            signature = txn.get("signature", "")
            token_address = txn.get("tokenAddress", "")
            wallet = txn.get("wallet", "")

            token_info = get_token_info(token_address)
            label = wallet_labels.get(wallet, wallet[:4] + "..." + wallet[-4:])

            msg = f"🔔 *New Transaction*\n"
            msg += f"*Wallet:* `{label}`\n"
            msg += f"*Token:* {token_info['name']} ({token_info['symbol']})\n"
            msg += f"*Amount:* {amount} SOL\n"
            msg += f"*Price:* ${token_info['price']}\n"
            msg += f"*Market Cap:* ${token_info['market_cap']}\n"
            msg += f"[View on Solscan](https://solscan.io/tx/{signature})"

            send_telegram_message(msg)

    except Exception as e:
        print("Error processing webhook:", e)

    return "ok", 200

@app.route("/set_label", methods=["POST"])
def set_label():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text.startswith("/setlabel "):
        return "ignored", 200

    parts = text.strip().split(maxsplit=2)
    if len(parts) != 3:
        send_telegram_message("❌ Usage:\n/setlabel <wallet_address> <label>", chat_id)
        return "bad format", 200

    wallet, label = parts[1], parts[2]
    wallet_labels[wallet] = label
    save_labels()
    send_telegram_message(f"✅ Label set for `{wallet}` as *{label}*", chat_id)
    return "ok", 200

@app.route("/removelabel", methods=["POST"])
def remove_label():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text.startswith("/removelabel "):
        return "ignored", 200

    parts = text.strip().split()
    if len(parts) != 2:
        send_telegram_message("❌ Usage:\n/removelabel <wallet_address>", chat_id)
        return "bad format", 200

    wallet = parts[1]
    if wallet in wallet_labels:
        del wallet_labels[wallet]
        save_labels()
        send_telegram_message(f"🗑️ Removed label for `{wallet}`", chat_id)
    else:
        send_telegram_message(f"⚠️ No label found for `{wallet}`", chat_id)
    return "ok", 200

@app.route("/listlabels", methods=["POST"])
def list_labels():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text.strip() != "/listlabels":
        return "ignored", 200

    if not wallet_labels:
        send_telegram_message("📭 No wallet labels set.", chat_id)
        return "ok", 200

    label_msg = "*📋 Wallet Labels:*\n"
    for wallet, label in wallet_labels.items():
        label_msg += f"`{wallet}` → *{label}*\n"

    send_telegram_message(label_msg, chat_id)
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
