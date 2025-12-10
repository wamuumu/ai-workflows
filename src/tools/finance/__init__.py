import yfinance as yf

from tools.decorator import tool

@tool(
    name="convert_currency",
    description="Convert an amount from one currency to another.",
    category="finance"
)
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    try:
        if from_currency == to_currency:
            return {"result": amount, "rate": 1.0}
        symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if history.empty:
            return {"error": f"Could not retrieve exchange rate for {from_currency} to {to_currency}."}
        rate = history['Close'].iloc[-1].item()
        converted_amount = amount * rate
        return {"result": converted_amount, "rate": rate}
    except Exception as e:
        return {"error": str(e)}

@tool( 
    name="get_stock_price", 
    description="Get current stock price for a given stock symbol.", 
    category="finance"
)
def get_stock_price(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get("regularMarketPrice")
        return {"symbol": symbol, "price": price}
    except Exception as e:
        return {"error": str(e)}