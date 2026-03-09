function TooltipIcon({ text }) {
  return (
    <span className="tooltip-icon-wrapper" tabIndex={0} aria-label={text}>
      <span className="info-icon" aria-hidden="true">i</span>
      <span className="tooltip-bubble">{text}</span>
    </span>
  );
}

export default TooltipIcon;
