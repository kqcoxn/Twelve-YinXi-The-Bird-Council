import { useState } from "react";
import { useCouncilStore } from "../stores/council";

export default function InputPanel() {
  const [proposal, setProposal] = useState("");
  const [category, setCategory] = useState("");
  const { submitProposal, isLoading, error } = useCouncilStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!proposal.trim() || isLoading) return;
    await submitProposal(proposal.trim(), category || undefined);
    setProposal("");
    setCategory("");
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
      {error && <div className="error-msg">{error}</div>}
    </div>
  );
}
