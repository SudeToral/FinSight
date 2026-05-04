import yfinance as yf
import datetime

def test_yf():
    symbol = "GOOGL"
    print(f"Testing {symbol}...")
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d", interval="1m")
    print(f"History (1d, 1m) rows: {len(hist)}")
    if not hist.empty:
        print(hist.tail(1))
    else:
        print("Empty history! Trying period='5d'...")
        hist = ticker.history(period="5d", interval="1m")
        print(f"History (5d, 1m) rows: {len(hist)}")
        if not hist.empty:
            print(hist.tail(1))

if __name__ == "__main__":
    test_yf()
