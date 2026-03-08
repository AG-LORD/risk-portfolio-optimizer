import pandas as pd

def calculate_returns(price_data):

    returns = price_data.pct_change()

    returns.dropna(inplace=True)

    return returns