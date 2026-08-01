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
        <a href="#answer-checks">02 · Answer checks</a>
        <a href="#scoring">03 · Scoring</a>
        <a href="#reliability">04 · Reliability</a>
        <a href="#eligibility">05 · Eligibility</a>
        <a href="#isolation">06 · Isolation</a>
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
            <p>
              <strong>Why twenty?</strong> With ideal yes-or-no questions, each answer halves
              the search space. Twenty answers can distinguish up to 2²⁰, or 1,048,576,
              possibilities. See
              <a
                href="https://en.wikipedia.org/wiki/Twenty_questions"
                target="_blank"
                rel="noreferrer"
              >Twenty Questions on Wikipedia</a>.
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

      <section id="answer-checks" class="content-section answer-checks-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">02 · Answer checks</p>
            <p class="section-note">Blind adjudication</p>
          </div>
          <div>
            <h2>Three checks produce one answer.</h2>
            <p class="lead">
              The Guesser never sees the research or review. It receives only the final YES, NO,
              or UNKNOWN.
            </p>
            <div class="answer-roles">
              <article>
                <span>01 · Oracle</span>
                <h3>Research the question.</h3>
                <p>
                  The Oracle must not answer from its own knowledge, where a plausible answer
                  may still be wrong. It must search the live web, cite evidence, and then
                  propose YES, NO, or UNKNOWN.
                </p>
              </article>
              <article>
                <span>02 · Reviewer</span>
                <h3>Check every YES or NO.</h3>
                <p>
                  The Reviewer checks each Oracle YES or NO using the subject, question, and
                  evidence, without seeing the Oracle’s answer.
                </p>
              </article>
              <article>
                <span>03 · Judge</span>
                <h3>Resolve disagreement.</h3>
                <p>
                  If the first two decisions disagree, the Judge decides from the same limited
                  material, without seeing either answer.
                </p>
              </article>
            </div>
            <div class="decision-path" aria-label="Answer review decision path">
              <p><strong>Oracle UNKNOWN</strong><span>→ final</span></p>
              <p><strong>Oracle YES or NO</strong><span>→ Reviewer</span></p>
              <p><strong>Agreement</strong><span>→ final</span></p>
              <p><strong>Disagreement</strong><span>→ Judge → final</span></p>
            </div>
            <p>
              Early runs exposed rare but basic Oracle errors. In one case, it answered YES to
              “born before 1800?” while citing 1875. A full run asks hundreds of questions, so
              even rare errors add up. Reviewer and Judge use different model families and
              providers to reduce correlated mistakes.
            </p>
          </div>
        </div>
      </section>

      <section id="scoring" class="content-section dark-method">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">03 · Scoring</p>
            <p class="section-note">{{ manifest.score_policy.version }}</p>
          </div>
          <div>
            <h2>The model score is the average number of questions.</h2>
            <p class="lead">
              Lower is better. A failed trial counts as {{ penalty }} questions.
            </p>
            <div class="formula" aria-label="Question score formula">
              <div>
                <span>Trial score</span>
                <strong>questions used · failed trial = {{ penalty }}</strong>
              </div>
              <div>
                <span>Subject average</span>
                <strong>
                  (trial 1 + … + trial {{ manifest.active_cohort.iterations }}) ÷
                  {{ manifest.active_cohort.iterations }}
                </strong>
              </div>
              <div>
                <span>Final model score</span>
                <strong>
                  (subject average 1 + … + subject average
                  {{ manifest.active_cohort.target_ids.length }}) ÷
                  {{ manifest.active_cohort.target_ids.length }}
                </strong>
              </div>
            </div>
            <p>
              First, average the trials for each subject. Then average the subject results. This
              gives every subject equal weight. Infrastructure failures are not scored.
            </p>
            <h3>Repeated-trial confidence interval</h3>
            <p>
              Each model score includes a 95% confidence interval for repeated seeded trials on
              these fixed subjects. The calculation estimates the trial variance separately for
              each subject, divides it by that subject’s trial count, and combines the seven
              equally weighted variance estimates. It uses a Welch–Satterthwaite t interval so
              subjects may have different trial variance.
            </p>
            <div class="formula" aria-label="Question score confidence interval formula">
              <div>
                <span>Standard error</span>
                <strong>√[Σ(subject trial variance ÷ trials) ÷ subjects²]</strong>
              </div>
              <div>
                <span>95% interval</span>
                <strong>model score ± t critical value × standard error</strong>
              </div>
            </div>
            <p>
              A wider interval means the repeated trials were less consistent. The interval does
              not cover new subjects, model or provider changes, or future benchmark versions.
              It assumes separate seeded calls act as independent repetitions within each
              subject. A unique seed supports that assumption but does not prove it. The interval
              describes the mean score, not the range of individual trials. Individual model
              intervals are not a pairwise significance test.
            </p>
            <p>
              The <RouterLink :to="{ name: 'results-reliability' }">Stability result view</RouterLink>
              ranks the exact interval width from narrowest to widest. Every model uses the same
              95% confidence level. Question score remains visible but does not affect this rank,
              so a consistently poor model can still be highly repeatable.
            </p>
          </div>
        </div>
      </section>

      <section id="reliability" class="content-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">04 · Reliability</p>
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
            <p class="eyebrow">05 · Eligibility</p>
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
            <p class="eyebrow">06 · Isolation</p>
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
  grid-template-columns: repeat(6, 1fr);
  border-bottom: var(--rule-default);
  background: var(--paper-bright);
}

