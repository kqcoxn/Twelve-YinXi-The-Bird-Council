import type { SeatState } from "../types";

export default function BellVisualization({
  stressLevel,
  fractureRisk,
}: {
  stressLevel?: number;
  fractureRisk?: number;
}) {
  const stress = stressLevel ?? 0;
  const risk = fractureRisk ?? 0;

  const getBellState = () => {
    if (stress >= 80) return { label: "CRITICAL", color: "#ef4444" };
    if (stress >= 60) return { label: "STRESSED", color: "#f59e0b" };
    if (stress >= 40) return { label: "WARNING", color: "#eab308" };
    return { label: "HEALTHY", color: "#4ade80" };
  };

  const bellState = getBellState();

  return (
    <div className="bell-viz">
      <h3 className="viz-title">Bell 状态</h3>
      <div className="bell-content">
        <div
          className="bell-indicator"
          style={{ borderColor: bellState.color }}
        >
          <div className="bell-status" style={{ color: bellState.color }}>
            {bellState.label}
          </div>
          <div className="bell-ring">
            <svg viewBox="0 0 100 100" className="bell-svg">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={bellState.color}
                strokeWidth="2"
              />
              <circle
                cx="50"
                cy="50"
                r={35 + (stress / 100) * 10}
                fill={bellState.color}
                opacity={0.2 + (stress / 100) * 0.3}
              />
              <text
                x="50"
                y="55"
                textAnchor="middle"
                fill={bellState.color}
                fontSize="20"
                fontWeight="bold"
              >
                {stress}%
              </text>
            </svg>
          </div>
        </div>
        <div className="bell-metrics">
          <div className="metric">
            <span className="metric-label">压力水平</span>
            <span className="metric-value" style={{ color: bellState.color }}>
              {stress}%
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">断裂风险</span>
            <span
              className="metric-value"
              style={{ color: risk > 70 ? "#ef4444" : "#94a3b8" }}
            >
              {risk}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
