<script setup lang="ts">
import { computed, onActivated, onDeactivated, ref } from "vue";
import { useRouter } from "vue-router";

import ComparisonRankingTable from "@/components/ComparisonRankingTable.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import ReasoningEffort from "@/components/ReasoningEffort.vue";
import RunTableAction from "@/components/RunTableAction.vue";
import ScoreDotPlot, { type ScoreDot } from "@/components/ScoreDotPlot.vue";
import { getLeaderboard, getManifest } from "@/lib/api";
import { money, number, percent } from "@/lib/format";
import { illustrativeRound } from "@/lib/illustrative-round";
import { setRouteContext } from "@/lib/route-context";
import { useRepeatAverages } from "@/lib/use-repeat-averages";
import type {
  LeaderboardDocument,
  LeaderboardRow,
  ManifestDocument,
} from "@/lib/types";

const manifest = ref<ManifestDocument | null>(null);
const leaderboard = ref<LeaderboardDocument | null>(null);
const error = ref<string | null>(null);
const active = ref(true);
const router = useRouter();
const {
  averages: repeatAverages,
  loading: repeatAveragesLoading,
  error: repeatAveragesError,
  load: loadRepeatAverages,
} = useRepeatAverages();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Deep20Bench",
    description:
      manifest.value?.site.description ??
      "Deep20Bench is a Twenty Questions benchmark for large language models (LLMs), testing world knowledge, question strategy, state tracking, and decision discipline.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

onActivated(() => {
  active.value = true;
  applyRouteContext();
});
onDeactivated(() => {
  active.value = false;
});

const load = async (): Promise<void> => {
  try {
    [manifest.value, leaderboard.value] = await Promise.all([
      getManifest(),
      getLeaderboard(),
    ]);
    if (active.value) applyRouteContext();
  } catch (reason: unknown) {
    error.value = reason instanceof Error ? reason.message : "Publication data is unavailable.";
  }
};

void load();
applyRouteContext();

const evaluated = computed(() =>
  (leaderboard.value?.leaderboard ?? []).filter((row) => row.status === "evaluated"),
);
const totalTrials = computed(() => {
  const cohort = manifest.value?.active_cohort;
  return cohort === undefined ? 0 : cohort.target_ids.length * cohort.iterations;
});
const failurePenalty = computed(() => {
  const value = manifest.value;
  return value === null
    ? 51
    : value.active_cohort.max_questions + value.score_policy.failure_penalty_offset;
});
const winnerRows = computed(() => {
  const winner = manifest.value?.winner;
  if (winner === null || winner === undefined) return [];
  return winner.model_ids.flatMap((modelId) => {
    const row = evaluated.value.find((candidate) => candidate.model.model_id === modelId);
    return row === undefined ? [] : [row];
  });
});
const runLink = (row: LeaderboardRow) => ({
  name: "run",
  params: { executionId: row.execution_id },
});
const openRun = (row: LeaderboardRow): void => {
  if (row.execution_id !== null) void router.push(runLink(row));
};
const scoreDots = computed<ScoreDot[]>(() =>
  evaluated.value.map((row) => ({
    modelId: row.model.model_id,
    label: row.model.display_name,
    value: Number(row.question_score),
    display: number(row.question_score),
    confidenceLower:
      row.question_score_confidence_interval === null
        ? undefined
        : Number(row.question_score_confidence_interval.lower),
    confidenceUpper:
      row.question_score_confidence_interval === null
        ? undefined
        : Number(row.question_score_confidence_interval.upper),
    confidenceDisplay:
      row.question_score_confidence_interval === null
        ? undefined
        : `${number(row.question_score_confidence_interval.lower, 2)}–${number(
            row.question_score_confidence_interval.upper,
            2,
          )}`,
    link: row.execution_id === null ? undefined : runLink(row),
  })),
);
</script>

