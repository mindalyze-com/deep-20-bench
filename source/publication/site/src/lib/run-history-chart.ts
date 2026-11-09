import { duration, money, moneyEpisode, number } from "./format";
import type { LeaderboardRow, PublicRunSummary } from "./types";

export type HistoryValueFormat = "number" | "currency" | "duration" | "episode-cost";

export interface HistoryComponent {
  label: string;
  value: number;
  display: string;
  color: string;
}

export interface HistoryCoordinates {
  x: string | number | null;
  xDisplay: string;
  y?: string | number | null;
  yDisplay?: string;
  lower?: string | number;
  upper?: string | number;
  detail?: string;
  components?: HistoryComponent[];
}

export interface HistoryChartRun {
  executionId: string;
  modelId: string;
  modelName: string;
  completedAt: string | null;
  latest: boolean;
  x: number;
  xDisplay: string;
  y?: number;
  yDisplay?: string;
  lower?: number;
  upper?: number;
  detail?: string;
  components?: HistoryComponent[];
}

const coordinates = (value: HistoryCoordinates): Omit<HistoryChartRun,
  "executionId" | "modelId" | "modelName" | "completedAt" | "latest"> | null => {
  if (value.x === null || !Number.isFinite(Number(value.x)) ||
      (value.y !== undefined && (value.y === null || !Number.isFinite(Number(value.y))))) return null;
  return {
    ...value,
    x: Number(value.x),
    y: value.y === undefined ? undefined : Number(value.y),
    lower: value.lower === undefined ? undefined : Number(value.lower),
    upper: value.upper === undefined ? undefined : Number(value.upper),
  };
};

/** Preserve each execution; this projection performs no aggregation or ranking. */
export const resultHistory = (
  rows: readonly LeaderboardRow[],
  metric: (row: LeaderboardRow) => HistoryCoordinates,
): HistoryChartRun[] => rows.flatMap(row => {
  const point = coordinates(metric(row));
  return row.execution_id === null || point === null ? [] : [{
    ...point,
    executionId: row.execution_id,
    modelId: row.model.model_id,
    modelName: row.model.display_name,
    completedAt: row.completed_at,
    latest: row.is_latest !== false,
  }];
});

export const runHistory = (
  runs: readonly PublicRunSummary[],
  latestIds: ReadonlySet<string>,
  metric: (run: PublicRunSummary) => HistoryCoordinates,
): HistoryChartRun[] => runs.flatMap(run => {
  const point = coordinates(metric(run));
  return point === null ? [] : [{
    ...point,
    executionId: run.execution_id,
    modelId: run.model_id,
    modelName: run.model_name,
    completedAt: run.completed_at,
    latest: latestIds.has(run.execution_id),
  }];
});

export const historyValue = (value: number, format: HistoryValueFormat): string =>
  format === "currency" ? money(value) : format === "episode-cost" ? moneyEpisode(value) :
    format === "duration" ? duration(value) : number(value);

/** Earlier minus latest, for display only; signed source values remain unchanged. */
export const historyDifference = (value: number, latest: number, format: HistoryValueFormat): string => {
  const delta = value - latest;
  return `${delta > 0 ? "+" : delta < 0 ? "−" : ""}${historyValue(Math.abs(delta), format)}`;
};

export interface PositionedHistoryRun {
  run: HistoryChartRun;
  x: number;
  y: number;
}

export interface HistoryMarkerGroup {
  x: number;
  y: number;
  members: HistoryChartRun[];
}

/** Cluster overlapping markers at a real run's position, never at an averaged value. */
export const groupHistoryMarkers = (points: readonly PositionedHistoryRun[], radius = 10): HistoryMarkerGroup[] => {
  const groups: HistoryMarkerGroup[] = [];
  for (const point of points) {
    const group = groups.find(candidate => Math.hypot(candidate.x - point.x, candidate.y - point.y) <= radius);
    if (group) group.members.push(point.run);
    else groups.push({ x: point.x, y: point.y, members: [point.run] });
  }
  return groups;
};
