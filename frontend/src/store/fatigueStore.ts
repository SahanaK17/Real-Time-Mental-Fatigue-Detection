/**
 * Fatigue Store — Live prediction state
 */
import { create } from 'zustand';
import type { FatigueLevel, FeatureImpact } from '@/types';

interface LiveFatigueData {
  fatigueScore: number;
  fatigueLevel: FatigueLevel;
  confidence: number;
  topFeatures: FeatureImpact[];
  timestamp?: string;
}

interface FatigueStore {
  liveData: LiveFatigueData | null;
  history: LiveFatigueData[];
  setLiveData: (data: LiveFatigueData) => void;
  clearHistory: () => void;
}

export const useFatigueStore = create<FatigueStore>((set) => ({
  liveData: null,
  history: [],
  setLiveData: (data) =>
    set((state) => ({
      liveData: data,
      history: [data, ...state.history].slice(0, 300), // Keep 5 minutes of history
    })),
  clearHistory: () => set({ history: [] }),
}));
