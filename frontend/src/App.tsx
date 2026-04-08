import { useEffect } from "react";
import { useUIStore } from "./stores/ui";
import { useCouncilStore } from "./stores/council";
import InputPanel from "./components/InputPanel";
import CouncilHall from "./components/CouncilHall";
import SeatVisualization from "./components/SeatVisualization";
import "./styles/global.css";

export default function App() {
  const { viewMode, setViewMode } = useUIStore();
  const { fetchUser } = useCouncilStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">十二音希：群鸟议会</h1>
        <nav className="app-nav">
          <button
            className={`nav-btn ${viewMode === "input" ? "active" : ""}`}
            onClick={() => setViewMode("input")}
          >
            议题
          </button>
          <button
            className={`nav-btn ${viewMode === "council" ? "active" : ""}`}
            onClick={() => setViewMode("council")}
          >
            议会
          </button>
          <button
            className={`nav-btn ${viewMode === "seats" ? "active" : ""}`}
            onClick={() => setViewMode("seats")}
          >
            席位
          </button>
        </nav>
      </header>

      <aside className="sidebar">
        <InputPanel />
      </aside>

      <main className="main-content">
        {viewMode === "input" && <CouncilHall />}
        {viewMode === "council" && <CouncilHall />}
        {viewMode === "seats" && <SeatVisualization />}
      </main>
    </div>
  );
}
