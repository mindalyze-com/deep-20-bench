<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import ModelName from "@/components/ModelName.vue";
import PublicationTime from "@/components/PublicationTime.vue";
import RankBadge from "@/components/RankBadge.vue";
import { getModel, peekModel } from "@/lib/api";
import {
  duration,
  formatCount,
  moneyEpisode,
  number,
  outcomeLabel,
  plural,
  reasoningEffortLabel,
} from "@/lib/format";
import {
  editionRoute,
  comparisonRoute,
  episodeRoute,
  modelRoute,
  runRoute,
  subjectRoute,
} from "@/lib/route-location";
import { setRouteContext, useActiveRouteContext } from "@/lib/route-context";
import type {
  PublicModelObservation,
  PublicModelRound,
  PublicModelSubjectResult,
} from "@/lib/types";
import { useEditionContext } from "@/lib/use-edition-context";
import { useKeyedPublicationLoad } from "@/lib/use-keyed-publication-load";

const route = useRoute();
const { editionId, selectedEdition } = useEditionContext();
const slug = computed(() => String(route.params.slug ?? ""));
const { document, loading, error } = useKeyedPublicationLoad({
  parameters: (): [string, string] => [editionId.value, slug.value],
  clearBeforeLoad: true,
  load: getModel,
  initial: () => peekModel(editionId.value, slug.value),
  fallbackError: "The model summary could not be loaded.",
});

const model = computed(() => document.value);
const result = computed(() => model.value?.result ?? null);
const name = computed(() => result.value?.model.display_name ?? "");
const executionId = computed(() => result.value?.execution_id ?? "");
const editionLabel = computed(() => selectedEdition.value?.label ?? editionId.value);
const subjectsById = computed(() => new Map(
  (model.value?.subjects ?? []).map((subject) => [subject.target_id, subject]),
));
const roundsById = computed(() => new Map(
  (model.value?.subjects ?? []).flatMap((subject) =>
    subject.rounds.map((item) => [`${item.target_id}/${item.trial_id}`, item] as const)),
));
const formatErrors = computed(() => result.value?.contract?.violations ?? 0);

const ordinal = (value: number): string => {
  const tens = value % 100;
  const suffix = tens >= 11 && tens <= 13 ? "th"
    : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[value % 10] ?? "th";
  return `${value}${suffix}`;
};
const subjectStanding = (subject: PublicModelSubjectResult): string =>
  subject.rank === null
    ? "no ranked result"
    : subject.rank === 1
      ? `best of ${subject.ranked_models} models`
      : `${ordinal(subject.rank)} of ${subject.ranked_models} models`;
const subjectName = (targetId: string | null): string =>
  targetId === null ? "" : subjectsById.value.get(targetId)?.display_name ?? targetId;
const roundLabel = (trialNumber: number): string => `round ${trialNumber}`;
const roundFor = (reference: { target_id: string; trial_id: string }): PublicModelRound | undefined =>
  roundsById.value.get(`${reference.target_id}/${reference.trial_id}`);
const roundLink = (item: { target_id: string; trial_id: string }) =>
  episodeRoute(executionId.value, item.target_id, item.trial_id);

interface ObservationGroup {
  title: string;
  kinds: readonly PublicModelObservation["kind"][];
  empty?: string;
}
const groups: readonly ObservationGroup[] = [
  { title: "Best ranks vs other models", kinds: ["strongest_subject"] },
  { title: "Lowest ranks vs other models", kinds: ["hardest_subject"] },
  {
    title: "Single rounds",
    kinds: ["fewest_questions", "most_questions", "uneven_subject", "wrong_guesses"],
  },
  {
    title: "Failed rounds and format errors",
    kinds: ["model_failure", "format_errors"],
    empty: "Every round was solved, and every reply used the required format.",
  },
];
const groupObservations = (group: ObservationGroup): PublicModelObservation[] =>
  (model.value?.observations ?? []).filter((item) => group.kinds.includes(item.kind));

