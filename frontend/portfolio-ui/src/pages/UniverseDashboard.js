import { useState } from "react";
import StockUniverseDashboard from "../components/StockUniverseDashboard";
import CandlestickChart from "../components/CandlestickChart";
import StockDetailPanel from "../components/StockDetailPanel";
import "../styles/dashboard.css";

export default function UniverseDashboard({
  onLogout,
  onBackToDashboard,
  onBuildPortfolio,
  selectedStocks = [],
  onSelectedStocksChange
}) {
  const [detail, setDetail] = useState(null);
  const [detailTicker, setDetailTicker] = useState("");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState("");

  const selectedTickers = selectedStocks.map((stock) => stock.ticker);
  const isReady = selectedStocks.length >= 2;

  const handleSelectStock = (stock) => {
    const nextStocks = selectedStocks.some((item) => item.ticker === stock.ticker)
      ? selectedStocks.filter((item) => item.ticker !== stock.ticker)
      : [...selectedStocks, stock];
    onSelectedStocksChange?.(nextStocks);
  };

  const closeDetails = () => {
    setDetailTicker("");
    setDetail(null);
    setDetailError("");
  };

  const handleViewStock = (ticker) => {
    setDetailTicker(ticker);
    setDetail(null);
    setDetailError("");
    setLoadingDetail(true);

    fetch(`http://127.0.0.1:5000/stocks/${ticker}/details`)
      .then((response) => {
        if (!response.ok) throw new Error(`Couldn't load details for ${ticker}`);
        return response.json();
      })
      .then(setDetail)
      .catch((error) => setDetailError(error.message))
      .finally(() => setLoadingDetail(false));
  };

  return (
    <main className="universe-page">
      <header className="universe-page-header">
        <div>
          <p className="universe-brand">RiskLens</p>
          <h1>NIFTY 50 Stock Universe</h1>
          <p className="universe-subtitle">Select stocks to build your optimized portfolio.</p>
        </div>
        <div className="universe-header-actions">
          {onBackToDashboard && <button className="universe-secondary-button" onClick={onBackToDashboard}>Back to Dashboard</button>}
          {onLogout && <button className="logout-btn" onClick={onLogout}>Logout</button>}
        </div>
      </header>

      <section className="selection-summary" aria-label="Portfolio selection summary">
        <div><span>NIFTY 50</span><strong>50 Stocks</strong></div>
        <div><span>Selected</span><strong>{selectedStocks.length} {selectedStocks.length === 1 ? "Stock" : "Stocks"}</strong></div>
        <div><span>Minimum Selection</span><strong>2 Stocks</strong></div>
        <div className={isReady ? "summary-ready" : "summary-pending"}><span>Portfolio Status</span><strong>{isReady ? "Ready" : "Select at least 2 stocks"}</strong></div>
      </section>

      <StockUniverseDashboard
        onSelectStock={handleSelectStock}
        onViewStock={handleViewStock}
        selectedTickers={selectedTickers}
      />

      <section className="portfolio-selection-panel">
        <div className="portfolio-selection-heading">
          <div>
            <h2>Portfolio Selection</h2>
            <p>{selectedStocks.length} {selectedStocks.length === 1 ? "stock" : "stocks"} selected</p>
          </div>
          <span className={isReady ? "selection-ready" : "selection-pending"}>{isReady ? "Ready to continue" : "2 stocks required"}</span>
        </div>
        <div className="selected-stock-chips">
          {selectedStocks.length ? selectedStocks.map((stock) => (
            <span key={stock.ticker} className={`selected-stock-chip ${stock.color || "yellow"}`}>
              {stock.ticker} <b>·</b> {stock.signal}
            </span>
          )) : <span className="no-stocks-selected">Your selected stocks will appear here.</span>}
        </div>
        <div className="portfolio-selection-footer">
          <p>{isReady ? "Your portfolio is ready for investment and risk setup." : "Select at least 2 stocks to continue."}</p>
          <button className="continue-portfolio-button" onClick={() => onBuildPortfolio(selectedStocks)} disabled={!isReady}>
            Continue to Investment & Risk →
          </button>
        </div>
      </section>

      {detailTicker && (
        <div className="stock-details-overlay" role="dialog" aria-modal="true" aria-label={`${detailTicker} stock details`}>
          <section className="stock-details-modal">
            <header className="stock-details-header">
              <div>
                <h2>{detailTicker}</h2>
                {detail?.composite?.sector && <span>{detail.composite.sector}</span>}
              </div>
              <div className="stock-details-header-summary">
                {detail?.composite && <><span className={`detail-signal-pill ${String(detail.composite.signal || "HOLD").toLowerCase()}`}>{detail.composite.signal}</span><span>{(Number(detail.composite.confidence || 0) * 100).toFixed(0)}% confidence</span><span>Risk: {detail.composite.risk_level}</span></>}
                <button className="stock-details-close" onClick={closeDetails} aria-label="Close stock details">×</button>
              </div>
            </header>
            <div className="stock-details-body">
              {loadingDetail && <div className="universe-feedback">Loading {detailTicker} details...</div>}
              {detailError && <div className="universe-feedback universe-error">{detailError}</div>}
              {detail && (
                <div className="stock-details-layout">
                  <section className="stock-chart-panel">
                    <div><h3>Price & Technical Trend</h3><p>Price action with SMA 20, SMA 50, and RSI.</p></div>
                    <CandlestickChart candles={detail.candles} overlays={detail.overlays} rsi={detail.rsi} markers={detail.markers} height={420} />
                  </section>
                  <StockDetailPanel composite={detail.composite} />
                </div>
              )}
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
