import { create } from "zustand";

type ViewMode = "input" | "council" | "seats" | "analysis";

interface UIStore {
  viewMode: ViewMode;
  sidebarOpen: boolean;
  darkMode: boolean;

  setViewMode: (mode: ViewMode) => void;
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  viewMode: "input",
  sidebarOpen: false,
  darkMode: true,

  setViewMode: (mode: ViewMode) => set({ viewMode: mode }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
}));
