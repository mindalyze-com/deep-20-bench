<script setup lang="ts">
import { computed, nextTick, onActivated, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getEpisode } from "@/lib/api";
import {
  dateTime,
  duration,
  integer,
  money,
  moneyDetailed,
  number,
  percent,
  reasoningEffortLabel,
  seconds,
  statusLabel,
} from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type {
  EpisodeDocument,
  PublicComponentTelemetry,
  PublicContractViolationTurn,
  PublicOracleSupportRole,
  PublicTrialSummary,
} from "@/lib/types";
import {
  useRunWorkspace,
  useSubjectWorkspace,
} from "@/lib/workspace-context";

const route = useRoute();
const { document: runDocument, run } = useRunWorkspace();
const { document: subjectDocument, subject } = useSubjectWorkspace();
const episodeDocument = ref<EpisodeDocument | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
type EpisodeTab = "transcript" | "reliability" | "usage";
const activeTab = ref<EpisodeTab>("transcript");
const episodeTabs: EpisodeTab[] = ["transcript", "reliability", "usage"];

const executionId = computed(() => String(route.params.executionId ?? ""));
const targetId = computed(() => String(route.params.targetId ?? ""));
const trialId = computed(() => String(route.params.trialId ?? ""));
const trial = computed(
  () =>
    subjectDocument.value?.trials.find(
      (candidate) => candidate.trial_id === trialId.value,
    ) ?? null,
);
const episode = computed(() => episodeDocument.value?.episode ?? null);
const episodeTrials = computed(() =>
  (subjectDocument.value?.trials ?? []).filter(
    (candidate) => candidate.status !== "infrastructure_failure",
  ),
);
const episodeIndex = computed(() =>
  episodeTrials.value.findIndex(
    (candidate) => candidate.trial_id === trialId.value,
  ),
);
const evidenceCount = computed(
  () =>
    episode.value?.turns.reduce(
      (total, turn) =>
        total + (turn.turn_type === "action" ? turn.evidence.length : 0),
      0,
    ) ?? 0,
);
const violationTurns = computed(() =>
  episode.value?.turns.filter(
    (turn): turn is PublicContractViolationTurn =>
      turn.turn_type === "contract_violation",
  ) ?? [],
);
const turnMap = computed(() =>
  (episode.value?.turns ?? []).map((turn) => {
    if (turn.turn_type === "contract_violation") {
      return {
        turnNumber: turn.turn_number,
        marker: turn.counted ? `Q${turn.counted_questions}` : "END",
        answer: "FORMAT",
        tone: "format",
        label: `Turn ${turn.turn_number}: output contract violation`,
      };
    }
    const actionLabel =
      turn.action === "ASK"
        ? turn.question ?? "Question"
        : `Guess: ${turn.guess_name ?? "Unnamed guess"}`;
    return {
      turnNumber: turn.turn_number,
      marker: turn.counted ? `Q${turn.counted_questions}` : "G",
      answer: turn.answer,
      tone: turn.answer.toLowerCase(),
      label: `Turn ${turn.turn_number}: ${actionLabel}. ${turn.answer}`,
    };
  }),
);
const answerCounts = computed(() =>
  turnMap.value.reduce(
    (counts, turn) => {
      if (turn.tone === "yes") counts.yes += 1;
      else if (turn.tone === "no") counts.no += 1;
      else if (turn.tone === "unknown") counts.unknown += 1;
      else counts.format += 1;
      return counts;
    },
    { yes: 0, no: 0, unknown: 0, format: 0 },
  ),
);

const violationDetails = {
  invalid_json: {
    label: "Invalid JSON",
    description: "The response could not be decoded as one complete JSON action.",
  },
  invalid_action: {
    label: "Invalid action",
    description:
      "The response contained JSON, but it did not match either allowed ASK or GUESS action.",
  },
  output_limit_exceeded: {
    label: "Output limit exceeded",
    description:
      "The provider reached the configured output limit before returning a complete action.",
  },
  empty_output: {
    label: "Empty output",
    description: "The provider completed without returning any action text.",
  },
  incomplete_output: {
    label: "Incomplete output",
    description: "The provider call ended without returning a completed structured action.",
  },
} satisfies Record<
  PublicContractViolationTurn["violation_kind"],
  { label: string; description: string }
>;

interface TelemetryRow {
  role: string;
  values: PublicComponentTelemetry;
}

interface SupportRow {
  role: string;
  description: string;
  values: PublicOracleSupportRole;
}

const telemetryRows = computed<TelemetryRow[]>(() => {
  const current = episode.value;
  if (current === null) return [];
  return [
    { role: "Guesser", values: current.telemetry.guesser },
    { role: "Oracle support", values: current.telemetry.oracle },
    { role: "Validator", values: current.telemetry.validator },
  ];
});

const supportRows = computed<SupportRow[]>(() => {
  const current = episode.value;
  if (current === null) return [];
  return [
    {
      role: "Primary Oracle",
      description: "Searches evidence and proposes an answer.",
      values: current.oracle_support.oracle,
    },
    {
      role: "Reviewer",
      description: "Checks each Oracle YES or NO independently.",
      values: current.oracle_support.reviewer,
    },
    {
      role: "Judge",
      description: "Decides when the Oracle and Reviewer disagree.",
      values: current.oracle_support.judge,
    },
  ];
});

const sourceLabel = (sourceUrl: string): string => {
  try {
    return new URL(sourceUrl).hostname.replace(/^www\./, "");
  } catch {
    return "source";
  }
};

const jumpToTurn = (turnNumber: number): void => {
  const target = document.getElementById(`turn-${turnNumber}`);
  if (target === null) return;
  target.focus({ preventScroll: true });
  target.scrollIntoView({
    block: "start",
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth",
  });
};

const selectEpisodeTab = (tab: EpisodeTab, focus = false): void => {
  activeTab.value = tab;
  if (!focus) return;
  void nextTick(() => {
    document.getElementById(`episode-tab-${tab}`)?.focus();
  });
};

const onEpisodeTabKeydown = (event: KeyboardEvent, current: EpisodeTab): void => {
  const currentIndex = episodeTabs.indexOf(current);
  let nextIndex: number | null = null;
  if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % episodeTabs.length;
  else if (event.key === "ArrowLeft") {
    nextIndex = (currentIndex - 1 + episodeTabs.length) % episodeTabs.length;
  } else if (event.key === "Home") nextIndex = 0;
  else if (event.key === "End") nextIndex = episodeTabs.length - 1;
  if (nextIndex === null) return;
  event.preventDefault();
  const next = episodeTabs[nextIndex];
  if (next !== undefined) selectEpisodeTab(next, true);
};

const episodeTo = (candidate: PublicTrialSummary) => ({
  name: "episode" as const,
  params: {
    executionId: executionId.value,
    targetId: targetId.value,
    trialId: candidate.trial_id,
  },
});

