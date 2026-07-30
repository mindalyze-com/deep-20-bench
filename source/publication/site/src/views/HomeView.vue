<script setup lang="ts">
import { computed, onActivated, onDeactivated, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import ReasoningEffort from "@/components/ReasoningEffort.vue";
import ScoreDotPlot, { type ScoreDot } from "@/components/ScoreDotPlot.vue";
import { getLeaderboard, getManifest } from "@/lib/api";
import { dateTime, money, number, percent } from "@/lib/format";
import { illustrativeRound } from "@/lib/illustrative-round";
import { setRouteContext } from "@/lib/route-context";
import type {
  LeaderboardDocument,
  LeaderboardRow,
  ManifestDocument,
} from "@/lib/types";

const manifest = ref<ManifestDocument | null>(null);
const leaderboard = ref<LeaderboardDocument | null>(null);
const error = ref<string | null>(null);
const active = ref(true);

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Deep20Bench",
    description:
      manifest.value?.site.description ??
      "Tests how LLMs use world knowledge, question planning, and state tracking.",
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
const scoreDots = computed<ScoreDot[]>(() =>
  evaluated.value.map((row) => ({
    label: row.model.display_name,
    value: Number(row.question_score),
    display: number(row.question_score, 1),
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
            <h1>Can an LLM ask its way to the answer?</h1>
            <p>
              A model identifies a hidden person, place, or thing by asking yes-or-no questions.
              Deep20Bench measures knowledge, question strategy, and state tracking.
            </p>
            <div class="hero-actions">
              <RouterLink class="button button-primary" :to="{ name: 'results' }">
                See the benchmark ↓
              </RouterLink>
              <div v-if="manifest.winner" class="live-result">
                <p class="eyebrow">Live result · leader</p>
                <strong>{{ number(manifest.winner.question_score) }}</strong>
                <span>{{ manifest.winner.display_names.join(" · ") }}</span>
              </div>
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
            <header class="adjudication-heading">
              <div>
                <p class="eyebrow">How answers are checked</p>
                <h3>One player. Three independent checks.</h3>
              </div>
              <p>
                The Guesser receives only the final YES, NO, or UNKNOWN.
              </p>
            </header>
            <div class="role-grid">
              <article>
                <span>01</span>
                <h4>Guesser</h4>
                <p>The model under test asks about the hidden subject.</p>
              </article>
              <article>
                <span>02</span>
                <h4>Oracle</h4>
                <p>Researches the question on the live web and cites evidence.</p>
              </article>
              <article>
                <span>03</span>
                <h4>Second-eye Reviewer</h4>
                <p>Checks every YES or NO without seeing the Oracle’s answer.</p>
              </article>
              <article>
                <span>04</span>
                <h4>Judge</h4>
                <p>Decides again after a disagreement, without seeing either answer.</p>
              </article>
            </div>
            <aside class="failure-note">
              <p class="eyebrow">Why the extra checks</p>
              <p>
                Early runs exposed rare but basic Oracle errors: it answered YES to “born before
                1800?” while citing 1875. A full run asks hundreds of questions, so even rare
                errors add up. Reviewer and Judge use different model families and providers to
                reduce correlated mistakes.
              </p>
            </aside>
          </div>
        </div>
      </section>

      <section class="content-section cohort-section">
        <div class="content-inner cohort-layout">
          <div>
            <p class="eyebrow">From game to benchmark</p>
            <h2>The same game, made comparable.</h2>
            <p>
              Every model plays behind the same information boundary. Subjects receive equal
              weight and failed trials remain in the score.
            </p>
            <RouterLink class="text-link" :to="{ name: 'methodology' }">
              Read the full method →
            </RouterLink>
          </div>
          <div class="protocol-flow" aria-label="Benchmark protocol">
            <p class="eyebrow">Protocol</p>
            <div>
              <span><i>?</i>Hidden subject</span>
              <b aria-hidden="true">→</b>
              <span><i>◇</i>Model</span>
              <b aria-hidden="true">→</b>
              <span><i>?</i>Yes / no questions</span>
            </div>
            <p>Up to {{ manifest.active_cohort.max_questions }} questions · exact guess required</p>
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
              />
            </article>

            <div class="leaderboard-layout">
              <div class="score-chart">
                <p class="chart-title">Score comparison</p>
                <ScoreDotPlot :items="scoreDots" />
              </div>
              <dl class="result-counts">
                <div><dt>Official models</dt><dd>{{ evaluated.length }}</dd></div>
                <div><dt>Trials / model</dt><dd>{{ totalTrials }}</dd></div>
              </dl>
            </div>

            <div class="table-wrap" tabindex="0" aria-label="Scrollable official leaderboard">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Reasoning</th>
                    <th data-numeric>Score</th>
                    <th data-numeric>Success</th>
                    <th data-numeric>Contract</th>
                    <th data-numeric>Run cost</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in evaluated"
                    :key="row.model.model_id"
                    :class="{ 'result-row--clickable': row.execution_id !== null }"
                  >
                    <td>{{ row.rank ?? "—" }}</td>
                    <td>
                      <RouterLink
                        v-if="row.execution_id"
                        class="result-row-link"
                        :to="runLink(row)"
                        :aria-label="`Open full details for ${row.model.display_name}`"
                      >
                        {{ row.model.display_name }}
                      </RouterLink>
                      <strong v-else>{{ row.model.display_name }}</strong>
                      <small>{{ row.model.model_id }} · {{ row.model.provider }}</small>
                    </td>
                    <td><ReasoningEffort :effort="row.model.reasoning_effort" compact /></td>
                    <td data-numeric>{{ number(row.question_score) }}</td>
                    <td data-numeric>{{ percent(row.success_rate) }}</td>
                    <td data-numeric>
                      {{ percent(row.contract?.compliance_rate) }}
                      <small v-if="row.contract?.status === 'breached'">
                        {{ row.contract.violations }} violations
                      </small>
                    </td>
                    <td data-numeric>{{ money(row.total_cost_usd) }}</td>
                  </tr>
                </tbody>
              </table>
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
          <p class="home-build-stamp">
            Homepage built
            <time :datetime="manifest.provenance.built_at">
              {{ dateTime(manifest.provenance.built_at) }}
            </time>
          </p>
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

.live-result {
  display: grid;
  grid-template-columns: auto auto;
  column-gap: 0.65rem;
  align-items: end;
}

.live-result .eyebrow {
  grid-column: 1 / -1;
  margin: 0 0 0.12rem;
  color: rgb(255 255 255 / 55%);
  font-size: var(--text-micro);
}

.live-result strong {
  color: var(--acid);
  font-family: var(--font-display);
  font-size: 2.1rem;
  font-weight: 460;
  font-variant-numeric: tabular-nums;
  line-height: 0.95;
}

.live-result span {
  max-width: 13rem;
  font-size: var(--text-small);
  line-height: 1.25;
}

.round-card {
  border: 1px solid rgb(255 255 255 / 30%);
  background: rgb(255 255 255 / 4%);
}

.round-head,
.round-columns,
.round-card li {
  display: grid;
  align-items: center;
  gap: 0.8rem;
  padding: 0.78rem 0.95rem;
  border-bottom: 1px solid rgb(255 255 255 / 16%);
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
  border: 1px solid var(--line);
  background: var(--line);
  gap: 1px;
}

.ability-grid article,
.trust-grid article {
  min-height: 13.5rem;
  padding: 1.25rem;
  background: var(--paper-bright);
}

.ability-grid article > span,
.trust-grid article > span {
  display: grid;
  width: 1.75rem;
  height: 1.75rem;
  border: 1px solid var(--muted);
  border-radius: 50%;
  color: var(--ink);
  font: 620 var(--text-micro) var(--font-sans);
  place-items: center;
}

.ability-grid h3,
.trust-grid h3 {
  margin: 3.9rem 0 0.55rem;
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 470;
}

.ability-grid p,
.trust-grid p {
  margin: 0;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.5;
}

.adjudication {
  margin-top: clamp(3rem, 6vw, 5rem);
  padding-top: clamp(2.5rem, 5vw, 4rem);
  border-top: 1px solid var(--line);
}

.adjudication-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(17rem, 0.52fr);
  gap: 2rem;
  align-items: end;
  margin-bottom: clamp(2rem, 4vw, 3.25rem);
}

.adjudication-heading h3 {
  max-width: 15ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.3rem, 4.2vw, 4.2rem);
  font-weight: 470;
  letter-spacing: -0.042em;
  line-height: 0.99;
}

.adjudication-heading > p {
  margin: 0;
  color: var(--muted);
  line-height: 1.65;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--line);
  background: var(--line);
  gap: 1px;
}

.role-grid article {
  min-height: 13.5rem;
  padding: 1.25rem;
  background: var(--paper-bright);
}

.role-grid article > span {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 710;
  letter-spacing: 0.08em;
}

.role-grid h4 {
  margin: 4rem 0 0.55rem;
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 470;
}

.role-grid p {
  margin: 0;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.5;
}

.failure-note {
  display: grid;
  grid-template-columns: minmax(10rem, 0.3fr) minmax(0, 1fr);
  gap: clamp(1.5rem, 4vw, 4rem);
  margin-top: 1rem;
  padding: clamp(1.25rem, 2.5vw, 2rem);
  background: var(--ink);
  color: white;
}

.failure-note .eyebrow,
.failure-note > p:last-child {
  margin: 0;
}

.failure-note .eyebrow {
  color: var(--acid);
}

.failure-note > p:last-child {
  max-width: 58rem;
  color: rgb(255 255 255 / 72%);
  line-height: 1.65;
}

.cohort-section {
  background: #e8e5dc;
}

.cohort-layout {
  display: grid;
  grid-template-columns: minmax(15rem, 0.82fr) minmax(18rem, 0.9fr) minmax(15rem, 0.62fr);
  gap: clamp(2.5rem, 5vw, 5rem);
  align-items: center;
}

.cohort-layout h2 {
  max-width: 10ch;
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

.protocol-flow > .eyebrow {
  margin-bottom: 2.7rem;
}

.protocol-flow > div {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  gap: 0.7rem;
  align-items: center;
}

.protocol-flow span {
  display: grid;
  gap: 0.6rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 680;
  text-align: center;
  text-transform: uppercase;
}

.protocol-flow i {
  display: grid;
  width: 3.1rem;
  height: 3.1rem;
  margin-inline: auto;
  border: 1px solid var(--ink);
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-style: normal;
  font-weight: 450;
  place-items: center;
}

.protocol-flow b {
  font-weight: 450;
}

.protocol-flow > p:last-child {
  margin: 1.9rem 0 0;
  font-size: var(--text-micro);
  font-weight: 650;
  letter-spacing: 0.08em;
  text-align: center;
  text-transform: uppercase;
}

.cohort-facts,
.result-counts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 0;
  border: 1px solid var(--ink);
}

.cohort-facts div,
.result-counts div {
  display: flex;
  min-height: 7.6rem;
  padding: 1rem;
  border-right: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  flex-direction: column;
  justify-content: space-between;
}

.cohort-facts div:nth-child(even),
.result-counts div:nth-child(even) {
  border-right: 0;
}

.cohort-facts div:nth-last-child(-n + 2),
.result-counts div:nth-last-child(-n + 2) {
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
  background: linear-gradient(115deg, #5363ff 0%, #3f4df0 100%);
  color: white;
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(12rem, 0.3fr);
  margin-top: 1rem;
  border: 1px solid var(--line);
  background: var(--paper-bright);
}

.score-chart {
  min-width: 0;
  overflow: hidden;
  border-right: 1px solid var(--line);
}

.chart-title {
  margin: 0;
  padding: clamp(1.2rem, 3vw, 2rem) clamp(1.2rem, 3vw, 2rem) 0;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 760;
  text-transform: uppercase;
}

.score-chart :deep(.score-dot-plot) {
  padding: 0 clamp(0.65rem, 1.5vw, 1rem) 0.5rem;
}

.result-counts {
  grid-template-columns: 1fr;
  border: 0;
}

.result-counts div,
.result-counts div:nth-child(even) {
  border-right: 0;
  border-bottom: 1px solid var(--line);
}

.result-counts div:last-child {
  border-bottom: 0;
}

.table-wrap {
  margin-top: 1rem;
}

.empty-results {
  padding: clamp(2rem, 5vw, 4rem);
  border: 1px solid var(--line);
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
  border-top: 1px solid var(--line);
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

.origin-strip > div:last-child > .home-build-stamp {
  width: fit-content;
  margin: 1.4rem 0 0;
  padding-top: 0.7rem;
  border-top: 1px solid rgb(12 17 27 / 22%);
  color: rgb(12 17 27 / 62%);
  font-size: var(--text-micro);
  font-weight: 680;
  letter-spacing: 0.04em;
  line-height: 1.45;
  text-transform: uppercase;
}

.home-build-stamp time {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 940px) {
  .home-hero-inner,
  .cohort-layout,
  .winner-card,
  .leaderboard-layout,
  .origin-strip {
    grid-template-columns: 1fr;
  }

  .ability-grid {
    grid-template-columns: 1fr 1fr;
  }

  .adjudication-heading {
    grid-template-columns: 1fr;
  }

  .role-grid {
    grid-template-columns: 1fr 1fr;
  }

  .score-chart {
    border-right: 0;
    border-bottom: 1px solid var(--line);
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
  .role-grid,
  .failure-note {
    grid-template-columns: 1fr;
  }

  .ability-grid article,
  .trust-grid article,
  .role-grid article {
    min-height: 11rem;
  }

  .ability-grid h3,
  .trust-grid h3,
  .role-grid h4 {
    margin-top: 3rem;
  }

  .empty-results dl {
    grid-template-columns: 1fr;
  }
}
</style>
