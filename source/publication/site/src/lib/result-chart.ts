import type { RouteLocationRaw } from "vue-router";

import { confidenceIntervalLabel, number } from "./format";
import { runRoute } from "./route-location";
import type { LeaderboardRow } from "./types";

export interface ScoreDot {
  modelId: string;
  label: string;
  value: number;
  display: string;
  confidenceLower?: number;
  confidenceUpper?: number;
  confidenceDisplay?: string;
  detail?: string;
  link?: RouteLocationRaw;
}

export const leaderboardScoreDot = (
  row: LeaderboardRow,
  detail?: string,
): ScoreDot => {
  const interval = row.question_score_confidence_interval;
  return {
    modelId: row.model.model_id,
    label: row.model.display_name,
    value: Number(row.question_score ?? 0),
    display: number(row.question_score),
    confidenceLower: interval === null ? undefined : Number(interval.lower),
    confidenceUpper: interval === null ? undefined : Number(interval.upper),
    confidenceDisplay:
      interval === null ? undefined : confidenceIntervalLabel(interval),
    detail,
    link: row.execution_id === null ? undefined : runRoute(row.execution_id),
  };
};

export const questionScoreChartSummary =
  "Lower is better. The blue marker is the average question score. The colored line is its 95% confidence interval (CI). The companion plot shows each exact CI width. Its three bands divide the displayed width scale into equal ranges.";