const observationText = (observation: PublicModelObservation): string => {
  const subject = observation.target_id === null
    ? undefined
    : subjectsById.value.get(observation.target_id);
  const first = observation.rounds[0] === undefined ? undefined : roundFor(observation.rounds[0]);
  switch (observation.kind) {
    case "strongest_subject":
    case "hardest_subject":
      return subject === undefined
        ? ""
        : `${subject.display_name}: ${subjectStanding(subject)}, average ` +
          `${number(observation.value)} questions.`;
    case "fewest_questions":
      return `Fewest questions in a solved round: ${observation.count ?? "-"}, on ` +
        `${subjectName(observation.target_id)}.`;
    case "most_questions":
      return `Most questions in a solved round: ${observation.count ?? "-"}, on ` +
        `${subjectName(observation.target_id)}.`;
    case "uneven_subject": {
      const values = observation.rounds
        .map((reference) => roundFor(reference)?.penalized_questions)
        .filter((value): value is string => value !== null && value !== undefined)
        .map(Number);
      return `Largest spread between rounds: ${subjectName(observation.target_id)}, from ` +
        `${number(Math.min(...values), 0)} to ${number(Math.max(...values), 0)} questions.`;
    }
    case "wrong_guesses": {
      const total = observation.count ?? 0;
      const most = Number(observation.value ?? 0);
      const rounds = model.value?.result.terminal_trials ?? "-";
      if (total === 1) {
        return `1 wrong guess in ${rounds} rounds, on ${subjectName(observation.target_id)}.`;
      }
      return most <= 1
        ? `${formatCount(total, "wrong guess", "wrong guesses")} in ${rounds} rounds, ` +
          "never more than one per round."
        : `${formatCount(total, "wrong guess", "wrong guesses")} in ${rounds} rounds, ` +
          `up to ${most} in one round on ${subjectName(observation.target_id)}.`;
    }
    case "model_failure":
      return `Not solved: ${subjectName(observation.target_id)}. ` +
        `${outcomeLabel(first?.terminal_reason ?? "model_failure")} after ` +
        `${observation.count ?? "-"} questions; scored as ${number(observation.value, 0)}.`;
    case "format_errors":
      return `${formatCount(observation.count ?? 0, "format error")} in ` +
        `${formatCount(observation.rounds.length, "round")}. Each one before the question limit ` +
        "used a counted turn.";
  }
  return "";
};

const scopeText = computed(() => {
  const current = model.value;
  if (current === null) return "";
  const subjects = current.subjects.length;
  return `These results come from one run: ${subjects} fixed ${plural(subjects, "subject")}, ` +
    `${current.iterations} ${plural(current.iterations, "round")} each, a ` +
    `${current.max_questions}-question limit, and reasoning setting ` +
    `${reasoningEffortLabel(current.result.model.reasoning_effort).toLowerCase()}. ` +
    "They do not predict results on other subjects or settings.";
});

const applyContext = useActiveRouteContext(() => {
  if (result.value === null) return;
  setRouteContext({
    title: name.value,
    description: `Deep20Bench results for ${name.value} in edition ${editionLabel.value}.`,
    level: "Model summary",
    position: null,
    crumbs: [
      { label: "Results", to: editionRoute("results") },
      { label: "Models", to: editionRoute("models") },
      { label: name.value },
    ],
    previous: null,
    next: null,
  });
});
watch(result, applyContext);
</script>

