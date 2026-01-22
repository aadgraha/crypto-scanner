import sys
import ccxt
import pandas as pd
from datetime import datetime, UTC

if len(sys.argv) != 2:
    print("Usage: python main.py [timeframe]")
    print("Example: python main.py 4h")
    sys.exit(1)

timeframe = sys.argv[1]   # args => 15m, 4h, 1d, 1w

exchange = ccxt.binance({
    "enableRateLimit": True
})

markets = exchange.load_markets()
symbols = [
    s for s in markets
    if s.endswith("/USDT") and markets[s]["active"]
]

def scan_symbol(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=250
        )

        df = pd.DataFrame(
            ohlcv,
            columns=["ts","open","high","low","close","volume"]
        )

        if len(df) < 200:
            return None

        df["ema20"]  = df["close"].ewm(span=20).mean()
        df["ema50"]  = df["close"].ewm(span=50).mean()
        df["ema100"] = df["close"].ewm(span=100).mean()
        df["ema200"] = df["close"].ewm(span=200).mean()

        last = df.iloc[-1]

        if (
            last["close"] > last["ema20"] >
            last["ema50"] >
            last["ema100"] >
            last["ema200"]
        ):
            return {
                "symbol": symbol,
                "price": round(last["close"], 6),
                "ema20": round(last["ema20"], 6),
                "ema50": round(last["ema50"], 6),
                "ema100": round(last["ema100"], 6),
                "ema200": round(last["ema200"], 6),
            }
    except Exception as e:
        return None

results = []
start = datetime.now(UTC)
total = len(symbols)

for i, sym in enumerate(symbols):
    base = sym.split("/")
    msg = f"[{i}/{total}] Scanning {base[0]}/{base[1]}"
    print(msg.ljust(50), end="\r", flush=True)
    r = scan_symbol(sym)
    if r:
        results.append(r)

print("\n===================================")
print(f"EMA TREND SCANNER ({timeframe})")
print("Price > EMA20 > EMA50 > EMA100 > EMA200")
print("===================================\n")

for r in results:
    print(
        f"{r['symbol']:12} "
        f"P:{r['price']:>10} "
        f"E20:{r['ema20']:>10} "
        f"E50:{r['ema50']:>10} "
        f"E100:{r['ema100']:>10} "
        f"E200:{r['ema200']:>10}"
    )

print(f"\nFound: {len(results)} coins")
print(f"Time: {(datetime.now(UTC) - start).seconds}s")
