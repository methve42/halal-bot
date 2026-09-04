import json
import time
import requests
import io
import yfinance as yf
import pandas as pd

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 1. Wechselkurs EUR/USD abrufen
try:
    eur_usd = yf.Ticker("EURUSD=X")
    usd_to_eur_rate = eur_usd.info.get("regularMarketPrice") or eur_usd.info.get("previousClose") or 1.08
except Exception:
    usd_to_eur_rate = 1.08

print(f"Wechselkurs: 1 EUR = {usd_to_eur_rate} USD")

# 2. Haram-Ausschlüsse (Qualitatives Sharia-Screening)
FORBIDDEN_SECTORS = ["Financial Services", "Financial"]
FORBIDDEN_INDUSTRIES = [
    "Banks—Diversified", "Banks—Regional", "Insurance—Financial", "Insurance Brokers",
    "Insurance—Diversified", "Insurance—Life", "Insurance—Property & Casualty",
    "Credit Services", "Capital Markets", "Asset Management", "Mortgage Real Estate Investment Trusts",
    "Beverages—Brewers", "Beverages—Wineries & Distilleries", "Tobacco",
    "Gambling", "Casinos & Gambling", "Aerospace & Defense"
]

# 3. Aktienticker sammeln
tickers = set()

try:
    res = requests.get("https://en.wikipedia.org/wiki/Nasdaq-100", headers=HEADERS)
    tables = pd.read_html(io.StringIO(res.text))
    for table in tables:
        if 'Ticker' in table.columns:
            tickers.update([t.replace('.', '-') for t in table['Ticker'].tolist()])
        elif 'Symbol' in table.columns:
            tickers.update([t.replace('.', '-') for t in table['Symbol'].tolist()])
except Exception as e:
    print("NASDAQ-Abruf fehlgeschlagen:", e)

extra_tickers = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "AMD", "PLTR", "NET", "CRWD", 
    "COIN", "MSTR", "ARM", "SMCI", "SNOW", "DDOG", "ZS", "PANW", "SHOP", "SQ", 
    "MELI", "SE", "ASML.AS", "SAP.DE"
]
tickers.update(extra_tickers)

TICKERS_LIST = sorted(list(tickers))
print(f"Starte Analyse von {len(TICKERS_LIST)} Titeln (Fokus: Analysten-Kurspotenzial)...")

results = []

# MINDEST-KURSPOTENZIAL DER ANALYSTEN (0.15 = mindestens +15% erwarteter Anstieg)
MIN_UPSIDE_THRESHOLD = 0.15

for symbol in TICKERS_LIST:
    try:
        time.sleep(0.15)  # Schutz gegen Rate-Limiting
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or "shortName" not in info:
            continue

        # --- SHARIA-FILTER 1: BRANCHEN-PRÜFUNG ---
        sector = info.get("sector", "") or ""
        industry = info.get("industry", "") or ""

        if any(fs.lower() in sector.lower() for fs in FORBIDDEN_SECTORS):
            continue
            
        if any(fi.lower() in industry.lower() for fi in FORBIDDEN_INDUSTRIES):
            continue

        # --- SHARIA-FILTER 2: SCHULDENQUOTE (< 30%) ---
        market_cap = info.get("marketCap", 0)
        total_debt = info.get("totalDebt", 0)
        debt_ratio = (total_debt / market_cap) if market_cap > 0 else 1.0

        if debt_ratio >= 0.30:
            continue

        # --- REINES ANALYSTEN-KURSPOTENZIAL BERECHNEN ---
        raw_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        raw_target = info.get("targetMeanPrice", 0)

        # Nur Aktien auswerten, für die echte Zielpreise vorliegen
        if raw_price <= 0 or raw_target <= 0:
            continue

        # Kurspotenzial = (Zielpreis - Kurs) / Kurs
        upside = (raw_target - raw_price) / raw_price

        # Währung in Euro umrechnen
        currency = info.get("currency", "USD").upper()
        if currency == "USD":
            price_eur = raw_price / usd_to_eur_rate
            target_eur = raw_target / usd_to_eur_rate
        else:
            price_eur = raw_price
            target_eur = raw_target

        # Nur Werte aufnehmen, die das Mindest-Kurspotenzial erreichen
        if upside >= MIN_UPSIDE_THRESHOLD:
            results.append({
                "ticker": symbol,
                "name": info.get("shortName", symbol),
                "sector": sector,
                "price": round(price_eur, 2),
                "target": round(target_eur, 2),
                "growth": round(upside * 100, 1),  # Reines Analysten-Kurspotenzial in %
                "debt_ratio": round(debt_ratio * 100, 1),
                "currency": "€"
            })
    except Exception:
        continue

# Sortierung: Höchstes Kurspotenzial oben
results = sorted(results, key=lambda x: x["growth"], reverse=True)

# Speichern
with open("data.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Scan abgeschlossen! {len(results)} Sharia-konforme Aktien mit Kurspotenzial gespeichert.")
