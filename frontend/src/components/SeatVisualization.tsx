import { useEffect, useState } from "react";
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

function SeatNode({
  seat,
  state,
  onClick,
}: {
  seat: SeatConfig;
  state?: SeatState;
  onClick: () => void;
}) {
  const status = state?.status || "active";
  const stress = state?.stress ?? 0;
  const color = statusColors[status] || statusColors.active;

  return (
    <div
      className="seat-node"
      style={{ borderColor: color, cursor: "pointer" }}
      onClick={onClick}
    >
      <div className="seat-icon" style={{ backgroundColor: color }}>
        <span className="seat-id">{seat.seat_id}</span>
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
  const { seats, seatStates, fetchSeats, setSelectedSeat } = useSeatsStore();
  const [selectedSeatId, setSelectedSeatId] = useState<string | null>(null);

  useEffect(() => {
    fetchSeats();
  }, [fetchSeats]);

  if (!seats.length) return <div className="loading">加载中...</div>;

  const selectedSeat = seats.find((s) => s.seat_id === selectedSeatId) || null;
  const selectedState = selectedSeatId ? seatStates[selectedSeatId] : undefined;

  return (
    <div className="seat-viz">
      <h3 className="viz-title">23 席位状态</h3>
      <div className="seats-grid">
        {seats.map((seat) => (
          <SeatNode
            key={seat.seat_id}
            seat={seat}
            state={seatStates[seat.seat_id]}
            onClick={() => {
              setSelectedSeat(seat.seat_id);
              setSelectedSeatId(seat.seat_id);
            }}
          />
        ))}
      </div>

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
