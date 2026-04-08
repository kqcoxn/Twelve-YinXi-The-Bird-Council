import { create } from "zustand";
import type {
  CouncilState,
  CouncilConclusion,
  CouncilResponse,
  UserProfile,
  DebateTranscript,
  FullCouncilResponse,
} from "../types";
import * as api from "../api/client";

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

  submitProposal: (proposal: string, category?: string) => Promise<void>;
  fetchSession: (sessionId: string) => Promise<void>;
  fetchUser: () => Promise<void>;
  setView: (view: "dramatic" | "practical" | "psychological") => void;
  clearError: () => void;
}

export const useCouncilStore = create<CouncilStore>((set) => ({
  session: null,
  conclusion: null,
  transcript: null,
  views: null,
  isLoading: false,
  loadingStep: "",
  error: null,
  user: null,

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
}));
