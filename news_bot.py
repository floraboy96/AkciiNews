import feedparser
import requests
import os
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Список тикеров, по которым нужны новости
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
    except Exception:
        return text

def get_news_for_ticker(ticker, limit=2):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        title_uk = translate(entry.title)
        link = entry.link
        items.append(f"🔹 {ticker}: {title_uk}\n{link}")
    return items

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    return requests.post(url, data=payload).json()

def main():
    all_items = []
    for ticker in TICKERS:
        all_items.extend(get_news_for_ticker(ticker))

    if not all_items:
        send_to_telegram("Свіжих новин по обраних тікерах не знайдено.")
        return

    # Telegram ограничивает сообщение 4096 символами — режем на части
    message = "📊 Новини по вашому списку акцій:\n\n" + "\n\n".join(all_items)
    for i in range(0, len(message), 4000):
        send_to_telegram(message[i:i+4000])

if __name__ == "__main__":
    main()
