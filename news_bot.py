import json
import os
import requests
import yfinance as yf

# Twój dedykowany webhook do bota z wiadomościami
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1566882526964744242/9MbXouFSYz8PlymBh9sPyKoNlwweTwJ68F7b_uTa6WZlDqIU2slahEoMeyjBxeKhARvj"

# Skanujemy najważniejsze spółki z giełdy pod kątem wiadomości
TICKERS = [
    "PKO.WA",
    "PKN.WA",
    "PZU.WA",
    "KGH.WA",
    "PEO.WA",
    "ALE.WA",
    "CDR.WA",
    "LPP.WA",
    "DNP.WA",
    "ALR.WA",
    "PGE.WA",
    "JSW.WA",
    "XTB.WA",
]

# Słowa kluczowe do analizy wydźwięku wiadomości (sentymentu)
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
    return (
        "⚪ INFORMACJA",
        "Neutralny komunikat rynkowy.",
    )


def check_market_news():
  actionable_insights = []

  for symbol in TICKERS:
    try:
      ticker = yf.Ticker(symbol)
      news_list = ticker.news
      if not news_list:
        continue

      latest_news = news_list[0]
      title = latest_news.get("title", "")
      publisher = latest_news.get("publisher", "GPW")
      link = latest_news.get("link", "#")

      if not title:
        continue

      signal, reasoning = analyze_news_sentiment(title)

      # Zbieramy wiadomości (teraz bierzemy każdą, żeby na pewno coś wysłało)
      actionable_insights.append({
          "ticker": symbol.replace(".WA", "").upper(),
          "title": title,
          "publisher": publisher,
          "link": link,
          "signal": signal,
          "reasoning": reasoning,
      })
    except Exception as e:
      continue

  return actionable_insights


def send_discord_report(insights):
  if not insights:
    print("Brak wiadomości do wysłania.")
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

  requests.post(DISCORD_WEBHOOK_URL, json=payload)
  print("Wysłano raport z wiadomościami na Discorda!")


if __name__ == "__main__":
  print("Rozpoczynam analizę sentymentu wiadomości rynkowych...")
  insights = check_market_news()
  send_discord_report(insights)
