export interface SiteMetadata {
  title: string;
  short_title: string;
  description: string;
  base_path: string;
  creator_name: string;
  citation_label: string;
}

export interface ScorePolicy {
  version: "average-then-average-v1";
  failure_penalty_offset: number;
}

export interface CohortConfig {
  cohort_id: string;
  display_name: string;
  active: boolean;
  benchmark_id: string;
  benchmark_version: number;
  target_ids: string[];
  iterations: number;
  base_seed: number;
  max_questions: number;
  model_ids: string[];
}

export interface DatasetProvenance {
  built_at: string;
  source_run_count: number;
  official_run_count: number;
  lab_run_count: number;
  latest_completed_at: string | null;
  subject_catalog_hash: string;
}

export interface Winner {
  model_ids: string[];
  display_names: string[];
  question_score: string;
  joint: boolean;
}

export interface PublicModel {
  model_id: string;
  display_name: string;
  route: string;
  provider: string;
  reasoning_effort: string;
  seed_capability: string;
  configuration_hash: string;
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

export type EfficiencyStatus =
  | "ranked"
  | "question_score_unavailable"
  | "recorded_guesser_cost_unavailable"
  | "no_terminal_episodes"
  | "no_guesser_calls";

export interface LeaderboardRow {
  rank: number | null;
  model: PublicModel;
  efficiency_rank: number | null;
  pareto_efficient: boolean;
  status: "evaluated" | "awaiting_official_run";
  execution_id: string | null;
  completed_at: string | null;
  question_score: string | null;
  success_rate: string | null;
  total_cost_usd: string | null;
  guesser_cost_per_episode_usd: string | null;
  full_cost_per_episode_usd: string | null;
  runtime_per_episode_ms: string | null;
  guesser_think_time_per_episode_ms: string | null;
  guesser_latency_per_call_ms: string | null;
  cost_adjusted_question_score: string | null;
  efficiency_status: EfficiencyStatus;
  successful: number;
  terminal_trials: number;
  contract: ContractReliability | null;
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
  guesser_calls: number;
}

export interface PublicRunComparison {
  guesser_cost_per_episode_usd: string | null;
  full_cost_per_episode_usd: string | null;
  support_cost_per_episode_usd: string | null;
  support_cost_share: string | null;
  runtime_per_episode_ms: string | null;
  guesser_think_time_per_episode_ms: string | null;
  guesser_latency_per_call_ms: string | null;
  cost_adjusted_question_score: string | null;
  efficiency_status: EfficiencyStatus;
}

export interface PublicRunSummary {
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
  question_score: string | null;
  total_cost_usd: string;
  successful: number;
  model_failed: number;
  infrastructure_failed: number;
  terminal_trials: number;
  contract: ContractReliability;
  totals: PublicRunTotals;
  comparison: PublicRunComparison;
}

export interface PublicSubjectSummary {
  target_id: string;
  display_name: string;
  entity_type: string;
  success_rate: string | null;
  average_questions: string | null;
  successful: number;
  model_failed: number;
  infrastructure_failed: number;
  contract: ContractReliability;
}

export interface PublicTrialSummary {
  trial_id: string;
  trial_number: number;
  status: "success" | "model_failure" | "infrastructure_failure";
  counted_questions: number;
  penalized_questions: string | null;
  cost_usd: string;
  duration_ms: number;
  contract: ContractReliability | null;
  failure_code: string | null;
}

export interface PublicEvidence {
  source_url: string;
  excerpt: string;
  validation: "model_reported";
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

export interface PublicationRunReference {
  execution_id: string;
  model_id: string;
  model_name: string;
  classification: "official" | "lab";
}

export interface ManifestDocument {
  document_type: "manifest";
  schema_version: 1;
  dataset_schema_version: 5;
  site: SiteMetadata;
  score_policy: ScorePolicy;
  active_cohort: CohortConfig;
  provenance: DatasetProvenance;
  winner: Winner | null;
  models: PublicModel[];
  official_runs: PublicationRunReference[];
  lab_runs: PublicationRunReference[];
}

export interface LeaderboardDocument {
  document_type: "leaderboard";
  schema_version: 1;
  leaderboard: LeaderboardRow[];
}

export interface RunDocument {
  document_type: "run";
  schema_version: 1;
  run: PublicRunSummary;
  subjects: PublicSubjectSummary[];
}

export interface SubjectDocument {
  document_type: "subject";
  schema_version: 1;
  execution_id: string;
  target_id: string;
  profile: {
    subject_name: string;
    subject_description: string;
    subject_reference_url: string | null;
  };
  trials: PublicTrialSummary[];
}

export interface EpisodeDocument {
  document_type: "episode";
  schema_version: 1;
  execution_id: string;
  target_id: string;
  trial_id: string;
  episode: PublicEpisodeDetail;
}