const applyRouteContext = (): void => {
  const currentRun = run.value;
  const currentSubject = subject.value;
  const currentTrial = trial.value;
  const index = episodeIndex.value;
  if (
    currentRun === null ||
    currentSubject === null ||
    currentTrial === null ||
    index < 0
  ) {
    return;
  }
  const previousTrial = episodeTrials.value[index - 1];
  const nextTrial = episodeTrials.value[index + 1];
  setRouteContext({
    title: `Episode ${currentTrial.trial_number} · ${currentSubject.display_name}`,
    description: `Questions, answers, and Oracle evidence for finding ${currentSubject.display_name}.`,
    level: "Episode",
    position: `${index + 1} of ${episodeTrials.value.length}`,
    crumbs: [
      { label: "Results", to: { name: "results" } },
      {
        label: currentRun.model_name,
        to: {
          name: "run",
          params: { executionId: currentRun.execution_id },
        },
      },
      {
        label: currentSubject.display_name,
        to: {
          name: "subject",
          params: {
            executionId: currentRun.execution_id,
            targetId: currentSubject.target_id,
          },
        },
      },
      { label: `Episode ${currentTrial.trial_number}` },
    ],
    previous: previousTrial
      ? { label: `Episode ${previousTrial.trial_number}`, to: episodeTo(previousTrial) }
      : null,
    next: nextTrial
      ? { label: `Episode ${nextTrial.trial_number}`, to: episodeTo(nextTrial) }
      : null,
  });
};

const load = async (): Promise<void> => {
  const requestedExecution = executionId.value;
  const requestedTarget = targetId.value;
  const requestedTrial = trialId.value;
  loading.value = true;
  error.value = null;
  activeTab.value = "transcript";
  episodeDocument.value = null;
  try {
    const loadedEpisode = await getEpisode(
      requestedExecution,
      requestedTarget,
      requestedTrial,
    );
    if (
      executionId.value !== requestedExecution ||
      targetId.value !== requestedTarget ||
      trialId.value !== requestedTrial
    ) {
      return;
    }
    if (
      !runDocument.value?.subjects.some(
        (candidate) => candidate.target_id === requestedTarget,
      ) ||
      !subjectDocument.value?.trials.some(
        (candidate) => candidate.trial_id === requestedTrial,
      )
    ) {
      throw new Error("The requested episode is not part of this run.");
    }
    episodeDocument.value = loadedEpisode;
    applyRouteContext();
  } catch (cause: unknown) {
    if (
      executionId.value !== requestedExecution ||
      targetId.value !== requestedTarget ||
      trialId.value !== requestedTrial
    ) {
      return;
    }
    episodeDocument.value = null;
    error.value = cause instanceof Error ? cause.message : "The episode could not be loaded.";
  } finally {
    if (
      executionId.value === requestedExecution &&
      targetId.value === requestedTarget &&
      trialId.value === requestedTrial
    ) {
      loading.value = false;
    }
  }
};

watch([executionId, targetId, trialId], () => void load(), { immediate: true });
onActivated(applyRouteContext);
</script>

