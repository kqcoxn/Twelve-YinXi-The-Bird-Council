import { useCouncilStore } from "../stores/council";
import BellVisualization from "./BellVisualization";
import VoteVisualization from "./VoteVisualization";

export default function CouncilHall() {
  const { session, isLoading } = useCouncilStore();

  if (!session && !isLoading) {
    return (
      <div className="council-hall">
        <h2 className="hall-title">群鸟议会</h2>
        <div className="hall-empty">暂无进行中的议题</div>
      </div>
    );
  }

  if (isLoading && !session) {
    return <div className="council-hall loading">加载中...</div>;
  }

  if (!session) return null;

  return (
    <div className="council-hall">
      <h2 className="hall-title">群鸟议会</h2>
      <div className="hall-session">
        <div className="session-header">
          <span className="session-id">Session: {session.id}</span>
          <span className="session-state">{session.state}</span>
        </div>
        <div className="session-content">
          <div className="session-proposal">
            <h4>议题</h4>
            <p>{session.proposal}</p>
          </div>
          {session.bell_state && (
            <BellVisualization
              stressLevel={session.bell_state.stress_level}
              fractureRisk={session.bell_state.fracture_risk}
            />
          )}
          {session.vote_map && session.seats && (
            <VoteVisualization votes={session.vote_map} seats={session.seats} />
          )}
          {session.conclusion && (
            <div className="session-conclusion">
              <h4>结论</h4>
              <p>{session.conclusion.summary}</p>
              {session.conclusion.narrative && (
                <div className="narrative">
                  <p>{session.conclusion.narrative}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
