# RiskPortfolioProject

RiskPortfolioProject is a full-stack portfolio optimization app with:

- Backend: Flask API (`Backend/`)
- Frontend: React dashboard (`frontend/portfolio-ui/`)

It helps users pick stocks, optimize allocations by risk appetite, and view portfolio risk/signal insights with simplified language.

## Features

- User authentication (signup/login/profile) with JWT
- Portfolio optimization with 3 distinct risk modes:
- `low`: minimize portfolio volatility
- `medium`: maximize Sharpe ratio
- `high`: maximize expected return
- Allocation outputs:
- Stock allocation
- Sector allocation
- Risk contribution by asset
- Risk metrics:
- Volatility
- Sharpe ratio
- VaR (95%)
- CVaR (95%)
- Diversification score
- Stock-level and portfolio-level BUY/HOLD/SELL signals
- Robust market-data handling:
- Failed Yahoo tickers are removed automatically
- Optimization continues with valid tickers
- Returns `removed_stocks` + `warning` in API response

## Project Structure

- `Backend/app.py`: main Flask app and API routes
- `Backend/routes/auth_routes.py`: auth endpoints
- `Backend/optimization/portfolio_optimizer.py`: optimization logic
- `Backend/risk/`: risk metric calculations
- `Backend/signals/`: signal generation
- `Backend/data/fetch_data.py`: Yahoo Finance data fetch + failed-ticker filtering
- `frontend/portfolio-ui/src/pages/Dashboard.js`: main dashboard UI

## Prerequisites

- Python 3.10+ (recommended 3.11)
- Node.js 18+ and npm
- PostgreSQL running locally

## Backend Setup

From project root:

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install flask flask-cors flask-jwt-extended flask-sqlalchemy numpy pandas scipy yfinance psycopg2-binary
```

Update database/JWT config in:

- `Backend/config.py`

Default config currently points to:

- `postgresql://postgres:1004@localhost:5432/risk_portfolio_db`

Run backend:

```powershell
cd Backend
python app.py
```

Backend runs on:

- `http://localhost:5000`

### Generate a dummy training dataset

```powershell
python Backend/optimization/generate_dummy_dataset.py --output Backend/data/dummy_training.csv
```

Then train the ensemble using the generated CSV:

```powershell
python Backend/optimization/train_ensemble.py --dataset Backend/data/dummy_training.csv --target target
```

## Frontend Setup

```powershell
cd frontend/portfolio-ui
npm install
npm start
```

Frontend runs on:

- `http://localhost:3000`

## Main API Endpoints

- `GET /` health check
- `GET /stocks` list supported stocks
- `POST /optimize` optimize portfolio
- `POST /signup` create user
- `POST /login` login user
- `GET /profile` protected profile route (JWT)

### `POST /optimize` request

```json
{
  "stocks": ["INFY", "TCS", "RELIANCE", "TATAMOTORS"],
  "investment": 100000,
  "risk": "medium"
}
```

### `POST /ensemble/predict` request

```json
{
  "features": [0.1, -0.2, 0.5, 1.0, -0.3]
}
```

### `POST /ensemble/predict` response

```json
{
  "predictions": [1.2345],
  "model": "simple_ensemble"
}
```

## Frontend ML Dashboard

The dashboard now includes an ML test panel that lets you:
- enter a feature vector directly
- run the saved ensemble model
- see the live prediction in the UI
- use sample values with one click

Make sure the backend is running on `http://localhost:5000` and the frontend on `http://localhost:3000`.

### Run the frontend

```powershell
cd frontend/portfolio-ui
npm install
npm start
```

### Run the backend

```powershell
cd Backend
python app.py
```

### Test the ML panel

1. Open the dashboard in your browser.
2. Find the `Quick Model Test` panel.
3. Click `Sample values`.
4. Click `Predict`.
5. Review the returned prediction in the panel.

### `POST /optimize` response (example)

```json
{
  "portfolio_metrics": {},
  "allocation": [],
  "sector_allocation": [],
  "performance_curve": [],
  "risk_contribution": [],
  "signals": [],
  "portfolio_signal": "HOLD",
  "portfolio_signal_reason": "Signals are mixed, so waiting is prudent.",
  "removed_stocks": ["TATAMOTORS"],
  "warning": "Some stocks were removed because market data was unavailable."
}
```

If fewer than 2 valid stocks remain:

```json
{
  "error": "Not enough valid stocks to build a portfolio."
}
```

## Notes

- The dashboard intentionally uses plain-language labels/tooltips to improve usability for non-finance users.
- Efficient Frontier visualization has been removed from the current UX by design.
