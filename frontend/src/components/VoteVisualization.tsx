import type { VoteMap, SeatConfig } from "../types";

export default function VoteVisualization({
  votes,
  seats,
}: {
  votes?: VoteMap;
  seats?: SeatConfig[];
}) {
  const voteData = votes || {};
  const seatList = seats || [];

  const counts = { support: 0, oppose: 0, neutral: 0 };
  Object.entries(voteData).forEach(([_, vote]) => {
    if (vote === 1) counts.support++;
    else if (vote === -1) counts.oppose++;
    else counts.neutral++;
  });

  const total = counts.support + counts.oppose + counts.neutral;
  const supportPct = total > 0 ? (counts.support / total) * 100 : 0;
  const opposePct = total > 0 ? (counts.oppose / total) * 100 : 0;

  return (
    <div className="vote-viz">
      <h3 className="viz-title">投票结果</h3>
      <div className="vote-summary">
        <div className="vote-bar">
          <div
            className="vote-segment support"
            style={{ width: `${supportPct}%` }}
          />
          <div
            className="vote-segment neutral"
            style={{ width: `${100 - supportPct - opposePct}%` }}
          />
          <div
            className="vote-segment oppose"
            style={{ width: `${opposePct}%` }}
          />
        </div>
        <div className="vote-counts">
          <span className="count support">支持 {counts.support}</span>
          <span className="count neutral">中立 {counts.neutral}</span>
          <span className="count oppose">反对 {counts.oppose}</span>
        </div>
      </div>
      <div className="vote-details">
        {seatList.map((seat) => {
          const vote = voteData[seat.id];
          const voteLabel =
            vote === 1
              ? "支持"
              : vote === -1
                ? "反对"
                : vote === 0
                  ? "中立"
                  : "未投票";
          const voteClass =
            vote === 1
              ? "support"
              : vote === -1
                ? "oppose"
                : vote === 0
                  ? "neutral"
                  : "";
          return (
            <div key={seat.id} className="vote-row">
              <span className="vote-seat">{seat.name}</span>
              <span className={`vote-result ${voteClass}`}>{voteLabel}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