<template>
  <div class="episode-view">
    <LoadingState v-if="loading" label="Loading episode" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else-if="run && subject && trial && episode">
      <header id="episode-overview" class="episode-hero">
        <div class="episode-hero-inner">
          <div class="episode-summary">
            <p class="eyebrow">Episode {{ trial.trial_number }}</p>
            <h1>Episode {{ trial.trial_number }}</h1>
            <p class="episode-deck">
              <template v-if="episode.success">
                Identified <em>{{ episode.subject_name }}</em> in
                {{ episode.counted_questions }} counted questions.
              </template>
              <template v-else>
                Did not identify <em>{{ episode.subject_name }}</em> after
                {{ episode.counted_questions }} counted questions.
              </template>
            </p>
            <RouterLink
              class="subject-return"
              :to="{
                name: 'subject',
                params: {
                  executionId: run.execution_id,
                  targetId: subject.target_id,
                },
              }"
            >
              Back to {{ subject.display_name }} attempts
              <span aria-hidden="true">↑</span>
            </RouterLink>
          </div>

          <dl class="episode-facts" aria-label="Episode summary">
            <div>
              <dt>Outcome</dt>
              <dd>
                <span
                  class="outcome-dot"
                  :class="{ success: episode.success }"
                  aria-hidden="true"
                ></span>
                {{ episode.success ? "Success" : statusLabel(episode.terminal_reason) }}
              </dd>
            </div>
            <div>
              <dt>Questions</dt>
              <dd>
                {{ trial.counted_questions }}
                <small>Penalized {{ number(trial.penalized_questions) }}</small>
              </dd>
            </div>
            <div>
              <dt>Output contract</dt>
              <dd>{{ statusLabel(episode.contract.status) }}</dd>
            </div>
            <div><dt>Duration</dt><dd>{{ duration(episode.duration_ms) }}</dd></div>
            <div>
              <dt>Episode cost</dt>
              <dd>
                {{ money(episode.total_cost_usd) }}
                <small>All {{ episode.total_turns }} turns</small>
              </dd>
            </div>
          </dl>
        </div>
      </header>

      <nav class="episode-tabs" aria-label="Episode detail views" role="tablist">
        <button
          id="episode-tab-transcript"
          type="button"
          role="tab"
          aria-controls="transcript"
          :aria-selected="activeTab === 'transcript'"
          :tabindex="activeTab === 'transcript' ? 0 : -1"
          @click="selectEpisodeTab('transcript')"
          @keydown="onEpisodeTabKeydown($event, 'transcript')"
        >
          <span>Transcript</span>
          <small>{{ episode.turns.length }} turns</small>
        </button>
        <button
          id="episode-tab-reliability"
          type="button"
          role="tab"
          aria-controls="reliability"
          :aria-selected="activeTab === 'reliability'"
          :tabindex="activeTab === 'reliability' ? 0 : -1"
          @click="selectEpisodeTab('reliability')"
          @keydown="onEpisodeTabKeydown($event, 'reliability')"
        >
          <span>Reliability</span>
          <small>{{ episode.contract.violations }} violations</small>
        </button>
        <button
          id="episode-tab-usage"
          type="button"
          role="tab"
          aria-controls="technical"
          :aria-selected="activeTab === 'usage'"
          :tabindex="activeTab === 'usage' ? 0 : -1"
          @click="selectEpisodeTab('usage')"
          @keydown="onEpisodeTabKeydown($event, 'usage')"
        >
          <span>Models & usage</span>
          <small>{{ money(episode.total_cost_usd) }}</small>
        </button>
      </nav>

      <section
        v-if="episode.contract.status === 'breached'"
        class="contract-warning"
        aria-labelledby="episode-contract-heading"
      >
        <div class="content-inner warning">
          <div>
            <p class="eyebrow">Reliability warning</p>
            <h2 id="episode-contract-heading">Model broke the output contract.</h2>
          </div>
          <div>
            <p>
              The Guesser produced {{ episode.contract.violations }} invalid structured
              responses. Violations before the limit consumed counted turns. The fixed feedback
              disclosed only the public action format, never whether an attempted answer was
              correct.
            </p>
            <dl class="warning-facts">
              <div><dt>Compliance</dt><dd>{{ percent(episode.contract.compliance_rate) }}</dd></div>
              <div><dt>Violations</dt><dd>{{ episode.contract.violations }}</dd></div>
              <div><dt>Turn penalties</dt><dd>{{ episode.contract.counted_penalties }}</dd></div>
            </dl>
          </div>
        </div>
      </section>

      <div class="episode-content">
        <section
          v-show="activeTab === 'transcript'"
          id="transcript"
          class="content-section transcript"
          role="tabpanel"
          aria-labelledby="episode-tab-transcript transcript-heading"
          tabindex="0"
        >
          <div class="content-inner">
            <header class="section-heading">
              <div>
                <p class="eyebrow">Transcript</p>
                <h2 id="transcript-heading">Questions and answers.</h2>
              </div>
              <p>
                Turns appear in recorded order. Each action shows the Guesser first, followed by
                the adjudicated Oracle or Validator token.
              </p>
            </header>

            <details v-if="episode.guesser_disclosure" class="disclosure setup-disclosure">
              <summary>
                <span>
                  <strong>Exact Guesser setup</strong>
                  <small>System message and BEGIN event</small>
                </span>
                <span aria-hidden="true">Open details ↓</span>
              </summary>
              <div class="setup-body">
                <p>
                  These messages introduced this episode to the Guesser. The BEGIN event
                  contains the broad category and an opaque subject-independent variation token.
                </p>
                <article>
                  <span>System message</span>
                  <pre>{{ episode.guesser_disclosure.system_message }}</pre>
                </article>
                <article>
                  <span>BEGIN event</span>
                  <pre>{{ episode.guesser_disclosure.begin_message }}</pre>
                </article>
                <p class="detail-note">
                  Published recorded outputs are canonical structured actions. Malformed provider
                  completions remain in owner-only diagnostics and are not shown here.
                </p>
              </div>
            </details>

            <nav class="turn-map" aria-labelledby="turn-map-title">
              <header>
                <div>
                  <p class="eyebrow">Turn map</p>
                  <h3 id="turn-map-title">The path to the guess.</h3>
                </div>
                <p>Select a marker to jump to that turn.</p>
              </header>
              <ol>
                <li v-for="turn in turnMap" :key="turn.turnNumber">
                  <button
                    type="button"
                    :class="`tone-${turn.tone}`"
                    :aria-label="turn.label"
                    @click="jumpToTurn(turn.turnNumber)"
                  >
                    <span>{{ turn.marker }}</span>
                    <strong>{{ turn.answer }}</strong>
                  </button>
                </li>
              </ol>
              <footer aria-label="Turn answer totals">
                <span><i class="tone-yes" aria-hidden="true"></i>{{ answerCounts.yes }} YES</span>
                <span><i class="tone-no" aria-hidden="true"></i>{{ answerCounts.no }} NO</span>
                <span
                  ><i class="tone-unknown" aria-hidden="true"></i
                  >{{ answerCounts.unknown }} UNKNOWN</span
                >
                <span v-if="answerCounts.format > 0"
                  ><i class="tone-format" aria-hidden="true"></i
                  >{{ answerCounts.format }} FORMAT</span
                >
              </footer>
            </nav>

            <div class="turn-list">
              <article
                v-for="turn in episode.turns"
                :key="turn.turn_number"
                :id="`turn-${turn.turn_number}`"
                class="turn"
                tabindex="-1"
                :class="{
                  guess: turn.turn_type === 'action' && turn.action === 'GUESS',
                  violation: turn.turn_type === 'contract_violation',
                }"
              >
                <div class="turn-marker">
                  <span>
                    {{
                      turn.counted
                        ? `Q${turn.counted_questions}`
                        : turn.turn_type === "action"
                          ? "G"
                          : "END"
                    }}
                  </span>
                  <i aria-hidden="true"></i>
                </div>

                <template v-if="turn.turn_type === 'action'">
                  <div class="turn-body">
                    <div class="turn-label">
                      <span>
                        {{ turn.action === "ASK" ? "1 · Guesser asks" : "1 · Guesser guesses" }}
                      </span>
                      <span v-if="!turn.counted">No question charge</span>
                    </div>
                    <h3>
                      {{ turn.action === "ASK" ? turn.question : turn.guess_name }}
                    </h3>
                    <p v-if="turn.guess_description" class="guess-description">
                      {{ turn.guess_description }}
                    </p>
                    <p v-if="turn.validator_explanation" class="validator-note">
                      <strong>Validator rationale</strong>
                      {{ turn.validator_explanation }}
                    </p>

                    <details v-if="turn.recorded_output" class="disclosure turn-disclosure">
                      <summary>
                        <span>
                          <strong>Recorded Guesser output</strong>
                          <small>Canonical structured JSON</small>
                        </span>
                        <span aria-hidden="true">View ↓</span>
                      </summary>
                      <pre>{{ turn.recorded_output }}</pre>
                    </details>

                    <details v-if="turn.evidence.length" class="disclosure turn-disclosure evidence">
                      <summary>
                        <span>
                          <strong>Oracle evidence</strong>
                          <small>
                            {{ turn.evidence.length }} model-reported
                            {{ turn.evidence.length === 1 ? "source" : "sources" }}
                          </small>
                        </span>
                        <span aria-hidden="true">View ↓</span>
                      </summary>
                      <p class="detail-note">
                        The Oracle reported these excerpts and URLs. They are not independently
                        checked.
                      </p>
                      <div class="evidence-list">
                        <article v-for="(item, index) in turn.evidence" :key="`${item.source_url}-${index}`">
                          <span>Source {{ String(index + 1).padStart(2, "0") }}</span>
                          <blockquote>{{ item.excerpt }}</blockquote>
                          <a :href="item.source_url" target="_blank" rel="noreferrer">
                            Open {{ sourceLabel(item.source_url) }}
                            <span aria-hidden="true">↗</span>
                            <span class="visually-hidden">(opens in a new tab)</span>
                          </a>
                        </article>
                      </div>
                    </details>
                  </div>

                  <div class="answer" :class="`answer-${turn.answer.toLowerCase()}`">
                    <span>
                      2 · {{ turn.adjudicator === "oracle" ? "Oracle" : "Validator" }} answers
                    </span>
                    <strong>{{ turn.answer }}</strong>
                  </div>
                </template>

                <template v-else>
                  <div class="turn-body">
                    <div class="turn-label">
                      <span>1 · Guesser output rejected</span>
                      <span>{{ turn.counted ? "Turn charged" : "Limit reached" }}</span>
                    </div>
                    <h3>Model broke the output contract.</h3>
                    <p class="guess-description">
                      {{ violationDetails[turn.violation_kind].label }} ·
                      {{
                        turn.feedback_event === "FORMAT_ERROR"
                          ? "fixed format reminder sent"
                          : "episode ended without another retry"
                      }}
                    </p>
                    <details class="disclosure turn-disclosure violation-detail">
                      <summary>
                        <span>
                          <strong>Why this output was rejected</strong>
                          <small>
                            {{ violationDetails[turn.violation_kind].label }} · turn
                            {{ turn.turn_number }}
                          </small>
                        </span>
                        <span aria-hidden="true">View ↓</span>
                      </summary>
                      <div class="violation-body">
                        <p>{{ violationDetails[turn.violation_kind].description }}</p>
                        <dl>
                          <div>
                            <dt>Recorded type</dt>
                            <dd><code>{{ turn.violation_kind }}</code></dd>
                          </div>
                          <div><dt>Turn</dt><dd>{{ turn.turn_number }}</dd></div>
                          <div>
                            <dt>Question charge</dt>
                            <dd>{{ turn.counted ? `Yes · Q${turn.counted_questions}` : "No" }}</dd>
                          </div>
                          <div><dt>Feedback</dt><dd>{{ turn.feedback_event ?? "No retry" }}</dd></div>
                        </dl>
                        <p class="detail-note">
                          The malformed provider text is excluded from the public dataset. The
                          full completion stays in the isolated owner-only diagnostic artifact.
                        </p>
                      </div>
                    </details>
                  </div>
                  <div class="answer answer-format">
                    <span>2 · Protocol response</span>
                    <strong>FORMAT</strong>
                  </div>
                </template>
              </article>
            </div>
          </div>
        </section>

        <section
          v-show="activeTab === 'reliability'"
          id="reliability"
          class="content-section reliability"
          role="tabpanel"
          aria-labelledby="episode-tab-reliability reliability-heading"
          tabindex="0"
        >
          <div class="content-inner">
            <header class="section-heading">
              <div>
                <p class="eyebrow">Independent aspect</p>
                <h2 id="reliability-heading">Output-contract reliability.</h2>
              </div>
              <p>
                Gameplay success and contract compliance are separate. Counted-turn penalties
                already affect the question total; this section does not add another penalty.
              </p>
            </header>
            <dl class="reliability-grid">
              <div><dt>Status</dt><dd>{{ statusLabel(episode.contract.status) }}</dd></div>
              <div><dt>Valid outputs</dt><dd>{{ episode.contract.valid_outputs }}</dd></div>
              <div><dt>Evaluated outputs</dt><dd>{{ episode.contract.evaluated_outputs }}</dd></div>
              <div><dt>Compliance</dt><dd>{{ percent(episode.contract.compliance_rate) }}</dd></div>
              <div><dt>Violations</dt><dd>{{ episode.contract.violations }}</dd></div>
              <div>
                <dt>Counted-turn penalties</dt>
                <dd>{{ episode.contract.counted_penalties }}</dd>
              </div>
            </dl>
            <section
              v-if="episode.contract.status === 'breached'"
              class="violation-summary"
              aria-labelledby="violation-summary-title"
            >
              <header>
                <p class="eyebrow">Recorded violations</p>
                <h3 id="violation-summary-title">Where the contract broke.</h3>
              </header>
              <ol>
                <li v-for="turn in violationTurns" :key="turn.turn_number">
                  <span>Turn {{ turn.turn_number }}</span>
                  <strong>{{ violationDetails[turn.violation_kind].label }}</strong>
                  <p>{{ violationDetails[turn.violation_kind].description }}</p>
                  <small>
                    {{ turn.counted ? `Counted as Q${turn.counted_questions}` : "No turn charge" }}
                    · {{ turn.feedback_event ?? "No retry" }}
                  </small>
                </li>
              </ol>
            </section>
          </div>
        </section>

        <section
          v-show="activeTab === 'usage'"
          id="technical"
          class="content-section technical"
          role="tabpanel"
          aria-labelledby="episode-tab-usage technical-heading"
          tabindex="0"
        >
          <div class="content-inner">
            <header class="section-heading">
              <div>
                <p class="eyebrow">Technical details</p>
                <h2 id="technical-heading">Models and usage.</h2>
              </div>
              <p>
                Models, prompt versions, tokens, cache use, latency, and recorded cost for this
                episode.
              </p>
            </header>

            <div class="technical-context">
              <article>
                <span>Hidden subject</span>
                <strong>{{ episode.subject_name }}</strong>
                <p>{{ episode.subject_description }}</p>
                <a
                  v-if="episode.subject_reference_url"
                  :href="episode.subject_reference_url"
                  target="_blank"
                  rel="noreferrer"
                >
                  Subject reference <span aria-hidden="true">↗</span>
                  <span class="visually-hidden">(opens in a new tab)</span>
                </a>
              </article>
              <article>
                <span>Episode scope</span>
                <strong>{{ money(episode.total_cost_usd) }} across {{ episode.total_turns }} turns</strong>
                <p>
                  Includes {{ evidenceCount }} evidence
                  {{ evidenceCount === 1 ? "item" : "items" }} and all model activity for this
                  episode.
                </p>
                <RouterLink
                  :to="{
                    name: 'run',
                    params: { executionId: run.execution_id },
                  }"
                >
                  Full run {{ money(run.total_cost_usd) }} <span aria-hidden="true">→</span>
                </RouterLink>
              </article>
              <article>
                <span>Public post-run view</span>
                <strong>Published actions, bounded detail</strong>
                <p>
                  Typed actions and canonical stored outputs are public. Malformed completions,
                  adjudicator prompts, hidden reasoning, and provider payloads are excluded.
                </p>
              </article>
            </div>

            <div class="model-grid">
              <article
                v-for="model in episode.models"
                :key="`${model.role}-${model.requested_model}`"
                :class="{ tested: model.role === 'guesser' }"
              >
                <span>
                  {{
                    model.role === "guesser"
                      ? "Model under test · Guesser · scored"
                      : `Benchmark support · ${statusLabel(model.role)} · not scored`
                  }}
                </span>
                <h3>{{ model.requested_model }}</h3>
                <p>
                  {{ model.requested_provider }} ·
                  {{ reasoningEffortLabel(model.reasoning_effort) }} reasoning
                </p>
                <dl>
                  <div>
                    <dt>Resolved model</dt>
                    <dd>{{ model.resolved_models.join(", ") || "Not reported" }}</dd>
                  </div>
                  <div>
                    <dt>Resolved provider</dt>
                    <dd>{{ model.resolved_providers.join(", ") || "Not reported" }}</dd>
                  </div>
                  <div><dt>Prompt contract</dt><dd><code>{{ model.prompt_version }}</code></dd></div>
                  <div>
                    <dt>Configuration</dt>
                    <dd><code>{{ model.configuration_id ?? "role-local" }}</code></dd>
                  </div>
                </dl>
              </article>
            </div>

            <section class="support-section" aria-labelledby="support-heading">
              <header>
                <p class="eyebrow">Oracle support</p>
                <h3 id="support-heading">Blind review roles.</h3>
              </header>
              <div class="support-grid">
                <article v-for="row in supportRows" :key="row.role">
                  <span>{{ row.role }}</span>
                  <strong>{{ row.values.requested_model }}</strong>
                  <p>{{ row.description }}</p>
                  <dl>
                    <div><dt>Calls</dt><dd>{{ row.values.calls }}</dd></div>
                    <div><dt>Cost</dt><dd>{{ money(row.values.cost_usd) }}</dd></div>
                    <div>
                      <dt>Reasoning</dt>
                      <dd>{{ reasoningEffortLabel(row.values.reasoning_effort) }}</dd>
                    </div>
                  </dl>
                </article>
              </div>
            </section>

            <div class="table-wrap telemetry-wrap" tabindex="0" aria-label="Scrollable component telemetry">
              <table class="data-table telemetry-table">
                <thead>
                  <tr>
                    <th>Component</th>
                    <th data-numeric>Calls</th>
                    <th data-numeric>Total tokens</th>
                    <th data-numeric>Input</th>
                    <th data-numeric>Cached input</th>
                    <th data-numeric>Cache write</th>
                    <th data-numeric>Output</th>
                    <th data-numeric>Reasoning</th>
                    <th data-numeric>Latency</th>
                    <th data-numeric>Cost</th>
                    <th data-numeric>Cache savings</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in telemetryRows" :key="row.role">
                    <th>{{ row.role }}</th>
                    <td data-numeric>{{ row.values.calls }}</td>
                    <td data-numeric>{{ integer(row.values.total_tokens) }}</td>
                    <td data-numeric>{{ integer(row.values.input_tokens) }}</td>
                    <td data-numeric>{{ integer(row.values.cached_input_tokens) }}</td>
                    <td data-numeric>{{ integer(row.values.cache_write_tokens) }}</td>
                    <td data-numeric>{{ integer(row.values.output_tokens) }}</td>
                    <td data-numeric>{{ integer(row.values.reasoning_tokens) }}</td>
                    <td data-numeric>{{ seconds(row.values.latency_ms) }} s</td>
                    <td data-numeric>{{ moneyDetailed(row.values.cost_usd) }}</td>
                    <td data-numeric>{{ moneyDetailed(row.values.estimated_cache_savings_usd) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <details class="disclosure provenance-details">
              <summary>
                <span>
                  <strong>IDs and timing</strong>
                  <small>Execution IDs, timestamps, and totals</small>
                </span>
                <span aria-hidden="true">View ↓</span>
              </summary>
              <dl>
                <div><dt>Execution</dt><dd><code>{{ run.execution_id }}</code></dd></div>
                <div><dt>Episode run</dt><dd><code>{{ episode.episode_run_id }}</code></dd></div>
                <div><dt>Episode</dt><dd><code>{{ episode.episode_id }}</code></dd></div>
                <div><dt>Trial</dt><dd><code>{{ trial.trial_id }}</code></dd></div>
                <div><dt>Started</dt><dd>{{ dateTime(episode.started_at) }}</dd></div>
                <div><dt>Completed</dt><dd>{{ dateTime(episode.completed_at) }}</dd></div>
                <div><dt>Git commit</dt><dd><code>{{ run.git_commit }}</code></dd></div>
                <div><dt>Cache status</dt><dd>{{ statusLabel(episode.cache_status) }}</dd></div>
                <div><dt>Total tokens</dt><dd>{{ integer(episode.total_tokens) }}</dd></div>
                <div><dt>Episode cost</dt><dd>{{ money(episode.total_cost_usd) }}</dd></div>
              </dl>
            </details>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.episode-hero {
  background: var(--ink);
  color: white;
  scroll-margin-top: 1rem;
}

.episode-hero-inner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(29rem, 0.9fr);
  gap: clamp(2.5rem, 6vw, 6rem);
  align-items: end;
  width: min(100%, var(--max));
  margin-inline: auto;
  padding: clamp(3rem, 6vw, 5rem) var(--gutter);
}

.episode-summary h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3.8rem, 7vw, 7rem);
  font-weight: 500;
  letter-spacing: -0.07em;
  line-height: 0.9;
}

