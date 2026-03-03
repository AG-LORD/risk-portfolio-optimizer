import React, { useState } from "react";
import axios from "axios";
import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

function App() {
  const [stocks, setStocks] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleOptimize = async () => {
    const stockArray = stocks
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s !== "");

    if (stockArray.length === 0) {
      alert("Please enter at least one stock.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/optimize",
        { stocks: stockArray }
      );

      setResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Error connecting to backend or invalid stock symbols.");
    }

    setLoading(false);
  };

  const pieData = result
    ? {
        labels: Object.keys(result.allocation),
        datasets: [
          {
            label: "Portfolio Allocation",
            data: Object.values(result.allocation),
            backgroundColor: [
              "#4CAF50",
              "#2196F3",
              "#FFC107",
              "#FF5722",
              "#9C27B0",
              "#00BCD4"
            ],
          },
        ],
      }
    : null;

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h2>Risk-Aware Portfolio Optimizer</h2>

      <input
        type="text"
        placeholder="RELIANCE.NS, INFY.NS, HDFCBANK.NS"
        value={stocks}
        onChange={(e) => setStocks(e.target.value)}
        style={{ width: "400px", padding: "8px" }}
      />

      <button
        onClick={handleOptimize}
        style={{ marginLeft: "10px", padding: "8px 12px" }}
      >
        Optimize
      </button>

      {loading && <p style={{ marginTop: "20px" }}>Loading...</p>}

      {result && (
        <div style={{ marginTop: "30px" }}>
          <h3>Portfolio Metrics</h3>
          <p><b>Expected Return:</b> {result.portfolio_return}</p>
          <p><b>Volatility:</b> {result.portfolio_volatility}</p>
          <p><b>Sharpe Ratio:</b> {result.sharpe_ratio}</p>

          <h3>Allocation</h3>
          <Pie data={pieData} />
        </div>
      )}
    </div>
  );
}

export default App;