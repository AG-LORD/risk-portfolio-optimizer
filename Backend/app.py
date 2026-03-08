from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

from data.fetch_data import fetch_data
from preprocessing.preprocess import calculate_returns
from risk.risk_metrics import calculate_risk
from optimization.portfolio_optimizer import optimize_portfolio

app = Flask(__name__)
CORS(app)


# ---------------------------------
# Health Check
# ---------------------------------

@app.route("/")
def home():
    return "Backend Running Successfully 🚀"


# ---------------------------------
# Stock List (for dropdown)
# ---------------------------------

@app.route("/stocks", methods=["GET"])
def get_stocks():

    stocks = [
        "RELIANCE",
        "TCS",
        "INFY",
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "ITC",
        "LT",
        "BAJFINANCE",
        "AXISBANK"
    ]

    return jsonify(stocks)


# ---------------------------------
# Portfolio Optimization
# ---------------------------------

@app.route("/optimize", methods=["POST"])
def optimize():

    try:

        data = request.json

        if not data or "stocks" not in data:
            return jsonify({"error": "Stocks list missing"}), 400

        stocks = data["stocks"]
        investment_amount = data.get("investment", 100000)
        try:
            investment_amount = float(investment_amount)
        except (TypeError, ValueError):
            return jsonify({"error": "Investment must be a valid number"}), 400

        if investment_amount <= 0:
            return jsonify({"error": "Investment must be greater than 0"}), 400

        if len(stocks) < 2:
            return jsonify({"error": "Enter at least 2 stocks"}), 400


        # Convert to Yahoo tickers without duplicating suffix.
        tickers = [
            s if s.upper().endswith(".NS") else f"{s}.NS"
            for s in stocks
        ]


        # Fetch data
        price_data = fetch_data(tickers)

        if price_data.empty:
            return jsonify({"error": "No market data found"}), 400


        # Calculate returns
        returns = calculate_returns(price_data)

        mean_returns, cov_matrix = calculate_risk(returns)


        # Optimize portfolio
        weights, portfolio_return, volatility, sharpe = optimize_portfolio(
            mean_returns,
            cov_matrix
        )


        # -----------------------------
        # Allocation for Pie Chart
        # -----------------------------

        allocation_chart = []

        for stock, weight in zip(stocks, weights):

            allocation_chart.append({
                "name": stock,
                "value": round(float(weight * 100), 2)
            })


        # -----------------------------
        # Fake portfolio performance curve
        # (based on cumulative returns)
        # -----------------------------

        portfolio_returns = returns.dot(weights)

        cumulative = (1 + portfolio_returns).cumprod()

        performance = []

        for date, value in cumulative.tail(30).items():

            performance.append({
                "date": str(date.date()),
                "portfolio": round(value * investment_amount, 2)
            })


        # -----------------------------
        # Metrics
        # -----------------------------

        metrics = {

            "portfolio_value": round(performance[-1]["portfolio"], 2),

            "returns": round(float(portfolio_return * 100), 2),

            "sharpe": round(float(sharpe), 2),

            "volatility": round(float(volatility * 100), 2)

        }


        return jsonify({

            "performance": performance,

            "allocation": allocation_chart,

            "metrics": metrics

        })


    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)
