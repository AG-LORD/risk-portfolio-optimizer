# Risk Portfolio Project - Complete Logic Flow

## 🎯 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. AUTHENTICATION          2. KYC VERIFICATION        3. MAIN APP      │
│     (LoginPage)             (KYCPage)                  (Dashboard)       │
│     ├─ Signup              ├─ 5-step verification     ├─ Home Screen    │
│     │  └─ JWT Token       │  └─ Token stored         │  └─ Guide       │
│     │  └─ kyc_status       └─ kyc_status: approved   └─ Universe       │
│     │     = "pending"                                 │  └─ Stock list  │
│     │                                                 │  └─ Signals     │
│     └─ Login                                          └─ Portfolio      │
│        └─ Blocked if kyc                                └─ Optimizer    │
│           ≠ "approved"                                  └─ Results      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📱 FRONTEND FLOW (React)

### **Navigation System** (`App.js`)

```
┌──────────────────────────────────────────────────────────────────┐
│                    App State Management                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  view = derived from localStorage:                             │
│  ├─ No token             → "login"  (LoginPage)                │
│  ├─ token + kyc ≠ approved → "kyc"   (KYCPage)                │
│  └─ token + kyc = approved → "dashboard" (Dashboard Suite)    │
│                                                                  │
│  portfolioStocks = []  (persists across screens)               │
│  dashboardScreen = "home" | "universe" | "optimizer"           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### **1️⃣ LoginPage Flow**

```
LoginPage renders:
│
├─ Signup Form
│  ├─ Input: name, email, password
│  ├─ POST /signup
│  │  └─ Backend creates User in DB
│  │  └─ Returns: JWT token, kyc_status="pending"
│  └─ handleSignup() → saves token to localStorage
│                    → sets view to "kyc"
│
└─ Login Form
   ├─ Input: email, password
   ├─ POST /login
   │  └─ Backend BLOCKS if kyc_status ≠ "approved"
   │  └─ Returns: JWT token
   └─ handleLogin() → saves kyc_status to localStorage
                    → sets view to "dashboard"
```

### **2️⃣ KYCPage Flow**

```
KYCPage renders 5-step wizard:
│
├─ Step 1: PAN card number
├─ Step 2: Aadhaar number
├─ Step 3: Selfie upload
├─ Step 4: Review details
└─ Step 5: Submit
   ├─ POST /kyc/submit (with JWT in header)
   │  └─ Backend updates User.kyc_status = "approved"
   └─ handleKYCComplete()
      ├─ Sets localStorage kyc_status = "approved"
      └─ Sets view to "dashboard"
```

### **3️⃣ Dashboard Suite Flow**

The dashboard has 3 sub-screens controlled by `dashboardScreen` state:

#### **Screen A: Home (PortfolioDashboard.js)**

```
PortfolioDashboard renders:
├─ Welcome message
├─ User guides / educational cards
├─ "Browse Stocks" button
│  └─ Triggers: setDashboardScreen("universe")
└─ "Build Portfolio" button (if user has stock ideas)
   └─ Triggers: setDashboardScreen("optimizer")
```

#### **Screen B: Universe (UniverseDashboard.js)**

```
UniverseDashboard renders:
│
├─ Fetch: GET /dashboard/stocks
│  └─ Backend returns: [{ticker, signal, confidence, color, sector}, ...]
│
├─ Display 50 stocks in grid/table:
│  ├─ Color-coded by signal:
│  │  ├─ GREEN  = BUY   (composite_score >= +0.7)
│  │  ├─ YELLOW = HOLD  (between +0.7 and -0.7)
│  │  └─ RED    = SELL  (composite_score <= -0.7)
│  │
│  └─ Click stock → opens StockDetailPanel modal
│     ├─ Fetch: GET /stocks/<ticker>/details
│     │  └─ Returns: candlestick data, indicators, SHAP breakdown
│     │
│     └─ Modal displays:
│        ├─ Candlestick chart (CandlestickChart.jsx)
│        ├─ Technical indicators (RSI, SMA20, SMA50)
│        ├─ ML prediction + confidence
│        ├─ "Add to Portfolio" button
│        │  └─ setPortfolioStocks([...stocks, new_stock])
│        └─ "Close" button
│
└─ "Back to Home" or "Build Portfolio" button
   └─ Triggers: setDashboardScreen("optimizer")
