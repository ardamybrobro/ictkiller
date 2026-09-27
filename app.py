import os
import logging

from flask import Flask, request, jsonify
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tv-telegram-webhook")

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


@app.route("/webhook", methods=["POST"])
def tradingview_webhook():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables.")
        return jsonify({"status": "error", "message": "Server not configured"}), 500

    # TradingView can send JSON or plain text depending on the alert message format.
    # Try JSON first, fall back to raw text.
    payload = request.get_json(silent=True)
    if payload is not None:
        message_text = str(payload)
    else:
        message_text = request.data.decode("utf-8") if request.data else "(empty webhook body)"

    log.info("Received webhook: %s", message_text)

    telegram_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"📩 TradingView Alert:\n{message_text}",
    }

    try:
        response = requests.post(
            TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN),
            json=telegram_payload,
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error("Failed to forward message to Telegram: %s", e)
        return jsonify({"status": "error", "message": "Failed to reach Telegram"}), 502

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200


if __name__ == "__main__":
    # For local testing only. Use a production WSGI server (gunicorn, waitress, etc.)
    # for anything beyond local testing.
    app.run(host="0.0.0.0", port=5000)
