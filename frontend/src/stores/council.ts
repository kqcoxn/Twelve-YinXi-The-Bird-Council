import { create } from "zustand";
import type {
  CouncilState,
  CouncilConclusion,
  CouncilResponse,
  UserProfile,
} from "../types";
import * as api from "../api/client";

interface CouncilStore {
  session: CouncilState | null;
  conclusion: CouncilConclusion | null;
  isLoading: boolean;
  error: string | null;
  user: UserProfile | null;

  submitProposal: (proposal: string, category?: string) => Promise<void>;
  fetchSession: (sessionId: string) => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useCouncilStore = create<CouncilStore>((set) => ({
  session: null,
  conclusion: null,
  isLoading: false,
  error: null,
  user: null,

  submitProposal: async (proposal: string, category?: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.submitProposal(proposal, category);
      set({ session: res });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ isLoading: false });
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

  clearError: () => set({ error: null }),
}));
