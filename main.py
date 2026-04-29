import asyncio
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from telegram import Bot

# --- CONFIG ---
API_KEY = 'YOUR_FINNHUB_KEY'
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

WATCHLIST = ['OANDA:EUR_USD', 'OANDA:GBP_USD', 'OANDA:USD_JPY', 'OANDA:AUD_USD', 'OANDA:EUR_JPY']
bot = Bot(token=TELEGRAM_TOKEN)

def get_candle_patterns(df):
    """Detects Engulfing, Pin Bar, and Rejection candles."""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Calculate Body and Wicks
    body = abs(latest['close'] - latest['open'])
    upper_wick = latest['high'] - max(latest['open'], latest['close'])
    lower_wick = min(latest['open'], latest['close']) - latest['low']
    total_range = latest['high'] - latest['low']
    
    pattern = None
    
    # 1. PIN BAR / REJECTION (Long wick, small body)
    if total_range != 0:
        if lower_wick > (body * 2) and lower_wick > (total_range * 0.6):
            pattern = "BULLISH PIN BAR"
        elif upper_wick > (body * 2) and upper_wick > (total_range * 0.6):
            pattern = "BEARISH PIN BAR"
            
    # 2. ENGULFING
    if latest['close'] > latest['open'] and prev['close'] < prev['open']: # Bullish
        if latest['close'] > prev['open'] and latest['open'] < prev['close']:
            pattern = "BULLISH ENGULFING"
    elif latest['close'] < latest['open'] and prev['close'] > prev['open']: # Bearish
        if latest['close'] < prev['open'] and latest['open'] > prev['close']:
            pattern = "BEARISH ENGULFING"
            
    return pattern

async def scan_market():
    print("🚀 Pattern Scanner Active...")
    while True:
        for symbol in WATCHLIST:
            url = f'https://finnhub.io/api/v1/indicator?symbol={symbol}&resolution=5&cnt=50&token={API_KEY}'
            r = requests.get(url).json()
            if 'c' not in r: continue
            
            df = pd.DataFrame({'open': r['o'], 'high': r['h'], 'low': r['l'], 'close': r['c']})
            rsi = RSIIndicator(close=df['close']).rsi().iloc[-1]
            pattern = get_candle_patterns(df)
            
            # SIGNAL LOGIC
            signal = None
            conf = 70 # Base confidence
            
            if rsi < 35 and "BULLISH" in str(pattern):
                signal = "CALL (BUY)"
                conf += 25
            elif rsi > 65 and "BEARISH" in str(pattern):
                signal = "PUT (SELL)"
                conf += 25

            if signal:
                pair = symbol.split(':')[-1]
                msg = (
                    f"🎯 *STRONG REVERSAL SIGNAL*\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"💹 *Pair:* {pair}\n"
                    f"🔥 *Action:* {signal}\n"
                    f"🕯 *Pattern:* `{pattern}`\n"
                    f"📊 *RSI:* {rsi:.1f}\n"
                    f"💎 *Confidence:* `{conf}%` \n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"⚡ *Enter at start of next 5m candle*"
                )
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            
            await asyncio.sleep(1.5) # Avoid rate limits
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(scan_market())
