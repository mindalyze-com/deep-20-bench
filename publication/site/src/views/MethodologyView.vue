<script setup lang="ts">
import { computed, onActivated, onDeactivated, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getManifest } from "@/lib/api";
import { setRouteContext } from "@/lib/route-context";
import type { ManifestDocument } from "@/lib/types";

const manifest = ref<ManifestDocument | null>(null);
const error = ref<string | null>(null);
const active = ref(true);

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Method",
    description: "The Deep20Bench protocol, score, eligibility rules, and isolation boundary.",
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
    manifest.value = await getManifest();
    if (active.value) applyRouteContext();
  } catch (reason: unknown) {
    error.value = reason instanceof Error ? reason.message : "Method data is unavailable.";
  }
};

void load();
applyRouteContext();

const penalty = computed(() => {
  const value = manifest.value;
  return value === null
    ? 0
    : value.active_cohort.max_questions + value.score_policy.failure_penalty_offset;
});
</script>

<template>
  <div id="route-content" class="page methodology-page" tabindex="-1">
    <LoadingState v-if="manifest === null && error === null" label="Loading method" />
    <ErrorState v-else-if="error !== null" :message="error" />
    <template v-else-if="manifest !== null">
      <section class="page-hero">
        <div class="page-hero-inner">
          <div>
            <p class="eyebrow">Methodology</p>
            <h1>How the benchmark works.</h1>
          </div>
          <p class="lede">
            A model identifies a hidden subject by asking yes-or-no questions. The publisher
            scores completed runs without rerunning or changing them.
          </p>
        </div>
      </section>

      <nav class="method-nav" aria-label="Methodology contents">
        <a href="#protocol">01 · Protocol</a>
        <a href="#scoring">02 · Scoring</a>
        <a href="#reliability">03 · Reliability</a>
        <a href="#eligibility">04 · Eligibility</a>
        <a href="#isolation">05 · Isolation</a>
      </nav>

      <section id="protocol" class="content-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">01 · Protocol</p>
            <p class="section-note">{{ manifest.active_cohort.display_name }}</p>
          </div>
          <div>
            <h2>Question, answer, guess.</h2>
            <p class="lead">
              The Guesser receives a broad category. It asks one question or makes one exact
              guess, then receives YES, NO, or UNKNOWN.
            </p>
            <dl class="fact-grid">
              <div><dt>Question limit</dt><dd>{{ manifest.active_cohort.max_questions }}</dd></div>
              <div><dt>Subjects</dt><dd>{{ manifest.active_cohort.target_ids.length }}</dd></div>
              <div><dt>Trials / subject</dt><dd>{{ manifest.active_cohort.iterations }}</dd></div>
              <div><dt>Base seed</dt><dd>{{ manifest.active_cohort.base_seed }}</dd></div>
            </dl>
            <p>
              The Validator checks final guesses. The Guesser never sees the subject, evidence,
              adjudicator state, or provider data.
            </p>
            <p>
              Invalid structured output is not judged. Before the limit, it consumes one counted
              turn and receives one fixed format reminder. It gives no semantic feedback.
              Episode pages show the typed violation, charge, and protocol response.
            </p>
          </div>
        </div>
      </section>

      <section id="scoring" class="content-section dark-method">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">02 · Scoring</p>
            <p class="section-note">{{ manifest.score_policy.version }}</p>
          </div>
          <div>
            <h2>The score is a question count.</h2>
            <p class="lead">Lower is better. The score stays in the unit used by the game.</p>
            <div class="formula" aria-label="Question score formula">
              <div>
                <span>Trial value</span>
                <strong>success: questions · failure: {{ penalty }}</strong>
              </div>
              <div>
                <span>Subject value</span>
                <strong>average of {{ manifest.active_cohort.iterations }} trials</strong>
              </div>
              <div>
                <span>Model score</span>
                <strong>
                  average of {{ manifest.active_cohort.target_ids.length }} subject values
                </strong>
              </div>
            </div>
            <p>
              A successful trial uses its counted questions. A model failure receives
              {{ penalty }}, one above the question limit. Subject averages are averaged again,
              so every subject has equal weight. Infrastructure failures are not scored.
            </p>
          </div>
        </div>
      </section>

      <section id="reliability" class="content-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">03 · Reliability</p>
            <p class="section-note">Independent aspect</p>
          </div>
          <div>
            <h2>Success does not erase a broken contract.</h2>
            <p class="lead">
              Every invalid structured response remains visible, even when the model later finds
              the subject.
            </p>
            <div class="reliability-grid">
              <article>
                <span>Turn consequence</span>
                <strong>One counted turn before the limit</strong>
              </article>
              <article>
                <span>Semantic feedback</span>
                <strong>None · format only</strong>
              </article>
              <article>
                <span>Published measure</span>
                <strong>Valid ÷ evaluated outputs</strong>
              </article>
            </div>
            <p>
              Episode, subject, run, and leaderboard pages report compliance, violations,
              affected trials, and counted penalties. The turn already affects the question
              total, so reliability adds no second score penalty.
            </p>
          </div>
        </div>
      </section>

      <section id="eligibility" class="content-section eligibility-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">04 · Eligibility</p>
            <p class="section-note">Official selection</p>
          </div>
          <div>
            <h2>Rules for official results.</h2>
            <p class="lead">Completed benchmark evidence is the qualification rule.</p>
            <ul class="check-list">
              <li>Signed run files pass integrity checks.</li>
              <li>The run is terminal and contains every active subject.</li>
              <li>Every subject has every configured completed trial.</li>
              <li>Completed model failures remain valid scored trials.</li>
              <li>Missing or infrastructure-failed trials wait for a retry.</li>
            </ul>
            <p>
              If several current runs qualify for one model, the newest completed run is used.
              The publisher never selects the best score. Invalid discovered input stops the
              build.
            </p>
          </div>
        </div>
      </section>

      <section id="isolation" class="content-section isolation-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">05 · Isolation</p>
            <p class="section-note">Information boundary</p>
          </div>
          <div>
            <h2>The publisher reads completed runs.</h2>
            <div class="flow" aria-label="One-way publication data flow">
              <span>Model calls</span><i aria-hidden="true">→</i>
              <span>Signed artifacts</span><i aria-hidden="true">→</i>
              <span>Public projection</span><i aria-hidden="true">→</i>
              <span>Static site</span>
            </div>
            <p>
              The publisher is a separate package. It does not import provider, prompt, session,
              retry, or credential code. Published data never returns to the Guesser.
            </p>
            <div class="button-row">
              <RouterLink class="button button-secondary" :to="{ name: 'data' }">
                View public data →
              </RouterLink>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.method-nav {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  border-bottom: 1px solid var(--line);
  background: var(--paper-bright);
}

