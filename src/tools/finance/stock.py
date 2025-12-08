import yfinance as yf

from tools.decorator import tool

@tool(name="get_stock_price", description="Get current stock price for a given stock symbol.", category="finance")
def get_stock_price(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get("regularMarketPrice")
        return {"symbol": symbol, "price": price}
    except Exception as e:
        return {"error": str(e)}