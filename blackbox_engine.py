import os
import time
import threading
import requests
from flask import Flask
import numpy as np

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1529405521788928051/NoeuuGexSsHyGHkB_Fd_zPYvXBgm0bQgV1plNiHNhi3W8M_11jPwBymXuq_p7o58X0Ye")
MASSIVE_API_KEY = os.environ.get("MASSIVE_API_KEY", "VpkvAEuj1LeOnZp551NHuiLz45eyMsJi")

def send_discord_alert(message):
    if DISCORD_WEBHOOK_URL:
        payload = {"content": message}
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"Discord Error: {e}")

price_history = []

def adaptive_technical_bot_with_massive():
    print("🚀 [SUCCESS] Bot thread is running and connecting to Massive API...")
    last_signal = None
    
    base_rsi_low = 30
    base_rsi_high = 70
    
    while True:
        try:
            ticker = "C:XAUUSD"
            url = f"https://api.massive.com/v2/snapshot/locale/global/markets/forex/tickers/{ticker}?apiKey={MASSIVE_API_KEY}"
            
            response = requests.get(url, timeout=5)
            data = response.json()
            
            current_price = float(data.get("ticker", {}).get("lastQuote", {}).get("p", 0))
            if current_price == 0:
                current_price = float(data.get("ticker", {}).get("day", {}).get("c", 0))
            
            if current_price > 0:
                price_history.append(current_price)
                if len(price_history) > 50:
                    price_history.pop(0)
                print(f"📈 Fetched XAUUSD Price: {current_price}") # ปริ้นท์ราคาปัจจุบันโชว์ใน Logs ให้เห็นจะๆ

            if len(price_history) >= 15:
                prices_arr = np.array(price_history)
                deltas = np.diff(prices_arr)
                
                volatility = np.std(deltas)
                if volatility == 0:
                    volatility = 1.0
                
                gain = np.where(deltas > 0, deltas, 0)
                loss = np.where(deltas < 0, -deltas, 0)
                avg_gain = np.mean(gain[-14:])
                avg_loss = np.mean(loss[-14:])
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                dynamic_offset = min(int(volatility * 10), 10)
                current_rsi_low = max(15, base_rsi_low - dynamic_offset)
                current_rsi_high = min(85, base_rsi_high + dynamic_offset)

                signal = "HOLD"
                if rsi < current_rsi_low:
                    signal = "BUY"
                elif rsi > current_rsi_high:
                    signal = "SELL"

                if signal != "HOLD" and signal != last_signal:
                    entry_price = current_price
                    risk_distance = max(volatility * 2, 3.0)
                    
                    if signal == "BUY":
                        tp_price = entry_price + (risk_distance * 2)
                        sl_price = entry_price - risk_distance
                    else:
                        tp_price = entry_price - (risk_distance * 2)
                        sl_price = entry_price + risk_distance

                    alert_msg = (
                        f"🎯 **Massive API Signal with TP/SL**\n"
                        f"Asset: {ticker}\n"
                        f"📊 **Action: {signal}**\n"
                        f"-----------------------------------\n"
                        f"📍 **Entry Price:** {entry_price:.2f}\n"
                        f"🟢 **Take Profit (TP):** {tp_price:.2f}\n"
                        f"🔴 **Stop Loss (SL):** {sl_price:.2f}\n"
                        f"-----------------------------------\n"
                        f"RSI: {rsi:.2f} | Volatility: {volatility:.2f}"
                    )
                    send_discord_alert(alert_msg)
                    last_signal = signal

        except Exception as e:
            print(f"⚠️ Error in Massive API loop: {e}")
        
        time.sleep(10)

@app.route("/")
def index():
    return "Massive API Adaptive Bot is running!"

print("🔌 Initializing Background Bot Thread...")
threading.Thread(target=adaptive_technical_bot_with_massive, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
