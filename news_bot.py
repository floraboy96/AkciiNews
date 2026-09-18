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
    except Exception:
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
    except Exception:
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
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
