import { create } from "zustand";
import type {
  CouncilState,
  CouncilConclusion,
  CouncilResponse,
  UserProfile,
  DebateTranscript,
  FullCouncilResponse,
  SpeechRecord,
} from "../types";
import * as api from "../api/client";
import { councilWebSocketClient, WebSocketEvent } from "../api/websocket";

interface CouncilStore {
  session: CouncilState | null;
  conclusion: CouncilConclusion | null;
  transcript: DebateTranscript | null;
  views: {
    dramatic?: string;
    practical?: string;
    psychological?: string;
  } | null;
  isLoading: boolean;
  loadingStep: string;
  error: string | null;
  user: UserProfile | null;
  isWebSocketConnected: boolean;
  liveEvents: Array<{ type: string; timestamp: string; data: any }>;
  currentRound: number;
  totalRounds: number;

  submitProposal: (proposal: string, category?: string) => Promise<void>;
  fetchSession: (sessionId: string) => Promise<void>;
  fetchUser: () => Promise<void>;
  setView: (view: "dramatic" | "practical" | "psychological") => void;
  clearError: () => void;
  connectWebSocket: (sessionId: string) => Promise<void>;
  disconnectWebSocket: () => void;
  addLiveSpeech: (speech: SpeechRecord) => void;
}

export const useCouncilStore = create<CouncilStore>((set, get) => ({
  session: null,
  conclusion: null,
  transcript: null,
  views: null,
  isLoading: false,
  loadingStep: "",
  error: null,
  user: null,
  isWebSocketConnected: false,
  liveEvents: [],
  currentRound: 0,
  totalRounds: 0,

  submitProposal: async (proposal: string, category?: string) => {
    set({ isLoading: true, error: null, loadingStep: "提交议题..." });
    try {
      const res: FullCouncilResponse = await api.submitProposal(
        proposal,
        category,
      );

      // Extract views from ui_commands
      let views = null;
      for (const cmd of res.ui_commands || []) {
        if (cmd.command_type === "show_views" && cmd.payload.views) {
          views = cmd.payload.views;
          break;
        }
      }

      set({
        session: res.council_state,
        conclusion: res.conclusion,
        transcript: res.transcript || null,
        views,
        isLoading: false,
        loadingStep: "",
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Unknown error",
        isLoading: false,
        loadingStep: "",
      });
    }
  },

  fetchSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.getSession(sessionId);
      set({ session: res.council });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchUser: async () => {
    try {
      const user = await api.getUserProfile();
      set({ user });
    } catch {
      set({ user: null });
    }
  },

  setView: (view: "dramatic" | "practical" | "psychological") => {
    // This is handled by local state in the component
  },

  clearError: () => set({ error: null }),

  connectWebSocket: async (sessionId: string) => {
    // Disconnect existing connection if any
    get().disconnectWebSocket();

    try {
      await councilWebSocketClient.connect(sessionId);
      set({ isWebSocketConnected: true });

      // Set up event handlers
      councilWebSocketClient.on("council_started", (event: WebSocketEvent) => {
        set((state) => ({
          liveEvents: [
            ...state.liveEvents,
            {
              type: "council_started",
              timestamp: new Date().toISOString(),
              data: event.payload,
            },
          ],
          loadingStep: "议会开始...",
        }));
      });

      councilWebSocketClient.on("step_started", (event: WebSocketEvent) => {
        set({ loadingStep: event.payload.message || "处理中..." });
      });

      councilWebSocketClient.on("step_completed", (event: WebSocketEvent) => {
        // Step completed, continue to next step
      });

      councilWebSocketClient.on("seat_prevote", (event: WebSocketEvent) => {
        set((state) => ({
          liveEvents: [
            ...state.liveEvents,
            {
              type: "seat_prevote",
              timestamp: new Date().toISOString(),
              data: event.payload,
            },
          ],
        }));
      });

      councilWebSocketClient.on("knife_cut", (event: WebSocketEvent) => {
        set((state) => ({
          liveEvents: [
            ...state.liveEvents,
            {
              type: "knife_cut",
              timestamp: new Date().toISOString(),
              data: event.payload,
            },
          ],
          loadingStep: "餐刀切分完成",
        }));
      });

      councilWebSocketClient.on("round_started", (event: WebSocketEvent) => {
        set({
          currentRound: event.payload.round,
          totalRounds: event.payload.total_rounds,
          loadingStep: `辩论第 ${event.payload.round}/${event.payload.total_rounds} 轮`,
        });
      });

      councilWebSocketClient.on("seat_speaking", (event: WebSocketEvent) => {
        const speechData = event.payload;
        const newSpeech: SpeechRecord = {
          seat_id: speechData.seat_id,
          seat_name: speechData.seat_name,
          speech: speechData.speech,
          stance: speechData.stance,
          confidence: speechData.confidence,
          round: speechData.round,
        };

        set((state) => {
          // Update or create transcript with new speech
          let newTranscript = state.transcript || {
            rounds: [],
            total_speeches: 0,
          };

          // Find or create the round
          let roundIndex = newTranscript.rounds.findIndex(
            (r) => r.round_num === speechData.round,
          );

          if (roundIndex === -1) {
            newTranscript.rounds.push({
              round_num: speechData.round,
              speeches: [],
            });
            roundIndex = newTranscript.rounds.length - 1;
          }

          // Add speech to round
          newTranscript.rounds[roundIndex].speeches.push(newSpeech);
          newTranscript.total_speeches += 1;

          return {
            transcript: { ...newTranscript },
            liveEvents: [
              ...state.liveEvents,
              {
                type: "seat_speaking",
                timestamp: new Date().toISOString(),
                data: speechData,
              },
            ],
          };
        });
      });

      councilWebSocketClient.on("bell_update", (event: WebSocketEvent) => {
        set((state) => ({
          liveEvents: [
            ...state.liveEvents,
            {
              type: "bell_update",
              timestamp: new Date().toISOString(),
              data: event.payload,
            },
          ],
        }));
      });

      councilWebSocketClient.on("vote_update", (event: WebSocketEvent) => {
        set((state) => ({
          liveEvents: [
            ...state.liveEvents,
            {
              type: "vote_update",
              timestamp: new Date().toISOString(),
              data: event.payload,
            },
          ],
        }));
      });

      councilWebSocketClient.on("conclusion", (event: WebSocketEvent) => {
        set({
          loadingStep: "结论已生成",
        });
      });

      councilWebSocketClient.on(
        "council_completed",
        (event: WebSocketEvent) => {
          set({
            isLoading: false,
            loadingStep: "",
            liveEvents: [
              ...get().liveEvents,
              {
                type: "council_completed",
                timestamp: new Date().toISOString(),
                data: event.payload,
              },
            ],
          });
        },
      );

      councilWebSocketClient.on("error", (event: WebSocketEvent) => {
        set({
          error: event.payload.message || "WebSocket 错误",
          isLoading: false,
          loadingStep: "",
        });
      });

      councilWebSocketClient.on("connected", () => {
        console.log("[Store] WebSocket connected");
      });
    } catch (err) {
      console.error("[Store] Failed to connect WebSocket:", err);
      set({ isWebSocketConnected: false });
    }
  },

  disconnectWebSocket: () => {
    councilWebSocketClient.disconnect();
    councilWebSocketClient.clearAllHandlers();
    set({ isWebSocketConnected: false, liveEvents: [] });
  },

  addLiveSpeech: (speech: SpeechRecord) => {
    // This is now handled by WebSocket events
  },
}));
