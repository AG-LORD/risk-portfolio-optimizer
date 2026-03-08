import { useState } from "react";
import "../styles/dashboard.css";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts";

const COLORS = ["#22c55e", "#3b82f6", "#a855f7", "#f59e0b", "#f97316"];

function Dashboard({ onLogout }) {

  const [symbol, setSymbol] = useState("");
  const [stocks, setStocks] = useState([]);
  const [risk, setRisk] = useState("medium");
  const [investment, setInvestment] = useState("");

  const [showResults, setShowResults] = useState(false);

  const [portfolioData, setPortfolioData] = useState([]);
  const [allocation, setAllocation] = useState([]);
  const [metrics, setMetrics] = useState({});

  const [loading, setLoading] = useState(false);
  const safeMetrics = metrics || {};


  // ADD STOCK
  const addStock = () => {

    if (symbol.trim() !== "") {

      setStocks([...stocks, symbol.toUpperCase()]);
      setSymbol("");

    }

  };


  // OPTIMIZE PORTFOLIO (CALL BACKEND)

  const optimize = async () => {

    if (stocks.length < 2) {
      alert("Please add at least 2 stocks");
      return;
    }

    if (!investment) {
      alert("Enter investment amount");
      return;
    }

    setLoading(true);

    try {

      const response = await fetch("http://localhost:5000/optimize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          stocks: stocks,
          investment: investment,
          risk: risk
        })
      });

      const data = await response.json();
      if (!response.ok) {
        alert(data.error || "Failed to optimize portfolio");
        setShowResults(false);
        return;
      }

      setPortfolioData(Array.isArray(data.performance) ? data.performance : []);
      setAllocation(Array.isArray(data.allocation) ? data.allocation : []);
      setMetrics(data.metrics || {});
      setShowResults(true);

    } catch (error) {

      console.error("Backend error:", error);
      alert("Backend connection failed");

    } finally {
      setLoading(false);
    }

  };


  return (

    <div className="dashboard-page">

      {/* HEADER */}

      <header className="dashboard-header">

        <h2>Risk-Aware Portfolio Optimizer</h2>

        <button className="logout-btn" onClick={onLogout}>
          Logout
        </button>

      </header>


      {/* INPUT PANEL */}

      <div className="input-card">

        <h3>Portfolio Setup</h3>

        {/* STOCK INPUT */}

        <div className="stock-input">

          <input
            type="text"
            placeholder="Add stock (RELIANCE.NS)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />

          <button onClick={addStock}>Add</button>

        </div>


        {/* SELECTED STOCKS */}

        <div className="stock-tags">

          {stocks.map((s, i) => (
            <span key={i}>{s}</span>
          ))}

        </div>


        {/* INVESTMENT */}

        <input
          type="number"
          className="investment-input"
          placeholder="Investment Amount ($)"
          value={investment}
          onChange={(e) => setInvestment(e.target.value)}
        />


        {/* RISK LEVEL */}

        <div className="risk-buttons">

          <button
            className={risk === "low" ? "risk-active" : ""}
            onClick={() => setRisk("low")}
          >
            Low
          </button>

          <button
            className={risk === "medium" ? "risk-active" : ""}
            onClick={() => setRisk("medium")}
          >
            Medium
          </button>

          <button
            className={risk === "high" ? "risk-active" : ""}
            onClick={() => setRisk("high")}
          >
            High
          </button>

        </div>


        {/* OPTIMIZE BUTTON */}

        <button className="optimize-btn" onClick={optimize}>

          {loading ? "Optimizing..." : "Optimize Portfolio"}

        </button>

      </div>


      {/* RESULTS */}

      {showResults && (

        <>

          {/* METRICS */}

          <div className="metrics">

            <div className="metric-card">
              <p>Portfolio Value</p>
              <h3>${safeMetrics.portfolio_value ?? "--"}</h3>
            </div>

            <div className="metric-card">
              <p>Total Returns</p>
              <h3>{safeMetrics.returns ?? "--"}%</h3>
            </div>

            <div className="metric-card">
              <p>Sharpe Ratio</p>
              <h3>{safeMetrics.sharpe ?? "--"}</h3>
            </div>

            <div className="metric-card">
              <p>Volatility</p>
              <h3>{safeMetrics.volatility ?? "--"}%</h3>
            </div>

          </div>


          {/* CHARTS */}

          <div className="charts">

            {/* PERFORMANCE */}

            <div className="chart-box">

              <h3>Performance</h3>

              <ResponsiveContainer width="100%" height={250}>

                <LineChart data={portfolioData}>

                  <XAxis dataKey="date" />

                  <YAxis />

                  <Tooltip />

                  <Line
                    type="monotone"
                    dataKey="portfolio"
                    stroke="#22c55e"
                    strokeWidth={2}
                  />

                </LineChart>

              </ResponsiveContainer>

            </div>


            {/* ALLOCATION */}

            <div className="chart-box">

              <h3>Allocation</h3>

              <ResponsiveContainer width="100%" height={250}>

                <PieChart>

                  <Pie
                    data={allocation}
                    dataKey="value"
                    outerRadius={90}
                    label
                  >

                    {allocation.map((entry, index) => (

                      <Cell
                        key={index}
                        fill={COLORS[index % COLORS.length]}
                      />

                    ))}

                  </Pie>

                </PieChart>

              </ResponsiveContainer>

            </div>

          </div>

        </>

      )}

    </div>

  );

}

export default Dashboard;
