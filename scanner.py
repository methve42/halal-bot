import json
import yfinance as yf
import pandas as pd
import requests
import io

# Browser-Header setzen, damit Wikipedia den Zugriff erlaubt
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 1. Aktuellen Wechselkurs EUR/USD abrufen
try:
    eur_usd = yf.Ticker("EURUSD=X")
    usd_to_eur_rate = eur_usd.info.get("regularMarketPrice") or eur_usd.info.get("previousClose") or 1.08
except Exception:
    usd_to_eur_rate = 1.08

print(f"Aktueller Wechselkurs: 1 EUR = {usd_to_eur_rate} USD")

# 2. Haram-Branchen & Industrien (Qualitatives Sharia-Screening)
FORBIDDEN_SECTORS = ["Financial Services", "Financial"]
FORBIDDEN_INDUSTRIES = [
    "Banks—Diversified", "Banks—Regional", "Insurance—Financial", "Insurance Brokers",
    "Insurance—Diversified", "Insurance—Life", "Insurance—Property & Casualty",
    "Credit Services", "Capital Markets", "Asset Management", "Mortgage Real Estate Investment Trusts",
    "Beverages—Brewers", "Beverages—Wineries & Distilleries", "Tobacco",
    "Gambling", "Casinos & Gambling", "Aerospace & Defense"
]

# 3. Ticker-Listen über Wikipedia abrufen
tickers = set()

# S&P 500
try:
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=HEADERS)
    tables = pd.read_html(io.StringIO(res.text))
    tickers.update([t.replace('.', '-') for t in tables[0]['Symbol'].tolist()])
except Exception as e:
    print("S&P 500 Fehler:", e)

# NASDAQ 100
try:
    res = requests.get("https://en.wikipedia.org/wiki/Nasdaq-100", headers=HEADERS)
    tables = pd.read_html(io.StringIO(res.text))
    for table in tables:
        if 'Ticker' in table.columns:
            tickers.update([t.replace('.', '-') for t in table['Ticker'].tolist()])
        elif 'Symbol' in table.columns:
            tickers.update([t.replace('.', '-') for t in table['Symbol'].tolist()])
except Exception as e:
    print("NASDAQ Fehler:", e)

# DAX 40
try:
    res = requests.get("https://en.wikipedia.org/wiki/DAX", headers=HEADERS)
    tables = pd.read_html(io.StringIO(res.text))
    for table in tables:
        if 'Ticker' in table.columns:
            tickers.update([f"{t.strip()}.DE" for t in table['Ticker'].tolist()])
        elif 'Symbol' in table.columns:
            tickers.update([f"{t.strip()}.DE" for t in table['Symbol'].tolist()])
except Exception as e:
    print("DAX Fehler:", e)

# Fallback-Liste, falls Wikipedia fehlschlägt
if not tickers:
    tickers = {"AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "AMD", "PLTR", "NET", "CRWD", "SAP.DE", "ASML.AS"}

TICKERS_LIST = sorted(list(tickers))
print(f"{len(TICKERS_LIST)} Aktien geladen. Starte Analyse...")

results = []

for symbol in TICKERS_LIST:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

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

        # --- WACHSTUMS- & POTENZIAL-PRÜFUNG ---
        earnings_growth = info.get("earningsGrowth", 0) or 0
        revenue_growth = info.get("revenueGrowth", 0) or 0
        
        raw_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        raw_target = info.get("targetMeanPrice", 0)

        if raw_price <= 0:
            continue

        # Währung prüfen & in Euro umrechnen
        currency = info.get("currency", "USD").upper()
        
        if currency == "USD":
            price_eur = raw_price / usd_to_eur_rate
            target_eur = raw_target / usd_to_eur_rate if raw_target > 0 else 0
        elif currency == "EUR":
            price_eur = raw_price
            target_eur = raw_target
        else:
            price_eur = raw_price / usd_to_eur_rate
            target_eur = raw_target / usd_to_eur_rate if raw_target > 0 else 0

        # Kurspotenzial
        upside = 0
        if raw_price > 0 and raw_target > 0:
            upside = (raw_target - raw_price) / raw_price

        # Maximales Wachstum
        max_growth = max(earnings_growth, revenue_growth, upside)

        # FILTER: Nur Aktien mit MEHR ALS 100% Wachstum (> 1.0)
        if max_growth > 1.0:
            results.append({
                "ticker": symbol,
                "name": info.get("shortName", symbol),
                "sector": sector,
                "price": round(price_eur, 2),
                "target": round(target_eur, 2),
                "growth": round(max_growth * 100, 1),
                "debt_ratio": round(debt_ratio * 100, 1),
                "currency": "€"
            })
    except Exception:
        continue

# Speichern
with open("data.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Scan fertig! {len(results)} Halal-Aktien mit >100% Wachstum gefunden.")
