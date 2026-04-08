import type {
  CouncilResponse,
  UserProfile,
  SeatConfig,
  SeatState,
  CouncilState,
  FullCouncilResponse,
} from "../types";

const API_BASE = "/api/v1";

export interface ProposalRequest {
  proposal: string;
  category?: string;
}

export async function submitProposal(
  proposal: string,
  category?: string,
): Promise<FullCouncilResponse> {
  const response = await fetch(`${API_BASE}/council/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "default_user",
      session_id: `session_${Date.now()}`,
      user_input: proposal,
      category: category || "general",
      action_type: "submit_proposal",
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} - ${errorText}`);
  }

  return response.json();
}

export async function getSession(
  sessionId: string,
): Promise<{ council: CouncilState }> {
  const response = await fetch(`${API_BASE}/council/session/${sessionId}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getSeats(): Promise<SeatConfig[]> {
  const response = await fetch(`${API_BASE}/seats`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getSeatState(seatId: string): Promise<SeatState> {
  const response = await fetch(`${API_BASE}/seats/${seatId}/state`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getUserProfile(): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/user/profile`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function healthCheck(): Promise<{
  status: string;
  version: string;
  llm_configured: boolean;
}> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export interface CouncilHistoryResponse {
  sessions: Array<{
    case_id: string;
    proposal_title: string;
    conclusion: string | null;
    minority_opinion: string | null;
    triggered_reconsider: boolean;
    triggered_fracture: boolean;
    created_at: string;
  }>;
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

export async function getCouncilHistory(
  userId: string = "default_user",
  limit: number = 20,
  offset: number = 0,
): Promise<CouncilHistoryResponse> {
  const response = await fetch(
    `${API_BASE}/council/history?user_id=${userId}&limit=${limit}&offset=${offset}`,
  );
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function requestReconsider(
  sessionId: string,
  reason: string,
): Promise<{
  session_id: string;
  triggered: boolean;
  reason: string;
  message: string;
}> {
  const response = await fetch(`${API_BASE}/council/reconsider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "default_user",
      session_id: sessionId,
      reason,
    }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function askSeatQuestion(
  sessionId: string,
  seatId: string,
  question: string,
): Promise<{
  seat_id: string;
  seat_name: string;
  question: string;
  response: string;
}> {
  const response = await fetch(`${API_BASE}/council/ask-seat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "default_user",
      session_id: sessionId,
      seat_id: seatId,
      question,
    }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function supplementTestimony(
  sessionId: string,
  testimony: string,
): Promise<{ session_id: string; supplemented: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/council/supplement`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "default_user",
      session_id: sessionId,
      testimony,
    }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export interface RelationshipGraphData {
  edges: Array<{
    from_seat_id: string;
    to_seat_id: string;
    agreement_score: number;
    interaction_count: number;
    last_interaction: string | null;
    influence_strength: number;
  }>;
  clustering_coefficient: number;
  density: number;
  updated_at: string | null;
}

export async function getRelationshipGraph(): Promise<RelationshipGraphData> {
  const response = await fetch(`${API_BASE}/council/relationship-graph`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
