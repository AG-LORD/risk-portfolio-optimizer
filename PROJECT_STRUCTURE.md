# RiskPortfolioProject - Project Structure and Current Build Status

## Project Structure

```text
RiskPortfolioProject/
|-- Backend/
|   |-- app.py
|   |-- data/
|   |   |-- fetch_data.py
|   |   `-- stock_sectors.py
|   |-- models/
|   |   |-- signal_generator.py
|   |   `-- train_model.py
|   |-- optimization/
|   |   `-- portfolio_optimizer.py
|   |-- preprocessing/
|   |   `-- preprocess.py
|   |-- risk/
|   |   `-- risk_metrics.py
|   `-- signals/
|       `-- trading_signals.py
|-- frontend/
|   `-- portfolio-ui/
|       |-- public/
|       |-- src/
|       |   |-- pages/
|       |   |   |-- Dashboard.js
|       |   |   `-- LoginPage.js
|       |   |-- styles/
|       |   |   |-- dashboard.css
|       |   |   |-- login.css
|       |   |   `-- portfolio.css
|       |   |-- App.js
|       |   `-- index.js
|       |-- package.json
|       `-- tailwind.config.js
|-- venv/
`-- .git/
```

## What We Have Built So Far

### Backend (Flask)
- `GET /` health route is implemented.
- `GET /stocks` returns a predefined NIFTY 50 stock list.
- `POST /optimize` is implemented end-to-end with:
  - Input validation (stocks, investment, risk level)
  - Yahoo Finance data fetch (2y daily)
  - Daily returns + covariance calculations
  - Portfolio optimization via SLSQP (Sharpe/max-sharpe or min-variance mode)
  - Dynamic market regime switch based on volatility
  - Risk metrics: expected return, volatility, Sharpe, VaR, CVaR, drawdown, beta
  - Allocation outputs: stock allocation + sector allocation + diversification score
  - Performance curve versus NIFTY benchmark (`^NSEI`)
  - Efficient frontier (random portfolios)
  - Risk contribution by asset
  - Correlation matrix
  - Technical signals (RSI + SMA20/SMA50) + portfolio-level BUY/HOLD/SELL signal

### Backend Modules
- `data/fetch_data.py`: fetches stock and benchmark data from Yahoo Finance.
- `preprocessing/preprocess.py`: computes percentage returns.
- `risk/risk_metrics.py`: mean/covariance and tail risk calculations.
- `optimization/portfolio_optimizer.py`: optimizer + efficient frontier + risk contribution.
- `signals/trading_signals.py`: indicator-based signal generation.
- `data/stock_sectors.py`: stock-to-sector mapping for NIFTY symbols.

### Frontend (React)
- Login screen UI implemented (`LoginPage.js`) with local form state and password show/hide.
- App-level auth toggle flow implemented (`App.js`) between Login and Dashboard.
- Dashboard UI implemented (`Dashboard.js`) with:
  - Stock selection from backend dropdown
  - Risk selection (low/medium/high)
  - Investment input
  - Optimize action calling backend
  - Metrics cards
  - Portfolio summary
  - Signal cards and indicator table
  - Performance line chart with time-range filters
  - Stock and sector allocation pie charts
  - Efficient frontier scatter chart
  - Risk contribution bar chart
  - Correlation matrix heat-style table

## Current Gaps / Next Build Areas
- `Backend/models/train_model.py` and `Backend/models/signal_generator.py` are present but currently empty.
- Login is UI-only (no real authentication backend yet).
- No root-level consolidated run/setup documentation yet.
- No automated backend test suite is visible yet.
