import numpy as np              # Import NumPy for numerical calculations
import pandas as pd            # Import Pandas for data handling

TRADING_DAYS = 252             # Number of trading days in a year (used for annual calculations)

def calculate_risk(returns):
    # Function to calculate basic risk metrics from returns data

    mean_returns = returns.mean()  
    # Calculate average return for each asset

    cov_matrix = returns.cov()     
    # Calculate covariance matrix (measures how assets move together)

    return mean_returns, cov_matrix  
    # Return mean returns and covariance matrix


def calculate_tail_risk(portfolio_returns, confidence_level=0.95):
    # Function to calculate tail risk (VaR and CVaR)

    returns = pd.Series(portfolio_returns).dropna()  
    # Convert input to Pandas Series and remove missing values

    if returns.empty:
        return 0.0, 0.0  
        # If no data available, return zero risk

    percentile = (1 - confidence_level) * 100  
    # Calculate percentile level (e.g., 5% for 95% confidence)

    var_raw = float(np.percentile(returns.values, percentile))  
    # Compute Value at Risk (VaR) at given confidence level

    tail = returns[returns <= var_raw]  
    # Select worst-case returns (tail losses)

    cvar_raw = float(tail.mean()) if not tail.empty else var_raw  
    # Compute Conditional VaR (average of worst losses)

    var_loss = max(0.0, -var_raw)  
    # Convert VaR to positive loss value

    cvar_loss = max(0.0, -cvar_raw)  
    # Convert CVaR to positive loss value

    return var_loss, cvar_loss  
    # Return final VaR and CVaR values (risk measures)