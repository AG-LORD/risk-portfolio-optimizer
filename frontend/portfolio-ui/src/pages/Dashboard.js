import { useEffect, useMemo, useState } from "react";
import "../styles/dashboard.css";
import {
  Bar,
  BarChart,
  Brush,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import TooltipIcon from "../components/TooltipIcon";

const STOCK_COLORS = ["#06b6d4", "#60a5fa", "#34d399", "#f59e0b", "#f87171", "#a78bfa"];
const SECTOR_COLORS = ["#22c55e", "#0ea5e9", "#f97316", "#eab308", "#ef4444", "#8b5cf6", "#14b8a6"];
const SIGNAL_LABELS = { BUY: "BUY", HOLD: "HOLD", SELL: "SELL" };
const RANGE_MAP = { "1M": 21, "3M": 63, "6M": 126, "1Y": 252 };

const metricDescriptions = {
  sharpe: "How much return you get for each unit of risk. Higher is better.",
  volatility: "How much the portfolio value can fluctuate during the year.",
  var_95: "Worst expected daily loss in normal conditions (95% confidence).",
  cvar_95: "Average loss on very bad days when the market crashes.",
  max_drawdown: "Largest drop from peak value during the investment period.",
  portfolio_beta: "How sensitive the portfolio is to the overall market movement.",
  diversification_score: "Higher score means better spread across sectors."
};

const signalDescriptions = {
  BUY: "The stock shows strong positive momentum. It may be a good time to invest.",
  HOLD: "The stock is neutral. It is stable but not showing strong momentum yet.",
  SELL: "The stock momentum is weak right now. It may be better to avoid buying it."
};

const RISK_HELP = {
  low: {
    title: "LOW",
    sub: "Target Volatility < 10%",
    desc: "Conservative portfolio with stable returns."
  },
  medium: {
    title: "MEDIUM",
    sub: "Target Volatility < 20%",
    desc: "Balanced risk and return."
  },
  high: {
    title: "HIGH",
    sub: "Target Volatility < 35%",
    desc: "Aggressive growth with higher volatility."
  }
};

const ENSEMBLE_FEATURES = [
  { key: "recent_return", label: "Recent Return", description: "Latest price return change." },
  { key: "volatility", label: "Volatility", description: "Short-term price movement size." },
  { key: "momentum", label: "Momentum", description: "Direction and speed of trend." },
  { key: "sector_exposure", label: "Sector Exposure", description: "Industry weight signal." },
  { key: "risk_score", label: "Risk Score", description: "Risk signal for the asset mix." }
];

const formatCurrency = (value) => {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return "--";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(numeric);
};

function Dashboard({ onLogout }) {
  const [symbol, setSymbol] = useState("");
  const [stockOptions, setStockOptions] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [risk, setRisk] = useState("medium");
  const [investment, setInvestment] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedRange, setSelectedRange] = useState("6M");

  const [ensembleFeatures, setEnsembleFeatures] = useState({
    recent_return: 0.12,
    volatility: -0.16,
    momentum: 0.74,
    sector_exposure: 1.25,
    risk_score: -0.08
  });
  const [ensembleFeatureMetadata, setEnsembleFeatureMetadata] = useState(ENSEMBLE_FEATURES);
  const [ensemblePrediction, setEnsemblePrediction] = useState(null);
  const [ensembleLoading, setEnsembleLoading] = useState(false);
  const [ensembleError, setEnsembleError] = useState("");
  const [ensembleStatus, setEnsembleStatus] = useState("Ready");
  const [ensembleExplanations, setEnsembleExplanations] = useState([]);
  const [ensembleBasePredictions, setEnsembleBasePredictions] = useState(null);

  const [metrics, setMetrics] = useState({});
  const [summary, setSummary] = useState({});
  const [signals, setSignals] = useState([]);
  const [portfolioSignal, setPortfolioSignal] = useState("HOLD");
  const [portfolioSignalReason, setPortfolioSignalReason] = useState("");
  const [allocation, setAllocation] = useState([]);
  const [sectorAllocation, setSectorAllocation] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [riskContribution, setRiskContribution] = useState([]);

  const safeMetrics = metrics || {};

  useEffect(() => {
    const loadStocks = async () => {
      try {
        const response = await fetch("http://localhost:5000/stocks");
        const data = await response.json();
        setStockOptions(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error("Failed to load stocks:", error);
      }
    };

    // Feature metadata is bundled in the frontend by default; only load stock list.
    loadStocks();
  }, []);

  const filteredPerformance = useMemo(() => {
    const count = RANGE_MAP[selectedRange] || RANGE_MAP["6M"];
    return performanceData.slice(-count);
  }, [performanceData, selectedRange]);

  const updateEnsembleFeature = (key, value) => {
    setEnsembleFeatures((prev) => ({
      ...prev,
      [key]: Number(value)
    }));
  };

  const fillSampleFeatures = () => {
    setEnsembleFeatures({
      recent_return: 0.12,
      volatility: -0.16,
      momentum: 0.74,
      sector_exposure: 1.25,
      risk_score: -0.08
    });
    setEnsemblePrediction(null);
    setEnsembleError("");
    setEnsembleStatus("Ready");
  };

  const runEnsemblePrediction = async () => {
    setEnsembleLoading(true);
    setEnsembleError("");
    setEnsemblePrediction(null);
    setEnsembleStatus("Connecting...");

    try {
      const response = await fetch("http://localhost:5000/ensemble/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ features: ensembleFeatures })
      });
      const data = await response.json();
      if (!response.ok) {
        setEnsembleError(data.error || "Failed to get prediction");
        setEnsembleStatus("Error");
      } else {
        const predictionValue = Array.isArray(data.predictions) ? data.predictions[0] : null;
        setEnsemblePrediction(predictionValue);
        setEnsembleExplanations(Array.isArray(data.explanations) ? data.explanations : []);
        setEnsembleBasePredictions(data.base_predictions || null);
        setEnsembleStatus("Connected");
      }
    } catch (error) {
      console.error(error);
      setEnsembleError("Backend connection failed");
      setEnsembleStatus("Error");
    } finally {
      setEnsembleLoading(false);
    }
  };

  const sectorByStock = useMemo(() => {
    const map = {};
    signals.forEach((item) => {
      map[item.stock] = item.sector;
    });
    return map;
  }, [signals]);

  const addStock = () => {
    const selected = symbol.trim().toUpperCase();
    if (selected && !stocks.includes(selected)) {
      setStocks((prev) => [...prev, selected]);
      setSymbol("");
    }
  };

  const removeStock = (stock) => {
    setStocks((prev) => prev.filter((s) => s !== stock));
  };

  const optimize = async () => {
    if (stocks.length < 2) {
      alert("Please add at least 2 stocks");
      return;
    }
    const investmentValue = Number(investment);
    if (!investment || Number.isNaN(investmentValue) || investmentValue <= 0) {
      alert("Enter investment amount");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("http://localhost:5000/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stocks, investment: investmentValue, risk })
      });
      const data = await response.json();
      if (!response.ok) {
        alert(data.error || "Failed to optimize portfolio");
        setShowResults(false);
        return;
      }

      setMetrics(data.portfolio_metrics || data.metrics || {});
      setSummary(data.portfolio_summary || {});
      setSignals(Array.isArray(data.signals) ? data.signals : []);
      setPortfolioSignal(data.portfolio_signal || "HOLD");
      setPortfolioSignalReason(data.portfolio_signal_reason || "");
      setAllocation(Array.isArray(data.allocation) ? data.allocation : []);
      setSectorAllocation(Array.isArray(data.sector_allocation) ? data.sector_allocation : []);
      setPerformanceData(Array.isArray(data.performance_curve || data.performance) ? (data.performance_curve || data.performance) : []);
      setRiskContribution(Array.isArray(data.risk_contribution) ? data.risk_contribution : []);
      setShowResults(true);
    } catch (error) {
      console.error(error);
      alert("Backend connection failed");
    } finally {
      setLoading(false);
    }
  };

  const getSignalClass = (signal) => `badge badge-${String(signal || "HOLD").toLowerCase()}`;
  const getEnsembleStatusClass = (status) => {
    const normalized = String(status || "").toLowerCase();
    if (normalized.includes("connected")) return "connected";
    if (normalized.includes("connecting")) return "connecting";
    if (normalized.includes("error")) return "error";
    return "ready";
  };
  const portfolioSignalExplanation = signalDescriptions[portfolioSignal] || signalDescriptions.HOLD;

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <h2>Quant Portfolio Control Center</h2>
        <button className="logout-btn" onClick={onLogout}>Logout</button>
      </header>

      <section className="panel">
        <div className="section-title">Portfolio Setup</div>
        <div className="stock-input">
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            <option value="">Select NIFTY 50 stock</option>
            {stockOptions.map((stock) => <option key={stock} value={stock}>{stock}</option>)}
          </select>
          <button onClick={addStock}>Add</button>
        </div>
        <div className="stock-tags">
          {stocks.map((s) => (
            <span key={s}>
              {s}
              {sectorByStock[s] ? <em className="sector-tag">{sectorByStock[s]}</em> : null}
              <button onClick={() => removeStock(s)}>x</button>
            </span>
          ))}
        </div>
        <input
          type="number"
          className="investment-input"
          placeholder="Investment Amount (INR)"
          value={investment}
          onChange={(e) => setInvestment(e.target.value)}
        />
        <div className="risk-buttons">
          <button className={risk === "low" ? "risk-active" : ""} onClick={() => setRisk("low")}>LOW</button>
          <button className={risk === "medium" ? "risk-active" : ""} onClick={() => setRisk("medium")}>MEDIUM</button>
          <button className={risk === "high" ? "risk-active" : ""} onClick={() => setRisk("high")}>HIGH</button>
        </div>
        <div className="risk-help-grid">
          {Object.entries(RISK_HELP).map(([key, details]) => (
            <div key={key} className={`risk-help-card ${risk === key ? "active" : ""}`} title={details.desc}>
              <p>{details.title}</p>
              <small>{details.sub}</small>
              <span>{details.desc}</span>
            </div>
          ))}
        </div>

        <section className="ensemble-panel">
          <div className="ensemble-header">
            <div>
              <div className="section-title">Ensemble Explainability</div>
              <p className="ensemble-note">Provide feature values and run explainability to see feature contributions.</p>
            </div>
          </div>
          <div className="feature-row">
            {ensembleFeatureMetadata.map(({ key, label, description }) => (
              <div key={key} className="feature-box">
                <label>{label}</label>
                <input
                  type="number"
                  value={ensembleFeatures[key] ?? 0}
                  step="0.01"
                  onChange={(e) => updateEnsembleFeature(key, e.target.value)}
                  aria-label={label}
                />
                <small>{description}</small>
              </div>
            ))}
          </div>
          <div className="prediction-actions">
            <button className="predict-btn" onClick={runEnsemblePrediction} disabled={ensembleLoading}>
              {ensembleLoading ? "Predicting..." : "Predict"}
            </button>
            <button className="sample-btn" onClick={fillSampleFeatures} type="button">
              Sample values
            </button>
            <span className={`model-badge status-${getEnsembleStatusClass(ensembleStatus)}`}>
              {ensembleStatus}
            </span>
          </div>
          {ensemblePrediction !== null && (
            <div className="prediction-result">
              <div className="prediction-main">
                <span>Prediction</span>
                <strong>{Number(ensemblePrediction).toFixed(6)}</strong>
              </div>
              <div className="explanation-list">
                {ensembleExplanations.map(({ key, label, contribution }) => (
                  <div className="explain-row" key={key}>
                    <span>{label}</span>
                    <strong className={Number(contribution) >= 0 ? 'pos' : 'neg'}>{Number(contribution).toFixed(6)}</strong>
                  </div>
                ))}
              </div>
              {ensembleBasePredictions && (
                <div className="base-preds">
                  <small>Base model outputs</small>
                  <div className="base-row">Ridge: {ensembleBasePredictions.ridge && ensembleBasePredictions.ridge[0] ? Number(ensembleBasePredictions.ridge[0]).toFixed(6) : "--"}</div>
                  <div className="base-row">RandomForest: {ensembleBasePredictions.random_forest && ensembleBasePredictions.random_forest[0] ? Number(ensembleBasePredictions.random_forest[0]).toFixed(6) : "--"}</div>
                  <div className="base-row">HGB: {ensembleBasePredictions.hist_gradient_boosting && ensembleBasePredictions.hist_gradient_boosting[0] ? Number(ensembleBasePredictions.hist_gradient_boosting[0]).toFixed(6) : "--"}</div>
                </div>
              )}
            </div>
          )}
          {ensembleError && <div className="error-text">{ensembleError}</div>}
        </section>

        <button className="optimize-btn" onClick={optimize} disabled={loading}>
          {loading ? <span className="spinner" /> : null}
          {loading ? "Optimizing..." : "Optimize Portfolio"}
        </button>
      </section>

      {showResults && (
        <>
          <section className="panel">
            <div className="section-title">Portfolio Metrics</div>
            <div className="metrics">
              <div className="metric-card"><p>Portfolio Value</p><h3>{formatCurrency(safeMetrics.portfolio_value)}</h3></div>
              <div className="metric-card"><p>Estimated yearly return</p><h3>{safeMetrics.expected_return ?? safeMetrics.returns ?? "--"}%</h3></div>
              <div className="metric-card"><p>Risk vs Return Score <TooltipIcon text={metricDescriptions.sharpe} /></p><h3>{safeMetrics.sharpe ?? "--"}</h3></div>
              <div className="metric-card"><p>Expected fluctuation <TooltipIcon text={metricDescriptions.volatility} /></p><h3>{safeMetrics.volatility ?? "--"}%</h3></div>
              <div className="metric-card"><p>Possible daily loss (95%) <TooltipIcon text={metricDescriptions.var_95} /></p><h3>{safeMetrics.var_95 ?? "--"}%</h3></div>
              <div className="metric-card"><p>Loss during worst market days (95%) <TooltipIcon text={metricDescriptions.cvar_95} /></p><h3>{safeMetrics.cvar_95 ?? "--"}%</h3></div>
              <div className="metric-card"><p>Biggest drop seen <TooltipIcon text={metricDescriptions.max_drawdown} /></p><h3>{safeMetrics.max_drawdown ?? "--"}%</h3></div>
              <div className="metric-card"><p>Market movement sensitivity <TooltipIcon text={metricDescriptions.portfolio_beta} /></p><h3>{safeMetrics.portfolio_beta ?? "--"}</h3></div>
              <div className="metric-card"><p>Diversification score <TooltipIcon text={metricDescriptions.diversification_score} /></p><h3>{safeMetrics.diversification_score ?? "--"}%</h3></div>
              <div className="metric-card"><p>NIFTY Return</p><h3>{safeMetrics.benchmark_return ?? "--"}%</h3></div>
            </div>
          </section>

          <section className="panel">
            <div className="section-title">Portfolio Summary</div>
            <div className="summary-grid">
              <div><span>Investment Amount</span><strong>{formatCurrency(summary.investment_amount ?? safeMetrics.investment_amount ?? investment)}</strong></div>
              <div><span>Stocks Selected</span><strong>{summary.stocks_selected ?? stocks.length}</strong></div>
              <div><span>Sectors Covered</span><strong>{summary.sectors_covered ?? "--"}</strong></div>
              <div><span>Risk Level</span><strong>{String(summary.risk_level || risk).toUpperCase()}</strong></div>
              <div><span>Portfolio Signal</span><strong className={getSignalClass(summary.portfolio_signal || portfolioSignal)}>{summary.portfolio_signal || portfolioSignal}</strong></div>
              <div><span>Estimated yearly return</span><strong>{summary.expected_return ?? safeMetrics.expected_return ?? safeMetrics.returns ?? "--"}%</strong></div>
            </div>
          </section>

          <section className="panel">
            <div className="section-title">Signals</div>
            <div className="recommendation-card">
              <p>Portfolio Signal: <strong className={getSignalClass(portfolioSignal)}>{SIGNAL_LABELS[portfolioSignal] || "HOLD"}</strong></p>
              <p>Explanation: {portfolioSignalReason || portfolioSignalExplanation}</p>
            </div>
            <div className="signal-grid">
              {signals.map((item) => (
                <div className="signal-card" key={item.stock}>
                  <p>{item.stock} <em className="sector-tag">{item.sector}</em></p>
                  <div className={getSignalClass(item.signal)}>{SIGNAL_LABELS[item.signal]}</div>
                  <p>{signalDescriptions[item.signal] || signalDescriptions.HOLD}</p>
                  <span>Confidence: {Math.round((item.confidence || 0) * 100)}%</span>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="section-title">Performance Chart</div>
            <div className="range-buttons">
              {Object.keys(RANGE_MAP).map((range) => (
                <button
                  key={range}
                  className={selectedRange === range ? "active" : ""}
                  onClick={() => setSelectedRange(range)}
                >
                  {range}
                </button>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={filteredPerformance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => formatCurrency(value)} />
                <Tooltip formatter={(value, name) => [formatCurrency(value), name]} />
                <Legend />
                <Line type="monotone" dataKey="portfolio" name="Portfolio Value" stroke="#22c55e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="benchmark" name="NIFTY Benchmark" stroke="#60a5fa" strokeWidth={2} dot={false} />
                <Brush dataKey="date" height={24} stroke="#60a5fa" />
              </LineChart>
            </ResponsiveContainer>
          </section>

          <section className="panel">
            <div className="section-title">Allocation Charts</div>
            <div className="allocation-grid">
              <div className="chart-card">
                <h4>Stock Allocation</h4>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Tooltip formatter={(value, name) => [`${value}%`, name]} />
                    <Pie
                      data={allocation}
                      dataKey="value"
                      nameKey="name"
                      outerRadius={110}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                    >
                      {allocation.map((entry, index) => (
                        <Cell key={`${entry.name}-${index}`} fill={STOCK_COLORS[index % STOCK_COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-card">
                <h4>Sector Allocation</h4>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Tooltip formatter={(value, name) => [`${value}%`, name]} />
                    <Pie
                      data={sectorAllocation}
                      dataKey="value"
                      nameKey="name"
                      outerRadius={110}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                    >
                      {sectorAllocation.map((entry, index) => (
                        <Cell key={`${entry.name}-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="section-title">Risk Contribution by Asset</div>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={riskContribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="stock" />
                <YAxis />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="value" name="Risk Contribution (%)" fill="#38bdf8" />
              </BarChart>
            </ResponsiveContainer>
          </section>

          <section className="panel">
            <div className="section-title">Indicator Panel</div>
            <div className="table-wrap">
              <table className="indicator-table">
                <thead>
                  <tr>
                    <th>Stock</th>
                    <th>Sector</th>
                    <th>RSI</th>
                    <th>SMA20</th>
                    <th>SMA50</th>
                    <th>Signal</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((item) => (
                    <tr key={item.stock}>
                      <td>{item.stock}</td>
                      <td><em className="sector-tag">{item.sector}</em></td>
                      <td>{item.rsi ?? "--"}</td>
                      <td>{item.sma20 ?? "--"}</td>
                      <td>{item.sma50 ?? "--"}</td>
                      <td><span className={getSignalClass(item.signal)}>{SIGNAL_LABELS[item.signal]}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default Dashboard;
