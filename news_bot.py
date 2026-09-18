import feedparser
import requests
import os
import time
import numpy as np
import yfinance as yf
from datetime import datetime
from deep_translator import MyMemoryTranslator

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TICKERS = [
    "AAPL", "AMZN", "GOOGL", "META", "MSFT",
    "NFLX", "NVDA", "ORCL", "AVGO", "PFE",
    "MDT", "MCD", "TSLA", "MRNA", "CSCO",
    "NKE", "SONY", "IBKR"
]

CRYPTO_TICKERS = [
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
    "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "GRAM-USD",
    "ZEC-USD", "BCH-USD", "ENA-USD", "NEAR-USD", "ARB-USD", "LTC-USD", "STRK-USD"
]

translator = MyMemoryTranslator(source="en-GB", target="uk-UA")

def translate(text):
    try:
        result = translator.translate(text)
        time.sleep(1.2)
        return result
    except Exception as e:
        print(f"Translate error: {e}")
        time.sleep(1.2)
        return text

def get_market_fear():
    """VIX — загальний 'індекс страху' фондового ринку"""
    try:
        vix = yf.Ticker("^VIX").history(period="5d", interval="1d")
        if vix.empty:
            return "⚪ Індекс страху (VIX): н/д"
        value = round(float(vix['Close'].iloc[-1]), 1)
        if value < 20:
            mood = "🟢 спокійний ринок"
        elif value < 30:
            mood = "🟡 підвищена нервозність"
        else:
            mood = "🔴 паніка / сильний страх"
        return f"📉 Індекс страху акцій (VIX): {value} — {mood}"
    except Exception as e:
        print(f"VIX error: {e}")
        return "⚪ Індекс страху (VIX): н/д"

def calculate_metrics(ticker, period=14):
    """Повертає RSI, співвідношення обсягу та історичну волатильність"""
    try:
        data = yf.Ticker(ticker).history(period="1mo", interval="1d")
        if data.empty or len(data) < period:
            return None, None, None

        close = data['Close']

        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = round(float(rsi.iloc[-1]), 1)

        volume = data['Volume']
        avg_volume = volume.rolling(window=20).mean()
        last_volume = float(volume.iloc[-1])
        avg_volume_value = float(avg_volume.iloc[-1])
        volume_ratio = round(last_volume / avg_volume_value, 2) if avg_volume_value > 0 else None

        daily_returns = close.pct_change().dropna()
        daily_std = daily_returns.std()
        annual_volatility = round(float(daily_std * np.sqrt(252) * 100), 1)

        return rsi_value, volume_ratio, annual_volatility
    except Exception as e:
        print(f"Data error for {ticker}: {e}")
        return None, None, None

def get_dividend_info(ticker):
    """Дивідендна дохідність та дата останньої виплати"""
    try:
        info = yf.Ticker(ticker).info

        yield_value = info.get("dividendYield")
        last_div_date_ts = info.get("lastDividendDate")

        if not yield_value:
            return "⚪ Дивіденди: не виплачуються"

        yield_pct = round(yield_value, 2) if yield_value < 1 else round(yield_value / 100, 2)
        if yield_pct > 50:
            yield_pct = round(yield_pct / 100, 2)

        result = f"💰 Дивіденди: {yield_pct}% річних"

        if last_div_date_ts:
            try:
                date_str = datetime.fromtimestamp(last_div_date_ts).strftime("%d.%m.%Y")
                result += f" (остання виплата: {date_str})"
            except Exception:
                pass

        return result
    except Exception as e:
        print(f"Dividend error for {ticker}: {e}")
        return "⚪ Дивіденди: н/д"

def get_rsi_signal(rsi):
    if rsi is None:
        return "⚪ RSI: н/д"
    if rsi < 30:
        return f"🟢 RSI: {rsi} (перепродано — можлива зона уваги)"
    elif rsi > 70:
        return f"🔴 RSI: {rsi} (перекуплено — обережно)"
    else:
        return f"⚪ RSI: {rsi} (нейтрально)"

def get_volume_signal(ratio):
    if ratio is None:
        return "⚪ Обсяг: н/д"
    if ratio >= 2:
        return f"🔥 Обсяг: x{ratio} від середнього (сплеск активності!)"
    elif ratio >= 1.3:
        return f"📈 Обсяг: x{ratio} від середнього (підвищений)"
    else:
        return f"⚪ Обсяг: x{ratio} від середнього (звичайний)"

def get_volatility_signal(vol):
    if vol is None:
        return "⚪ Волатильність: н/д"
    if vol < 20:
        return f"🟢 Волатильність: {vol}% (спокійно)"
    elif vol < 40:
        return f"🟡 Волатильність: {vol}% (підвищена нервозність)"
    else:
        return f"🔴 Волатильність: {vol}% (висока — ризиковано)"

def get_news_for_ticker(ticker, limit=2):
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            title_uk = translate(entry.title)
            link = entry.link
            items.append(f"{title_uk}\n{link}")
        return items
    except Exception as e:
        print(f"News error for {ticker}: {e}")
        return []

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    response = requests.post(url, data=payload)
    print(f"Telegram response: {response.status_code} {response.text}")
    return response.json()

def build_stock_block(ticker):
    print(f"Processing {ticker}...")
    rsi, volume_ratio, volatility = calculate_metrics(ticker)
    rsi_signal = get_rsi_signal(rsi)
    volume_signal = get_volume_signal(volume_ratio)
    volatility_signal = get_volatility_signal(volatility)
    dividend_signal = get_dividend_info(ticker)
    news = get_news_for_ticker(ticker)

    block = f"📌 {ticker}\n{rsi_signal}\n{volume_signal}\n{volatility_signal}\n{dividend_signal}"
    if news:
        block += "\n" + "\n".join(news)
    return block

def build_crypto_block(ticker):
    print(f"Processing {ticker}...")
    rsi, volume_ratio, volatility = calculate_metrics(ticker)
    rsi_signal = get_rsi_signal(rsi)
    volume_signal = get_volume_signal(volume_ratio)
    volatility_signal = get_volatility_signal(volatility)

    name = ticker.replace("-USD", "")
    block = f"🪙 {name}\n{rsi_signal}\n{volume_signal}\n{volatility_signal}"
    return block

def main():
    blocks = []

    fear_block = get_market_fear()
    blocks.append(fear_block)

    blocks.append("━━━━━━━━━━━━━━\n📈 АКЦІЇ США")
    for ticker in TICKERS:
        blocks.append(build_stock_block(ticker))

    blocks.append("━━━━━━━━━━━━━━\n🪙 КРИПТОВАЛЮТИ")
    for ticker in CRYPTO_TICKERS:
        blocks.append(build_crypto_block(ticker))

    message = "📊 Аналітика та новини:\n\n" + "\n\n".join(blocks)
    print(f"Total message length: {len(message)}")

    for i in range(0, len(message), 4000):
        chunk = message[i:i+4000]
        send_to_telegram(chunk)

if __name__ == "__main__":
    main()
