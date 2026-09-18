import feedparser
import requests
import os
import time
import yfinance as yf
from deep_translator import MyMemoryTranslator

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TICKERS = [
    "AAPL", "AMZN", "GOOGL", "META", "MSFT",
    "NFLX", "NVDA", "ORCL", "AVGO", "PFE",
    "MDT", "MCD", "TSLA", "MRNA", "CSCO",
    "NKE", "SONY", "IBKR"
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
    """VIX — 'індекс страху' всього ринку"""
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
        return f"📉 Індекс страху (VIX): {value} — {mood}"
    except Exception as e:
        print(f"VIX error: {e}")
        return "⚪ Індекс страху (VIX): н/д"

def calculate_rsi_and_volume(ticker, period=14):
    try:
        data = yf.Ticker(ticker).history(period="1mo", interval="1d")
        if data.empty or len(data) < period:
            return None, None

        close = data['Close']
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = round(float(rsi.iloc[-1]), 1)

        # Объём: сравниваем последний день со средним за 20 дней
        volume = data['Volume']
        avg_volume = volume.rolling(window=20).mean()
        last_volume = float(volume.iloc[-1])
        avg_volume_value = float(avg_volume.iloc[-1])

        if avg_volume_value > 0:
            volume_ratio = round(last_volume / avg_volume_value, 2)
        else:
            volume_ratio = None

        return rsi_value, volume_ratio
    except Exception as e:
        print(f"Data error for {ticker}: {e}")
        return None, None

def get_signal(rsi):
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

def main():
    blocks = []

    # Общий индекс страха — добавляем один раз в начало
    fear_block = get_market_fear()
    blocks.append(fear_block)

    for ticker in TICKERS:
        print(f"Processing {ticker}...")
        rsi, volume_ratio = calculate_rsi_and_volume(ticker)
        rsi_signal = get_signal(rsi)
        volume_signal = get_volume_signal(volume_ratio)
        news = get_news_for_ticker(ticker)

        block = f"📌 {ticker}\n{rsi_signal}\n{volume_signal}"
        if news:
            block += "\n" + "\n".join(news)
        blocks.append(block)

    message = "📊 Аналітика та новини по акціях:\n\n" + "\n\n".join(blocks)
    print(f"Total message length: {len(message)}")

    for i in range(0, len(message), 4000):
        chunk = message[i:i+4000]
        send_to_telegram(chunk)

if __name__ == "__main__":
    main()import feedparser
import requests
import os
import time
import yfinance as yf
from deep_translator import MyMemoryTranslator

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TICKERS = [
    "AAPL", "AMZN", "GOOGL", "META", "MSFT",
    "NFLX", "NVDA", "ORCL", "AVGO", "PFE",
    "MDT", "MCD", "TSLA", "MRNA", "CSCO",
    "NKE", "SONY", "IBKR"
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
    """VIX — 'індекс страху' всього ринку"""
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
        return f"📉 Індекс страху (VIX): {value} — {mood}"
    except Exception as e:
        print(f"VIX error: {e}")
        return "⚪ Індекс страху (VIX): н/д"

def calculate_rsi_and_volume(ticker, period=14):
    try:
        data = yf.Ticker(ticker).history(period="1mo", interval="1d")
        if data.empty or len(data) < period:
            return None, None

        close = data['Close']
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = round(float(rsi.iloc[-1]), 1)

        # Объём: сравниваем последний день со средним за 20 дней
        volume = data['Volume']
        avg_volume = volume.rolling(window=20).mean()
        last_volume = float(volume.iloc[-1])
        avg_volume_value = float(avg_volume.iloc[-1])

        if avg_volume_value > 0:
            volume_ratio = round(last_volume / avg_volume_value, 2)
        else:
            volume_ratio = None

        return rsi_value, volume_ratio
    except Exception as e:
        print(f"Data error for {ticker}: {e}")
        return None, None

def get_signal(rsi):
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

def main():
    blocks = []

    # Общий индекс страха — добавляем один раз в начало
    fear_block = get_market_fear()
    blocks.append(fear_block)

    for ticker in TICKERS:
        print(f"Processing {ticker}...")
        rsi, volume_ratio = calculate_rsi_and_volume(ticker)
        rsi_signal = get_signal(rsi)
        volume_signal = get_volume_signal(volume_ratio)
        news = get_news_for_ticker(ticker)

        block = f"📌 {ticker}\n{rsi_signal}\n{volume_signal}"
        if news:
            block += "\n" + "\n".join(news)
        blocks.append(block)

    message = "📊 Аналітика та новини по акціях:\n\n" + "\n\n".join(blocks)
    print(f"Total message length: {len(message)}")

    for i in range(0, len(message), 4000):
        chunk = message[i:i+4000]
        send_to_telegram(chunk)

if __name__ == "__main__":
    main()
