
import { create } from "zustand";
import type { InsightSelection } from "./types";

export const useSelectionStore = create<{
    selection: InsightSelection | null;
    setSelection: (s: InsightSelection | null) => void;
}>((set) => ({ selection: null, setSelection: (selection) => set({ selection }) }));