.method-nav a {
  padding: 1.2rem var(--gutter);
  border-right: var(--rule-default);
  font-size: var(--text-ui);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-decoration: none;
}

.method-nav a:last-child {
  border-right: 0;
}

.section-note {
  color: var(--muted);
  font-size: var(--text-small);
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
  border: var(--rule-strong);
}

.fact-grid div {
  display: flex;
  min-height: 8rem;
  padding: 1rem;
  border-right: var(--rule-strong);
  border-bottom: var(--rule-strong);
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
  font-size: var(--text-micro);
  font-weight: 780;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.fact-grid dd {
  margin: 0;
  font-family: var(--font-display);
  font-size: 2.35rem;
}

.answer-checks-section {
  background: var(--paper-bright);
}

.answer-roles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 2.5rem 0 1rem;
  border: var(--rule-default);
  background: var(--line);
  gap: 1px;
}

.answer-roles article {
  min-height: 14rem;
  padding: 1.2rem;
  background: white;
}

.answer-roles span {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 780;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.answer-roles h3 {
  margin: 2.5rem 0 0.65rem;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 500;
}

.answer-roles p {
  margin: 0;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.5;
}

.decision-path {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 0 0 2rem;
  border: var(--rule-strong);
}

.decision-path p {
  display: flex;
  min-height: 6.5rem;
  margin: 0;
  padding: 1rem;
  border-right: var(--rule-strong);
  flex-direction: column;
  justify-content: space-between;
}

.decision-path p:last-child {
  border-right: 0;
}

.decision-path strong,
.decision-path span {
  font-size: var(--text-small);
}

.decision-path span {
  color: var(--blue-ink);
  font-weight: 720;
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
  border: var(--rule-inverse);
}

.formula div {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 1.15rem;
  border-bottom: var(--rule-inverse);
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
  border: var(--rule-default);
}

.reliability-grid article {
  display: flex;
  min-height: 9rem;
  padding: 1rem;
  border-right: var(--rule-default);
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
  border-top: var(--rule-strong);
}

.check-list li {
  position: relative;
  padding: 1rem 1rem 1rem 2.6rem;
  border-bottom: var(--rule-default);
}

.check-list li::before {
  position: absolute;
  top: 0.82rem;
  left: 0;
  display: grid;
  width: 1.5rem;
  height: 1.5rem;
  border: var(--border-width) solid var(--blue);
  color: var(--blue);
  content: "✓";
  place-items: center;
}

.isolation-section {
  background: var(--surface-rail);
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
  border: var(--rule-strong);
  font-size: var(--text-small);
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
    border-bottom: var(--rule-muted);
  }

  .method-nav a:nth-child(even) {
    border-right: 0;
  }

  .method-nav a:nth-last-child(-n + 2) {
    border-bottom: 0;
  }

  .method-nav a:last-child {
    grid-column: auto;
  }

  .answer-roles,
  .decision-path,
  .flow,
  .reliability-grid {
    grid-template-columns: 1fr;
  }

  .answer-roles article,
  .decision-path p,
  .flow i {
    border-right: 0;
  }

  .answer-roles article,
  .decision-path p {
    min-height: auto;
    border-bottom: var(--rule-default);
  }

  .answer-roles article:last-child,
  .decision-path p:last-child {
    border-bottom: 0;
  }

  .flow i {
    transform: rotate(90deg);
    text-align: center;
  }

  .reliability-grid article {
    border-right: 0;
    border-bottom: var(--rule-default);
  }

  .reliability-grid article:last-child {
    border-bottom: 0;
  }
}
</style>