.episode-deck {
  max-width: 36rem;
  margin: 1.4rem 0 0;
  color: rgb(255 255 255 / 72%);
  font-family: var(--font-text);
  font-size: clamp(1.25rem, 2.2vw, 2rem);
  line-height: 1.35;
}

.episode-deck em {
  color: var(--acid);
}

.subject-return {
  display: inline-block;
  margin-top: 1.5rem;
  color: var(--acid);
  font-size: 0.76rem;
  font-weight: 720;
}

.episode-facts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  margin: 0;
  border: 1px solid rgb(255 255 255 / 20%);
}

.episode-facts > div {
  min-width: 0;
  min-height: 7rem;
  padding: 1.1rem;
  border-right: 1px solid rgb(255 255 255 / 16%);
  border-bottom: 1px solid rgb(255 255 255 / 16%);
}

.episode-facts > div:nth-child(even) {
  border-right: 0;
}

.episode-facts > div:last-child {
  grid-column: 1 / -1;
  border-right: 0;
  border-bottom: 0;
}

.episode-facts dt,
.warning-facts dt,
.reliability-grid dt,
.technical-context article > span,
.model-grid article > span,
.model-grid dt,
.support-grid article > span,
.support-grid dt,
.violation-body dt,
.provenance-details dt {
  color: var(--muted);
  font-size: 0.62rem;
  font-weight: 780;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.episode-facts dt {
  color: rgb(255 255 255 / 55%);
}

.episode-facts dd {
  margin: 0.8rem 0 0;
  font-family: var(--font-display);
  font-size: 1.55rem;
}

.episode-facts dd small {
  display: block;
  margin-top: 0.35rem;
  color: rgb(255 255 255 / 55%);
  font-family: var(--font-sans);
  font-size: 0.62rem;
}

.outcome-dot {
  display: inline-block;
  width: 0.65rem;
  height: 0.65rem;
  margin-right: 0.4rem;
  border-radius: 50%;
  background: var(--coral);
}

.outcome-dot.success {
  background: var(--acid);
}

.contract-warning {
  padding: clamp(2rem, 5vw, 4rem) var(--gutter);
  border-block: 1px solid var(--coral);
  background: #fff5f1;
}

.warning > div:last-child > p {
  margin: 0;
  line-height: 1.65;
}

.warning-facts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 1.5rem 0 0;
  border: 1px solid var(--line);
}

