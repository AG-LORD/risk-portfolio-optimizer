import numpy as np
from scipy.optimize import minimize

def optimize_portfolio(mean_returns, cov_matrix, risk_free_rate=0.06/252):

    num_assets = len(mean_returns)

    def negative_sharpe(weights):
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )
        sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
        return -sharpe

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    initial_weights = num_assets * [1./num_assets]

    result = minimize(
        negative_sharpe,
        initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    weights = result.x
    portfolio_return = np.dot(weights, mean_returns)
    portfolio_volatility = np.sqrt(
        np.dot(weights.T, np.dot(cov_matrix, weights))
    )
    sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility

    return weights, portfolio_return, portfolio_volatility, sharpe