```

#### **Screen C: Portfolio Optimizer (Dashboard.js)**

```
Dashboard renders:
│
├─ Selected Stocks Display:
│  ├─ Shows: portfolioStocks array
│  ├─ Each stock:
│  │  ├─ Ticker name
│  │  ├─ Current price
│  │  ├─ Trading signal (BUY/HOLD/SELL)
│  │  └─ "Remove" button
│  │
│  └─ "Clear All" or "Add More Stocks" button
│
├─ Portfolio Configuration:
│  ├─ Investment Amount: $_____ (text input)
│  ├─ Risk Level: [LOW] [MEDIUM] [HIGH] (radio buttons)
│  │
│  └─ "OPTIMIZE" button
│     ├─ POST /optimize
│     │  ├─ Body: {
│     │  │    "stocks": ["INFY", "TCS", ...],
│     │  │    "investment": 100000,
│     │  │    "risk_level": "medium"
│     │  │  }
│     │  └─ Backend calculates:
│     │     1. Fetch 2-year OHLCV data for each stock
│     │     2. Calculate daily returns + covariance
│     │     3. Run Markowitz optimization (SLSQP)
│     │     4. Return: weights, metrics, charts data
│     │
│     └─ setDashboardScreen("results")
│
├─ Results Display (after optimization):
│  ├─ 📊 Metrics Cards:
│  │  ├─ Expected Annual Return
│  │  ├─ Portfolio Volatility (Risk)
│  │  ├─ Sharpe Ratio
│  │  ├─ Value at Risk (VaR, 95%)
│  │  ├─ Conditional Value at Risk (CVaR, 95%)
│  │  └─ Maximum Drawdown
│  │
│  ├─ 🎯 Allocation Results:
│  │  ├─ Stock Allocation (pie chart)
│  │  │  └─ Shows % weight per stock
│  │  │
│  │  ├─ Sector Allocation (pie chart)
│  │  │  └─ Aggregates stock weights by sector
│  │  │
│  │  └─ Risk Contribution by Asset (bar chart)
│  │     └─ Shows marginal risk contribution of each stock
│  │
│  ├─ 📈 Performance Visualization:
│  │  ├─ Portfolio vs Benchmark (line chart)
│  │  │  └─ Compares cumulative returns: optimized portfolio vs NIFTY 50
│  │  │
│  │  └─ Efficient Frontier (scatter plot)
│  │     └─ Random portfolios + optimal point highlighted
│  │
│  ├─ 🔗 Correlation Matrix (heat map)
│  │  └─ Shows correlation between selected stocks
│  │
│  └─ Buttons:
│     ├─ "Adjust & Re-optimize" → back to config
│     ├─ "Back to Universe" → setDashboardScreen("universe")
│     └─ "Logout" → handleLogout()
│
└─ Logout button
```

---

## 🔌 BACKEND FLOW (Flask)

### **App.py - Entry Point**

```
Flask App Initialization:
│
├─ Load Config (database URL, JWT secret)
├─ Initialize SQLAlchemy Database
├─ Initialize JWT Manager
├─ Enable CORS (allow React to call)
│
├─ Register Blueprints:
│ ├─ auth_bp        → /signup, /login, /kyc/submit, /kyc/status, /profile
│ ├─ dashboard_bp   → /dashboard/stocks, /dashboard/refresh
│ └─ stock_detail_bp → /stocks/<ticker>/details
│
└─ Define Constants:
  ├─ NIFTY_50_STOCKS = ["INFY", "TCS", ...]
  ├─ BENCHMARK_TICKER = "^NSEI"
  └─ Trading logic functions (calculate_max_drawdown, etc.)