.warning-facts div {
  padding: 0.9rem;
  border-right: 1px solid var(--line);
}

.warning-facts div:last-child {
  border-right: 0;
}

.warning-facts dd {
  margin: 0.35rem 0 0;
  font-weight: 760;
}

.transcript {
  padding-top: clamp(3.5rem, 7vw, 6rem);
}

.disclosure {
  border: 1px solid var(--line);
  background: var(--paper-bright);
}

.disclosure > summary {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.15rem;
  cursor: pointer;
  list-style: none;
}

.disclosure > summary::-webkit-details-marker {
  display: none;
}

.disclosure > summary > span:first-child {
  display: grid;
  gap: 0.25rem;
}

.disclosure > summary strong {
  font-size: 0.75rem;
}

.disclosure > summary small {
  color: var(--muted);
  font-size: 0.64rem;
}

.disclosure > summary > span:last-child {
  color: var(--blue-ink);
  font-size: 0.62rem;
  font-weight: 780;
  text-transform: uppercase;
}

.setup-disclosure {
  margin-bottom: 2rem;
}

.setup-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: clamp(1.2rem, 3vw, 2rem);
  border-top: 1px solid var(--line);
}

.setup-body > p:first-child,
.setup-body .detail-note {
  grid-column: 1 / -1;
}

