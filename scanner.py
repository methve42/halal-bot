import json
import yfinance as yf

WATCHLIST = ["285A.T", "KXIAY", "IONQ", "CAMT", "NVDA", "ASML", "ARM", "SMCI", "TSM"]

def scan_market():
    results = []
    for symbol in WATCHLIST:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            target = info.get("targetMeanPrice", 0)
            debt = info.get("totalDebt", 0)
            market_cap = info.get("marketCap", 1)
            
            if not price or not target:
                continue

            growth = ((target - price) / price) * 100
            debt_ratio = (debt / market_cap) * 100 if market_cap else 100

            if debt_ratio < 30.0 and growth >= 20.0:
                results.append({
                    "ticker": symbol,
                    "name": info.get("shortName", symbol),
                    "sector": info.get("sector", "Tech"),
                    "price": round(price, 2),
                    "target1Y": round(target, 2),
                    "growth1Y": f"+{round(growth, 1)}%",
                    "debtRatio": f"{round(debt_ratio, 1)}%",
                    "desc": f"Tages-Scan Update: Kurspotenzial +{round(growth, 1)}% bei geringer Verschuldung ({round(debt_ratio, 1)}%)."
                })
        except Exception as e:
            print(f"Fehler bei {symbol}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scan_market()
