import numpy as np


def calculate_returns(price_data):
    returns = price_data.pct_change().dropna()
    return returns