<template>
  <div id="route-content" class="page home-page" tabindex="-1">
    <LoadingState v-if="manifest === null && error === null" label="Loading overview" />
    <ErrorState v-else-if="error !== null" :message="error" />
    <template v-else-if="manifest !== null && leaderboard !== null">
      <section class="home-hero">
        <div class="hero-grid" aria-hidden="true"></div>
        <div class="home-hero-inner">
          <div class="hero-copy">
            <p class="eyebrow">Deep20Bench · Twenty Questions for LLMs</p>
            <h1>Deep20Bench: can an LLM ask its way to the answer?</h1>
            <p>
              A model identifies a hidden person, place, or thing by asking yes-or-no questions.
              Deep20Bench measures knowledge, question strategy, and state tracking.
            </p>
            <div class="hero-actions">
              <RouterLink class="button button-primary" :to="{ name: 'results' }">
                See the benchmark ↓
              </RouterLink>
            </div>
          </div>
          <aside class="round-card" aria-label="Illustrative Twenty Questions round">
            <div class="round-head">
              <span>Illustrative round</span>
              <span>Not benchmark data</span>
            </div>
            <div class="round-columns" aria-hidden="true">
              <span>Turn</span>
              <span>Question</span>
              <span>Answer</span>
            </div>
            <ol>
              <li v-for="(turn, index) in illustrativeRound.turns" :key="turn.prompt">
                <span>{{ String(index + 1).padStart(2, "0") }}</span>
                <p>{{ turn.prompt }}</p>
                <strong>
                  {{ turn.kind === "guess" ? `${turn.prompt} — ${turn.answer}` : turn.answer }}
                </strong>
              </li>
            </ol>
          </aside>
        </div>
      </section>

      <section id="how-it-works" class="content-section">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow">Why this game works</p>
              <h2>Simple rules. Several abilities.</h2>
            </div>
            <p>Each answer should change the model’s next question.</p>
          </header>
          <div class="ability-grid">
            <article>
              <span>01</span>
              <h3>World knowledge</h3>
              <p>Know which categories and facts are useful.</p>
            </article>
            <article>
              <span>02</span>
              <h3>Question strategy</h3>
              <p>Choose questions that remove many possibilities.</p>
            </article>
            <article>
              <span>03</span>
              <h3>State tracking</h3>
              <p>Use every prior YES, NO, and UNKNOWN.</p>
            </article>
            <article>
              <span>04</span>
              <h3>Decision discipline</h3>
              <p>Make an exact guess before the limit.</p>
            </article>
          </div>
          <div class="adjudication">
            <div>
              <p class="eyebrow">How answers are checked</p>
              <h3>Three checks. One final answer.</h3>
            </div>
            <div class="adjudication-summary">
              <p>
                The Oracle researches each question. An independent Reviewer checks every YES or
                NO. If they disagree, a blind Judge decides. The Guesser receives only the final
                answer.
              </p>
              <RouterLink
                class="text-link"
                :to="{ name: 'methodology', hash: '#answer-checks' }"
              >
                See the full answer-checking method →
              </RouterLink>
            </div>
          </div>
        </div>
      </section>

      <section class="content-section cohort-section">
        <div class="content-inner cohort-layout">
          <div class="cohort-copy">
            <p class="eyebrow">Benchmark design</p>
            <h2>A score built from repeated trials.</h2>
            <p>
              Each model completes the full subject set several times. Trials are averaged within
              each subject and then across subjects, so every subject contributes equally to the
              final score.
            </p>
            <RouterLink class="text-link" :to="{ name: 'methodology' }">
              Read the full method →
            </RouterLink>
          </div>
          <dl class="cohort-facts">
            <div><dt>Subjects</dt><dd>{{ manifest.active_cohort.target_ids.length }}</dd></div>
            <div><dt>Trials / subject</dt><dd>{{ manifest.active_cohort.iterations }}</dd></div>
            <div><dt>Trials / model</dt><dd>{{ totalTrials }}</dd></div>
            <div><dt>Question limit</dt><dd>{{ manifest.active_cohort.max_questions }}</dd></div>
          </dl>
        </div>
      </section>

      <section class="content-section leaderboard-section">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow">Official results</p>
              <h2>Which models ask best?</h2>
            </div>
            <p>
              Lower is better. A failed trial contributes {{ failurePenalty }} questions.
            </p>
          </header>

          <template v-if="evaluated.length > 0">
            <article v-if="manifest.winner" class="winner-card">
              <div>
                <p class="eyebrow">
                  {{ manifest.winner.joint ? "Joint official leader" : "Official leader" }}
                </p>
                <h3>{{ manifest.winner.display_names.join(" · ") }}</h3>
                <div class="winner-efforts">
                  <ReasoningEffort
                    v-for="row in winnerRows"
                    :key="row.model.model_id"
                    :effort="row.model.reasoning_effort"
                    dark
                  />
                </div>
                <RouterLink
                  v-for="row in winnerRows"
                  :key="row.execution_id ?? row.model.model_id"
                  class="winner-link"
                  :to="runLink(row)"
                >
                  {{ manifest.winner.joint ? row.model.display_name : "View full run" }} →
                </RouterLink>
              </div>
              <QuestionScore
                :score="manifest.winner.question_score"
                :max-questions="manifest.active_cohort.max_questions"
                variant="hero"
                theme="dark"
                explain
                :confidence-interval="
                  manifest.winner.joint
                    ? null
                    : (winnerRows[0]?.question_score_confidence_interval ?? null)
                "
              />
            </article>

            <div class="leaderboard-layout">
              <div class="score-chart">
                <h3 class="chart-title">Question score</h3>
                <p class="chart-description">
                  Lower is better. The blue marker is the average question score. The blue line
                  is its 95% confidence interval across repeated runs. Shorter lines
                  suggest more consistent performance; longer lines indicate more variation
                  between runs.
                </p>
                <ScoreDotPlot
                  :items="scoreDots"
                  :repeat-averages="repeatAverages"
                  :repeat-averages-loading="repeatAveragesLoading"
                  :repeat-averages-error="repeatAveragesError"
                  @request-repeat-averages="loadRepeatAverages"
                />
              </div>
            </div>

            <ComparisonRankingTable
              variant="home"
              label="Scrollable official leaderboard"
            >
                <tbody>
                  <tr
                    v-for="row in evaluated"
                    :key="row.model.model_id"
                    :class="{
                      'result-row--clickable': row.execution_id !== null,
                      'result-row--navigable': row.execution_id !== null,
                    }"
                    @click="openRun(row)"
                  >
                    <td class="rank-column">{{ row.rank ?? "—" }}</td>
                    <td class="model-column">
                      <ModelRunLink
                        v-if="row.execution_id"
                        :to="runLink(row)"
                        :name="row.model.display_name"
                        :meta="`${row.model.model_id} · ${row.model.provider}`"
                      />
                      <strong v-else>{{ row.model.display_name }}</strong>
                      <small v-if="row.execution_id === null">
                        {{ row.model.model_id }} · {{ row.model.provider }}
                      </small>
                    </td>
                    <td class="run-column">
                      <RunTableAction
                        v-if="row.execution_id"
                        :to="runLink(row)"
                        :name="row.model.display_name"
                      />
                      <span v-else aria-hidden="true">—</span>
                    </td>
                    <td class="primary-metric-column" data-numeric>
                      <QuestionScore
                        :score="row.question_score"
                        :confidence-interval="row.question_score_confidence_interval"
                        variant="table"
                      />
                    </td>
                    <td class="reasoning-column">
                      <ReasoningEffort :effort="row.model.reasoning_effort" compact />
                    </td>
                    <td class="success-column" data-numeric>{{ percent(row.success_rate) }}</td>
                    <td class="contract-column" data-numeric>
                      {{ percent(row.contract?.compliance_rate) }}
                      <small v-if="row.contract?.status === 'breached'">
                        {{ row.contract.violations }} violations
                      </small>
                    </td>
                    <td class="cost-column" data-numeric>{{ money(row.total_cost_usd) }}</td>
                  </tr>
                </tbody>
            </ComparisonRankingTable>

            <div class="mobile-result-list" aria-label="Official leaderboard">
              <MobileResultCard
                v-for="row in evaluated"
                :key="`mobile-${row.model.model_id}`"
                :rank="row.rank ?? '—'"
                :name="row.model.display_name"
                :provider="row.model.provider"
                :to="row.execution_id === null ? null : runLink(row)"
                :metrics="[
                  {
                    label: 'Score',
                    value: number(row.question_score),
                    tone: 'primary',
                  },
                  {
                    label: 'Repeatability',
                    value:
                      row.question_score_confidence_interval === null
                        ? '—'
                        : `${number(row.question_score_confidence_interval.lower, 2)}–${number(
                            row.question_score_confidence_interval.upper,
                            2,
                          )}`,
                  },
                  { label: 'Success', value: percent(row.success_rate) },
                  { label: 'Cost', value: money(row.total_cost_usd) },
                ]"
              />
            </div>
          </template>

          <article v-else class="empty-results">
            <p class="eyebrow">Current status</p>
            <h3>Official comparison in progress.</h3>
            <p>Results appear after a complete, integrity-checked run covers every subject.</p>
            <dl>
              <div><dt>Active cohort</dt><dd>{{ manifest.active_cohort.display_name }}</dd></div>
              <div><dt>Trials / model</dt><dd>{{ totalTrials }}</dd></div>
              <div><dt>Failure penalty</dt><dd>{{ failurePenalty }} questions</dd></div>
            </dl>
          </article>
        </div>
      </section>

      <section class="content-section trust-section">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow">Why trust the comparison</p>
              <h2>Controlled and inspectable.</h2>
            </div>
            <p>Scores stay compact while the evidence remains available.</p>
          </header>
          <div class="trust-grid">
            <article>
              <span>01</span>
              <h3>Strict isolation</h3>
              <p>The Guesser sees the category, prior actions, and final answer tokens.</p>
            </article>
            <article>
              <span>02</span>
              <h3>Failures stay visible</h3>
              <p>Failures receive a declared penalty. Invalid outputs consume turns.</p>
            </article>
            <article>
              <span>03</span>
              <h3>Every score is inspectable</h3>
              <p>Runs link to subjects, episodes, transcripts, evidence, and usage.</p>
            </article>
          </div>
        </div>
      </section>

      <section class="origin-strip">
        <div>
          <p class="eyebrow">Origin</p>
          <h2>From a holiday game to a benchmark.</h2>
        </div>
        <div>
          <p>
            Patrick Heusser and Markus Tuor came up with the idea while playing Twenty Questions
            with the kids. Patrick then designed and built the benchmark.
          </p>
          <div class="button-row">
            <RouterLink class="button button-secondary" :to="{ name: 'story' }">
              Origin and prior work
            </RouterLink>
            <RouterLink class="button button-primary" :to="{ name: 'data' }">
              Explore public data
            </RouterLink>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.home-hero {
  position: relative;
  padding: clamp(3.6rem, 6.5vw, 6.2rem) var(--gutter);
  overflow: hidden;
  background: var(--ink);
  color: white;
}

