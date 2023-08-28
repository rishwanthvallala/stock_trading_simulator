
# Stock Trading Simulator

Welcome to the Stock Trading Simulator app! This project is a basic stock trading web application that allows users to view stock prices, buy and sell stocks, and track their portfolio history.

## Features

- View stock prices: Users can see the current prices of various stocks.
- Buy and sell stocks: Users can buy and sell stocks using available funds.
- Portfolio history: Users can view their trading history, including the stocks they've bought and sold.
- Real-time charting: The app provides a basic chart displaying historical closing prices of a selected stock.

## Live Demo

Check out the live demo of the Stock Trading Simulator app [here](https://rishwanthvallala.pythonanywhere.com/login).

## Tech Stack

- **Backend Framework:** Flask (Python)
- **Database:** SQLite3
- **Frontend:** HTML, CSS, JavaScript
- **API:** Finnhub API for stock data

## Setup

1. Clone the repository:

   ```sh
   git clone https://github.com/your-username/stock-trading-simulator.git
   cd stock-trading-simulator
   ```

2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Set up your Finnhub API key:
   - Sign up for an API key at [Finnhub](https://finnhub.io/).
   - Create a `.env` file in the project directory.
   - Add your API key to the `.env` file:
     ```
     FINNHUB_API_KEY=your-api-key
     ```

4. Run the app:

   ```sh
   flask run
   ```

5. Access the app in your browser at [http://localhost:5000](http://localhost:5000).

## Deployment

The project can be deployed to platforms like PythonAnywhere, Heroku, etc. Make sure to follow their deployment guides and update your environment variables accordingly.

