import feedparser
import requests
import os
import yfinance as yf
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TICKERS = [
    "AAPL", "AMZN", "GOOGL", "META", "MSFT",
    "NFLX", "NVDA", "ORCL", "AVGO", "PFE",
    "MDT", "MCD", "TSLA", "MRNA", "CSCO",
    "NKE", "SONY", "IBKR"
]

translator = GoogleTranslator(source="en", target="uk")

def translate(text):
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"Translate error: {e}")
        return text

def calculate_rsi(ticker, period=14):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if data.empty or len(data) < period:
            return None

        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(float(rsi.iloc[-1]), 1)
    except Exception as e:
        print(f"RSI error for {ticker}: {e}")
        return None

def get_signal(rsi):
    if rsi is None:
        return "⚪ RSI: н/д"
    if rsi < 30:
        return f"🟢 RSI: {rsi} (перепродано — можлива зона уваги)"
    elif rsi > 70:
        return f"🔴 RSI: {rsi} (перекуплено — обережно)"
    else:
        return f"⚪ RSI: {rsi} (нейтрально)"

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
    for ticker in TICKERS:
        print(f"Processing {ticker}...")
        rsi = calculate_rsi(ticker)
        signal = get_signal(rsi)
        news = get_news_for_ticker(ticker)

        block = f"📌 {ticker}\n{signal}"
        if news:
            block += "\n" + "\n".join(news)
        blocks.append(block)

    if not blocks:
        send_to_telegram("Даних не знайдено.")
        return

    message = "📊 Аналітика та новини по акціях:\n\n" + "\n\n".join(blocks)
    print(f"Total message length: {len(message)}")

    for i in range(0, len(message), 4000):
        chunk = message[i:i+4000]
        send_to_telegram(chunk)

if __name__ == "__main__":
    main()