.home-page > .content-section {
  padding-block: clamp(2.6rem, 3.8vw, 3.4rem);
}

.home-hero-inner {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(21rem, 0.76fr);
  gap: clamp(3rem, 7vw, 7rem);
  align-items: center;
  width: min(100%, var(--max));
  margin-inline: auto;
}

.hero-grid {
  position: absolute;
  inset: 0;
  opacity: 0.075;
  background-image:
    linear-gradient(rgb(255 255 255 / 24%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(255 255 255 / 24%) 1px, transparent 1px);
  background-size: 88px 88px;
  mask-image: linear-gradient(to right, black, transparent 68%);
}

.hero-copy,
.round-card {
  position: relative;
}

.hero-copy {
  width: min(100%, 48rem);
}

.hero-copy h1,
.cohort-layout h2,
.origin-strip h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3.35rem, 5.35vw, 5.15rem);
  font-weight: 470;
  letter-spacing: -0.048em;
  line-height: 0.94;
}

.hero-copy > p:last-of-type {
  max-width: 38rem;
  margin: 1.4rem 0 0;
  color: rgb(255 255 255 / 68%);
  font-size: 0.88rem;
  line-height: 1.65;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: clamp(1.2rem, 3vw, 2.5rem);
  align-items: center;
  margin-top: 2rem;
}

