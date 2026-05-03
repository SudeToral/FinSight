import yfinance as yf
ticker = yf.Ticker("AAPL")
print(ticker.news[:2])
