import { useState } from "react";

const SIGNAL_CLASS = { BUY: "buy", SELL: "sell", HOLD: "hold" };

function SignalPill({ children, signal = "HOLD" }) {
  return <span className={`detail-signal-pill ${SIGNAL_CLASS[signal] || "hold"}`}>{children}</span>;
}

function IndicatorRow({ label, value, detail }) {
  return <div className="detail-indicator-row"><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</div>;
}

const labelFor = (key) => ({ stochastic: "Stochastic", williams_r: "Williams %R", obv: "OBV", roc: "ROC" }[key] || key.replaceAll("_", " "));

export default function StockDetailPanel({ composite }) {
  const [activeTab, setActiveTab] = useState("snapshot");
  if (!composite) return <div className="detail-empty">No recommendation data available for this stock yet.</div>;

  const { signal, confidence, expected_return, risk_level, cvar_95, components } = composite;
  const ml = components?.ml || {};
  const leading = components?.leading || {};
  const lagging = components?.lagging || {};
  const leadingEntries = Object.entries(leading.detail || {}).filter(([key]) => key !== "india_vix");
  const vix = leading.detail?.india_vix;

  return (
    <section className="stock-detail-panel" aria-label="Stock analysis details">
      <div className="stock-detail-tabs" role="tablist" aria-label="Stock analysis sections">
        <button type="button" className={activeTab === "snapshot" ? "active" : ""} onClick={() => setActiveTab("snapshot")} role="tab" aria-selected={activeTab === "snapshot"}>Investment Snapshot</button>
        <button type="button" className={activeTab === "ml" ? "active" : ""} onClick={() => setActiveTab("ml")} role="tab" aria-selected={activeTab === "ml"}>ML Model</button>
        <button type="button" className={activeTab === "technical" ? "active" : ""} onClick={() => setActiveTab("technical")} role="tab" aria-selected={activeTab === "technical"}>Technical Evidence</button>
      </div>

      <div className="stock-detail-tab-content">
        {activeTab === "snapshot" && <section className="detail-signal-summary">
          <div className="snapshot-primary"><strong className={`detail-signal ${SIGNAL_CLASS[signal] || "hold"}`}>{signal}</strong><SignalPill signal={signal}>{(confidence * 100).toFixed(0)}% Confidence</SignalPill><span className="detail-risk">Risk: {risk_level}</span></div>
          <div className="detail-key-metrics"><div><span>Expected Return</span><strong>{(expected_return * 100).toFixed(1)}%</strong></div><div><span>CVaR (95%)</span><strong>{(cvar_95 * 100).toFixed(1)}%</strong></div></div>
        </section>}

        {activeTab === "ml" && <section className="detail-tab-panel">
          <div className="detail-model-meta"><span>Signal <SignalPill signal={ml.signal}>{ml.signal || "—"}</SignalPill></span><span>Confidence <b>{ml.confidence == null ? "—" : `${(ml.confidence * 100).toFixed(0)}%`}</b></span></div>
          <div className="detail-probabilities">{Object.entries(ml.probabilities || {}).map(([key, value]) => <div key={key}><span>{key}</span><i><b style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} /></i><strong>{(value * 100).toFixed(0)}%</strong></div>)}</div>
          {ml.top_factors?.length > 0 && <details className="detail-factors-disclosure" open><summary>Top Factors</summary><div className="detail-factors">{ml.top_factors.map(([feature, value]) => <span key={feature}>{feature.replaceAll("_", " ")}<em className={value >= 0 ? "positive" : "negative"}>{value >= 0 ? "+" : ""}{value.toFixed(3)}</em></span>)}</div></details>}
        </section>}

        {activeTab === "technical" && <section className="detail-tab-panel technical-tab-panel">
          <section className="detail-indicator-group"><h4>Lagging Indicators <SignalPill signal={lagging.signal}>{lagging.signal || "—"}</SignalPill></h4><IndicatorRow label="RSI" value={lagging.rsi ?? "—"} /><IndicatorRow label="SMA 20" value={lagging.sma20 ?? "—"} /><IndicatorRow label="SMA 50" value={lagging.sma50 ?? "—"} /><IndicatorRow label="10-day Momentum" value={lagging.momentum_10d == null ? "—" : `${(Number(lagging.momentum_10d) * 100).toFixed(2)}%`} /></section>
          <section className="detail-indicator-group"><h4>Leading Indicators <SignalPill signal={leading.signal}>{leading.signal || "—"}</SignalPill></h4>{leadingEntries.map(([key, value]) => <IndicatorRow key={key} label={labelFor(key)} value={typeof value === "object" ? "—" : String(value)} />)}<IndicatorRow label="India VIX" value={vix?.current ?? "—"} detail={vix?.regime ? `${vix.regime} regime` : undefined} /></section>
        </section>}
      </div>
    </section>
  );
}
