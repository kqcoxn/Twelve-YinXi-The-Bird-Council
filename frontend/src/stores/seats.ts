import { create } from "zustand";
import type { SeatConfig, SeatState } from "../types";
import * as api from "../api/client";

interface SeatsStore {
  seats: SeatConfig[];
  seatStates: Record<string, SeatState>;
  isLoading: boolean;
  selectedSeat: string | null;

  fetchSeats: () => Promise<void>;
  fetchSeatState: (seatId: string) => Promise<void>;
  setSelectedSeat: (seatId: string | null) => void;
}

export const useSeatsStore = create<SeatsStore>((set, get) => ({
  seats: [],
  seatStates: {},
  isLoading: false,
  selectedSeat: null,

  fetchSeats: async () => {
    set({ isLoading: true });
    try {
      const seats = await api.getSeats();
      set({ seats });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchSeatState: async (seatId: string) => {
    try {
      const state = await api.getSeatState(seatId);
      set((s) => ({ seatStates: { ...s.seatStates, [seatId]: state } }));
    } catch {
      // Ignore errors for individual seat state fetches
    }
  },

  setSelectedSeat: (seatId: string | null) => set({ selectedSeat: seatId }),
}));