.round-card {
  border: var(--rule-inverse);
  background: rgb(255 255 255 / 4%);
}

.round-head,
.round-columns,
.round-card li {
  display: grid;
  align-items: center;
  gap: 0.8rem;
  padding: 0.78rem 0.95rem;
  border-bottom: var(--rule-inverse-subtle);
}

.round-head,
.round-columns {
  grid-template-columns: 1fr auto;
  font-size: var(--text-micro);
  font-weight: 680;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.round-head span:last-child,
.round-card li > span {
  color: rgb(255 255 255 / 48%);
}

.round-columns {
  grid-template-columns: 2rem 1fr auto;
  color: rgb(255 255 255 / 47%);
}

.round-card ol {
  margin: 0;
  padding: 0;
  list-style: none;
}

.round-card li {
  grid-template-columns: 2rem minmax(0, 1fr) auto;
  min-height: 3.7rem;
}

.round-card li p {
  margin: 0;
  font-size: var(--text-small);
}

.round-card li strong {
  color: var(--acid);
  font-size: var(--text-micro);
  letter-spacing: 0.02em;
  text-align: right;
  text-transform: uppercase;
}

.round-card li:last-child {
  border-bottom: 0;
}

.ability-grid,
.trust-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: var(--rule-default);
  background: var(--line);
  gap: 1px;
}

