import type { RouteLocationRaw } from "vue-router";

export interface ReliabilityChartItem {
  label: string;
  score: number;
  scoreDisplay: string;
  confidenceDisplay: string;
  intervalWidth: number;
  intervalWidthDisplay: string;
  reliabilityRank: number;
  link?: RouteLocationRaw;
}
