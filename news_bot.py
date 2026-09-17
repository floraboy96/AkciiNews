import feedparser
import requests
import os

# Берём токен и chat_id из GitHub Secrets
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# RSS-лента с новостями по рынку акций США
RSS_URL = "https://feeds.marketwatch.com/marketwatch/topstories/"

def get_news(limit=5):
    feed = feedparser.parse(RSS_URL)
    news_items = []
    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        news_items.append(f"• {title}\n{link}")
    return news_items

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    response = requests.post(url, data=payload)
    return response.json()

def main():
    news_items = get_news()
    if not news_items:
        send_to_telegram("Свежих новостей не найдено.")
        return

    message = "📊 Новости рынка акций США:\n\n" + "\n\n".join(news_items)
    send_to_telegram(message)

if __name__ == "__main__":
    main()
