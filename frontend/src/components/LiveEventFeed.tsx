import { useEffect, useRef } from "react";
import { useCouncilStore } from "../stores/council";

export default function LiveEventFeed() {
  const {
    liveEvents,
    loadingStep,
    currentRound,
    totalRounds,
    isWebSocketConnected,
  } = useCouncilStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [liveEvents]);

  if (liveEvents.length === 0 && !loadingStep) {
    return null;
  }

  return (
    <div className="live-event-feed">
      <div className="feed-header">
        <h3>实时事件流</h3>
        <div className="connection-status">
          <span
            className={`status-dot ${isWebSocketConnected ? "connected" : "disconnected"}`}
          />
          {isWebSocketConnected ? "已连接" : "未连接"}
        </div>
      </div>

      {loadingStep && (
        <div className="current-step">
          <div className="step-spinner" />
          <span>{loadingStep}</span>
          {currentRound > 0 && totalRounds > 0 && (
            <span className="round-indicator">
              第 {currentRound}/{totalRounds} 轮
            </span>
          )}
        </div>
      )}

      <div className="event-list" ref={scrollRef}>
        {liveEvents.slice(-50).map((event, index) => (
          <div key={index} className={`event-item event-${event.type}`}>
            <span className="event-time">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
            <span className="event-type">{getEventLabel(event.type)}</span>
            <span className="event-data">{formatEventData(event)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function getEventLabel(type: string): string {
  const labels: Record<string, string> = {
    council_started: "议会开始",
    step_started: "步骤开始",
    step_completed: "步骤完成",
    seat_prevote: "席位预判",
    knife_cut: "餐刀切分",
    round_started: "轮次开始",
    seat_speaking: "席位发言",
    bell_update: "风铃更新",
    vote_update: "投票更新",
    conclusion: "结论生成",
    council_completed: "议会完成",
  };
  return labels[type] || type;
}

function formatEventData(event: { type: string; data: any }): string {
  const { type, data } = event;

  switch (type) {
    case "seat_prevote":
      return `${data.seat_name}: ${data.stance} (${(data.confidence * 100).toFixed(0)}%)`;
    case "seat_speaking":
      return `${data.seat_name} (${data.stance}): ${data.speech?.substring(0, 50)}...`;
    case "knife_cut":
      return `可见: ${data.visible_seats?.length || 0}席, 隐藏: ${data.hidden_seats?.length || 0}席`;
    case "bell_update":
      return `${data.seat_name}: 压力${data.stress}%, 健康${data.bell_health}%`;
    case "vote_update":
      return `支持: ${data.vote_map?.approve || 0}, 反对: ${data.vote_map?.oppose || 0}, 弃权: ${data.vote_map?.abstain || 0}`;
    default:
      return "";
  }
}
