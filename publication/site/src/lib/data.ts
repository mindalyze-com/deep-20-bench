import rawDataset from "../../public/data/deep20bench-v3.json";

export interface PublicModel {
  model_id: string;
  display_name: string;
  route: string;
  provider: string;
  reasoning_effort: string;
  seed_capability: string;
  configuration_hash: string;
}

export interface PublicEvidence {
  source_url: string;
  excerpt: string;
  validation: "model_reported";
}

export interface ContractReliability {
  evaluated_outputs: number;
  valid_outputs: number;
  violations: number;
  counted_penalties: number;
  affected_trials: number;
  compliance_rate: string | null;
  status: "clean" | "breached" | "not_evaluable";
}

export interface PublicActionTurn {
  turn_type: "action";
  turn_number: number;
  action: "ASK" | "GUESS";
  question: string | null;
  guess_name: string | null;
  guess_description: string | null;
  adjudicator: "oracle" | "guess_validator";
  answer: "YES" | "NO" | "UNKNOWN";
  validator_explanation: string | null;
  counted: boolean;
  counted_questions: number;
  evidence: PublicEvidence[];
  recorded_output: string | null;
}

export interface PublicContractViolationTurn {
  turn_type: "contract_violation";
  turn_number: number;
  violation_code: "invalid_guesser_output";
  violation_kind:
    | "invalid_json"
    | "invalid_action"
    | "output_limit_exceeded"
    | "empty_output"
    | "incomplete_output";
  feedback_event: "FORMAT_ERROR" | null;
  counted: boolean;
  counted_questions: number;
}

export type PublicTurn = PublicActionTurn | PublicContractViolationTurn;

export interface PublicEpisodeModelVersion {
  role: "guesser" | "oracle" | "validator";
  configuration_id: string | null;
  requested_model: string;
  requested_provider: string;
  resolved_models: string[];
  resolved_providers: string[];
  reasoning_effort: string;
  prompt_version: string;
}

export interface PublicComponentTelemetry {
  calls: number;
  cost_usd: string;
  latency_ms: number;
  total_tokens: number;
  input_tokens: number;
  cached_input_tokens: number;
  cache_write_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  estimated_cache_savings_usd: string;
}

export interface PublicOracleSupportRole {
  requested_model: string;
  requested_provider: string;
  reasoning_effort: string;
  calls: number;
  cost_usd: string;
}

export interface PublicOracleSupportUsage {
  oracle: PublicOracleSupportRole;
  reviewer: PublicOracleSupportRole;
  judge: PublicOracleSupportRole;
}

export interface PublicGuesserDisclosure {
  system_message: string;
  begin_message: string;
  output_storage: "canonical_structured_action";
}

export interface PublicEpisodeDetail {
  episode_run_id: string;
  episode_id: string;
  subject_name: string;
  subject_description: string;
  subject_reference_url: string | null;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  success: boolean;
  terminal_reason: string;
  scoring_eligible: boolean;
  publication_eligible: boolean;
  total_turns: number;
  counted_questions: number;
  ask_count: number;
  guess_count: number;
  rejected_guess_count: number;
  oracle_unknown_count: number;
  cache_status: string;
  total_cost_usd: string;
  total_tokens: number;
  contract: ContractReliability;
  models: PublicEpisodeModelVersion[];
  oracle_support: PublicOracleSupportUsage;
  guesser_disclosure: PublicGuesserDisclosure | null;
  telemetry: {
    guesser: PublicComponentTelemetry;
    oracle: PublicComponentTelemetry;
    validator: PublicComponentTelemetry;
  };
  turns: PublicTurn[];
}

export interface PublicTrial {
  trial_id: string;
  trial_number: number;
  status: "success" | "model_failure" | "infrastructure_failure";
  counted_questions: number;
  scored_questions: string | null;
  b20_score: string | null;
  cost_usd: string;
  duration_ms: number;
  contract: ContractReliability | null;
  failure_code: string | null;
  episode: PublicEpisodeDetail | null;
}

export interface PublicSubject {
  target_id: string;
  display_name: string;
  entity_type: string;
  success_rate: string | null;
  subject_score: string | null;
  b20_score: string | null;
  successful: number;
  model_failed: number;
  infrastructure_failed: number;
  contract: ContractReliability;
  trials: PublicTrial[];
}

export interface PublicRunCostTotals {
  guesser: string;
  primary_oracle: string;
  reviewer: string;
  judge: string;
  validator: string;
  total: string;
}

export interface PublicRunTotals {
  costs_usd: PublicRunCostTotals;
  total_tokens: number;
  runtime_ms: number;
  guesser_think_time_ms: number;
}

