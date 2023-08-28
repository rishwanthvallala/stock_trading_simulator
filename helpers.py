import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid

from flask import redirect, render_template, session
from functools import wraps
  
# api imports
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from iexfinance.stocks import Stock
import requests

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    
    # Query API
    try:
        def get_symbol_info(symbol: str, api_key: str) -> str:
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={api_key}"
            response = requests.get(url)
            data = response.json()
            return data['name']

        def get_current_price(symbol: str, api_key: str) -> tuple[str, float]:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            response = requests.get(url)
            data = response.json()
            price = float(data['c'])
            name = get_symbol_info(symbol, api_key)
            return name, price

        # usage
        api_key = 'cji82upr01qonds7l9hgcji82upr01qonds7l9i0'  # replace with your Finnhub API key
        name, price = get_current_price(symbol, api_key) 
        return {
            "name": name,
            "price": price,
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None

def chart_data_lookup(symbol='AAPL'):
    # Retrieve the historical price data from the Alpha Vantage API
    api_key = 'XJPS2APPCEM1DLFL'
    ts = TimeSeries(key=api_key)
    data, _ = ts.get_daily(symbol=symbol, outputsize='full') # type: ignore

    # Extract the dates and closing prices from the data
    dates = []
    closing_prices = []
    for date, values in data.items(): # type: ignore
        dates.append(date)
        closing_prices.append(float(values['4. close']))

    return dates, closing_prices


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
