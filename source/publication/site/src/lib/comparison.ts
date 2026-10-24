import type { LocationQuery } from "vue-router";
import type { ComparisonModel, ComparisonSubject, PublicTrialSummary } from "./types";
import { compareDecimal, multiplyInteger, subtractDecimal, sumDecimals } from "./exact-decimal";
import { duration, money, moneyEpisode, number, percent } from "./format";

export const MAX_COMPARISON_MODELS = 5;
export const ROUND_METRICS = ["questions", "cost", "duration", "format"] as const;
export type RoundMetric = typeof ROUND_METRICS[number];
export type ValueFormat = "questions" | "money" | "money-precise" | "duration" | "integer" | "percent";
export type ValueMark = "best" | "worst" | "tie" | null;
export interface ComparisonValue { numerator: string; denominator: number }
export interface ComparisonState {
  modelIds: string[];
  expanded: string[];
  metric: RoundMetric;
  baseline: string;
  sort: "original" | "name" | "gap";
}

export const queryList = (value: LocationQuery[string] | undefined): string[] =>
  [...new Set((Array.isArray(value) ? value : [value])
    .flatMap(item => typeof item === "string" ? item.slice(0, 2000).split(",") : [])
    .filter(Boolean))];

export const comparisonState = (query: LocationQuery): ComparisonState => {
  const modelIds = queryList(query.models).filter(id => /^M-\d{4}$/.test(id)).slice(0, MAX_COMPARISON_MODELS);
  return {
    modelIds,
    expanded: queryList(query.expanded).filter(id => /^T-\d{4}$/.test(id)),
    metric: ROUND_METRICS.includes(query.metric as RoundMetric) ? query.metric as RoundMetric : "questions",
    baseline: typeof query.baseline === "string" && modelIds.includes(query.baseline) ? query.baseline : "",
    sort: query.sort === "name" || query.sort === "gap" ? query.sort : "original",
  };
};

export const scalar = (value: string | number | null | undefined): ComparisonValue | null =>
  value === null || value === undefined ? null : { numerator: String(value), denominator: 1 };

export const compareValue = (left: ComparisonValue, right: ComparisonValue): number =>
  compareDecimal(multiplyInteger(left.numerator, right.denominator),
    multiplyInteger(right.numerator, left.denominator));

export const subtractValue = (left: ComparisonValue, right: ComparisonValue): ComparisonValue => ({
  numerator: subtractDecimal(multiplyInteger(left.numerator, right.denominator),
    multiplyInteger(right.numerator, left.denominator)),
  denominator: left.denominator * right.denominator,
});

export const valueMark = (
  value: ComparisonValue | null, values: readonly (ComparisonValue | null)[], higherIsBetter = false,
): ValueMark => {
  const available = values.filter((item): item is ComparisonValue => item !== null);
  if (value === null || available.length < 2) return null;
  const ordered = [...available].sort(compareValue);
  const lowest = ordered[0]!; const highest = ordered[ordered.length - 1]!;
  if (compareValue(lowest, highest) === 0) return "tie";
  if (compareValue(value, higherIsBetter ? highest : lowest) === 0) return "best";
  if (compareValue(value, higherIsBetter ? lowest : highest) === 0) return "worst";
  return null;
};

export const formatValue = (value: ComparisonValue | null, format: ValueFormat, digits = 2): string => {
  if (value === null) return "Unavailable";
  const numeric = Number(value.numerator) / value.denominator;
  switch (format) {
    case "money": return money(numeric);
    case "money-precise": return moneyEpisode(numeric);
    case "duration": return duration(numeric);
    case "integer": return number(numeric, 0);
    case "percent": return percent(String(numeric));
    default: return number(numeric, digits);
  }
};

export const roundValue = (round: PublicTrialSummary | undefined, metric: RoundMetric): ComparisonValue | null => {
  if (round === undefined || round.status === "infrastructure_failure") return null;
  switch (metric) {
    case "questions": return scalar(round.penalized_questions);
    case "cost": return scalar(round.cost_usd);
    case "duration": return scalar(round.duration_ms);
    case "format": return scalar(round.contract?.violations);
  }
};

export const subjectValue = (subject: ComparisonSubject | undefined, metric: RoundMetric): ComparisonValue | null => {
  if (subject === undefined) return null;
  if (metric === "questions") return scalar(subject.average_questions);
  const values = subject.rounds.map(round => roundValue(round, metric));
  if (values.length === 0 || values.some(value => value === null)) return null;
  return { numerator: sumDecimals(values.map(value => value!.numerator)), denominator: values.length };
};

export const roundMetricFormat = (metric: RoundMetric): ValueFormat =>
  ({ questions: "questions", cost: "money-precise", duration: "duration", format: "questions" } as const)[metric];

export interface MainComparisonMetric {
  key: string;
  label: string;
  format: ValueFormat;
  higherIsBetter?: boolean;
  note?: string;
  value: (model: ComparisonModel) => ComparisonValue | null;
}

export const mainComparisonMetrics: readonly MainComparisonMetric[] = [
  { key: "score", label: "Question score", format: "questions", note: "Average questions needed per round. Each subject counts equally; failed rounds get the penalty score.",
    value: model => scalar(model.result.question_score) },
  { key: "stability", label: "Stability (CI width)", format: "questions", note: "Width of the score's 95% confidence interval. Smaller means more consistent results across rounds.",
    value: model => {
      const interval = model.result.question_score_confidence_interval;
      return interval === null ? null : scalar(subtractDecimal(interval.upper, interval.lower));
    } },
  { key: "rank", label: "Leaderboard rank", format: "integer", note: "Position among all models in this edition. Equal scores are ranked by CI width.",
    value: model => scalar(model.result.rank) },
  { key: "model-cost", label: "Model cost per round", format: "money-precise", note: "Tested model only.",
    value: model => scalar(model.result.guesser_cost_per_episode_usd) },
  { key: "full-cost", label: "Full cost per round", format: "money-precise", note: "Tested model plus the answer checks.",
    value: model => scalar(model.result.full_cost_per_episode_usd) },
  { key: "model-total", label: "Total model cost", format: "money", note: "Tested model, whole run.",
    value: model => model.result.guesser_cost_per_episode_usd === null ? null : scalar(model.totals.costs_usd.guesser) },
  { key: "benchmark-total", label: "Total benchmark cost", format: "money", note: "Whole run, including answer checks.",
    value: model => scalar(model.result.total_cost_usd) },
  { key: "model-time", label: "Model time per round", format: "duration", note: "Time the tested model took to reply, as reported by the provider.",
    value: model => scalar(model.result.guesser_think_time_per_episode_ms) },
  { key: "runtime", label: "Benchmark runtime", format: "duration", note: "Clock time for the whole run, including answer checks and waiting.",
    value: model => scalar(model.totals.runtime_ms) },
  { key: "solved", label: "Rounds solved", format: "percent", higherIsBetter: true,
    note: "Share of rounds where the model found the subject. Differences are in percentage points (pp).",
    value: model => scalar(model.result.success_rate) },
  { key: "format", label: "Format errors", format: "integer", note: "Replies in the wrong format across the run.",
    value: model => scalar(model.result.contract?.violations) },
];