export interface PublicRun {
  execution_id: string;
  model_id: string;
  model_name: string;
  benchmark_id: string;
  benchmark_name: string;
  classification: "official" | "lab";
  reason_codes: string[];
  completed_at: string;
  created_at: string;
  git_commit: string;
  benchmark_mode: string;
  target_ids: string[];
  iterations: number;
  base_seed: number;
  max_questions: number;
  success_rate: string | null;
  descriptive_score: string | null;
  descriptive_b20_score: string | null;
  penalized_score: string | null;
  b20_score: string | null;
  total_cost_usd: string;
  successful: number;
  model_failed: number;
  infrastructure_failed: number;
  terminal_trials: number;
  contract: ContractReliability;
  totals: PublicRunTotals;
  subjects: PublicSubject[];
}

export interface LeaderboardRow {
  rank: number | null;
  model: PublicModel;
  status: "evaluated" | "awaiting_official_run";
  execution_id: string | null;
  completed_at: string | null;
  penalized_score: string | null;
  b20_score: string | null;
  success_rate: string | null;
  total_cost_usd: string | null;
  successful: number;
  terminal_trials: number;
  contract: ContractReliability | null;
}

export interface PublishedDataset {
  schema_version: 3;
  site: {
    title: string;
    short_title: string;
    description: string;
    base_path: string;
    creator_name: string;
    citation_label: string;
  };
  score_policy: {
    version: "penalized-mean-v1";
    failure_penalty_offset: number;
    b20: {
      version: "b20-linear-v1";
      target_questions: number;
    };
  };
  active_cohort: {
    cohort_id: string;
    display_name: string;
    benchmark_id: string;
    benchmark_version: number;
    target_ids: string[];
    iterations: number;
    base_seed: number;
    max_questions: number;
    model_ids: string[];
  };
  provenance: {
    source_run_count: number;
    official_run_count: number;
    lab_run_count: number;
    latest_completed_at: string | null;
    subject_catalog_hash: string;
  };
  winner: {
    model_ids: string[];
    display_names: string[];
    penalized_score: string;
    b20_score: string;
    joint: boolean;
  } | null;
  leaderboard: LeaderboardRow[];
  models: PublicModel[];
  official_runs: PublicRun[];
  lab_runs: PublicRun[];
}

export const dataset = rawDataset as PublishedDataset;

export const number = (value: string | number | null, digits = 2): string =>
  value === null
    ? "—"
    : new Intl.NumberFormat("en", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(Number(value));

export const percent = (value: string | null): string =>
  value === null
    ? "—"
    : new Intl.NumberFormat("en", {
        style: "percent",
        maximumFractionDigits: 0,
      }).format(Number(value));

export const money = (value: string | null): string =>
  value === null
    ? "—"
    : new Intl.NumberFormat("en", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(Number(value));

export const moneyDetailed = (value: string): string =>
  new Intl.NumberFormat("en", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(value));

export const date = (value: string | null): string =>
  value === null
    ? "—"
    : new Intl.DateTimeFormat("en", {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      }).format(new Date(value));

export const dateTime = (value: string): string =>
  new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(value));

export const duration = (milliseconds: number): string => {
  const seconds = milliseconds / 1_000;
  return seconds < 60
    ? `${number(seconds, 1)} s`
    : `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
};

export const seconds = (milliseconds: number): string =>
  number(milliseconds / 1_000, 1);

const REASON_LABELS: Record<string, string> = {
  incomplete: "Incomplete",
  experimental: "Experimental protocol",
  infrastructure_failures: "Infrastructure failures",
  not_publication_eligible: "Not publication eligible",
  benchmark_mismatch: "Different benchmark",
  subject_cohort_mismatch: "Different subjects",
  subject_catalog_mismatch: "Subject catalog changed",
  iteration_mismatch: "Different trial count",
  seed_mismatch: "Different seed",
  question_limit_mismatch: "Different question limit",
  model_not_in_cohort: "Outside active cohort",
  configuration_mismatch: "Model configuration changed",
  trial_coverage_mismatch: "Missing trials",
  scoring_coverage_mismatch: "Incomplete scoring",
  publication_coverage_mismatch: "Incomplete publication coverage",
};

export const reasonLabel = (reason: string): string =>
  REASON_LABELS[reason] ?? reason.replaceAll("_", " ");

const REASONING_EFFORT_LABELS: Record<string, string> = {
  none: "None",
  minimal: "Minimal",
  low: "Low",
  medium: "Medium",
  high: "High",
  "extra-high": "Extra high",
  xhigh: "Extra high",
  max: "Maximum",
  default: "Default",
};

export const reasoningEffortLabel = (effort: string): string => {
  const normalized = effort.trim().toLowerCase().replaceAll("_", "-");
  return (
    REASONING_EFFORT_LABELS[normalized] ??
    normalized.replaceAll("-", " ").replace(/\b\w/g, (character) => character.toUpperCase())
  );
};
