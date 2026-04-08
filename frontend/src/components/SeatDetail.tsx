import { useState } from "react";
import type { SeatConfig, SeatState } from "../types";

interface SeatDetailProps {
  seat: SeatConfig;
  state?: SeatState;
  onClose: () => void;
}

export function SeatDetail({ seat, state, onClose }: SeatDetailProps) {
  const [activeTab, setActiveTab] = useState<"info" | "traits" | "phrases">(
    "info",
  );

  if (!seat) return null;

  const stanceText = (stance?: string) => {
    if (!stance) return "未设定";
    return stance === "approve"
      ? "赞成"
      : stance === "oppose"
        ? "反对"
        : "弃权";
  };

  const bellHealthColor = (health: number) => {
    if (health >= 70) return "#4ade80";
    if (health >= 40) return "#eab308";
    return "#ef4444";
  };

  return (
    <div className="seat-detail-overlay" onClick={onClose}>
      <div className="seat-detail" onClick={(e) => e.stopPropagation()}>
        <div className="seat-detail-header">
          <h2>
            <span className="seat-detail-id">{seat.seat_id}</span>
            {seat.name}
          </h2>
          <button className="seat-detail-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="seat-detail-tabs">
          <button
            className={activeTab === "info" ? "active" : ""}
            onClick={() => setActiveTab("info")}
          >
            信息
          </button>
          <button
            className={activeTab === "traits" ? "active" : ""}
            onClick={() => setActiveTab("traits")}
          >
            特质
          </button>
          <button
            className={activeTab === "phrases" ? "active" : ""}
            onClick={() => setActiveTab("phrases")}
          >
            语录
          </button>
        </div>

        <div className="seat-detail-content">
          {activeTab === "info" && (
            <div className="tab-info">
              <div className="info-row">
                <span className="info-label">原型</span>
                <span className="info-value">{seat.archetype}</span>
              </div>
              <div className="info-row">
                <span className="info-label">核心信念</span>
                <span className="info-value">{seat.core_belief}</span>
              </div>
              {state && (
                <>
                  <div className="info-row">
                    <span className="info-label">当前立场</span>
                    <span className="info-value">
                      {stanceText(state.current_stance)}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">信心</span>
                    <span className="info-value">
                      {(state.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">铃铛健康</span>
                    <span
                      className="info-value"
                      style={{ color: bellHealthColor(state.bell_health) }}
                    >
                      {state.bell_health}/100
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">压力</span>
                    <span className="info-value">{state.stress}/100</span>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === "traits" && (
            <div className="tab-traits">
              {Object.entries(seat.traits).map(([key, value]) => (
                <div key={key} className="trait-row">
                  <span className="trait-label">{key}</span>
                  <div className="trait-bar">
                    <div
                      className="trait-fill"
                      style={{ width: `${(value as number) * 100}%` }}
                    />
                  </div>
                  <span className="trait-value">
                    {((value as number) * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}

          {activeTab === "phrases" && (
            <div className="tab-phrases">
              {seat.example_phrases.map((phrase, idx) => (
                <blockquote key={idx} className="phrase-item">
                  "{phrase}"
                </blockquote>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