.setup-body > p:first-child {
  max-width: 52rem;
  margin: 0 0 0.5rem;
  color: var(--muted);
  line-height: 1.65;
}

.setup-body article > span {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--muted);
  font-size: 0.62rem;
  font-weight: 760;
  text-transform: uppercase;
}

pre {
  max-width: 100%;
  margin: 0;
  padding: 1rem;
  overflow: auto;
  border: 1px solid rgb(255 255 255 / 18%);
  background: var(--ink);
  color: #f5f3ec;
  font: 0.72rem/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.detail-note {
  margin: 0;
  padding: 0.85rem 1rem;
  border-left: 3px solid var(--blue);
  background: #eef0ff;
  color: var(--ink-soft);
  font-size: 0.75rem;
  line-height: 1.55;
}

.turn-map {
  margin-bottom: 1.4rem;
  border: 1px solid var(--line);
  background: var(--paper-bright);
}

.turn-map > header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  padding: 1rem 1.1rem 0.9rem;
  border-bottom: 1px solid var(--line-soft);
}

.turn-map h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 500;
  letter-spacing: -0.035em;
}

.turn-map > header > p {
  margin: 0;
  color: var(--muted);
  font-size: 0.64rem;
}

.turn-map ol {
  display: flex;
  gap: 0.4rem;
  margin: 0;
  padding: 0.85rem 1rem;
  overflow-x: auto;
  list-style: none;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.turn-map li {
  flex: 0 0 auto;
}

.turn-map button {
  display: grid;
  width: 3.15rem;
  min-height: 3.15rem;
  padding: 0.35rem;
  place-content: center;
  border: 1px solid var(--line);
  background: white;
  color: var(--ink);
  cursor: pointer;
}

.turn-map button:hover {
  border-color: var(--ink);
}

.turn-map button span {
  font-family: var(--font-mono);
  font-size: 0.57rem;
}

.turn-map button strong {
  margin-top: 0.18rem;
  font-size: 0.55rem;
}

.turn-map button.tone-yes {
  border-bottom: 4px solid #72a93d;
}

.turn-map button.tone-no {
  border-bottom: 4px solid var(--coral);
}

.turn-map button.tone-unknown {
  border-bottom: 4px solid #d4a827;
}

.turn-map button.tone-format {
  border-bottom: 4px solid #8a72cf;
}

.turn-map > footer {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 1rem;
  padding: 0.7rem 1rem;
  border-top: 1px solid var(--line-soft);
  color: var(--muted);
  font-size: 0.58rem;
  font-weight: 700;
}

.turn-map > footer span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.turn-map > footer i {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
}

.turn-map > footer .tone-yes {
  background: #72a93d;
}

.turn-map > footer .tone-no {
  background: var(--coral);
}

.turn-map > footer .tone-unknown {
  background: #d4a827;
}

.turn-map > footer .tone-format {
  background: #8a72cf;
}

.turn-list {
  border-top: 1px solid var(--line);
}

.turn {
  display: grid;
  grid-template-columns: 3.5rem minmax(0, 1fr) minmax(8rem, 0.25fr);
  gap: clamp(1rem, 3vw, 2.5rem);
  padding: clamp(1.4rem, 3vw, 2.5rem) 0;
  scroll-margin-top: 1rem;
  border-bottom: 1px solid var(--line);
}

.turn-marker {
  display: grid;
  grid-template-rows: auto 1fr;
  justify-items: center;
  gap: 0.55rem;
}

.turn-marker span {
  display: grid;
  width: 2.8rem;
  height: 2.8rem;
  place-items: center;
  border: 1px solid var(--ink);
  background: var(--acid);
  font-size: 0.67rem;
  font-weight: 820;
}

.turn.guess .turn-marker span {
  background: var(--ink);
  color: var(--acid);
}

.turn.violation .turn-marker span {
  background: #ffc9bb;
}

.turn-marker i {
  width: 1px;
  min-height: 2rem;
  background: var(--line);
}

.turn-body {
  min-width: 0;
}

.turn-label {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: var(--muted);
  font-size: 0.62rem;
  font-weight: 760;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.turn-body h3 {
  margin: 1rem 0 0;
  font-family: var(--font-text);
  font-size: clamp(1.7rem, 3.3vw, 3rem);
  font-weight: 500;
  letter-spacing: -0.04em;
  line-height: 1.08;
  overflow-wrap: anywhere;
}

.guess-description {
  margin: 0.8rem 0 0;
  color: var(--muted);
  line-height: 1.65;
}

.validator-note {
  display: grid;
  gap: 0.35rem;
  margin: 1rem 0 0;
  padding: 0.9rem 1rem;
  border-left: 3px solid var(--blue);
  background: #eef0ff;
  line-height: 1.55;
}

.validator-note strong {
  color: var(--blue-ink);
  font-size: 0.62rem;
  text-transform: uppercase;
}

.turn-disclosure {
  margin-top: 1rem;
}

.turn-disclosure > pre,
.violation-body {
  border-top: 1px solid var(--line);
}

.evidence-list {
  display: grid;
  gap: 1px;
  padding-top: 1px;
  background: var(--line);
}

.evidence .detail-note {
  margin: 0 1rem 1rem;
}

.evidence-list article {
  padding: 1.1rem;
  background: var(--paper-bright);
}

.evidence-list article > span {
  color: var(--muted);
  font-size: 0.62rem;
  font-weight: 760;
  text-transform: uppercase;
}

.evidence-list blockquote {
  margin: 0.8rem 0;
  color: var(--ink-soft);
  line-height: 1.65;
}

.evidence-list a,
.technical-context a {
  color: var(--blue-ink);
  font-size: 0.75rem;
  font-weight: 720;
}

.answer {
  display: grid;
  align-content: center;
  justify-items: center;
  min-height: 7rem;
  padding: 1rem;
  background: var(--paper-bright);
  text-align: center;
}

.answer span {
  color: var(--muted);
  font-size: 0.57rem;
  font-weight: 760;
  text-transform: uppercase;
}

.answer strong {
  margin-top: 0.6rem;
  font-family: var(--font-sans);
  font-size: clamp(0.9rem, 1.6vw, 1.2rem);
  font-weight: 800;
  letter-spacing: 0.025em;
}

.answer-yes {
  background: #eff9e7;
}

.answer-no {
  background: #fff1ec;
}

.answer-unknown {
  background: #fff8d5;
}

.answer-format {
  background: #ffc9bb;
}

.violation-body {
  padding: 1rem;
}

.violation-body > p:first-child {
  margin-top: 0;
  line-height: 1.6;
}

.violation-body dl {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  margin: 1rem 0;
  border: 1px solid var(--line);
}

.violation-body dl div {
  min-width: 0;
  padding: 0.8rem;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.violation-body dd {
  margin: 0.35rem 0 0;
  overflow-wrap: anywhere;
}

.reliability {
  border-top: 7px solid var(--coral);
  background: #fff1ec;
}

.reliability-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 0;
  border: 1px solid var(--ink);
  background: var(--paper-bright);
}

.reliability-grid div {
  min-height: 7rem;
  padding: 1.1rem;
  border-right: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
}

.reliability-grid div:nth-child(3n) {
  border-right: 0;
}

.reliability-grid dd {
  margin: 0.8rem 0 0;
  font-family: var(--font-display);
  font-size: 1.8rem;
}

.technical {
  background: #f0eee7;
}

.technical-context,
.model-grid,
.support-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  border: 1px solid var(--line);
  background: var(--line);
}

.technical-context article,
.model-grid article,
.support-grid article {
  min-width: 0;
  padding: clamp(1.2rem, 3vw, 2rem);
  background: var(--paper-bright);
}

.technical-context strong,
.support-grid strong {
  display: block;
  margin-top: 0.7rem;
  overflow-wrap: anywhere;
}

.technical-context p,
.model-grid p,
.support-grid p {
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.6;
}

.model-grid {
  margin-top: 2rem;
}

.model-grid article.tested {
  box-shadow: inset 0 5px 0 var(--blue);
}

.model-grid h3 {
  margin: 1.2rem 0 0;
  font-family: var(--font-display);
  font-size: clamp(1.5rem, 2.6vw, 2.3rem);
  font-weight: 500;
  overflow-wrap: anywhere;
}

.model-grid dl,
.support-grid dl {
  margin: 1.2rem 0 0;
}

.model-grid dl div,
.support-grid dl div {
  padding: 0.7rem 0;
  border-top: 1px solid var(--line);
}

.model-grid dd,
.support-grid dd {
  margin: 0.3rem 0 0;
  font-size: 0.75rem;
  overflow-wrap: anywhere;
}

.support-section {
  margin-top: clamp(3rem, 7vw, 6rem);
}

.support-section > header h3 {
  margin: 0 0 1.5rem;
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3.8rem);
  font-weight: 500;
}

