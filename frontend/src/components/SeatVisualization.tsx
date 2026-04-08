import { useEffect, useState, useMemo } from "react";
import { useSeatsStore } from "../stores/seats";
import { SeatDetail } from "./SeatDetail";
import type { SeatConfig, SeatState } from "../types";

const statusColors: Record<string, string> = {
  active: "#4ade80",
  silent: "#94a3b8",
  fractured: "#ef4444",
  exiled: "#64748b",
  shadow: "#6b7280",
};

interface SeatNodeProps {
  seat: SeatConfig;
  state?: SeatState;
  onClick: () => void;
  x: number;
  y: number;
  angle: number;
}

function CircularSeatNode({
  seat,
  state,
  onClick,
  x,
  y,
  angle,
}: SeatNodeProps) {
  const status = state?.status || "active";
  const stress = state?.stress ?? 0;
  const color = statusColors[status] || statusColors.active;
  const pulseScale =
    1 + Math.sin(Date.now() * 0.003 + angle) * (stress / 100) * 0.15;

  return (
    <g
      className="circular-seat-node"
      transform={`translate(${x}, ${y}) scale(${pulseScale})`}
      onClick={onClick}
      style={{ cursor: "pointer" }}
    >
      {/* Outer glow ring */}
      <circle
        r="18"
        fill="none"
        stroke={color}
        strokeWidth="2"
        opacity="0.3"
        className="seat-glow"
      />

      {/* Main seat circle */}
      <circle r="14" fill={color} opacity="0.8" className="seat-circle" />

      {/* Inner stress indicator */}
      {stress > 0 && (
        <circle
          r={8 + (stress / 100) * 6}
          fill="none"
          stroke={color}
          strokeWidth="1"
          opacity={0.4 + (stress / 100) * 0.4}
          className="stress-ring"
        />
      )}

      {/* Seat number */}
      <text
        y="4"
        textAnchor="middle"
        fill="#0a0a0f"
        fontSize="10"
        fontWeight="bold"
        className="seat-number"
      >
        {seat.seat_id.replace("seat_", "")}
      </text>

      {/* Seat name label */}
      <text
        y="28"
        textAnchor="middle"
        fill={color}
        fontSize="8"
        className="seat-name-label"
      >
        {seat.name}
      </text>
    </g>
  );
}

export default function SeatVisualization() {
  const { seats, seatStates, fetchSeats, setSelectedSeat } = useSeatsStore();
  const [selectedSeatId, setSelectedSeatId] = useState<string | null>(null);
  const [animationPhase, setAnimationPhase] = useState(0);
  const [viewMode, setViewMode] = useState<"circular" | "grid">("circular");

  useEffect(() => {
    fetchSeats();
  }, [fetchSeats]);

  // Animation loop
  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationPhase((prev) => (prev + 1) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Calculate circular layout positions
  const circularPositions = useMemo(() => {
    if (seats.length === 0) return [];

    const centerX = 300;
    const centerY = 300;
    const radius = 220;

    return seats.map((seat, index) => {
      const angle = (index / seats.length) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      return { seat, x, y, angle: (angle * 180) / Math.PI };
    });
  }, [seats]);

  if (!seats.length) return <div className="loading">加载中...</div>;

  const selectedSeat = seats.find((s) => s.seat_id === selectedSeatId) || null;
  const selectedState = selectedSeatId ? seatStates[selectedSeatId] : undefined;

  return (
    <div className="seat-viz">
      <div className="viz-header">
        <h3 className="viz-title">23 席位状态</h3>
        <div className="view-toggle">
          <button
            className={`toggle-btn ${viewMode === "circular" ? "active" : ""}`}
            onClick={() => setViewMode("circular")}
          >
            圆形
          </button>
          <button
            className={`toggle-btn ${viewMode === "grid" ? "active" : ""}`}
            onClick={() => setViewMode("grid")}
          >
            网格
          </button>
        </div>
      </div>

      {viewMode === "circular" ? (
        <div className="circular-layout">
          <svg viewBox="0 0 600 600" className="circular-svg">
            <defs>
              <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
              </radialGradient>
              <filter id="seatGlow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Center glow */}
            <circle cx="300" cy="300" r="150" fill="url(#centerGlow)" />

            {/* Center text */}
            <text
              x="300"
              y="295"
              textAnchor="middle"
              fill="#e4e4e7"
              fontSize="24"
              fontWeight="bold"
            >
              群鸟议会
            </text>
            <text
              x="300"
              y="320"
              textAnchor="middle"
              fill="#a1a1aa"
              fontSize="12"
            >
              23 Seats
            </text>

            {/* Connection lines between seats */}
            {circularPositions.map(({ x, y }, i) => {
              const nextIndex = (i + 1) % circularPositions.length;
              const next = circularPositions[nextIndex];
              return (
                <line
                  key={`line-${i}`}
                  x1={x}
                  y1={y}
                  x2={next.x}
                  y2={next.y}
                  stroke="#2a2a3a"
                  strokeWidth="1"
                  opacity="0.5"
                />
              );
            })}

            {/* Seat nodes */}
            {circularPositions.map(({ seat, x, y, angle }) => (
              <CircularSeatNode
                key={seat.seat_id}
                seat={seat}
                state={seatStates[seat.seat_id]}
                x={x}
                y={y}
                angle={angle}
                onClick={() => {
                  setSelectedSeat(seat.seat_id);
                  setSelectedSeatId(seat.seat_id);
                }}
              />
            ))}
          </svg>
        </div>
      ) : (
        <div className="seats-grid">
          {seats.map((seat) => (
            <div
              key={seat.seat_id}
              className="seat-node"
              style={{
                borderColor:
                  statusColors[seatStates[seat.seat_id]?.status || "active"],
                cursor: "pointer",
              }}
              onClick={() => {
                setSelectedSeat(seat.seat_id);
                setSelectedSeatId(seat.seat_id);
              }}
            >
              <div
                className="seat-icon"
                style={{
                  backgroundColor:
                    statusColors[seatStates[seat.seat_id]?.status || "active"],
                }}
              >
                <span className="seat-id">{seat.seat_id}</span>
              </div>
              <div className="seat-info">
                <div className="seat-name">{seat.name}</div>
                {seatStates[seat.seat_id]?.stress &&
                  seatStates[seat.seat_id]!.stress > 0 && (
                    <div className="stress-bar">
                      <div
                        className="stress-fill"
                        style={{
                          width: `${Math.min(seatStates[seat.seat_id]!.stress, 100)}%`,
                        }}
                      />
                    </div>
                  )}
              </div>
              <div
                className="seat-status"
                style={{
                  color:
                    statusColors[seatStates[seat.seat_id]?.status || "active"],
                }}
              >
                {seatStates[seat.seat_id]?.status || "active"}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedSeat && (
        <SeatDetail
          seat={selectedSeat}
          state={selectedState}
          onClose={() => setSelectedSeatId(null)}
        />
      )}
    </div>
  );
}
