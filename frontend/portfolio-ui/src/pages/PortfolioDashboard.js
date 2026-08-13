import "../styles/dashboard.css";

const dashboardStats = (selectedStockCount) => [
  { title: "NIFTY 50", value: "50 Stocks", description: "Available for selection" },
  { title: "Selected Stocks", value: String(selectedStockCount), description: "Stocks currently selected" },
  { title: "Portfolio Status", value: "Not Configured", description: "Start building your portfolio" }
];

const steps = [
  ["01", "Select Stocks", "Choose stocks from the NIFTY 50 universe."],
  ["02", "Set Investment", "Enter the amount you want to invest."],
  ["03", "Choose Risk", "Select your preferred risk level."],
  ["04", "Optimize", "Generate an optimized portfolio based on your choices."]
];

function PortfolioDashboard({ onLogout, onSelectStocks, selectedStockCount = 0 }) {
  return (
    <main className="dashboard-page portfolio-home-page">
      <header className="dashboard-header">
        <div>
          <p className="portfolio-home-brand">RiskLens · Portfolio Analytics</p>
          <h2>Portfolio Dashboard</h2>
          <p className="portfolio-home-welcome">Build, optimize, and manage your investment portfolio.</p>
        </div>
        {onLogout && <button className="logout-btn" onClick={onLogout}>Logout</button>}
      </header>

      <section className="portfolio-home-hero">
        <div>
          <span className="portfolio-home-card-icon">Portfolio intelligence</span>
          <h1>Make every allocation more deliberate.</h1>
          <p>Build, analyze and optimize a portfolio using NIFTY 50 market signals, technical indicators and ML-driven risk features.</p>
        </div>
      </section>

      <section className="portfolio-overview" aria-label="Portfolio overview">
        {dashboardStats(selectedStockCount).map((stat) => (
          <article className="portfolio-stat-card" key={stat.title}>
            <span>{stat.title}</span>
            <strong>{stat.value}</strong>
            <small>{stat.description}</small>
          </article>
        ))}
      </section>

      <section className="portfolio-home-card" aria-label="NIFTY 50 stock selection">
        <div className="portfolio-home-content">
          <div className="portfolio-home-card-icon">NIFTY 50</div>
          <h3>Select NIFTY 50 Stocks</h3>
          <p>Select stocks from the NIFTY 50 universe and create a portfolio based on your investment amount and risk preference.</p>
          <div className="portfolio-home-features"><span>50-stock universe</span><span>Technical + ML signals</span><span>Portfolio optimization</span></div>
          <button className="portfolio-home-select-btn" onClick={onSelectStocks}>Select Stocks →</button>
        </div>
        <div className="portfolio-chart-art" aria-hidden="true">
          <div className="portfolio-chart-grid" />
          <span className="portfolio-chart-line line-one" />
          <span className="portfolio-chart-line line-two" />
          <span className="portfolio-chart-dot dot-one" />
          <span className="portfolio-chart-dot dot-two" />
          <span className="portfolio-chart-dot dot-three" />
          <div className="portfolio-chart-bars"><i /><i /><i /><i /><i /></div>
        </div>
      </section>

      <section className="portfolio-how-it-works">
        <div className="portfolio-section-heading">
          <h3>How Portfolio Optimization Works</h3>
          <p>A simple path from stock selection to an optimized allocation.</p>
        </div>
        <div className="portfolio-steps">
          {steps.map(([number, title, description]) => (
            <article className="portfolio-step-card" key={number}>
              <span className="portfolio-step-number">{number}</span>
              <h4>{title}</h4>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="portfolio-ready-card">
        <div>
          <h3>Ready to build your portfolio?</h3>
          <p>Start by selecting stocks from the NIFTY 50 universe.</p>
        </div>
        <button className="portfolio-home-select-btn" onClick={onSelectStocks}>Start Building →</button>
      </section>
    </main>
  );
}

export default PortfolioDashboard;
