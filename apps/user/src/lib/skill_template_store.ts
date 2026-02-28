import { create } from "zustand";

export type ConfidenceLevel = "low" | "medium" | "high";
export type Horizon = "30d" | "90d" | "180d";

export type SkillTemplateState = {
    targetRole: string;
    dominantElements: string;
    growthElements: string;
    confidence: ConfidenceLevel;
    horizon: Horizon;
};

type SkillTemplateStore = {
    template: SkillTemplateState;
    setTemplate: (next: Partial<SkillTemplateState>) => void;
    resetTemplate: () => void;
};

const DEFAULT_TEMPLATE: SkillTemplateState = {
    targetRole: "",
    dominantElements: "",
    growthElements: "",
    confidence: "medium",
    horizon: "90d",
};

export const useSkillTemplateStore = create<SkillTemplateStore>((set) => ({
    template: DEFAULT_TEMPLATE,
    setTemplate: (next) => set((state) => ({ template: { ...state.template, ...next } })),
    resetTemplate: () => set({ template: DEFAULT_TEMPLATE }),
}));
