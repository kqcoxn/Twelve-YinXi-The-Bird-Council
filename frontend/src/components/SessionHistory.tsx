import { useState, useEffect } from "react";
import * as api from "../api/client";

interface SessionHistoryProps {
  userId?: string;
  onSelectSession?: (caseId: string) => void;
}

export default function SessionHistory({
  userId = "default_user",
  onSelectSession,
}: SessionHistoryProps) {
  const [sessions, setSessions] = useState<
    api.CouncilHistoryResponse["sessions"]
  >([]);
  const [pagination, setPagination] = useState<
    api.CouncilHistoryResponse["pagination"] | null
  >(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchHistory = async (offset: number = 0) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getCouncilHistory(userId, 20, offset);
      setSessions(data.sessions);
      setPagination(data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch history");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [userId]);

  const handleLoadMore = () => {
    if (pagination?.has_more) {
      fetchHistory(pagination.offset + pagination.limit);
    }
  };

  if (isLoading && sessions.length === 0) {
    return <div className="session-history loading">加载中...</div>;
  }

  if (error) {
    return <div className="session-history error">{error}</div>;
  }

  if (sessions.length === 0) {
    return <div className="session-history empty">暂无历史议题</div>;
  }

  return (
    <div className="session-history">
      <h3 className="history-title">历史议题</h3>

      <div className="session-list">
        {sessions.map((session) => (
          <div
            key={session.case_id}
            className={`session-item ${expandedId === session.case_id ? "expanded" : ""}`}
          >
            <div
              className="session-header"
              onClick={() =>
                setExpandedId(
                  expandedId === session.case_id ? null : session.case_id,
                )
              }
            >
              <div className="session-title-text">
                {session.proposal_title || "无标题议题"}
              </div>
              <div className="session-meta">
                <span className="session-date">
                  {new Date(session.created_at).toLocaleDateString()}
                </span>
                {session.triggered_fracture && (
                  <span className="badge fracture">断裂</span>
                )}
                {session.triggered_reconsider && (
                  <span className="badge reconsider">复议</span>
                )}
              </div>
            </div>

            {expandedId === session.case_id && (
              <div className="session-details">
                {session.conclusion && (
                  <div className="detail-section">
                    <h5>结论</h5>
                    <p>{session.conclusion}</p>
                  </div>
                )}
                {session.minority_opinion && (
                  <div className="detail-section minority">
                    <h5>少数意见</h5>
                    <p>{session.minority_opinion}</p>
                  </div>
                )}
                {onSelectSession && (
                  <button
                    className="view-full-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectSession(session.case_id);
                    }}
                  >
                    查看完整记录
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {pagination?.has_more && (
        <button className="load-more-btn" onClick={handleLoadMore}>
          加载更多 ({pagination.total - pagination.offset - pagination.limit}{" "}
          条)
        </button>
      )}
    </div>
  );
}
