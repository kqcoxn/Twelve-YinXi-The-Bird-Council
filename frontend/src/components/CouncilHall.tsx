import { useState } from "react";
import { useCouncilStore } from "../stores/council";
import { useSeatsStore } from "../stores/seats";
import BellVisualization from "./BellVisualization";
import VoteVisualization from "./VoteVisualization";
import { DebateTranscript } from "./DebateTranscript";

type ViewMode = "dramatic" | "practical" | "psychological";

export default function CouncilHall() {
  const {
    session,
    conclusion,
    transcript,
    views,
    isLoading,
    loadingStep,
    error,
  } = useCouncilStore();
  const { seats, seatStates, setSelectedSeat } = useSeatsStore();
  const [activeView, setActiveView] = useState<ViewMode>("dramatic");

  if (!session && !isLoading) {
    return (
      <div className="council-hall">
        <h2 className="hall-title">群鸟议会</h2>
        <div className="hall-empty">暂无进行中的议题</div>
      </div>
    );
  }

  if (isLoading && !session) {
    return (
      <div className="council-hall loading">
        <div className="loading-spinner" />
        <p>{loadingStep || "处理中..."}</p>
      </div>
    );
  }

  if (!session) return null;

  const modeLabels: Record<string, string> = {
    light_chat: "轻聊模式",
    full_council: "完整议会",
    eternal_council: "永恒议会",
    safety_mode: "安全模式",
  };

  const stateLabels: Record<string, string> = {
    idle: "空闲",
    perceiving: "感知中",
    retrieving: "检索中",
    planning: "规划中",
    prevoting_23: "23席预判",
    knife_cutting: "餐刀切分",
    debating_12: "12席辩论",
    voting: "投票中",
    evaluating: "评估中",
    concluding: "生成结论",
    rendering: "渲染输出",
    output: "完成",
  };

  return (
    <div className="council-hall">
      <h2 className="hall-title">群鸟议会</h2>
      <div className="hall-session">
        <div className="session-header">
          <span className="session-id">Session: {session.id || "N/A"}</span>
          <span className="session-mode">
            {modeLabels[session.mode] || session.mode}
          </span>
          <span className="session-state">
            {stateLabels[session.orchestrator_state?.toLowerCase()] ||
              session.orchestrator_state}
          </span>
          {session.round > 0 && (
            <span className="session-round">{session.round}轮</span>
          )}
        </div>

        <div className="session-content">
          {/* Debate Transcript */}
          {transcript && transcript.total_speeches > 0 && (
            <DebateTranscript transcript={transcript} />
          )}

          {/* Bell & Vote */}
          <div className="session-visualizations">
            {session.bell_state && (
              <BellVisualization
                stressLevel={session.bell_state.stress_level}
                fractureRisk={session.bell_state.fracture_risk}
              />
            )}
            {session.vote_map && seats && seats.length > 0 && (
              <VoteVisualization votes={session.vote_map} seats={seats} />
            )}
          </div>

          {/* Conclusion */}
          {conclusion && (
            <div className="session-conclusion">
              <h4>结论</h4>
              <div className="conclusion-decision">
                <span className={`decision-badge ${conclusion.decision}`}>
                  {conclusion.decision === "approve" && "建议支持"}
                  {conclusion.decision === "oppose" && "建议反对"}
                  {conclusion.decision === "conditional" && "有条件支持"}
                  {conclusion.decision === "delay" && "建议暂缓"}
                </span>
              </div>
              <p className="conclusion-summary">{conclusion.summary}</p>

              {conclusion.main_reasons.length > 0 && (
                <div className="conclusion-reasons">
                  <h5>主要原因</h5>
                  <ul>
                    {conclusion.main_reasons.map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              {conclusion.risks.length > 0 && (
                <div className="conclusion-risks">
                  <h5>风险提示</h5>
                  <ul>
                    {conclusion.risks.map((risk, idx) => (
                      <li key={idx} className="risk-item">
                        {risk}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {conclusion.minority_opinion && (
                <div className="conclusion-minority">
                  <h5>少数派观点</h5>
                  <p>{conclusion.minority_opinion}</p>
                </div>
              )}
            </div>
          )}

          {/* Multi-view toggle */}
          {views && Object.values(views).some(Boolean) && (
            <div className="session-views">
              <div className="view-tabs">
                <button
                  className={activeView === "dramatic" ? "active" : ""}
                  onClick={() => setActiveView("dramatic")}
                >
                  戏剧视角
                </button>
                <button
                  className={activeView === "practical" ? "active" : ""}
                  onClick={() => setActiveView("practical")}
                >
                  实用视角
                </button>
                <button
                  className={activeView === "psychological" ? "active" : ""}
                  onClick={() => setActiveView("psychological")}
                >
                  心理视角
                </button>
              </div>
              <div className="view-content">
                {views[activeView] ? (
                  <div className="view-text">{views[activeView]}</div>
                ) : (
                  <div className="view-empty">该视角内容暂不可用</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