```

### **Route 1: Authentication (/routes/auth_routes.py)**

```
POST /signup
├─ Input: {name, email, password}
├─ Validation: Check if email already exists
├─ Action:
│  ├─ Create User in PostgreSQL
│  ├─ Hash password with werkzeug
│  └─ Set kyc_status = "pending"
└─ Response: {token, user}

POST /login
├─ Input: {email, password}
├─ Validation:
│  ├─ Check credentials
│  └─ BLOCK if kyc_status ≠ "approved"
└─ Response: {token, user}

POST /kyc/submit
├─ Input: {pan, aadhaar, selfie, ...} + JWT in header
├─ Action:
│  ├─ Verify JWT (extract user_id)
│  ├─ Store KYC docs in database
│  └─ Update User.kyc_status = "approved"
└─ Response: {message, kyc_status}

GET /profile
├─ Input: JWT in header
└─ Response: {id, name, email, kyc_status, ...}
```

### **Route 2: Dashboard Stock Universe (/routes/dashboard_routes.py)**

#### **GET /dashboard/stocks**

```
Logic:
│
├─ Check DASHBOARD_CACHE (from previous refresh)
│ ├─ If cache exists and is recent (< refresh interval)
│ │  └─ Return cached results immediately (FAST ✓)
│ │
│ └─ If cache empty or stale:
│    └─ Call refresh_dashboard() to recompute
│
└─ Return:
   └─ [{
      "ticker": "INFY",
      "signal": "BUY",
      "confidence": 0.85,
      "color": "green",
      "sector": "IT",
      "composite_score": 0.82,
      "ml_score": 0.80,
      "leading_score": 0.75,
      "lagging_score": 0.90,
      "risk_penalty": -0.10,
      ...
     }, ...]
```

#### **refresh_dashboard() - The Signal Generation Pipeline**

```
Step 1: Fetch Market Data
├─ For each ticker in UNIVERSE (50 stocks):
│  ├─ Fetch 1-year OHLCV from Yahoo Finance
│  └─ Filter out failed tickers (network errors, delisted, etc.)
│
├─ Fetch Benchmark Data (^NSEI, NIFTY 50 index)
├─ Fetch India VIX (volatility index)
└─ Load pre-trained Ensemble model from disk

Step 2: For Each Stock, Compute Signals
│
├─ Calculate 4 Components (each returns score in [-1, 1]):
│ │
│ ├─ A) LAGGING INDICATORS (20% weight)
│ │  └─ _lagging_component() [from composite_score.py]
│ │     ├─ Calculate RSI (14-day, typical momentum oscillator)
│ │     ├─ Calculate SMA20 and SMA50
│ │     ├─ Generate signal:
│ │     │  ├─ if RSI < 30 and price > SMA50  → BUY
│ │     │  ├─ if RSI > 70 and price < SMA20  → SELL
│ │     │  └─ else                            → HOLD
│ │     └─ Confidence from RSI extremeness
│ │
│ ├─ B) LEADING INDICATORS (25% weight)
│ │  └─ leading_signal() [from signals/leading_indicators.py]
│ │     ├─ Stochastic Oscillator (%K, %D)
│ │     ├─ Williams %R (momentum reversal signal)
│ │     ├─ On-Balance Volume (OBV, trend confirmation)
│ │     ├─ Rate of Change (ROC, momentum strength)
│ │     └─ Combine → score in [-1, 1]
│ │
│ ├─ C) ML ENSEMBLE CLASSIFIER (40% weight)
│ │  └─ get_ensemble_model().predict() [from optimization/ensemble.py]
│ │     ├─ Extract 5 features from price series:
│ │     │  ├─ Volatility (20-day rolling std)
│ │     │  ├─ Momentum (10-day ROC)
│ │     │  ├─ Trend strength (distance from SMA50)
│ │     │  ├─ Mean Reversion signal
│ │     │  └─ Market Regime (high volatility? Bull/bear?)
│ │     │
│ │     └─ Ensemble returns:
│ │        ├─ ML_score ∈ [-1, 1] (normalized from class probabilities)
│ │        └─ Feature importance breakdown
│ │
│ └─ D) RISK PENALTY (15% weight)
│    └─ calculate_tail_risk() [from risk/risk_metrics.py]
│       ├─ Calculate CVaR (Conditional Value at Risk, 95%)
│       │  └─ Worst 5% of daily returns
│       ├─ If CVaR is high (stock is risky):
│       │  └─ Reduce the signal score by penalty factor
│       └─ risk_penalty ∈ [-0.3, 0]
│
├─ Step 3: Weighted Fusion (composite_score.py)
│  └─ final_score = 0.40*ml_score + 0.25*leading_score 
│                 + 0.20*lagging_score + 0.15*risk_penalty
│
├─ Step 4: Signal Classification
│  └─ composite_score to signal:
│     ├─ score >= +0.7  → "BUY"   (green)
│     ├─ -0.7 < score < +0.7 → "HOLD"  (yellow)
│     └─ score <= -0.7  → "SELL"  (red)
│
└─ Step 5: Cache Result
   └─ Store in DASHBOARD_CACHE for fast future responses
