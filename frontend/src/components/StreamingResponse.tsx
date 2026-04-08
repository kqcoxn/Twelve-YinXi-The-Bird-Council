import { useState, useCallback } from "react";
import { sseClient, SSEEvent } from "../api/sse";

interface StreamingResponseProps {
  proposal: string;
  category?: string;
  onComplete?: (result: any) => void;
}

export default function StreamingResponse({
  proposal,
  category,
  onComplete,
}: StreamingResponseProps) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [content, setContent] = useState("");
  const [conclusion, setConclusion] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStream = useCallback(async () => {
    setIsStreaming(true);
    setContent("");
    setConclusion(null);
    setError(null);

    try {
      const result = await sseClient.streamProposal(
        proposal,
        category,
        (event: SSEEvent) => {
          switch (event.type) {
            case "token":
              if (event.content) {
                setContent((prev) => prev + event.content);
              }
              break;
            case "conclusion":
              if (event.data) {
                setConclusion(event.data);
                if (onComplete) onComplete(event.data);
              }
              break;
            case "complete":
              setIsStreaming(false);
              break;
            case "error":
              setError(event.message || "Streaming failed");
              setIsStreaming(false);
              break;
          }
        },
      );

      if (result && !conclusion) {
        setConclusion(result);
        if (onComplete) onComplete(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setIsStreaming(false);
    }
  }, [proposal, category, onComplete]);

  return (
    <div className="streaming-response">
      <button
        className="stream-btn"
        onClick={handleStream}
        disabled={isStreaming || !proposal.trim()}
      >
        {isStreaming ? "流式生成中..." : "流式响应"}
      </button>

      {isStreaming && (
        <div className="stream-content">
          <div className="typewriter-effect">{content}</div>
          <div className="stream-cursor" />
        </div>
      )}

      {conclusion && (
        <div className="conclusion-result">
          <h4>结论</h4>
          <p>{conclusion.summary || conclusion.content}</p>
          {conclusion.main_reasons && (
            <div className="conclusion-reasons">
              <h5>主要理由</h5>
              <ul>
                {conclusion.main_reasons.map((reason: string, i: number) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
          {conclusion.risks && (
            <div className="conclusion-risks">
              <h5>风险提示</h5>
              <ul>
                {conclusion.risks.map((risk: string, i: number) => (
                  <li key={i} className="risk-item">
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}
    </div>
  );
}