.telemetry-wrap {
  margin-top: 2rem;
}

.telemetry-table {
  min-width: 1120px;
}

.telemetry-table tbody th {
  font-size: 0.72rem;
}

.provenance-details {
  margin-top: 2rem;
}

.provenance-details > dl {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  margin: 0;
  border-top: 1px solid var(--line);
}

.provenance-details > dl > div {
  min-width: 0;
  padding: 1rem;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.provenance-details > dl > div:nth-child(even) {
  border-right: 0;
}

.provenance-details dd {
  margin: 0.4rem 0 0;
  font-size: 0.76rem;
  overflow-wrap: anywhere;
}

@media (max-width: 1080px) {
  .episode-hero-inner {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 780px) {
  .setup-body,
  .technical-context,
  .model-grid,
  .support-grid {
    grid-template-columns: 1fr;
  }

  .setup-body article,
  .setup-body > p:first-child,
  .setup-body .detail-note {
    grid-column: 1;
  }

  .turn {
    grid-template-columns: 2.8rem minmax(0, 1fr);
  }

  .answer {
    grid-column: 2;
    width: 100%;
    min-height: 4.8rem;
  }

  .turn-label {
    flex-direction: column;
  }

  .reliability-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .reliability-grid div:nth-child(3n) {
    border-right: 1px solid var(--ink);
  }

  .reliability-grid div:nth-child(even) {
    border-right: 0;
  }
}

@media (max-width: 560px) {
  .episode-hero-inner {
    padding-block: 3rem;
  }

  .episode-facts,
  .warning-facts,
  .reliability-grid,
  .violation-body dl,
  .provenance-details > dl {
    grid-template-columns: 1fr;
  }

  .episode-facts > div,
  .episode-facts > div:last-child,
  .warning-facts div,
  .reliability-grid div,
  .reliability-grid div:nth-child(3n),
  .provenance-details > dl > div {
    grid-column: 1;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .turn {
    gap: 0.8rem;
  }

  .disclosure > summary {
    align-items: flex-start;
  }

  .disclosure > summary > span:last-child {
    flex: 0 0 auto;
  }
}
</style>

<style scoped>
/* Workspace composition overrides the former long publication-page layout. */
.episode-view {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--paper);
}

.episode-view > .loading-state,
.episode-view > .error-state {
  grid-row: 1 / -1;
}

.episode-hero {
  border-bottom: 1px solid var(--line);
  background: var(--paper-bright);
  color: var(--ink);
}

.episode-hero-inner {
  display: grid;
  grid-template-columns: minmax(14rem, 0.55fr) minmax(0, 1.45fr);
  gap: clamp(1.5rem, 4vw, 4rem);
  align-items: end;
  width: 100%;
  max-width: none;
  padding: clamp(1.1rem, 2.5vw, 2rem) clamp(1rem, 3vw, 2.5rem);
}

.episode-summary .eyebrow {
  margin-bottom: 0.45rem;
  color: var(--blue-ink);
}

.episode-summary h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.7rem, 4vw, 4rem);
  font-weight: 500;
  letter-spacing: -0.055em;
  line-height: 0.92;
  white-space: nowrap;
}

.episode-deck {
  max-width: 38rem;
  margin: 0.75rem 0 0;
  color: var(--muted);
  font-family: var(--font-text);
  font-size: 0.88rem;
  line-height: 1.55;
}

.episode-deck em {
  color: var(--ink);
}

.subject-return {
  margin-top: 0.75rem;
  color: var(--blue-ink);
  font-size: 0.68rem;
}

.episode-facts {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  margin: 0;
  border: 1px solid var(--line);
  background: var(--line);
  gap: 1px;
}

.episode-facts > div,
.episode-facts > div:nth-child(even),
.episode-facts > div:last-child {
  grid-column: auto;
  min-width: 0;
  min-height: 0;
  padding: 0.8rem;
  border: 0;
  background: var(--paper-bright);
}

.episode-facts dt {
  color: var(--muted);
  font-size: 0.56rem;
}

.episode-facts dd {
  margin-top: 0.35rem;
  color: var(--ink);
  font-family: var(--font-text);
  font-size: 0.87rem;
  font-weight: 700;
}

.episode-facts dd small {
  margin-top: 0.14rem;
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 0.55rem;
}

.episode-tabs {
  display: flex;
  min-width: 0;
  overflow-x: auto;
  border-bottom: 1px solid var(--line);
  background: #e9e6dd;
  scrollbar-width: thin;
}