```

#### **GET /dashboard/stocks/<ticker>**

```
Input: /stocks/INFY/details
│
├─ Fetch cached universe data
├─ Find INFY's cached composite result
│
└─ Return full breakdown:
   ├─ ticker, signal, composite_score, confidence
   ├─ ml_component: {ml_score, top_3_features, feature_values}
   ├─ leading_component: {signal, score, stochastic, williams_r, obv, roc}
   ├─ lagging_component: {signal, rsi, sma20, sma50, confidence}
   ├─ risk_component: {cvar, risk_penalty, sector}
   │
   ├─ candlestick_data: [
   │  {"date": "2026-01-01", "open": 2100, "high": 2150, "low": 2090, "close": 2130},
   │  ...
   │]
   │
   ├─ performance:
   │  ├─ ytd_return: "+12.5%"
   │  ├─ volatility: "25.3%"
   │  └─ sharpe_ratio: 0.85
   │
   └─ sector: "IT"
```

### **Route 3: Portfolio Optimization (/routes/dashboard_routes.py or embedded in app.py)**

#### **POST /optimize**

```
Input:
├─ stocks: ["INFY", "TCS", "HCLTECH", ...]  (2-10 stocks)
├─ investment: 100000  (in rupees)
└─ risk_level: "low" | "medium" | "high"

Step 1: Data Fetching
├─ For each ticker:
│  ├─ Fetch 2-year daily OHLCV data from Yahoo Finance
│  ├─ Calculate daily percentage returns
│  └─ Skip any ticker with fetch error
│
└─ Filter out failed tickers from optimization

Step 2: Return & Covariance Matrix
├─ mean_returns = [μ₁, μ₂, ..., μₙ] (average daily return per stock)
└─ cov_matrix = Σ (covariance matrix between all stocks)

Step 3: Portfolio Optimization (SLSQP algorithm)
│
├─ Objective functions based on risk_level:
│ │
│ ├─ risk_level = "low":
│ │  └─ Minimize: variance = w^T * Σ * w
│ │
│ ├─ risk_level = "medium":
│ │  └─ Maximize: Sharpe ratio = (r_p - r_f) / σ_p
│ │
│ └─ risk_level = "high":
│    └─ Maximize: expected return = w^T * μ
│
├─ Constraints:
│ ├─ Σ wᵢ = 1  (all weights sum to 100%)
│ └─ 0 ≤ wᵢ ≤ max_weight (no short-selling, concentration limit)
│
├─ Optimization output:
│ └─ weights = [0.25, 0.35, 0.20, 0.20] (optimal allocation)
│
└─ SLSQP iteratively adjusts weights until convergence

Step 4: Calculate Risk Metrics
├─ portfolio_return = Σ(wᵢ * μᵢ)
├─ portfolio_volatility = √(w^T * Σ * w)
├─ annual_return = daily_return * 252
├─ annual_volatility = daily_volatility * √252
├─ sharpe_ratio = (annual_return - r_f) / annual_volatility
├─ VaR (95%) = worst 5% daily loss percentile
├─ CVaR (95%) = average of worst 5% daily losses
├─ max_drawdown = largest peak-to-trough decline
└─ beta = covariance(portfolio, benchmark) / variance(benchmark)