<template>
  <div id="route-content" class="page model-page" tabindex="-1">
    <LoadingState v-if="loading && model === null" label="Loading model summary" />
    <ErrorState v-else-if="error && model === null" :message="error" />

    <template v-else-if="model !== null && result !== null">
      <section class="page-hero site-boundary-shell">
        <div class="page-hero-inner site-boundary">
          <div>
            <p class="eyebrow">Model summary · Edition {{ editionLabel }}</p>
            <h1><ModelName :name="name" dark /></h1>
          </div>
          <div class="lede model-lede">
            <p>{{ scopeText }}</p>
            <p>
              This page always shows the model’s newest ranked run.
            </p>
            <div class="button-row">
              <RouterLink class="button button-primary" :to="runRoute(executionId)">
                See all {{ result.terminal_trials }} rounds →
              </RouterLink>
              <RouterLink class="button button-secondary" :to="comparisonRoute([result.model.model_id], editionId)">
                Compare this model
              </RouterLink>
              <RouterLink class="button button-secondary" :to="editionRoute('models')">
                All models
              </RouterLink>
            </div>
            <p class="run-cta-hint">Every question, answer, guess, and source.</p>
          </div>
        </div>
      </section>

      <section class="content-section" aria-labelledby="model-result-title">
        <div class="content-inner">
          <h2 id="model-result-title" class="visually-hidden">Result</h2>
          <dl class="stats-grid model-facts">
            <div>
              <dt>Rank</dt>
              <dd class="model-rank">
                <RankBadge :rank="result.rank" />
                <span>of {{ model.ranked_models }} models</span>
              </dd>
            </div>
            <div>
              <dt>Question score</dt>
              <dd>
                {{ number(result.question_score) }}
                <small>
                  Lower is better.
                  <template v-if="result.question_score_confidence_interval !== null">
                    95% confidence interval
                    {{ number(result.question_score_confidence_interval.lower) }} to
                    {{ number(result.question_score_confidence_interval.upper) }}.
                  </template>
                </small>
              </dd>
            </div>
            <div>
              <dt>Rounds solved</dt>
              <dd>
                {{ result.successful }} of {{ result.terminal_trials }}
                <small>{{ formatCount(formatErrors, "format error") }}</small>
              </dd>
            </div>
            <div>
              <dt>Guesser cost per round</dt>
              <dd>
                {{ moneyEpisode(result.guesser_cost_per_episode_usd) }}
                <small>
                  <template v-if="result.guesser_think_time_per_episode_ms !== null">
                    Model time {{ duration(Number(result.guesser_think_time_per_episode_ms)) }}.
                  </template>
                </small>
              </dd>
            </div>
          </dl>
          <RouterLink class="run-callout" :to="runRoute(executionId)">
            <span>
              <strong>See how {{ result.model.display_name }} played.</strong>
              All {{ result.terminal_trials }} rounds, with every question, answer, guess,
              and source.
            </span>
            <span class="run-callout-action" aria-hidden="true">Open the full run →</span>
          </RouterLink>
        </div>
      </section>

      <section class="content-section" aria-labelledby="model-observations-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow">Observations</p>
              <h2 id="model-observations-title">What stood out in this run.</h2>
            </div>
            <p>
              Counts and ranks from this run only. A subject rank compares this model’s
              average on that subject with every other model in this edition. Each item links
              to its rounds.
            </p>
          </header>
          <div class="observation-groups">
            <section
              v-for="group in groups"
              :key="group.title"
              class="observation-group"
              :aria-label="group.title"
            >
              <h3>{{ group.title }}</h3>
              <ul v-if="groupObservations(group).length > 0">
                <li
                  v-for="(observation, index) in groupObservations(group)"
                  :key="`${observation.kind}-${index}`"
                >
                  {{ observationText(observation) }}
                  <span class="observation-rounds">
                    <template v-for="(reference, position) in observation.rounds" :key="reference.trial_id + reference.target_id">
                      <template v-if="position > 0">, </template>
                      <RouterLink :to="roundLink(reference)">
                        <template v-if="observation.kind === 'format_errors'">
                          {{ subjectName(reference.target_id) }}
                        </template>
                        {{ roundLabel(roundFor(reference)?.trial_number ?? 0) }}
                      </RouterLink>
                    </template>
                  </span>
                </li>
              </ul>
              <p v-else-if="group.empty">{{ group.empty }}</p>
            </section>
          </div>
        </div>
      </section>

      <section class="content-section" aria-labelledby="model-subjects-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow">Subjects</p>
              <h2 id="model-subjects-title">Results by subject.</h2>
            </div>
            <p>
              Failed rounds count as {{ model.max_questions + 1 }} questions. Rank compares
              this subject's average with the other models in edition {{ editionLabel }}.
              Select a subject or a round to see the game.
            </p>
          </header>
          <div class="table-wrap">
            <table class="data-table model-subject-table">
              <thead>
                <tr>
                  <th scope="col">Subject</th>
                  <th scope="col" data-numeric>Average questions</th>
                  <th scope="col" data-numeric>Subject rank</th>
                  <th scope="col" data-numeric>Solved</th>
                  <th scope="col">Rounds</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="subject in model.subjects" :key="subject.target_id">
                  <th scope="row">
                    <RouterLink :to="subjectRoute(executionId, subject.target_id)">
                      {{ subject.display_name }}
                    </RouterLink>
                  </th>
                  <td data-numeric>{{ number(subject.average_questions) }}</td>
                  <td data-numeric>
                    {{ subject.rank === null ? "-" : `${subject.rank} of ${subject.ranked_models}` }}
                  </td>
                  <td data-numeric>{{ subject.successful }} of {{ subject.rounds.length }}</td>
                  <td class="round-links">
                    <template v-for="(item, position) in subject.rounds" :key="item.trial_id">
                      <template v-if="position > 0">, </template>
                      <RouterLink
                        v-if="item.status !== 'infrastructure_failure'"
                        :to="roundLink(item)"
                        :aria-label="`Round ${item.trial_number}: ${item.status === 'success' ? `solved in ${item.counted_questions} questions` : outcomeLabel(item.terminal_reason ?? item.status)}`"
                      >
                        {{ item.status === "success" ? item.counted_questions : "not solved" }}
                      </RouterLink>
                      <span v-else>{{ outcomeLabel(item.status) }}</span>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section class="content-section" aria-labelledby="model-history-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow">Runs</p>
              <h2 id="model-history-title">Runs of this model.</h2>
            </div>
            <p>
              Each edition ranks only the newest complete run of a model. Earlier runs are
              not ranked and their details are not published.
            </p>
          </header>
          <ul class="run-history">
            <li>
              Current run in edition {{ editionLabel }}:
              <RouterLink :to="runRoute(executionId)">{{ executionId }}</RouterLink>,
              completed
              <PublicationTime v-if="result.completed_at !== null" :value="result.completed_at" date-only />.
            </li>
            <li v-for="other in model.other_editions" :key="other.edition_id">
              Edition {{ other.edition_label }}:
              <RouterLink :to="modelRoute(other.slug, other.edition_id)">
                {{ other.rank === null ? "unranked" : `rank ${other.rank} of ${other.ranked_models}` }},
                question score {{ number(other.question_score) }}
              </RouterLink>.
              Different rules and subjects, so scores are not comparable across editions.
            </li>
            <li v-for="run in model.superseded_runs" :key="run.execution_id">
              Replaced run {{ run.execution_id }}, completed
              <PublicationTime :value="run.completed_at" date-only />. Not published.
            </li>
          </ul>
          <p class="model-related">
            See also the <RouterLink :to="editionRoute('results')">results overview</RouterLink>,
            <RouterLink :to="editionRoute('methodology')">how scoring works</RouterLink>, and the
            <RouterLink :to="editionRoute('data')">data downloads</RouterLink>.
          </p>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.model-lede .button-row {
  margin-top: 1.25rem;
}