.episode-tabs button {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  gap: 0.18rem;
  min-width: 9.5rem;
  padding: 0.75rem 1.1rem 0.7rem;
  border: 0;
  border-right: 1px solid var(--line);
  color: var(--muted);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.episode-tabs button:hover {
  color: var(--ink);
  background: rgb(255 255 255 / 35%);
}

.episode-tabs button[aria-selected="true"] {
  color: var(--ink);
  background: var(--paper);
}

.episode-tabs button[aria-selected="true"]::after {
  position: absolute;
  right: 0.9rem;
  bottom: -1px;
  left: 0.9rem;
  height: 3px;
  background: var(--blue);
  content: "";
}

.episode-tabs span {
  font-size: 0.72rem;
  font-weight: 760;
}

.episode-tabs small {
  font-size: 0.58rem;
  opacity: 0.7;
}

.contract-warning {
  display: none;
}

.episode-content {
  min-height: 0;
  overflow: hidden;
}

.episode-content > .content-section {
  height: 100%;
  min-height: 0;
  overflow-x: clip;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  padding: clamp(1.3rem, 3vw, 2.5rem);
  scrollbar-gutter: stable;
}

.episode-content > .content-section > .content-inner {
  width: min(100%, 64rem);
}

.episode-content .section-heading {
  grid-template-columns: minmax(0, 1fr) minmax(15rem, 0.55fr);
  gap: 1.5rem;
  margin-bottom: clamp(1.5rem, 3vw, 2.5rem);
}

.episode-content .section-heading h2 {
  font-size: clamp(2.4rem, 4.5vw, 4rem);
}

.episode-content .section-heading > p {
  font-size: 0.78rem;
}

.setup-disclosure {
  margin-bottom: 1.2rem;
}

.turn-list {
  border-top: 1px solid var(--ink);
}

.turn {
  grid-template-columns: 3.5rem minmax(0, 1fr) minmax(8rem, 0.22fr);
}

.turn-body h3 {
  font-family: var(--font-text);
  font-size: clamp(1.15rem, 2vw, 1.55rem);
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.reliability-grid {
  margin-bottom: 1.5rem;
}

.violation-summary {
  border: 1px solid var(--line);
  border-top: 4px solid var(--coral);
  background: var(--paper-bright);
}

.violation-summary > header {
  padding: 1.25rem;
  border-bottom: 1px solid var(--line);
}

.violation-summary h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 3vw, 3rem);
  font-weight: 500;
  letter-spacing: -0.045em;
}

.violation-summary ol {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}

.violation-summary li {
  display: grid;
  grid-template-columns: 5rem minmax(10rem, 0.4fr) minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: start;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--line-soft);
}

.violation-summary li:last-child {
  border-bottom: 0;
}

.violation-summary li > span,
.violation-summary li > small {
  color: var(--muted);
  font-size: 0.63rem;
}

.violation-summary li > strong {
  font-size: 0.73rem;
}

.violation-summary li > p {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.5;
}

.technical-context,
.model-grid {
  margin-bottom: 1.2rem;
}

@media (max-width: 1500px) {
  .episode-hero-inner {
    grid-template-columns: minmax(15rem, 0.55fr) minmax(0, 1.45fr);
  }

  .episode-facts {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .episode-hero-inner {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .episode-view {
    grid-template-rows: auto auto minmax(0, 1fr);
  }

  .episode-hero-inner {
    grid-template-columns: 1fr;
    gap: 0.55rem;
    padding: 0.7rem 0.9rem 0.75rem;
  }

  .episode-summary h1 {
    font-size: clamp(1.85rem, 9vw, 2.6rem);
    line-height: 0.96;
  }

  .episode-deck {
    margin-top: 0.3rem;
    font-size: 0.74rem;
    line-height: 1.35;
  }

  .subject-return {
    margin-top: 0.35rem;
    font-size: 0.6rem;
  }

  .episode-facts {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }

  .episode-facts > div,
  .episode-facts > div:nth-child(even),
  .episode-facts > div:last-child {
    display: block;
    grid-column: auto;
    padding: 0.5rem 0.2rem;
  }

  .episode-facts dt {
    min-height: 1.5rem;
    font-size: 0.46rem;
    line-height: 1.25;
    overflow-wrap: anywhere;
  }

  .episode-facts dd {
    margin-top: 0.18rem;
    font-size: 0.7rem;
    overflow-wrap: anywhere;
  }

  .episode-facts dd small {
    font-size: 0.46rem;
    line-height: 1.25;
  }

  .episode-tabs {
    overflow: hidden;
  }

  .episode-tabs button {
    flex: 1 1 0;
    min-width: 0;
    padding: 0.68rem 0.55rem 0.64rem;
  }

  .episode-tabs span {
    overflow: hidden;
    font-size: 0.66rem;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .episode-tabs small {
    overflow: hidden;
    font-size: 0.53rem;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .episode-content > .content-section {
    padding: 0.9rem 1rem 1.5rem;
    scrollbar-gutter: auto;
  }

  .episode-content .section-heading {
    grid-template-columns: 1fr;
    gap: 0.8rem;
  }

  .episode-content .section-heading h2 {
    max-width: 11ch;
    font-size: 2.15rem;
    line-height: 0.98;
  }

  .episode-content .section-heading > p {
    font-size: 0.72rem;
    line-height: 1.55;
  }

  .setup-disclosure {
    margin-bottom: 0.9rem;
  }

  .turn-map {
    margin: 0 -1rem 0.9rem;
    border-right: 0;
    border-left: 0;
  }

  .turn-map > header {
    align-items: flex-start;
    padding: 0.8rem 1rem 0.7rem;
  }

  .turn-map h3 {
    font-size: 1.2rem;
  }

  .turn-map > header > p {
    max-width: 8rem;
    text-align: right;
  }

  .turn-map ol {
    gap: 0.35rem;
    padding: 0.68rem 1rem;
  }

  .turn-map button {
    width: 2.75rem;
    min-height: 2.75rem;
  }

  .turn-map > footer {
    padding-inline: 1rem;
  }

  .turn {
    grid-template-columns: 2.3rem minmax(0, 1fr) auto;
    gap: 0.65rem;
    padding: 0.95rem 0;
  }

  .answer {
    grid-row: 1;
    grid-column: 3;
    display: flex;
    width: auto;
    min-width: 2.9rem;
    min-height: 0;
    align-self: start;
    justify-content: center;
    padding: 0.42rem 0.5rem;
    border-radius: 999px;
  }

  .answer span {
    display: none;
  }

  .answer strong {
    margin: 0;
    font-family: var(--font-sans);
    font-size: 0.61rem;
    font-weight: 800;
    letter-spacing: 0.025em;
  }

  .turn-marker {
    gap: 0;
  }

  .turn-marker span {
    width: 2.2rem;
    height: 2.2rem;
    font-size: 0.59rem;
  }

  .turn-marker i {
    display: none;
  }

  .turn-label {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 0.3rem 0.6rem;
    font-size: 0.51rem;
  }

  .turn-body h3 {
    margin-top: 0.42rem;
    font-size: 1rem;
    line-height: 1.3;
  }

  .guess-description {
    margin-top: 0.5rem;
    font-size: 0.72rem;
    line-height: 1.5;
  }

  .validator-note {
    margin-top: 0.7rem;
    padding: 0.7rem 0.75rem;
    font-size: 0.7rem;
  }

  .turn-disclosure {
    margin-top: 0.65rem;
  }

  .turn-disclosure > summary {
    min-height: 2.8rem;
    padding: 0.62rem 0.7rem;
  }

  .turn-disclosure > summary strong {
    font-size: 0.66rem;
  }

  .turn-disclosure > summary small {
    font-size: 0.56rem;
  }

  .turn-disclosure > summary > span:last-child {
    font-size: 0.54rem;
  }

  .violation-summary li {
    grid-template-columns: 1fr;
    gap: 0.4rem;
  }
}

@media (max-height: 520px) {
  .episode-hero {
    display: none;
  }

  .episode-tabs button {
    padding-block: 0.55rem;
  }
}
</style>