Step 5: Calculate Sector Allocation
├─ For each stock:
│  ├─ Look up sector from stock_sectors.py mapping
│  └─ sector_allocation[sector] += weight[stock]
│
└─ Return: {"IT": 0.40, "Finance": 0.35, ...}

Step 6: Calculate Risk Contribution by Asset
├─ marginal_contribution[i] = weight[i] * (Σ * weight)[i] / portfolio_volatility
│  (How much does each stock contribute to total portfolio risk?)
│
└─ Return: [0.08, 0.12, 0.10, 0.05]

Step 7: Performance Comparison
├─ Calculate optimized portfolio cumulative return over 2 years
├─ Calculate benchmark (NIFTY 50) cumulative return over same period
│
└─ Align and return both as time series

Step 8: Generate Efficient Frontier
├─ Generate 5,000 random portfolio combinations
├─ Calculate return & volatility for each
│
└─ Return: list of random points + optimal point highlighted

Step 9: Calculate Correlation Matrix
├─ corr_matrix = correlation between selected stocks
│
└─ Return: n×n symmetric matrix for heatmap visualization

Step 10: Compile & Return Response
└─ {
    "status": "success",
    "stocks": ["INFY", "TCS", ...],
    "weights": [0.25, 0.35, ...],
    "investment": 100000,
    "allocation": [25000, 35000, ...],
    
    "metrics": {
      "expected_return": 0.00045 (daily),
      "expected_annual_return": 0.114 (11.4% per year),
      "volatility": 0.0085 (daily),
      "annual_volatility": 0.135 (13.5% per year),
      "sharpe_ratio": 0.85,
      "var_95": -0.02,
      "cvar_95": -0.028,
      "max_drawdown": -0.35,
      "beta": 0.92
    },
    
    "sector_allocation": {"IT": 0.40, "Finance": 0.35, ...},
    
    "risk_contribution": [0.08, 0.12, 0.10, 0.05],
    
    "performance": {
      "dates": ["2024-01-01", "2024-01-02", ...],
      "portfolio_cumulative_return": [1.0, 1.002, 1.005, ...],
      "benchmark_cumulative_return": [1.0, 1.001, 1.003, ...]
    },
    
    "efficient_frontier": {
      "random_returns": [...],
      "random_volatilities": [...],
      "optimal_return": 0.114,
      "optimal_volatility": 0.135
    },
    
    "correlation_matrix": [[1.0, 0.65, ...], [0.65, 1.0, ...], ...],
    
    "warning": null,
    "removed_stocks": []
  }
```

---

## 🗄️ DATABASE SCHEMA (PostgreSQL)

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  kyc_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Future tables (for KYC documents, transactions, portfolio history):
-- CREATE TABLE kyc_documents (...)
-- CREATE TABLE user_portfolios (...)
-- CREATE TABLE portfolio_history (...)
```

---

## 🔐 Security Features

1. **JWT Authentication**: 
   - Tokens issued on signup/login
   - Header: `Authorization: Bearer <token>`
   - Secret key: SHA-256 hashed (128+ char)

2. **KYC Enforcement**:
   - Login blocked until `kyc_status = "approved"`
   - Frontend enforces navigation to KYCPage

3. **CORS Enabled**:
   - Flask-CORS allows React frontend to make requests

4. **Password Hashing**:
   - werkzeug.security for bcrypt-style hashing

---

## 📊 Key Data Flows Summary

### **Flow A: Initial Stock Browsing**

```
User logs in → LocalStorage stores token + kyc_status
           → View = "dashboard"
           → PortfolioDashboard.js renders
           → User clicks "Browse Stocks"
           → View = "universe"
           → UniverseDashboard calls GET /dashboard/stocks
           → Backend refresh_dashboard() (if cache empty):
              - Fetch 50 stocks' OHLCV data from Yahoo
              - Compute signals (lagging + leading + ML + risk)
              - Score and cache results
           → Frontend displays 50 stocks color-coded by signal
           → User clicks stock → Modal fetches GET /stocks/<ticker>/details
           → User adds stocks to portfolioStocks array
```

