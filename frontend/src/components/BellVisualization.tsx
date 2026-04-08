import { useEffect, useState } from "react";
import type { SeatState } from "../types";

export default function BellVisualization({
  stressLevel,
  fractureRisk,
  seatName,
}: {
  stressLevel?: number;
  fractureRisk?: number;
  seatName?: string;
}) {
  const stress = stressLevel ?? 0;
  const risk = fractureRisk ?? 0;
  const [animationPhase, setAnimationPhase] = useState(0);
  const [particles, setParticles] = useState<
    Array<{ id: number; x: number; y: number; opacity: number }>
  >([]);

  // Animate bell swing based on stress
  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationPhase((prev) => (prev + 1) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Generate stress particles
  useEffect(() => {
    if (stress > 40) {
      const particleCount = Math.floor((stress - 40) / 10);
      const newParticles = Array.from({ length: particleCount }, (_, i) => ({
        id: Date.now() + i,
        x: 50 + Math.sin((animationPhase + i * 45) * (Math.PI / 180)) * 40,
        y: 50 + Math.cos((animationPhase + i * 45) * (Math.PI / 180)) * 40,
        opacity: 0.3 + (stress / 100) * 0.7,
      }));
      setParticles(newParticles);
    } else {
      setParticles([]);
    }
  }, [stress, animationPhase]);

  const getBellState = () => {
    if (stress >= 80) return { label: "CRITICAL", color: "#ef4444" };
    if (stress >= 60) return { label: "STRESSED", color: "#f59e0b" };
    if (stress >= 40) return { label: "WARNING", color: "#eab308" };
    return { label: "HEALTHY", color: "#4ade80" };
  };

  const bellState = getBellState();
  const swingAngle =
    Math.sin(animationPhase * (Math.PI / 180)) * (stress / 100) * 15;
  const crackOpacity = risk / 100;

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
              <defs>
                <radialGradient
                  id={`bellGrad-${stress}`}
                  cx="50%"
                  cy="50%"
                  r="50%"
                >
                  <stop
                    offset="0%"
                    stopColor={bellState.color}
                    stopOpacity="0.8"
                  />
                  <stop
                    offset="100%"
                    stopColor={bellState.color}
                    stopOpacity="0.2"
                  />
                </radialGradient>
                <filter id={`glow-${stress}`}>
                  <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              {/* Outer ring with swing animation */}
              <g transform={`rotate(${swingAngle}, 50, 50)`}>
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke={bellState.color}
                  strokeWidth="2"
                  filter={`url(#glow-${stress})`}
                />

                {/* Inner pulsing circle */}
                <circle
                  cx="50"
                  cy="50"
                  r={35 + Math.sin(animationPhase * 0.1) * (stress / 100) * 10}
                  fill={`url(#bellGrad-${stress})`}
                  opacity={0.2 + (stress / 100) * 0.3}
                />

                {/* Stress particles */}
                {particles.map((particle) => (
                  <circle
                    key={particle.id}
                    cx={particle.x}
                    cy={particle.y}
                    r="2"
                    fill={bellState.color}
                    opacity={particle.opacity}
                  />
                ))}

                {/* Crack effect for high fracture risk */}
                {risk > 50 && (
                  <g opacity={crackOpacity}>
                    <line
                      x1="30"
                      y1="30"
                      x2="70"
                      y2="70"
                      stroke="#ef4444"
                      strokeWidth="1.5"
                    />
                    <line
                      x1="50"
                      y1="20"
                      x2="50"
                      y2="80"
                      stroke="#ef4444"
                      strokeWidth="1"
                    />
                    <line
                      x1="20"
                      y1="50"
                      x2="80"
                      y2="50"
                      stroke="#ef4444"
                      strokeWidth="1"
                    />
                  </g>
                )}

                {/* Stress text */}
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
              </g>
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
