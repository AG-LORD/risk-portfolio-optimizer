import numpy as np                      # For numerical operations
from scipy.optimize import minimize    # For optimization (SLSQP algorithm)

TRADING_DAYS = 252                     # Number of trading days in a year
RISK_FREE_RATE_ANNUAL = 0.05           # Assumed risk-free rate (5%)
MAX_WEIGHT_PER_STOCK = 0.40            # Max allocation per stock (not used here directly)
DEFAULT_RISK_LEVEL = "medium"          # Default risk preference


def portfolio_return(weights, mean_returns):
    return np.sum(mean_returns * weights)  
    # Calculate expected portfolio return (weighted sum of returns)


def portfolio_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))  
    # Calculate portfolio risk (standard deviation using covariance matrix)


def negative_sharpe(weights, mean_returns, cov_matrix):
    ret = portfolio_return(weights, mean_returns)  
    # Get portfolio return

    vol = portfolio_volatility(weights, cov_matrix)  
    # Get portfolio volatility (risk)

    return -(ret / (vol + 1e-8))  
    # Return negative Sharpe ratio (because optimizer minimizes, not maximizes)


def portfolio_performance(
    weights,
    mean_returns,
    cov_matrix,
    risk_free_rate_annual=RISK_FREE_RATE_ANNUAL
):
    daily_return = portfolio_return(weights, mean_returns)  
    # Daily expected return

    daily_volatility = portfolio_volatility(weights, cov_matrix)  
    # Daily risk

    annual_return = daily_return * TRADING_DAYS  
    # Convert daily return to annual

    annual_volatility = daily_volatility * np.sqrt(TRADING_DAYS)  
    # Convert daily volatility to annual

    sharpe = (annual_return - risk_free_rate_annual) / (annual_volatility + 1e-12)  
    # Calculate Sharpe ratio

    return daily_return, daily_volatility, annual_return, annual_volatility, sharpe


def optimize_portfolio(
    mean_returns,
    cov_matrix,
    risk_level=DEFAULT_RISK_LEVEL,
    optimize_mode="max_sharpe",
    risk_free_rate_annual=RISK_FREE_RATE_ANNUAL
):

    num_assets = len(mean_returns)  
    # Number of stocks selected

    risk_key = (risk_level or DEFAULT_RISK_LEVEL).lower()  
    # Normalize risk level input

    constraints = [{
        "type": "eq",
        "fun": lambda x: np.sum(x) - 1
    }]
    # Constraint: sum of all weights must be 1 (100% investment)

    max_weight = max(
        1 / num_assets,
        min(MAX_WEIGHT_PER_STOCK, max(1 / num_assets + 0.10, 0.20))
    )
    bounds = tuple((0, max_weight) for _ in range(num_assets))  
    # Cap concentration while keeping the problem feasible for small baskets

    initial_weights = num_assets * [1/num_assets]  
    # Start with equal allocation across all stocks


    mode_key = (optimize_mode or "auto").lower()
    if mode_key == "auto":
        if risk_key == "low":
            mode_key = "min_variance"
        elif risk_key == "high":
            mode_key = "max_return"
        else:
            mode_key = "max_sharpe"


    # Define objective function based on explicit mode, with risk level as fallback
    if mode_key == "min_variance":
        objective = lambda w: portfolio_volatility(w, cov_matrix)  
        # Minimize risk

    elif mode_key == "max_return":
        objective = lambda w: -portfolio_return(w, mean_returns)  
        # Maximize expected return

    else:
        objective = lambda w: negative_sharpe(w, mean_returns, cov_matrix)  
        # Maximize risk-adjusted return


    result = minimize(
        objective,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )
    # Run optimization using SLSQP algorithm


    if not result.success:
        # If optimization fails, retry with same setup

        fallback_constraints = [constraints[0]]

        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=fallback_constraints
        )


    weights = np.asarray(result.x, dtype=float)
    weight_sum = float(np.sum(weights))

    if weight_sum <= 0:
        weights = np.asarray(initial_weights, dtype=float)
    else:
        weights = weights / weight_sum
    # Normalize weights so the final allocation stays fully invested

    print("Final Weights:", weights)
    print("Sum:", float(np.sum(weights)))


    # Calculate final performance metrics
    daily_return, daily_volatility, annual_return, annual_volatility, sharpe = portfolio_performance(
        weights,
        mean_returns,
        cov_matrix,
        risk_free_rate_annual=risk_free_rate_annual
    )


    return weights, daily_return, daily_volatility, annual_return, annual_volatility, sharpe  
    # Return optimized weights and performance metrics


def calculate_risk_contribution(weights, cov_matrix):
    weights = np.asarray(weights)  
    # Convert weights to NumPy array

    cov_matrix = np.asarray(cov_matrix)  
    # Convert covariance matrix to NumPy array

    portfolio_vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))  
    # Calculate total portfolio volatility

    if portfolio_vol <= 0:
        return np.zeros_like(weights, dtype=float)  
        # If no risk, return zero contribution

    marginal_risk = np.dot(cov_matrix, weights)  
    # Marginal contribution of each asset to total risk

    contribution = (weights * marginal_risk) / (portfolio_vol ** 2)  
    # Percentage contribution of each asset to total portfolio risk

    return contribution  
    # Return how much each stock contributes to overall portfolio risk