### **Flow B: Portfolio Construction & Optimization**

```
User selects N stocks (2-10) and invests $X at risk level L
           → View = "optimizer"
           → Dashboard.js renders Portfolio Builder
           → User clicks "OPTIMIZE"
           → POST /optimize {stocks, investment, risk_level}
           → Backend:
              1. Fetch 2-year returns for each stock
              2. Build covariance matrix
              3. Run SLSQP optimization
              4. Calculate metrics, allocations, charts
           → Returns full portfolio summary
           → Frontend displays:
              - Metrics cards (return, volatility, Sharpe, VaR, CVaR)
              - Pie charts (stock & sector allocation)
              - Line chart (portfolio vs benchmark performance)
              - Scatter plot (efficient frontier)
              - Heatmap (correlation matrix)
```

---

## 🔄 Caching Strategy

1. **Dashboard Stock Universe Cache** (DASHBOARD_CACHE dict in memory):
   - Refreshes on server restart or manual `/dashboard/refresh`
   - Stores computed signals for all 50 stocks
   - Subsequent requests return instantly (no Yahoo Finance fetch)

2. **Ensemble Model Cache** (loaded once at startup):
   - Pre-trained model from `Backend/data/ensemble_model.joblib`
   - Loaded by `get_ensemble_model()` in model_loader.py

3. **Frontend LocalStorage Cache**:
   - token (JWT)
   - kyc_status
   - hasSeenGuide (to show/hide welcome guide)

---

## ⚠️ Error Handling

1. **Failed Yahoo Finance Fetches**:
   - Individual tickers that fail are excluded
   - Optimization continues with remaining tickers
   - Response includes `removed_stocks` array

2. **Insufficient Data**:
   - If < 200 days of history for a stock, skip it
   - Prevents unreliable beta/volatility calculations

3. **KYC Blocks**:
   - Login endpoint returns 403 if kyc_status ≠ "approved"
   - Frontend redirects to KYCPage

4. **JWT Expiry**:
   - Protected routes check JWT validity
   - Expired tokens → 401 Unauthorized
   - Frontend redirects to login

---

## 🎓 Signal Scoring Breakdown Example

For **INFY** on a given day:

```
Lagging (RSI=35, SMA20>SMA50): signal=BUY, score=+0.65
Leading (Stoch=28, OBV↑, ROC↑): signal=BUY, score=+0.80
ML Ensemble (trained on 5 features): score=+0.75
Risk Penalty (CVaR=-2.5%, high risk): penalty=-0.20

composite_score = 0.20*(+0.65) + 0.25*(+0.80) + 0.40*(+0.75) + 0.15*(-0.20)
                = 0.13 + 0.20 + 0.30 - 0.03
                = 0.60

Signal Classification: 0.60 ∈ (-0.7, +0.7) → HOLD (yellow)
Color: 🟡 Yellow
Confidence: 65%
```

---

## 🚀 System Startup Sequence

```
1. Flask app.py starts
2. Database connection established (PostgreSQL)
3. JWT manager initialized
4. Blueprints registered
5. First user request to /dashboard/stocks:
   ├─ DASHBOARD_CACHE is empty
   ├─ refresh_dashboard() is called
   ├─ All 50 tickers fetched, signals computed (SLOW, ~10-30s)
   ├─ Results cached
   └─ Response returned
6. Subsequent requests return cached results instantly
7. Background refresh on /dashboard/refresh (manual trigger)
```

---

## 📝 Next Steps (Future Development)

1. **Background Task Scheduler** (Celery):
   - Refresh signals every 15 minutes
   - Don't wait for manual trigger

2. **Portfolio Monitoring**:
   - Track saved portfolios
   - Alert on signal changes
   - Suggest rebalancing

3. **User Preferences**:
   - Save favorite stocks
   - Store historical portfolios
   - Performance tracking

4. **Mobile App**:
   - React Native version of dashboard

5. **Advanced Signals**:
   - Sentiment analysis (news/social)
   - Insider trading data
   - Options market data
