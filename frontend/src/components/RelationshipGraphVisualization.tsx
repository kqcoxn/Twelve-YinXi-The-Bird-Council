import React, { useMemo } from "react";

interface RelationshipEdge {
  from_seat_id: string;
  to_seat_id: string;
  agreement_score: number;
  interaction_count: number;
  last_interaction: string | null;
  influence_strength: number;
}

interface RelationshipGraphData {
  edges: RelationshipEdge[];
  clustering_coefficient: number;
  density: number;
  updated_at: string | null;
}

interface SeatInfo {
  seat_id: string;
  name: string;
}

interface RelationshipGraphVisualizationProps {
  graphData: RelationshipGraphData | null;
  seats: SeatInfo[];
  width?: number;
  height?: number;
}

const RelationshipGraphVisualization: React.FC<
  RelationshipGraphVisualizationProps
> = ({ graphData, seats, width = 600, height = 400 }) => {
  const seatPositions = useMemo(() => {
    // Position seats in a circle
    const radius = Math.min(width, height) * 0.35;
    const centerX = width / 2;
    const centerY = height / 2;

    const positions: Record<string, { x: number; y: number }> = {};
    seats.forEach((seat, index) => {
      const angle = (index / seats.length) * 2 * Math.PI - Math.PI / 2;
      positions[seat.seat_id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    return positions;
  }, [seats, width, height]);

  const edgeColors = useMemo(() => {
    if (!graphData) return {};

    const colors: Record<string, string> = {};
    graphData.edges.forEach((edge) => {
      const key = `${edge.from_seat_id}-${edge.to_seat_id}`;
      // Green for positive, red for negative
      if (edge.agreement_score > 0.3) {
        colors[key] = "#22c55e"; // Green
      } else if (edge.agreement_score < -0.3) {
        colors[key] = "#ef4444"; // Red
      } else {
        colors[key] = "#94a3b8"; // Gray
      }
    });

    return colors;
  }, [graphData]);

  if (!graphData || graphData.edges.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        暂无关系网络数据
      </div>
    );
  }

  return (
    <div className="w-full">
      <svg width={width} height={height} className="bg-gray-900/50 rounded-lg">
        {/* Draw edges */}
        {graphData.edges.map((edge) => {
          const from = seatPositions[edge.from_seat_id];
          const to = seatPositions[edge.to_seat_id];
          if (!from || !to) return null;

          const key = `${edge.from_seat_id}-${edge.to_seat_id}`;
          const color = edgeColors[key] || "#94a3b8";
          const strokeWidth = Math.max(1, Math.abs(edge.agreement_score) * 4);
          const opacity = 0.3 + Math.abs(edge.agreement_score) * 0.7;

          return (
            <line
              key={key}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={color}
              strokeWidth={strokeWidth}
              opacity={opacity}
            >
              <title>
                {edge.from_seat_id} ↔ {edge.to_seat_id}
                {"\n"}同意度: {(edge.agreement_score * 100).toFixed(1)}%{"\n"}
                互动次数: {edge.interaction_count}
              </title>
            </line>
          );
        })}

        {/* Draw seat nodes */}
        {seats.map((seat) => {
          const pos = seatPositions[seat.seat_id];
          if (!pos) return null;

          return (
            <g key={seat.seat_id}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={8}
                fill="#3b82f6"
                stroke="#60a5fa"
                strokeWidth={2}
              >
                <title>{seat.name}</title>
              </circle>
              <text
                x={pos.x}
                y={pos.y + 20}
                textAnchor="middle"
                fill="#e2e8f0"
                fontSize={10}
              >
                {seat.name.substring(0, 4)}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-6 text-xs text-gray-400 justify-center">
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-green-500 rounded" />
          <span>高同意度 (&gt;0.3)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-gray-400 rounded" />
          <span>中性</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-red-500 rounded" />
          <span>低同意度 (&lt;-0.3)</span>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-2 gap-4 text-center">
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="text-lg font-semibold text-blue-400">
            {graphData.edges.length}
          </div>
          <div className="text-xs text-gray-500">关系连线</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="text-lg font-semibold text-purple-400">
            {(graphData.clustering_coefficient * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">集群系数</div>
        </div>
      </div>
    </div>
  );
};

export default RelationshipGraphVisualization;