.method-nav a {
  padding: 1.2rem var(--gutter);
  border-right: 1px solid var(--line);
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-decoration: none;
}

.method-nav a:last-child {
  border-right: 0;
}

.section-note {
  color: var(--muted);
  font-size: 0.75rem;
}

.lead {
  color: var(--ink);
  font-family: var(--font-text);
  font-size: clamp(1.2rem, 1.9vw, 1.65rem);
  line-height: 1.48;
}

.fact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 2.5rem 0;
  border: 1px solid var(--ink);
}

.fact-grid div {
  display: flex;
  min-height: 8rem;
  padding: 1rem;
  border-right: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  flex-direction: column;
  justify-content: space-between;
}

.fact-grid div:nth-child(even) {
  border-right: 0;
}

.fact-grid div:nth-last-child(-n + 2) {
  border-bottom: 0;
}

.fact-grid dt,
.formula span,
.reliability-grid span {
  color: var(--muted);
  font-size: 0.64rem;
  font-weight: 780;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.fact-grid dd {
  margin: 0;
  font-family: var(--font-display);
  font-size: 2.35rem;
}

.dark-method {
  background: var(--ink);
  color: white;
}

.dark-method :deep(.editorial-copy p),
.dark-method .section-note {
  color: rgb(255 255 255 / 63%);
}

.dark-method .lead {
  color: white;
}

.formula {
  margin: 2.5rem 0;
  border: 1px solid rgb(255 255 255 / 28%);
}

.formula div {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 1.15rem;
  border-bottom: 1px solid rgb(255 255 255 / 20%);
}

.formula div:last-child {
  border-bottom: 0;
  background: var(--acid);
  color: var(--ink);
}

.formula strong {
  font: 680 clamp(0.82rem, 2vw, 1.1rem) ui-monospace, monospace;
  text-align: right;
}

.reliability-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 2.5rem 0;
  border: 1px solid var(--line);
}

.reliability-grid article {
  display: flex;
  min-height: 9rem;
  padding: 1rem;
  border-right: 1px solid var(--line);
  flex-direction: column;
  justify-content: space-between;
}

.reliability-grid article:last-child {
  border-right: 0;
}

.reliability-grid strong {
  font-size: 0.85rem;
}

.eligibility-section {
  background: var(--paper-bright);
}

.check-list {
  margin: 2.5rem 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--ink);
}

.check-list li {
  position: relative;
  padding: 1rem 1rem 1rem 2.6rem;
  border-bottom: 1px solid var(--line);
}

.check-list li::before {
  position: absolute;
  top: 0.82rem;
  left: 0;
  display: grid;
  width: 1.5rem;
  height: 1.5rem;
  border: 1px solid var(--blue);
  color: var(--blue);
  content: "✓";
  place-items: center;
}

.isolation-section {
  background: #e8e5dc;
}

.flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
  gap: 0.55rem;
  align-items: center;
  margin: 2rem 0;
}

.flow span {
  display: grid;
  min-height: 5rem;
  padding: 0.7rem;
  border: 1px solid var(--ink);
  font-size: 0.72rem;
  font-weight: 740;
  text-align: center;
  place-items: center;
}

.flow i {
  color: var(--blue);
  font-style: normal;
}

@media (max-width: 760px) {
  .method-nav {
    grid-template-columns: 1fr 1fr;
  }

  .method-nav a {
    border-bottom: 1px solid rgb(17 19 28 / 20%);
  }

  .method-nav a:nth-child(even) {
    border-right: 0;
  }

  .method-nav a:last-child {
    grid-column: 1 / -1;
    border-bottom: 0;
  }

  .flow,
  .reliability-grid {
    grid-template-columns: 1fr;
  }

  .flow i {
    transform: rotate(90deg);
    text-align: center;
  }

  .reliability-grid article {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .reliability-grid article:last-child {
    border-bottom: 0;
  }
}
</style>
