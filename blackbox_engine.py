from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import requests
import datetime
import os

app = Flask(__name__)

# ดึงค่าจาก Environment Variables ของ Railway
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1529405521788928051/NoeuuGexSsHyGHkB_Fd_zPYvXBgm0bQgV1plNiHNhi3W8M_11jPwBymXuq_p7o58X0Ye") # เพิ่มตัวแปรสำหรับ Discord

# จำลองฐานข้อมูลความจำของกล่องดำ (Self-Learning Memory & Weights)
BLACKBOX_STATE = {
    "total_signals": 0,
    "correct_signals": 0,
    "current_weight_technical": 0.5,
    "current_weight_news": 0.5,
    "last_signal": None
}

def send_telegram_alert(message):
    """ฟังก์ชันส่งแจ้งเตือนเข้า Telegram (ถ้าตั้งค่าไว้)"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_discord_alert(message):
    """ฟังก์ชันส่งแจ้งเตือนเข้า Discord ผ่าน Webhook"""
    if not DISCORD_WEBHOOK_URL:
        return
    # Discord ใช้โครงสร้าง JSON แบบ embeds หรือ content ปกติ
    payload = {
        "content": message
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Discord Error: {e}")

def fetch_economic_news_impact():
    """จำลองระบบดึงข่าวและวิเคราะห์ผลกระทบเรียลไทม์"""
    news_analysis = {
        "has_high_impact_news": True,
        "news_title": "US CPI Data Release",
        "bias": "BULLISH",
        "score": 0.85
    }
    return news_analysis

@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    ticker = data.get('ticker', 'XAUUSD')
    action = data.get('action', 'HOLD')
    price = data.get('price', 0.0)
    tech_score = float(data.get('score', 0.5))

    # 1. วิเคราะห์ข่าว
    news_data = fetch_economic_news_impact()

    # 2. ปรับน้ำหนักคำนวณ
    w_tech = BLACKBOX_STATE["current_weight_technical"]
    w_news = BLACKBOX_STATE["current_weight_news"]
    final_confidence = (tech_score * w_tech) + (news_data["score"] * w_news)

    decision_text = "HOLD (รอดูก่อน ข่าวกับกราฟยังขัดแย้งกัน)"
    if final_confidence >= 0.70:
        decision_text = f"**EXECUTE {action}** ที่ราคา {price}"

    # 3. บันทึกสถิติ
    BLACKBOX_STATE["total_signals"] += 1
    BLACKBOX_STATE["last_signal"] = {
        "time": str(datetime.datetime.now()),
        "action": action,
        "price": price,
        "confidence": final_confidence
    }

    # 4. ข้อความแจ้งเตือน (จัดรูปแบบให้สวยงามบน Discord)
    alert_message = (
        f"🤖 **AI BLACKBOX XAUUSD ENGINE**\n"
        f"-----------------------------------\n"
        f"📌 **การตัดสินใจ:** {decision_text}\n"
        f"📊 **ความมั่นใจระบบ:** {final_confidence * 100:.2f}%\n"
        f"📰 **วิเคราะห์ข่าว:** {news_data['news_title']} ({news_data['bias']})\n"
        f"⚙️ **น้ำหนัก (Tech/News):** {w_tech:.2f} / {w_news:.2f}\n"
        f"📈 **สถิติสะสม:** ส่งสัญญาณไปแล้ว {BLACKBOX_STATE['total_signals']} ครั้ง"
    )

    # ส่งเข้าทั้งสองช่องทาง (เลือกเปิด/ปิดได้ตามตั้งค่าใน Railway)
    send_telegram_alert(alert_message)
    send_discord_alert(alert_message)

    return jsonify({
        "status": "success", 
        "confidence": final_confidence,
        "weights": BLACKBOX_STATE
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)