/* Displays cached NIFTY 50 signals and lets the parent manage selections. */
import { useEffect, useState } from "react";

const COLOR_STYLES = {
  green: { signal: "BUY", className: "buy" },
  yellow: { signal: "HOLD", className: "hold" },
  red: { signal: "SELL", className: "sell" }
};

export default function StockUniverseDashboard({ onSelectStock, onViewStock, selectedTickers = [] }) {
  const [stocks, setStocks] = useState([]);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    fetch("http://127.0.0.1:5000/dashboard/stocks")
      .then((response) => {
        if (!response.ok) throw new Error("Dashboard not ready yet");
        return response.json();
      })
      .then((data) => {
        setStocks(data.stocks || []);
        setLastRefreshed(data.last_refreshed_at);
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="universe-feedback">Loading stock universe...</div>;
  if (error) return <div className="universe-feedback universe-error">{error} — try again in a moment.</div>;

  const signalCount = (color) => stocks.filter((stock) => stock.color === color).length;

  return (
    <section className="stock-universe">
      <div className="stock-universe-toolbar">
        <div>
          <h2>NIFTY 50 Live Signals</h2>
          <p>Review each signal, then select stocks for your portfolio.</p>
        </div>
        <span className="last-refreshed">Last refreshed: {lastRefreshed ? new Date(lastRefreshed).toLocaleTimeString() : "—"}</span>
      </div>

      <div className="universe-signal-summary" aria-label="Market signal summary">
        <span><b>{stocks.length}</b> total stocks</span>
        <span className="buy"><b>{signalCount("green")}</b> BUY</span>
        <span className="hold"><b>{signalCount("yellow")}</b> HOLD</span>
        <span className="sell"><b>{signalCount("red")}</b> SELL</span>
        <span><b>{selectedTickers.length}</b> selected</span>
      </div>

      <div className="stock-universe-grid">
        {stocks.map((stock) => {
          const style = COLOR_STYLES[stock.color] || COLOR_STYLES.yellow;
          const isSelected = selectedTickers.includes(stock.ticker);
          const selectWithKeyboard = (event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onSelectStock(stock);
            }
          };

          return (
            <article
              key={stock.ticker}
              className={`stock-signal-card ${style.className} ${isSelected ? "selected" : ""}`}
              onClick={() => onSelectStock(stock)}
              onKeyDown={selectWithKeyboard}
              role="button"
              tabIndex={0}
              aria-pressed={isSelected}
            >
              <div className="stock-card-heading">
                <div>
                  <h3>{stock.ticker}</h3>
                  <p>{stock.sector}</p>
                </div>
                <div className="stock-card-actions">
                  {isSelected && <span className="stock-selected-check" aria-label="Selected">✓</span>}
                  <button
                    type="button"
                    className="stock-detail-button"
                    title={`View ${stock.ticker} chart and indicators`}
                    aria-label={`View ${stock.ticker} chart and indicators`}
                    onClick={(event) => {
                      event.stopPropagation();
                      onViewStock(stock.ticker);
                    }}
                  >
                    i
                  </button>
                </div>
              </div>
              <span className="stock-signal-badge">{style.signal}</span>
              <div className="stock-card-metrics">
                <div><span>Expected return</span><strong>{(stock.expected_return * 100).toFixed(1)}%</strong></div>
                <div><span>Confidence</span><strong>{(stock.confidence * 100).toFixed(0)}%</strong></div>
              </div>
              <p className="stock-risk">Risk: <strong>{stock.risk_level}</strong></p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
