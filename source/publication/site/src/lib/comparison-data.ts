import { compareDecimal, isDecimal } from "./exact-decimal";
import type { ComparisonDocument } from "./types";

const invalid = (): never => { throw new Error("Comparison data is invalid."); };
const object = (value: unknown): Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value)
    ? value as Record<string, unknown> : invalid();
const array = (value: unknown): unknown[] => Array.isArray(value) ? value : invalid();
const text = (value: unknown): string =>
  typeof value === "string" && value.length > 0 ? value : invalid();
const integer = (value: unknown, minimum = 0): number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= minimum ? value : invalid();
const decimal = (value: unknown, nullable = false, allowNegative = false): void => {
  if (value === null && nullable) return;
  if (!isDecimal(value) || (!allowNegative && compareDecimal(value, "0") < 0)) invalid();
};
const contract = (value: unknown): void => {
  if (value === null) return;
  const item = object(value);
  integer(item.violations);
  decimal(item.compliance_rate, true);
};

/** Validate fetched JSON before it becomes comparison state. */
export const parseComparisonDocument = (value: unknown): ComparisonDocument => {
  const document = object(value);
  if (document.document_type !== "comparison" || document.schema_version !== 1 ||
      !/^\d+\.\d+$/.test(text(document.edition_id))) invalid();
  const iterations = integer(document.iterations, 1);
  const limit = integer(document.max_questions, 1);
  const targets = array(document.target_ids).map(text);
  if (targets.some(id => !/^T-\d{4}$/.test(id))) invalid();
  if (new Set(targets).size !== targets.length) invalid();
  const modelIds = new Set<string>(); const executions = new Set<string>();
  for (const raw of array(document.models)) {
    const model = object(raw); const result = object(model.result); const identity = object(result.model);
    const modelId = text(identity.model_id); const executionId = text(result.execution_id);
    if (!/^M-\d{4}$/.test(modelId) || modelIds.has(modelId) || executions.has(executionId) ||
        result.status !== "evaluated") invalid();
    modelIds.add(modelId); executions.add(executionId);
    text(identity.display_name); text(identity.provider); text(identity.reasoning_effort);
    if (!Number.isFinite(Date.parse(text(result.completed_at)))) invalid();
    if (result.rank !== null) integer(result.rank, 1);
    for (const key of ["question_score", "success_rate", "total_cost_usd",
      "guesser_cost_per_episode_usd", "full_cost_per_episode_usd", "runtime_per_episode_ms",
      "guesser_think_time_per_episode_ms", "guesser_latency_per_call_ms", "ideal_distance_score"]) {
      decimal(result[key], true);
    }
    integer(result.successful); integer(result.terminal_trials); contract(result.contract);
    if (result.terminal_trials !== targets.length * iterations ||
        (result.success_rate !== null && compareDecimal(text(result.success_rate), "1") > 0)) invalid();
    if (result.question_score_confidence_interval !== null) {
      const interval = object(result.question_score_confidence_interval);
      for (const key of ["estimate", "lower", "upper"]) decimal(interval[key], false, key === "lower");
      if (compareDecimal(text(interval.lower), text(interval.estimate)) > 0 ||
          compareDecimal(text(interval.estimate), text(interval.upper)) > 0 ||
          compareDecimal(text(interval.estimate), text(result.question_score)) !== 0) invalid();
    }
    const totals = object(model.totals); const costs = object(totals.costs_usd);
    for (const key of ["guesser", "primary_oracle", "reviewer", "judge", "validator", "total"]) {
      decimal(costs[key]);
    }
    integer(totals.runtime_ms); integer(totals.guesser_think_time_ms); integer(totals.guesser_calls);
    const subjects = array(model.subjects);
    if (subjects.length !== targets.length) invalid();
    for (const [position, rawSubject] of subjects.entries()) {
      const subject = object(rawSubject);
      if (subject.target_id !== targets[position]) invalid();
      text(subject.display_name); decimal(subject.average_questions, true); decimal(subject.success_rate, true);
      integer(subject.successful); integer(subject.model_failed); integer(subject.infrastructure_failed);
      const rounds = array(subject.rounds);
      if (rounds.length !== iterations) invalid();
      const trialIds = new Set<string>();
      for (const [index, rawRound] of rounds.entries()) {
        const round = object(rawRound); const trialId = text(round.trial_id);
        if (trialIds.has(trialId) || round.trial_number !== index + 1 ||
            !["success", "model_failure"].includes(text(round.status))) invalid();
        trialIds.add(trialId);
        const count = integer(round.counted_questions);
        decimal(round.penalized_questions); decimal(round.cost_usd);
        integer(round.duration_ms); contract(round.contract);
        if (compareDecimal(text(round.penalized_questions),
          String(round.status === "success" ? count : limit + 1)) !== 0) invalid();
      }
    }
  }
  return value as ComparisonDocument;
};