.ability-grid article,
.trust-grid article {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-rows: auto auto;
  min-height: 9rem;
  padding: 1.5rem 1.25rem 1rem;
  column-gap: 0.85rem;
  row-gap: 0.65rem;
  align-content: center;
  background: var(--paper-bright);
}

.ability-grid article > span,
.trust-grid article > span {
  display: grid;
  grid-column: 1;
  grid-row: 1;
  align-self: center;
  width: 1.75rem;
  height: 1.75rem;
  border: var(--border-width) solid var(--text-secondary);
  border-radius: 50%;
  color: var(--ink);
  font: 620 var(--text-micro) var(--font-sans);
  place-items: center;
}

.ability-grid h3,
.trust-grid h3 {
  grid-column: 2;
  grid-row: 1;
  align-self: center;
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 470;
  line-height: 1.12;
}

.ability-grid p,
.trust-grid p {
  grid-column: 2;
  grid-row: 2;
  margin: 0;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.5;
}

.adjudication {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(17rem, 1fr);
  gap: clamp(2rem, 5vw, 5rem);
  align-items: end;
  margin-top: clamp(3rem, 6vw, 5rem);
  padding: clamp(2rem, 4vw, 3.5rem);
  background: var(--ink);
  color: white;
}

.adjudication .eyebrow {
  color: var(--acid);
}

.adjudication h3 {
  max-width: 12ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.3rem, 3.8vw, 3.8rem);
  font-weight: 470;
  letter-spacing: -0.042em;
  line-height: 0.99;
}

.adjudication-summary > p {
  margin: 0;
  color: rgb(255 255 255 / 72%);
  line-height: 1.65;
}

.adjudication .text-link {
  display: inline-block;
  margin-top: 1.25rem;
  color: var(--acid);
}

.cohort-section {
  background: var(--surface-rail);
}

.cohort-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(15rem, 21rem);
  gap: clamp(2.5rem, 5vw, 5rem);
  align-items: center;
}

.cohort-copy {
  max-width: 48rem;
}

.cohort-layout h2 {
  max-width: 13ch;
  font-size: clamp(2.5rem, 3.9vw, 3.9rem);
}

.cohort-layout p {
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.6;
}

.text-link {
  color: var(--blue-ink);
  font-size: var(--text-small);
  font-weight: 680;
}

.cohort-facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 0;
  border: var(--rule-strong);
}

.cohort-facts div {
  display: flex;
  min-height: 7.6rem;
  padding: 1rem;
  border-right: var(--rule-strong);
  border-bottom: var(--rule-strong);
  flex-direction: column;
  justify-content: space-between;
}

