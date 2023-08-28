import json
import os
import sqlite3
import time
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

from datetime import datetime, timezone


import requests


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00);")
db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, timestamp TEXT, PRIMARY KEY(id), FOREIGN KEY(user_id) REFERENCES users(id));")
db.execute("CREATE INDEX IF NOT EXISTS orders_by_user_id_index ON orders (user_id);")
print("Tables initialized.")
# Create new table, and index (for efficient search later on) to keep track of stock orders, by each user
db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, timestamp TEXT, PRIMARY KEY(id),  FOREIGN KEY(user_id) REFERENCES users(id))")
db.execute("CREATE INDEX IF NOT EXISTS orders_by_user_id_index ON orders (user_id)")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    # Retrieve portfolio data from the database for stocks with positive shares
    orders_db = db.execute("SELECT symbol, SUM(shares) as shares, price FROM orders WHERE user_id = ? GROUP BY symbol HAVING sum(shares) > 0", user_id)
    
    # Calculate total portfolio value
    cash = db.execute("SELECT cash FROM users WHERE id = ? ", user_id)[0]['cash']
    total = cash
    
    # Prepare data for multiple stocks' charts
    chart_data = {}
    for row in orders_db:
        symbol = row["symbol"]
        chart_data[symbol] = url_for("chart_data", symbol=symbol)  # Generate the correct URL
        # Update the total portfolio value by adding the value of each stock
        total += row["shares"] * row["price"]
    
    print ("Chart data:", chart_data)
    print ("Orders:", orders_db)
    

    '''chart_scripts = []
    for symbol, url in chart_data.items():
        chart_scripts.append(
            f"""
            fetch("{url}")
                .then(response => response.json())
                .then(chartData => {{
                    console.log("Fetched chartData:", chartData);
                    destroyChart("{symbol}");
                    createChart("{symbol}", chartData);
                }})
                .catch(error => console.error("Error fetching chart data:", error));
            """
        )
    print ("Chart scripts:", chart_scripts)
    chart_script = "\n".join(chart_scripts)'''
    
    return render_template("index.html", database=orders_db, cash=usd(cash), total=usd(total), chart_data=chart_data, )

@app.route("/chart_data/<symbol>")
@login_required
def chart_data(symbol):
    """Retrieve historical price data for a stock"""
    api_key = 'cji82upr01qonds7l9hgcji82upr01qonds7l9i0'  # Replace with your Finnhub API key
    
    try:
#        Calculate the timestamps for the past day
        now = int(time.time())
        past_day = now - 24 * 60 * 60  # 24 hours in seconds
        url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=1&from={past_day}&to={now}&token={api_key}"
        response = requests.get(url)
        data = response.json()
        
        timestamps = data['t']
        prices = data['c']
        
        chart_data = [{"timestamp": timestamp, "price": price} for timestamp, price in zip(timestamps, prices)]
        return jsonify(chart_data)
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return jsonify([])  # Return an empty list if there's an error



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    orders = db.execute("SELECT * FROM orders WHERE user_id = ?", user_id)
    return render_template("history.html", orders = orders)


    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        print("Rows fetched from the users table:", rows)

        password_input = request.form.get("password")
        if password_input is None or password_input == "":
            return apology("Must provide a password", 403)
        
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password_input):

            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol=request.form.get("symbol")
        data=lookup(symbol)
        if not data:
            return apology("stock doesnt exist")
        us=usd(data["price"])
        name=data["name"]
        return render_template("quote.html",name=name,usd=us)
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure cnformation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password",400)

        # Ensure password was  same as conformation
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password does not match")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 0:
            return apology("username already taken", 400)
        password_input = request.form.get("password")
        if password_input is None or password_input == "":
            return apology("Must provide a password", 403)

        hash=generate_password_hash(password_input, method='pbkdf2', salt_length=16)

        db.execute("insert into users (username,hash) values(?,?)",request.form.get("username"),hash)
        # Redirect user to home page
        return redirect("/login",200)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    symbol=request.form.get("symbol")
    data=lookup(symbol)
    if not data:
        return apology("stock doesnt exist")
    shares_input = request.form.get("shares")
    if not shares_input:
        return apology("Please provide the number of shares", 400)
    try:
        shares = int(shares_input)
    except ValueError:
        return apology("Invalid number of shares. Please provide a valid number", 400)

    if shares<=0:
        return apology("cant but negative shares")
    price = data["price"]
    symbol = data["symbol"]
    user_id = session["user_id"]
    cash=db.execute("select cash from users where id=(?)",user_id)[0]["cash"]
    balence = cash - price * shares
    if balence < 0:
        return apology("Insufficient Cash. Failed Purchase.")

    db.execute("update users SET cash = ? WHERE id = ?", balence, user_id)


    db.execute("INSERT INTO orders (user_id, symbol, shares, price, timestamp) VALUES (?, ?, ?, ?, ?)",user_id, symbol, shares, price, ctime())


    return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    owns = {}

    # Populate the owns dictionary with stock details
    table = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares, price FROM orders WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        user_id
    )
    for row in table:
        symbol = row["symbol"]
        shares_owned = row["total_shares"]
        price = row["price"]

        owns[symbol] = {
            "shares": shares_owned,
            "price": price
        }

    if request.method == "GET":
        print(owns)
        return render_template("sell.html", owns=owns)

    symbol = request.form.get("symbol")
    shares_input = request.form.get("shares")
    if not shares_input:
        return apology("Please provide the number of shares", 400)
    try:
        shares_to_sell = int(shares_input)
    except ValueError:
        return apology("Invalid number of shares. Please provide a valid number", 400)

    if symbol not in owns:
        return apology("You don't own this stock.")

    if shares_to_sell <= 0:
        return apology("Invalid number of shares to sell.")

    stock_info = owns[symbol]
    shares_owned = stock_info["shares"]

    if shares_to_sell > shares_owned:
        return apology("Insufficient shares to sell.")

    data = lookup(symbol)
    price = 0
    if data is not None: 
        price = data["price"]

    # Update the number of shares owned
    new_shares_owned = shares_owned - shares_to_sell
    cash=db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    balence=cash+(shares_to_sell*price)


    db.execute("update users SET cash = ? WHERE id = ?", balence, user_id)
    # Insert the sell record into the orders table
    db.execute("INSERT INTO orders (user_id, symbol, shares, price, timestamp) VALUES (?, ?, ?, ?, ?)",
               user_id, symbol, -shares_to_sell, price, ctime())
    table=db.execute("select * from orders where user_id = ?",user_id)
    print(table)
    # Update the owns dictionary after successful sell
    owns[symbol]["shares"] = new_shares_owned

    return redirect("/")




def ctime():
    """HELPER: get current UTC date and time"""
    utc = datetime.now(timezone.utc)
    return str(utc.date()) + ' @time ' + utc.time().strftime("%H:%M:%S")