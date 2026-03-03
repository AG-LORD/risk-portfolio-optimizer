
import numpy as np

def calculate_risk(returns):
    returns = returns.dropna()

    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    return mean_returns, cov_matrix