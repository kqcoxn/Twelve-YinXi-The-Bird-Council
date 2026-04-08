import { useEffect } from "react";
import { useSeatsStore } from "../stores/seats";
import type { SeatConfig, SeatState } from "../types";

const statusColors: Record<string, string> = {
  listening: "#4ade80",
  speaking: "#f59e0b",
  prevoting: "#60a5fa",
  debating: "#c084fc",
  voting: "#f472b6",
  resting: "#94a3b8",
  abstaining: "#64748b",
  fractured: "#ef4444",
};

function SeatNode({ seat, state }: { seat: SeatConfig; state?: SeatState }) {
  const status = state?.status || "resting";
  const stress = state?.bell_state?.stress_level ?? 0;
  const color = statusColors[status] || statusColors.resting;

  return (
    <div className="seat-node" style={{ borderColor: color }}>
      <div className="seat-icon" style={{ backgroundColor: color }}>
        <span className="seat-id">{seat.id}</span>
      </div>
      <div className="seat-info">
        <div className="seat-name">{seat.name}</div>
        {stress > 0 && (
          <div className="stress-bar">
            <div
              className="stress-fill"
              style={{ width: `${Math.min(stress, 100)}%` }}
            />
          </div>
        )}
      </div>
      <div className="seat-status" style={{ color }}>
        {status}
      </div>
    </div>
  );
}

export default function SeatVisualization() {
  const { seats, seatStates, fetchSeats } = useSeatsStore();

  useEffect(() => {
    fetchSeats();
  }, [fetchSeats]);

  if (!seats.length) return <div className="loading">加载中...</div>;

  return (
    <div className="seat-viz">
      <h3 className="viz-title">23 席位状态</h3>
      <div className="seats-grid">
        {seats.map((seat) => (
          <SeatNode key={seat.id} seat={seat} state={seatStates[seat.id]} />
        ))}
      </div>
    </div>
  );
}
