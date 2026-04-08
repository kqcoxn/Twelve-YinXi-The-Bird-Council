// Core types mirroring backend Pydantic models

export interface SeatConfig {
  seat_id: string;
  name: string;
  archetype: string;
  core_belief: string;
  traits: Record<string, number>;
  planner_preference: Record<string, any>;
  tone: Record<string, any>;
  bell_sensitivity: Record<string, number>;
  example_phrases: string[];
}

export interface SeatState {
  seat_id: string;
  name: string;
  status: "active" | "silent" | "fractured" | "exiled" | "shadow";
  current_stance: "approve" | "oppose" | "abstain";
  confidence: number;
  bell_health: number;
  stress: number;
  fracture_risk: number;
}

export interface VoteMap {
  approve: number;
  oppose: number;
  abstain: number;
}

export interface BellState {
  stress_level: number;
  fracture_risk: number;
  status: "healthy" | "stressed" | "critical" | "fracture_risk" | "fractured";
}

export interface CouncilState {
  id: string;
  mode: "light_chat" | "full_council" | "eternal_council" | "safety_mode";
  state: string;
  proposal: string;
  orchestrator_state: string;
  round: number;
  seats?: SeatConfig[];
  visible_seats: string[];
  hidden_seats: string[];
  vote_map?: VoteMap;
  bell_state?: BellState;
  conclusion?: CouncilConclusion;
  tension_level: number;
  knife_risk: number;
}

export interface CouncilConclusion {
  summary: string;
  decision: string;
  main_reasons: string[];
  risks: string[];
  next_steps: string[];
  minority_opinion: string;
}

export interface CouncilResponse {
  session_id: string;
  mode: string;
  conclusion: CouncilConclusion;
  council_state: CouncilState;
  ui_commands: UICommand[];
  created_at: string;
}

export interface UICommand {
  command_type: string;
  payload: Record<string, any>;
  timestamp: string;
}

export interface UserProfile {
  user_id: string;
  preferred_output_style: string;
  resonant_seats: string[];
  common_issue_types: string[];
}

export interface SpeechRecord {
  seat_id: string;
  seat_name: string;
  speech: string;
  stance: string;
  confidence: number;
  round: number;
}

export interface DebateTranscript {
  rounds: {
    round_num: number;
    speeches: SpeechRecord[];
  }[];
  total_speeches: number;
  created_at: string;
}

export interface SeatPrevote {
  seat_id: string;
  stance: "approve" | "oppose" | "abstain";
  confidence: number;
  stress_hint: number;
  risk_assessment: string;
}

// Extended CouncilResponse with transcript
export interface FullCouncilResponse extends CouncilResponse {
  transcript?: DebateTranscript;
  views?: {
    dramatic?: string;
    practical?: string;
    psychological?: string;
  };
}
