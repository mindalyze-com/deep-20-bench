<script setup lang="ts">
import { computed, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import IllustrativeRoundExample from "@/components/IllustrativeRoundExample.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getManifest } from "@/lib/api";
import { usePageRouteContext } from "@/lib/route-context";
import type { ManifestDocument } from "@/lib/types";
import { usePublicationLoad } from "@/lib/use-publication-load";

const manifest = ref<ManifestDocument | null>(null);
usePageRouteContext({
  title: "Method",
  description:
    "From one Twenty Questions round to repeated trials, scoring, official comparison, and publication.",
});
const { loading, error } = usePublicationLoad(async () => {
  manifest.value = await getManifest();
}, "Method data is unavailable.");

const penalty = computed(() => {
  const value = manifest.value;
  return value === null
    ? 0
    : value.active_cohort.max_questions + value.score_policy.failure_penalty_offset;
});
const totalTrials = computed(() => {
  const value = manifest.value;
  return value === null ? 0 : value.active_cohort.target_ids.length * value.active_cohort.iterations;
});
</script>

<template>
  <div id="route-content" class="page methodology-page" tabindex="-1">
    <LoadingState v-if="loading" label="Loading method" />
    <ErrorState v-else-if="error !== null" :message="error" />
    <template v-else-if="manifest !== null">
      <section class="page-hero site-boundary-shell">
        <div class="page-hero-inner site-boundary">
          <div>
            <p class="eyebrow">Methodology</p>
            <h1>From one round to a comparable score.</h1>
          </div>
          <p class="lede">
            Start with one model playing Twenty Questions. Then repeat the same controlled game
            across fixed subjects and convert the completed trials into one score.
          </p>
        </div>
      </section>

      <div class="method-nav-shell site-boundary-shell">
        <nav class="method-nav site-boundary" aria-label="Methodology contents">
          <a href="#game">01 · One round</a>
          <a href="#answer-checks">02 · Answer checks</a>
          <a href="#repetition">03 · Repetition</a>
          <a href="#scoring">04 · Scoring</a>
          <a href="#reliability">05 · Reliability</a>
          <a href="#eligibility">06 · Official runs</a>
          <a href="#publication">07 · Publication</a>
        </nav>
      </div>

      <section id="game" class="content-section game-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">01 · One round</p>
            <p class="section-note">Guesser = model under test</p>
          </div>
          <div>
            <h2>One hidden subject. One adaptive conversation.</h2>
            <p class="lead">
              The Guesser receives a broad category, but not the subject. It asks one yes-or-no
              question at a time, uses every prior answer, and eventually makes an exact guess.
            </p>
            <div class="method-round">
              <IllustrativeRoundExample />
            </div>
            <p>
              In this illustrative round, three questions count. The correct guess does not. An
              incorrect guess before the limit consumes one counted question and play continues.
            </p>
            <dl class="fact-grid" aria-label="Single-round rules">
              <div><dt>Starting clue</dt><dd>Broad category</dd></div>
              <div><dt>Answer tokens</dt><dd>YES · NO · UNKNOWN</dd></div>
              <div><dt>Question limit</dt><dd>{{ manifest.active_cohort.max_questions }}</dd></div>
              <div><dt>Final opportunity</dt><dd>Exact guess only</dd></div>
            </dl>
            <aside class="method-note">
              <strong>Why “Twenty Questions” with a limit of
                {{ manifest.active_cohort.max_questions }}?</strong>
              <p>
                Twenty Questions names the game, not the scoring limit. A hard stop at 20 would
                hide the difference between a model that succeeds shortly after 20 and one that
                never identifies the subject. The current policy therefore allows up to
                {{ manifest.active_cohort.max_questions }} counted questions. Every additional
                question increases the trial value and remains visible in the final average. A
                model that still has not succeeded receives one final guess-only opportunity, and
                a failure scores {{ penalty }}, one point worse than any successful trial.
              </p>
            </aside>
          </div>
        </div>
      </section>

      <section id="answer-checks" class="content-section answer-checks-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">02 · Answer checks</p>
            <p class="section-note">Separate, blind roles</p>
          </div>
          <div>
            <h2>Questions and guesses follow separate paths.</h2>
            <p class="lead">
              Factual questions go through evidence-backed adjudication. Exact guesses go to a
              separate Validator. The Guesser receives only the final answer token.
            </p>
            <div class="answer-roles">
              <article>
                <span>01 · Oracle</span>
                <h3>Search and cite evidence.</h3>
                <p>
                  The Oracle must search the live web instead of relying on memory. It cites
                  evidence and proposes YES, NO, or UNKNOWN.
                </p>
              </article>
              <article>
                <span>02 · Reviewer</span>
                <h3>Make a blind second decision.</h3>
                <p>
                  For every Oracle YES or NO, the no-web Reviewer uses the subject, question, and
                  evidence without seeing the Oracle answer.
                </p>
              </article>
              <article>
                <span>03 · Judge</span>
                <h3>Resolve disagreement.</h3>
                <p>
                  If the first two decisions differ, including Reviewer UNKNOWN, the no-web Judge
                  decides from the same limited material without seeing either answer.
                </p>
              </article>
              <article>
                <span>04 · Guess Validator</span>
                <h3>Check the proposed identity.</h3>
                <p>
                  The separate no-web Validator receives only the trusted subject and the
                  structured guess, then returns YES, NO, or UNKNOWN.
                </p>
              </article>
            </div>
            <div class="decision-path" aria-label="Question and guess decision paths">
              <article>
                <span>ASK path</span>
                <strong>Oracle → Reviewer when YES or NO → Judge on disagreement → final</strong>
                <small>Oracle UNKNOWN is final and bypasses review.</small>
              </article>
              <article>
                <span>GUESS path</span>
                <strong>Guess Validator → final</strong>
                <small>The factual-answer roles never evaluate the identity.</small>
              </article>
            </div>
            <div class="isolation-callout">
              <h3>The Guesser is fully isolated from adjudication.</h3>
              <p>
                It never sees the hidden subject, searches, evidence, citations, adjudicator
                prompts or decisions, provider traces, or private artifacts. Its visible history
                contains only the broad category, its own prior actions, final YES, NO, or UNKNOWN
                tokens, and the fixed format reminder after its own invalid output.
              </p>
            </div>
            <aside class="rationale-note">
              <p>
                Early runs exposed rare but basic Oracle errors. In one case, it answered YES to
                “born before 1800?” while citing 1875. A full run asks hundreds of questions, so
                even rare errors add up. Reviewer and Judge use different model families and
                providers to reduce correlated mistakes.
              </p>
            </aside>
          </div>
        </div>
      </section>

      <section id="repetition" class="content-section repetition-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">03 · Repetition</p>
            <p class="section-note">{{ manifest.active_cohort.display_name }}</p>
          </div>
          <div>
            <h2>One round becomes {{ totalTrials }} isolated trials.</h2>
            <p class="lead">
              Every model plays the same {{ manifest.active_cohort.target_ids.length }} subjects
              in {{ manifest.active_cohort.iterations }} fresh trials per subject.
            </p>
            <p>
              Each trial starts a new Guesser conversation. No questions, answers, guesses, or
              adjudicator state carry into another trial. A versioned, subject-independent
              variation token changes the repeated-call condition without revealing anything
              about the hidden subject.
            </p>
            <dl class="fact-grid" aria-label="Benchmark repetition">
              <div><dt>Subjects</dt><dd>{{ manifest.active_cohort.target_ids.length }}</dd></div>
              <div><dt>Trials / subject</dt><dd>{{ manifest.active_cohort.iterations }}</dd></div>
              <div><dt>Trials / model</dt><dd>{{ totalTrials }}</dd></div>
              <div><dt>Base seed</dt><dd>{{ manifest.active_cohort.base_seed }}</dd></div>
            </dl>
            <p>
              Repetition matters because model outputs vary across fresh calls. Multiple trials
              show whether a question strategy is consistently effective or succeeds only in
              some rounds.
            </p>
            <div id="subject-design" class="subject-design">
              <p class="eyebrow">Subject design and contamination</p>
              <h3>The current subject set is small.</h3>
              <p>
                Each subject has a canonical identity, accepted aliases, a clear description,
                and a public reference. The current cohort includes real people, fictional
                characters, and a mythological figure. It is a fixed list for every model in
                this protocol. It is not random, balanced, or representative, and it does not
                yet include places or objects.
              </p>
              <p>
                Seven subjects is too small for broad conclusions. The size is mainly a cost
                constraint: every additional subject adds repeated Guesser turns, live Oracle
                searches, Reviewer calls, and sometimes Judge calls. Five trials per subject
                help measure variation, but repetition does not make the small subject set more
                representative.
              </p>
              <h4>Versioning and contamination</h4>
              <p>
                The cohort and protocol are versioned together. Official comparisons use the
                same fixed cohort and protocol. Subject identities and transcripts become public
                after publication, so a later model may have seen the subject list or earlier
                runs. Deep20Bench does not claim that this public cohort is resistant to
                benchmark contamination.
              </p>
              <h4>Future cohorts</h4>
              <p>
                Future cohorts will aim to include more subjects and broader entity types,
                including places and objects. Their selection rules and identities will be fixed
                before evaluation. A changed cohort or protocol receives a new version, and its
                results will be reported separately instead of merged with the current
                leaderboard.
              </p>
            </div>
            <aside class="scope-note">
              <strong>Scope of the result</strong>
              <p>
                The score describes this benchmark version on these fixed subjects. It is a
                narrow task result, not a general ranking of model intelligence or a prediction
                for unseen subjects.
              </p>
            </aside>
          </div>
        </div>
      </section>

      <section id="scoring" class="content-section dark-method">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">04 · Scoring</p>
            <p class="section-note">{{ manifest.score_policy.version }}</p>
          </div>
          <div>
            <h2>Question score is the average counted questions.</h2>
            <p class="lead">
              Lower is better. A model failure counts as {{ penalty }}, one above the
              {{ manifest.active_cohort.max_questions }}-question limit.
            </p>
            <div class="score-rules">
              <article>
                <span>Successful trial</span>
                <strong>Counted questions used</strong>
              </article>
              <article>
                <span>Model failure</span>
                <strong>{{ penalty }} questions</strong>
              </article>
              <article>
                <span>Infrastructure failure</span>
                <strong>Not scored · waits for retry</strong>
              </article>
            </div>
            <div class="formula" aria-label="Question score formula">
              <div>
                <span>Trial score</span>
                <strong>questions used · failed trial = {{ penalty }}</strong>
              </div>
              <div>
                <span>Subject average</span>
                <strong class="math-expression score-average-formula">
                  <math
                    display="block"
                    aria-label="One divided by T, times the sum of trial scores from trial one through trial T"
                  >
                    <mrow>
                      <mfrac>
                        <mn>1</mn>
                        <mi>T</mi>
                      </mfrac>
                      <munderover>
                        <mo>∑</mo>
                        <mrow>
                          <mi>t</mi>
                          <mo>=</mo>
                          <mn>1</mn>
                        </mrow>
                        <mi>T</mi>
                      </munderover>
                      <msub>
                        <mtext>trial score</mtext>
                        <mi>t</mi>
                      </msub>
                    </mrow>
                  </math>
                  <small class="math-key"><i>T</i> = number of trials for the subject</small>
                </strong>
              </div>
              <div>
                <span>Final model score</span>
                <strong class="math-expression score-average-formula">
                  <math
                    display="block"
                    aria-label="One divided by S, times the sum of subject averages from subject one through subject S"
                  >
                    <mrow>
                      <mfrac>
                        <mn>1</mn>
                        <mi>S</mi>
                      </mfrac>
                      <munderover>
                        <mo>∑</mo>
                        <mrow>
                          <mi>s</mi>
                          <mo>=</mo>
                          <mn>1</mn>
                        </mrow>
                        <mi>S</mi>
                      </munderover>
                      <msub>
                        <mtext>subject average</mtext>
                        <mi>s</mi>
                      </msub>
                    </mrow>
                  </math>
                  <small class="math-key"><i>S</i> = number of subjects</small>
                </strong>
              </div>
            </div>
            <h3>Uncertainty across repeated trials</h3>
            <p>
              Each model score includes a 95% confidence interval for repeated seeded trials on
              these fixed subjects. The calculation estimates the trial variance separately for
              each subject, divides it by that subject’s trial count, and combines the equally
              weighted variance estimates. It uses a Welch–Satterthwaite t interval so subjects
              may have different trial variance.
            </p>
            <div class="formula" aria-label="Question score confidence interval formula">
              <div class="standard-error-formula">
                <span>Standard error</span>
                <strong class="math-expression">
                  <math
                    display="block"
                    aria-label="Standard error equals one divided by the number of subjects, times the square root of the sum across subjects of each subject's sample trial variance divided by its trial count"
                  >
                    <mrow>
                      <mi>SE</mi>
                      <mo>=</mo>
                      <mfrac>
                        <mn>1</mn>
                        <mi>S</mi>
                      </mfrac>
                      <msqrt>
                        <mrow>
                          <munderover>
                            <mo>∑</mo>
                            <mrow>
                              <mi>s</mi>
                              <mo>=</mo>
                              <mn>1</mn>
                            </mrow>
                            <mi>S</mi>
                          </munderover>
                          <mfrac>
                            <msubsup>
                              <mover accent="true">
                                <mi>σ</mi>
                                <mo>ˆ</mo>
                              </mover>
                              <mi>s</mi>
                              <mn>2</mn>
                            </msubsup>
                            <msub>
                              <mi>n</mi>
                              <mi>s</mi>
                            </msub>
                          </mfrac>
                        </mrow>
                      </msqrt>
                    </mrow>
                  </math>
                  <small class="math-key">
                    <i>S</i> = subjects · <i>n<sub>s</sub></i> = trials for subject <i>s</i> ·
                    <i>σ̂<sup>2</sup><sub>s</sub></i> = sample trial variance for subject <i>s</i>
                  </small>
                </strong>
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
            <p class="eyebrow">05 · Reliability</p>
            <p class="section-note">Structured action contract</p>
          </div>
          <div>
            <h2>Success does not erase a broken contract.</h2>
            <p class="lead">
              The Guesser must return exactly one valid ASK or GUESS action. Every invalid
              response remains visible, even when the model later finds the subject.
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
              Before the question limit, an invalid response consumes one counted turn and
              receives the same fixed format reminder. The reminder contains no parser detail,
              correctness feedback, evidence, or subject information.
            </p>
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
            <p class="eyebrow">06 · Official runs</p>
            <p class="section-note">Comparable evidence</p>
          </div>
          <div>
            <h2>Only complete, comparable runs enter the leaderboard.</h2>
            <p class="lead">
              The Guesser configuration changes between candidates. The subjects, game policy,
              Oracle, Reviewer, Judge, Guess Validator, trial count, and scoring policy stay fixed.
            </p>
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
            <p>
              Published cost comparisons use only each trial's retained terminal attempt.
              Superseded infrastructure attempts remain in the signed repair ledger and gross
              execution total, but do not increase public model or benchmark costs.
            </p>
          </div>
        </div>
      </section>

      <section id="publication" class="content-section publication-section">
        <div class="content-inner editorial-copy">
          <div>
            <p class="eyebrow">07 · Publication</p>
            <p class="section-note">One-way reporting</p>
          </div>
          <div>
            <h2>Publication happens after play is finished.</h2>
            <p class="lead">
              The static site reads completed, signed run artifacts. It never participates in a
              trial and never sends published information back to the Guesser.
            </p>
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
            <p>
              Public pages connect each score to model runs, subjects, episodes, transcripts,
              answer evidence, contract violations, usage, cost, and timing. Private prompts,
              hidden reasoning, provider traces, and credentials remain excluded.
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
.method-nav-shell {
  border-bottom: var(--rule-default);
  background: var(--paper-bright);
}

.method-nav {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-inline: var(--rule-default);
  background: var(--paper-bright);
}

.method-nav a {
  padding: 1.1rem clamp(0.6rem, 1.2vw, 1rem);
  border-right: var(--rule-default);
  font-size: var(--text-ui);
  font-weight: var(--font-weight-bold);
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

.method-round {
  --method-round-padding: clamp(1rem, 3vw, 2rem);

  width: min(100%, calc(var(--round-example-max) + clamp(2rem, 6vw, 4rem)));
  margin: 2.5rem 0;
  padding: var(--method-round-padding);
  background: var(--ink);
}

.method-note {
  padding: 1.2rem;
  border-left: 4px solid var(--blue);
  background: var(--surface-rail);
}

.method-note p,
.rationale-note p {
  margin: 0;
  max-width: none;
}

.method-note strong {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--ink);
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
.score-rules span,
.reliability-grid span {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.fact-grid dd {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.35rem, 2.4vw, 2.35rem);
  overflow-wrap: anywhere;
}

.answer-checks-section {
  background: var(--paper-bright);
}

.answer-roles {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  margin: 2.5rem 0 1rem;
  border: var(--rule-default);
  background: var(--line);
  gap: 1px;
}

.answer-roles article {
  min-height: 12rem;
  padding: 1.2rem;
  background: white;
}

.answer-roles span {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.answer-roles h3 {
  margin: var(--space-3) 0 0.65rem;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: var(--font-weight-medium);
}

.answer-roles p {
  margin: 0;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.5;
}

.decision-path {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  margin: 0 0 2rem;
  border: var(--rule-strong);
}

.decision-path article {
  display: flex;
  min-height: 9rem;
  margin: 0;
  padding: 1rem;
  border-right: var(--rule-strong);
  flex-direction: column;
  gap: 0.75rem;
}

.decision-path article:last-child {
  border-right: 0;
}

.decision-path strong,
.decision-path span,
.decision-path small {
  font-size: var(--text-small);
}

.decision-path span {
  color: var(--blue-ink);
  font-weight: var(--font-weight-bold);
}

.decision-path small {
  color: var(--muted);
  line-height: 1.5;
}

.isolation-callout {
  margin: 2.5rem 0;
  padding: clamp(1.5rem, 3vw, 2.5rem);
  background: var(--ink);
  color: white;
}

.isolation-callout h3 {
  margin: 0 0 var(--space-4);
  color: var(--acid);
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 3vw, 2.4rem);
  font-weight: var(--font-weight-medium);
}

.isolation-callout p {
  margin: 0;
  color: rgb(255 255 255 / 72%);
  line-height: 1.65;
}

.rationale-note {
  padding-top: 1.5rem;
  border-top: var(--rule-strong);
}

.repetition-section {
  background: var(--paper-bright);
}

.subject-design {
  margin-top: 2.5rem;
  padding-top: 2rem;
  border-top: var(--rule-strong);
}

.subject-design h3 {
  margin-top: 0.4rem;
}

.subject-design h4 {
  margin: 1.7rem 0 0.35rem;
  font-size: var(--text-ui);
}

.scope-note {
  margin-top: 2.5rem;
  padding: 1.4rem;
  background: var(--acid);
  color: var(--ink);
}

.scope-note > strong {
  font-size: var(--text-ui);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.scope-note p {
  margin-bottom: 0;
  color: var(--ink);
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

.score-rules {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 2.5rem 0;
  border: var(--rule-inverse);
}

.score-rules article {
  display: flex;
  min-height: 8rem;
  padding: 1rem;
  border-right: var(--rule-inverse);
  flex-direction: column;
  justify-content: space-between;
}

.score-rules article:last-child {
  border-right: 0;
}

.score-rules span {
  color: rgb(255 255 255 / 58%);
}

.score-rules strong {
  font-size: 0.86rem;
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
  font: var(--font-weight-semibold) clamp(0.82rem, 2vw, 1.1rem) var(--font-mono);
  text-align: right;
}

.formula .math-expression {
  display: flex;
  gap: 0.45rem;
  align-items: flex-end;
  flex-direction: column;
}

.math-expression math {
  font-size: clamp(1.35rem, 3vw, 1.9rem);
}

.math-expression.score-average-formula math {
  font-size: clamp(1.05rem, 2.4vw, 1.55rem);
}

.formula .score-average-formula {
  gap: var(--space-1);
}

.math-expression .math-key {
  max-width: 44rem;
  color: rgb(255 255 255 / 68%);
  font: var(--font-weight-medium) var(--text-caption)/1.35 var(--font-sans);
  letter-spacing: 0;
  text-wrap: balance;
}

.formula div:last-child .math-key {
  color: rgb(11 16 25 / 68%);
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

.publication-section {
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
  font-weight: var(--font-weight-bold);
  text-align: center;
  place-items: center;
}

.flow i {
  color: var(--blue);
  font-style: normal;
}

@media (max-width: 760px) {
  .method-nav-shell {
    padding-inline: 0;
  }

  .method-nav {
    border-inline: 0;
    grid-template-columns: 1fr 1fr;
  }

  .method-nav a {
    border-bottom: var(--rule-muted);
  }

  .method-nav a:nth-child(even) {
    border-right: 0;
  }

  .method-nav a:last-child {
    grid-column: 1 / -1;
    border-right: 0;
    border-bottom: 0;
  }

  .answer-roles,
  .decision-path,
  .flow,
  .score-rules,
  .reliability-grid {
    grid-template-columns: 1fr;
  }

  .answer-roles article,
  .decision-path article,
  .flow i {
    border-right: 0;
  }

  .answer-roles article,
  .decision-path article {
    min-height: auto;
    border-bottom: var(--rule-default);
  }

  .answer-roles article:last-child,
  .decision-path article:last-child {
    border-bottom: 0;
  }

  .flow i {
    transform: rotate(90deg);
    text-align: center;
  }

  .score-rules article,
  .reliability-grid article {
    border-right: 0;
    border-bottom: var(--rule-default);
  }

  .score-rules article:last-child,
  .reliability-grid article:last-child {
    border-bottom: 0;
  }
}
</style>
