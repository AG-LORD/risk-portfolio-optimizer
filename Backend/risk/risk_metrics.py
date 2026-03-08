import numpy as np

def calculate_risk(returns):

    mean_returns = returns.mean()

    cov_matrix = returns.cov()

    return mean_returns, cov_matrix