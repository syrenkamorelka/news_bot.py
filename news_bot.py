import os
import re
import requests
import feedparser
from datetime import datetime, timezone

# Dedykowany webhook do bota z wiadomościami
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1566882526964744242/9MbXouFSYz8PlymBh9sPyKoNlwweTwJ68F7b_uTa6WZlDqIU2slahEoMeyjBxeKhARvj"

# Polskie źródło wiadomości finansowych (Strumień RSS)
RSS_FEED_URL = "https://strefainwestorow.pl/rss.xml"

POSITIVE_KEYWORDS = [
    "zysk", "wzrost", "rekord", "kontrakt", "dywidenda", 
    "sukces", "rozwój", "przychód", "wygrana", "inwestycja", "zwiększa", "umowa"
]
NEGATIVE_KEYWORDS = [
    "strata", "spadek", "kara", "problem", "dług", 
    "kryzys", "rezygnacja", "śledztwo", "ryzyko", "zamknięcie", "spada", "obniżka"
]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def analyze_news_sentiment(title, summary=""):
    text = f"{title} {summary}".lower()
    
    pos_score = sum(1 for word in POSITIVE_KEYWORDS if word in text)
    neg_score = sum(1 for word in NEGATIVE_KEYWORDS if word in text)
    
    if pos_score > neg_score:
        return "🟢 SUGESTIA: KUPUJ / TRZYMAJ", "Wiadomość zawiera pozytywne informacje rynkowe."
    elif neg_score > pos_score:
        return "🔴 SUGESTIA: OSTRZEŻENIE / SPRZEDAJ", "Wiadomość wskazuje na ryzyko lub spadki."
    else:
        return "⚪ INFORMACJA", "Neutralny komunikat / bieżące wydarzenia z giełdy."

def fetch_polish_market_news():
    print("Pobieram najświeższe polskie wiadomości giełdowe...")
    feed = feedparser.parse(RSS_FEED_URL)
    actionable_insights = []

    if not feed.entries:
        print("Nie udało się pobrać wiadomości z kanału RSS.")
        return []

    # Sortujemy wpisy po dacie publikacji (jeśli feed ją podaje), od najnowszych
    # feedparser zazwyczaj trzyma datę w 'published_parsed' lub 'updated_parsed'
    sorted_entries = sorted(
        feed.entries, 
        key=lambda x: x.get('published_parsed', x.get('updated_parsed', (2000, 1, 1, 0, 0, 0, 0, 0, 0))), 
        reverse=True
    )

    # Bierzemy 4 bezwzględnie najnowsze artykuły z góry listy
    for entry in sorted_entries[:4]:
        title = entry.get('title', 'Brak tytułu')
        link = entry.get('link', '#')
        summary_raw = entry.get('summary', '')
        summary = clean_html(summary_raw)[:150] + "..." if summary_raw else ""
        
        # Opcjonalnie wyciągamy datę do wyświetlenia
        published_date = entry.get('published', 'Dzisiaj')

        signal, reasoning = analyze_news_sentiment(title, summary)

        actionable_insights.append({
            "title": title,
            "link": link,
            "summary": summary,
            "date": published_date,
            "signal": signal,
            "reasoning": reasoning
        })

    return actionable_insights

def send_discord_report(insights):
    if not insights:
        print("Brak artykułów do wysłania.")
        return

    fields = []
    for item in insights:
        fields.append({
            "name": f"{item['signal']}",
            "value": f"📰 **[{item['title']}]({item['link']})**\n_Data: {item['date']}_\n_{item['summary']}_\n💡 **Wniosek:** {item['reasoning']}",
            "inline": False
        })

    payload = {
        "content": "@everyone 🚨 **Najświeższy Przegląd Polskiego Rynku i Wiadomości GPW!**",
        "embeds": [{
            "title": "🔍 Świeże Wiadomości Giełdowe (Sortowane od najnowszych)",
            "description": "Bot przeskanował najnowsze publikacje finansowe:",
            "color": 3447003,
            "fields": fields,
            "footer": {"text": "SIGG Polish News Analyzer | GitHub Actions"}
        }]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"Wysłano raport na Discorda! Odpowiedź serwera: {response.status_code}")

if __name__ == "__main__":
    insights = fetch_polish_market_news()
    send_discord_report(insights)

