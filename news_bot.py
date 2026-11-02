import json
import os
import requests
import yfinance as yf

# Twój dedykowany webhook do bota z wiadomościami
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1566882526964744242/9MbXouFSYz8PlymBh9sPyKoNlwweTwJ68F7b_uTa6WZlDqIU2slahEoMeyjBxeKhARvj"

# Skracamy na próbę listę do najpopularniejszych spółek, żeby poszło błyskawicznie
TICKERS = ["PKO.WA", "PKN.WA", "PZU.WA", "KGH.WA", "PGE.WA", "JSW.WA"]

POSITIVE_KEYWORDS = [
    "zysk",
    "wzrost",
    "rekord",
    "kontrakt",
    "dywidenda",
    "sukces",
    "rozwój",
    "przychód",
    "wygrana",
    "inwestycja",
]
NEGATIVE_KEYWORDS = [
    "strata",
    "spadek",
    "kara",
    "problem",
    "dług",
    "kryzys",
    "rezygnacja",
    "śledztwo",
    "ryzyko",
    "zamknięcie",
]


def analyze_news_sentiment(title):
  title_lower = title.lower()
  pos_score = sum(1 for word in POSITIVE_KEYWORDS if word in title_lower)
  neg_score = sum(1 for word in NEGATIVE_KEYWORDS if word in title_lower)

  if pos_score > neg_score:
    return (
        "🟢 SUGESTIA: KUPUJ / TRZYMAJ",
        "Wiadomość ma pozytywny wydźwięk dla spółki.",
    )
  elif neg_score > pos_score:
    return (
        "🔴 SUGESTIA: OSTRZEŻENIE / SPRZEDAJ",
        "Wiadomość wskazuje na potencjalne problemy.",
    )
  else:
    return ("⚪ INFORMACJA", "Neutralny komunikat rynkowy.")


def check_market_news():
  actionable_insights = []

  for symbol in TICKERS:
    print(f"Sprawdzam wiadomości dla: {symbol}...")
    try:
      # Pobieramy dane z zabezpieczeniem przed zawieszeniem
      ticker = yf.Ticker(symbol)
      news_list = ticker.news

      if not news_list:
        print(f"Brak wiadomości dla {symbol}")
        continue

      latest_news = news_list[0]
      title = latest_news.get("title", "")
      publisher = latest_news.get("publisher", "GPW")
      link = latest_news.get("link", "#")

      if not title:
        continue

      signal, reasoning = analyze_news_sentiment(title)

      actionable_insights.append({
          "ticker": symbol.replace(".WA", "").upper(),
          "title": title,
          "publisher": publisher,
          "link": link,
          "signal": signal,
          "reasoning": reasoning,
      })
      print(
          f"Udało się pobrać news dla {symbol}:"
          f" {title[:30]}..."
      )

    except Exception as e:
      print(f"Błąd przy spółce {symbol}: {e}")
      continue

  return actionable_insights


def send_discord_report(insights):
  if not insights:
    print("Brak wiadomości do wysłania na Discorda.")
    # Wyślij chociaż informację, że bot działa, żebyś widział, że skrypt dotarł do końca
    payload_empty = {
        "content": (
            "@everyone 🤖 Bot wiadomości uruchomił się, ale Yahoo Finance nie"
            " zwróciło w tej chwili żadnych nowych artykułów dla tych"
            " spółek."
        )
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload_empty)
    return

  fields = []
  for item in insights[:5]:
    fields.append({
        "name": f"{item['signal']} | {item['ticker']} ({item['publisher']})",
        "value": (
            f"**Tytuł:** [{item['title']}]({item['link']})\n**Wniosek:**"
            f" {item['reasoning']}"
        ),
        "inline": False,
    })

  payload = {
      "content": (
          "@everyone 🚨 **Nowe wiadomości i inteligentna analiza rynkowa ze"
          " spółek!**"
      ),
      "embeds": [{
          "title": "🔍 Automatyczna Analiza Wydarzeń Giełdowych",
          "description": (
              "Bot przeskanował podane firmy i przeanalizował ich najnowsze"
              " komunikaty:"
          ),
          "color": 3447003,
          "fields": fields,
          "footer": {"text": "SIGG AI News Analyzer | GitHub Actions"},
      }],
  }

  response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
  print(
      f"Wysłano raport na Discorda! Odpowiedź serwera: {response.status_code}"
  )


if __name__ == "__main__":
  print("Rozpoczynam bezpieczne pobieranie wiadomości...")
  insights = check_market_news()
  send_discord_report(insights)
