from flask import Flask, request, jsonify
from flask_cors import CORS

from data.fetch_data import fetch_data
from preprocessing.preprocess import calculate_returns
from risk.risk_metrics import calculate_risk
from optimization.portfolio_optimizer import optimize_portfolio

app = Flask(__name__)
CORS(app)


# -------------------------------
# Health Check Route
# -------------------------------
@app.route("/")
def home():
    return "Backend Running Successfully 🚀"


# -------------------------------
# Portfolio Optimization Route
# -------------------------------
@app.route("/optimize", methods=["POST"])
def optimize():
    try:
        data = request.json

        # Validate input
        if not data or "stocks" not in data:
            return jsonify({"error": "Stocks list missing"}), 400

        stocks = data["stocks"]

        if not isinstance(stocks, list) or len(stocks) == 0:
            return jsonify({"error": "Stocks must be a non-empty list"}), 400

        # Fetch price data
        price_data = fetch_data(stocks)

        if price_data.empty:
            return jsonify({"error": "No data fetched for given stocks"}), 400

        # Calculate returns
        returns = calculate_returns(price_data)

        # Risk metrics
        mean_returns, cov_matrix = calculate_risk(returns)

        # 🔎 Debug prints (optional, safe here)
        print("Mean Returns:\n", mean_returns)
        print("Cov Matrix:\n", cov_matrix)

        # Optimization
        weights, portfolio_return, volatility, sharpe = optimize_portfolio(
            mean_returns, cov_matrix
        )

        # Allocation dictionary
        allocation = {
            stock: round(float(weight), 4)
            for stock, weight in zip(stocks, weights)
        }

        return jsonify({
            "allocation": allocation,
            "portfolio_return": round(float(portfolio_return), 6),
            "portfolio_volatility": round(float(volatility), 6),
            "sharpe_ratio": round(float(sharpe), 6)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# Run Server
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)