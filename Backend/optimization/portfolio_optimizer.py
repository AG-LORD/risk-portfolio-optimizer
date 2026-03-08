import numpy as np
from scipy.optimize import minimize

def optimize_portfolio(mean_returns, cov_matrix):

    num_assets = len(mean_returns)

    def portfolio_performance(weights):

        returns = np.sum(mean_returns * weights)

        volatility = np.sqrt(
            np.dot(weights.T,
            np.dot(cov_matrix, weights))
        )

        sharpe = returns / volatility

        return returns, volatility, sharpe


    def negative_sharpe(weights):

        return -portfolio_performance(weights)[2]


    constraints = ({
        "type": "eq",
        "fun": lambda x: np.sum(x) - 1
    })

    bounds = tuple((0,1) for _ in range(num_assets))

    initial_weights = num_assets * [1/num_assets]

    result = minimize(
        negative_sharpe,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )

    weights = result.x

    returns, volatility, sharpe = portfolio_performance(weights)

    return weights, returns, volatility, sharpe