.cohort-facts div:nth-child(even) {
  border-right: 0;
}

.cohort-facts div:nth-last-child(-n + 2) {
  border-bottom: 0;
}

dt {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 710;
  text-transform: uppercase;
}

dd {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 3vw, 2.9rem);
}

.winner-card {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(18rem, 1fr);
  gap: clamp(2rem, 6vw, 6rem);
  padding: clamp(1.5rem, 3vw, 2.5rem);
  background: var(--gradient-accent);
  color: white;
}

.leaderboard-section {
  --overview-result-gap: clamp(1.5rem, 4vw, 2.5rem);
}

.winner-card h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.2rem, 3.7vw, 3.7rem);
  font-weight: 470;
  letter-spacing: -0.042em;
}

.winner-efforts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  margin: 1.2rem 0;
}

.winner-link {
  display: block;
  width: fit-content;
  margin-top: 0.6rem;
  color: var(--acid);
  font-weight: 750;
}

.leaderboard-layout {
  margin-top: var(--overview-result-gap);
  border: var(--rule-default);
  background: var(--paper-bright);
}

.score-chart {
  min-width: 0;
  overflow: hidden;
}

.chart-title {
  margin: 0;
  padding: clamp(1.2rem, 3vw, 2rem) clamp(1.2rem, 3vw, 2rem) 0;
  color: var(--ink);
  font-family: var(--font-display);
  font-size: clamp(2rem, 3.4vw, 3.2rem);
  font-weight: 470;
  letter-spacing: -0.04em;
  line-height: 1;
}

.chart-description {
  max-width: 52rem;
  margin: 0.55rem 0 0;
  padding: 0 clamp(1.2rem, 3vw, 2rem);
  color: var(--muted);
  font-size: var(--text-small);
}

.score-chart :deep(.score-dot-plot) {
  padding: 0 clamp(0.65rem, 1.5vw, 1rem) 0.5rem;
}

.table-wrap {
  margin-top: var(--overview-result-gap);
}

.empty-results {
  padding: clamp(2rem, 5vw, 4rem);
  border: var(--rule-default);
  background: var(--paper-bright);
}

.empty-results h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.3rem, 5vw, 4.7rem);
  font-weight: 500;
}

.empty-results > p {
  color: var(--muted);
}

.empty-results dl {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 2rem 0 0;
  border-top: var(--rule-default);
}

.empty-results dl div {
  padding: 1rem 1rem 0;
}

.empty-results dd {
  margin-top: 0.5rem;
  font-family: inherit;
  font-size: 1rem;
}

.trust-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.origin-strip {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(20rem, 1fr);
  gap: clamp(2rem, 8vw, 8rem);
  padding: clamp(3.2rem, 6vw, 5.5rem) max(var(--gutter), calc((100vw - var(--max)) / 2));
  background: var(--acid);
}

.origin-strip h2 {
  font-size: clamp(2.5rem, 4vw, 4rem);
}

.origin-strip > div:last-child {
  align-self: end;
}

.origin-strip > div:last-child > p {
  max-width: 42rem;
  line-height: 1.7;
}

.origin-strip .button-primary {
  border-color: var(--ink);
  background: transparent;
}

@media (max-width: 940px) {
  .home-hero-inner,
  .cohort-layout,
  .winner-card,
  .origin-strip {
    grid-template-columns: 1fr;
  }

  .ability-grid {
    grid-template-columns: 1fr 1fr;
  }

  .adjudication {
    grid-template-columns: 1fr 1fr;
  }

}

@media (max-width: 620px) {
  .home-hero {
    padding-block: 3rem;
  }

  .home-hero-inner {
    gap: 3rem;
  }

  .hero-copy h1 {
    font-size: clamp(3rem, 14vw, 4.1rem);
  }

  .hero-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .round-card li strong {
    max-width: 8rem;
  }

  .ability-grid,
  .trust-grid,
  .adjudication {
    grid-template-columns: 1fr;
  }

  .mobile-result-list {
    margin-top: var(--overview-result-gap);
  }

  .empty-results dl {
    grid-template-columns: 1fr;
  }
}
</style>
