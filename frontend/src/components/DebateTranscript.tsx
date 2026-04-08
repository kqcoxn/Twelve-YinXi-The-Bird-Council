import type { DebateTranscript, SpeechRecord } from "../types";

interface DebateTranscriptProps {
  transcript: DebateTranscript;
}

const stanceColors: Record<string, string> = {
  approve: "#4ade80",
  oppose: "#ef4444",
  abstain: "#64748b",
};

const stanceLabels: Record<string, string> = {
  approve: "赞成",
  oppose: "反对",
  abstain: "弃权",
};

export function DebateTranscript({ transcript }: DebateTranscriptProps) {
  if (!transcript.rounds || transcript.rounds.length === 0) {
    return (
      <div className="transcript-empty">
        <p>辩论记录为空</p>
      </div>
    );
  }

  return (
    <div className="debate-transcript">
      <div className="transcript-header">
        <h3>辩论记录</h3>
        <span className="transcript-stats">
          {transcript.rounds.length} 轮 / {transcript.total_speeches} 次发言
        </span>
      </div>

      <div className="transcript-content">
        {transcript.rounds.map((round) => (
          <div key={round.round_num} className="transcript-round">
            <div className="round-header">第 {round.round_num} 轮</div>
            <div className="round-speeches">
              {round.speeches.map((speech, idx) => (
                <SpeechCard key={idx} speech={speech} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SpeechCard({ speech }: { speech: SpeechRecord }) {
  const color = stanceColors[speech.stance] || "#94a3b8";
  const label = stanceLabels[speech.stance] || speech.stance;

  return (
    <div className="speech-card" style={{ borderLeftColor: color }}>
      <div className="speech-header">
        <span className="speech-seat" style={{ color }}>
          {speech.seat_name}
        </span>
        <span className="speech-stance" style={{ backgroundColor: color }}>
          {label}
        </span>
        <span className="speech-confidence">
          {(speech.confidence * 100).toFixed(0)}%
        </span>
      </div>
      <div className="speech-text">{speech.speech}</div>
    </div>
  );
}
