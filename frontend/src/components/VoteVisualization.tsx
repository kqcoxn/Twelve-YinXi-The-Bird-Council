import type { VoteMap, SeatConfig } from "../types";

export default function VoteVisualization({
  votes,
  seats,
}: {
  votes?: VoteMap;
  seats?: SeatConfig[];
}) {
  const voteData = votes || { approve: 0, oppose: 0, abstain: 0 };
  const seatList = seats || [];

  const total = voteData.approve + voteData.oppose + voteData.abstain;
  const approvePct = total > 0 ? (voteData.approve / total) * 100 : 0;
  const opposePct = total > 0 ? (voteData.oppose / total) * 100 : 0;
  const abstainPct = total > 0 ? (voteData.abstain / total) * 100 : 0;

  return (
    <div className="vote-viz">
      <h3 className="viz-title">投票结果</h3>
      <div className="vote-summary">
        <div className="vote-bar">
          <div
            className="vote-segment support"
            style={{ width: `${approvePct}%` }}
          />
          <div
            className="vote-segment neutral"
            style={{ width: `${abstainPct}%` }}
          />
          <div
            className="vote-segment oppose"
            style={{ width: `${opposePct}%` }}
          />
        </div>
        <div className="vote-counts">
          <span className="count support">支持 {voteData.approve}</span>
          <span className="count neutral">弃权 {voteData.abstain}</span>
          <span className="count oppose">反对 {voteData.oppose}</span>
        </div>
      </div>
    </div>
  );
}
