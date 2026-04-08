import { useState } from "react";
import { useCouncilStore } from "../stores/council";

export default function InputPanel() {
  const [proposal, setProposal] = useState("");
  const [category, setCategory] = useState("");
  const { submitProposal, isLoading, error, clearError } = useCouncilStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!proposal.trim() || isLoading) return;
    clearError();
    await submitProposal(proposal.trim(), category || undefined);
    // Only clear form on success (handled by store)
    if (!error) {
      setProposal("");
      setCategory("");
    }
  };

  const handleRetry = () => {
    clearError();
    if (proposal.trim()) {
      submitProposal(proposal.trim(), category || undefined);
    }
  };

  return (
    <div className="input-panel">
      <h2 className="panel-title">提交议题</h2>
      <form onSubmit={handleSubmit} className="input-form">
        <textarea
          className="proposal-input"
          placeholder="输入你的议题或提案..."
          value={proposal}
          onChange={(e) => setProposal(e.target.value)}
          rows={6}
          disabled={isLoading}
        />
        <input
          className="category-input"
          placeholder="分类（可选）"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="submit-btn"
          disabled={isLoading || !proposal.trim()}
        >
          {isLoading ? "处理中..." : "提交议题"}
        </button>
      </form>

      {isLoading && (
        <div className="loading-indicator">
          <div className="loading-spinner" />
          <span>议会正在讨论中...</span>
        </div>
      )}

      {error && (
        <div className="error-msg">
          <p>{error}</p>
          <button className="retry-btn" onClick={handleRetry}>
            重试
          </button>
        </div>
      )}
    </div>
  );
}
