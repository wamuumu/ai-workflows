"""
Finance Tools Module
====================

This module provides finance-related tools for currency conversion
and stock price retrieval using the Yahoo Finance API.

Main Responsibilities:
    - Convert between currencies using live exchange rates
    - Retrieve current stock prices for given symbols

Key Dependencies:
    - yfinance: Yahoo Finance API wrapper
    - tools.decorator: For @tool registration

External APIs:
    - Yahoo Finance: Stock and currency data
"""

import yfinance as yf

from typing import TypedDict
from tools.decorator import tool


class CurrencyConversionOutput(TypedDict):
    """
    Structured output for currency conversion.
    
    Attributes:
        result: The converted amount in target currency.
        rate: The exchange rate used for conversion.
    """
    result: float
    rate: float


class StockPriceOutput(TypedDict):
    """
    Structured output for stock price lookup.
    
    Attributes:
        symbol: The stock ticker symbol queried.
        price: The current market price.
    """
    symbol: str
    price: float


@tool(
    name="convert_currency",
    description="Convert an amount from one currency to another.",
    category="finance"
)
def convert_currency(amount: float, from_currency: str, to_currency: str) -> CurrencyConversionOutput:
    """
    Convert an amount between currencies using live exchange rates.
    
    Fetches the current exchange rate from Yahoo Finance and applies
    it to the given amount.
    
    Args:
        amount: The amount to convert.
        from_currency: Source currency code (e.g., "USD", "EUR").
        to_currency: Target currency code (e.g., "GBP", "JPY").
        
    Returns:
        CurrencyConversionOutput with converted amount and rate.
        Returns error dict if conversion fails.
    """
    try:
        # Same currency - no conversion needed
        if from_currency == to_currency:
            return {"result": amount, "rate": 1.0}
        
        # Construct Yahoo Finance currency pair symbol
        symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        
        if history.empty:
            return {"error": f"Could not retrieve exchange rate for {from_currency} to {to_currency}."}
        
        # Get latest closing rate and compute conversion
        rate = history['Close'].iloc[-1].item()
        converted_amount = amount * rate
        return CurrencyConversionOutput(result=converted_amount, rate=rate)
    except Exception as e:
        return {"error": str(e)}


@tool( 
    name="get_stock_price", 
    description="Get current stock price for a given stock symbol.", 
    category="finance"
)
def get_stock_price(symbol: str) -> StockPriceOutput:
    """
    Retrieve current market price for a stock.
    
    Queries Yahoo Finance for the regular market price of
    the specified stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL").
        
    Returns:
        StockPriceOutput with symbol and current price.
        Returns error dict if lookup fails.
    """
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get("regularMarketPrice")
        return StockPriceOutput(symbol=symbol, price=price)
    except Exception as e:
        return {"error": str(e)}