.run-cta-hint {
  margin: 0.6rem 0 0;
  color: rgb(255 255 255 / 65%);
  font-size: var(--text-small);
}

/* The run holds the full games; this panel points there right after the headline numbers. */
.run-callout {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.5rem;
  align-items: center;
  justify-content: space-between;
  margin-top: 1.25rem;
  padding: 1rem 1.25rem;
  border: var(--rule-default);
  border-left: 3px solid var(--blue);
  background: var(--paper-bright);
  color: var(--ink);
  text-decoration: none;
}

.run-callout:hover,
.run-callout:focus-visible {
  border-color: var(--blue);
}

.run-callout strong {
  margin-right: 0.35rem;
}

.run-callout > span:first-child {
  color: var(--text-secondary);
  line-height: 1.5;
}

.run-callout strong {
  color: var(--ink);
}

.run-callout-action {
  flex: 0 0 auto;
  padding: 0.55rem 0.9rem;
  background: var(--acid);
  color: var(--ink);
  font-size: var(--text-ui);
  font-weight: var(--font-weight-bold);
}

.model-facts dd small {
  display: block;
  margin-top: 0.35rem;
  color: var(--text-secondary);
  font-size: var(--text-small);
  font-weight: var(--font-weight-medium);
  line-height: 1.4;
}

.model-rank {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.model-rank span {
  font-size: var(--text-small);
}

.observation-groups {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem 2.5rem;
}

.observation-group h3 {
  margin: 0 0 0.5rem;
  font-size: var(--text-body);
}

.observation-group ul {
  margin: 0;
  padding-left: 1.1rem;
}

.observation-group li + li {
  margin-top: 0.4rem;
}

.observation-rounds {
  color: var(--text-secondary);
}

.round-links {
  white-space: nowrap;
}

.run-history {
  margin: 0 0 1.25rem;
  padding-left: 1.1rem;
}

.run-history li + li {
  margin-top: 0.4rem;
}

@media (max-width: 760px) {
  .observation-groups {
    grid-template-columns: minmax(0, 1fr);
  }

  .model-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .round-links {
    white-space: normal;
  }
}
</style>
