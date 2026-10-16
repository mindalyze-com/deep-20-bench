<script setup lang="ts">
import { editionRoute } from "@/lib/route-location";
import { computed, ref } from "vue";

import EditionComparison from "@/components/EditionComparison.vue";
import { useEditionContext } from "@/lib/use-edition-context";
import ErrorState from "@/components/ErrorState.vue";
import IllustrativeRoundExample from "@/components/IllustrativeRoundExample.vue";
import MethodDetails from "@/components/MethodDetails.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getManifest, peekManifest } from "@/lib/api";
import { usePageRouteContext } from "@/lib/route-context";
import { questionScoreRankingRule } from "@/lib/result-chart";
import type { ManifestDocument } from "@/lib/types";
import { usePublicationLoad } from "@/lib/use-publication-load";

const { qualified } = useEditionContext();
const initialManifest = peekManifest();
const manifest = ref<ManifestDocument | null>(initialManifest);
usePageRouteContext({
  title: "Method",
  description:
    "How the game works, how answers are checked, and what the scores mean.",
});
const { loading, error } = usePublicationLoad(async () => {
  manifest.value = await getManifest();
}, "Method data is unavailable.", initialManifest !== null);

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
            <p class="eyebrow">Method · Edition {{ manifest.active_cohort.edition_label }}</p>
            <h1>How Deep20Bench works</h1>
          </div>
          <p class="lede">
            Deep20Bench measures how many questions an AI model needs to find a hidden subject.
            Each model plays the same subjects several times. The fewer questions it needs, the
            better its score. A round where it never finds the subject gets a fixed penalty.
          </p>
        </div>
      </section>

      <div class="method-nav-shell site-boundary-shell">
        <nav class="method-nav site-boundary" aria-label="Methodology contents">
          <a href="#game">01 · The game</a>
          <a href="#answer-checks">02 · Answer checks</a>
          <a href="#scoring">03 · The score</a>
          <a href="#repetition">04 · Comparisons</a>
          <a href="#publication">05 · Explore results</a>
        </nav>
      </div>

      <section id="game" class="content-section game-section">
        <div class="content-inner editorial-copy">
          <div><p class="eyebrow">01 · The game</p></div>
          <div>
            <h2>Find a hidden subject.</h2>
            <p class="lead">
              The model under test, called the Guesser, must identify a hidden subject: a
              person, character, or thing. It starts with only a broad category, asks one
              question at a time, and guesses when it is ready.
            </p>
            <div class="method-round">
              <IllustrativeRoundExample />
            </div>
            <p>
              The Guesser has up to {{ manifest.active_cohort.max_questions }} counted questions,
              then one final guess. See <a href="#scoring">what counts toward the score</a>.
            </p>
            <div class="answer-guide" aria-labelledby="answer-meanings-title">
              <h3 id="answer-meanings-title">What the answers mean</h3>
              <p>
                Most questions get a clear Yes or No. The other answers cover questions the
                facts do not settle clearly.
              </p>
              <dl class="answer-meanings">
                <div><dt>Yes</dt><dd>The information supports a clear Yes.</dd></div>
                <div v-if="qualified"><dt>Rather yes</dt><dd>It points toward Yes, but an important gap remains.</dd></div>
                <div v-if="qualified"><dt>Rather no</dt><dd>It points toward No, but an important gap remains.</dd></div>
                <div><dt>No</dt><dd>The information supports a clear No.</dd></div>
                <div><dt>Unknown</dt><dd>There is no clear direction, or unclear wording or conflicting evidence could change the answer.</dd></div>
              </dl>
              <p>
                Not finding something in a search is not enough for No<template v-if="qualified"> or Rather no</template>.
                <template v-if="qualified">Rather yes and Rather no are clues, not probabilities,
                  and they do not say how often something is true. The Guesser should keep other
                  possibilities open and check important assumptions with another question.</template>
              </p>
            </div>
            <MethodDetails title="Guess rules and the question limit" anchor="game-details">
              <p>
                Guesses get only Yes, No, or Unknown. Only Yes ends a round successfully.
              </p>
              <p v-if="qualified">
                A guess must name the subject exactly. If the subject is a general kind of
                thing, a recognized subtype also counts if it keeps the defining features and
                meets the subject’s stated limits. Extra detail does not make a correct guess
                wrong.
              </p>
              <p v-else>A guess must identify the exact subject; accepted alternative names count.</p>
              <p>
                The limit is higher than twenty so that a model that needs, say, 25 questions
                scores better than one that never finds the subject. Every extra question still
                raises the score. At the limit, the model can only guess. If that guess is
                wrong, the round scores {{ penalty }}, one more than any successful round.
              </p>
            </MethodDetails>
          </div>
        </div>
      </section>

      <section id="answer-checks" class="content-section answer-checks-section">
        <div class="content-inner editorial-copy">
          <div><p class="eyebrow">02 · Answer checks</p></div>
          <div>
            <h2>How answers are checked.</h2>
            <p class="lead">
              Other models know the hidden subject and answer the Guesser’s questions. Up to
              three of them handle each question, each with a separate job:
            </p>
            <ol class="answer-roles">
              <li><h3>Oracle: find an answer.</h3>
                <p>Searches for evidence and proposes an answer. Unknown is final; every other
                  answer needs a second check.</p></li>
              <li><h3>Reviewer: check independently.</h3>
                <p>Checks the question without seeing the Oracle’s answer. If they agree,
                  that answer is final.</p></li>
              <li><h3>Judge: resolve disagreement.</h3>
                <p>Decides whenever their answers differ, including Reviewer Unknown.
                  It sees neither earlier answer.</p></li>
            </ol>
            <p>
              The second check exists because a single answering model can make basic mistakes.
              In early runs, one Oracle said Yes to “born before 1800?” while citing 1875. The
              Reviewer and Judge use different model families and providers to reduce shared
              mistakes.
            </p>
            <p>
              Guesses go to a separate <strong>Guess Validator</strong>, which checks whether
              the guess names the subject. The Guesser receives only the final answer, with no
              explanation.
            </p>
            <aside class="isolation-callout">
              <h3>The Guesser cannot see the answer checks.</h3>
              <p>It sees the category, its own questions and guesses, and the final answers.
                The hidden subject, searches, evidence, and other models’ conversations stay private.</p>
            </aside>
            <p>
              A repeated question can reuse an earlier, fully checked answer. The transcript
              marks every reused answer.
            </p>
            <MethodDetails title="What the checking models can see" anchor="check-details">
              <p>
                <strong>Oracle:</strong> the subject and the current question, but no earlier
                turns. It searches the web and keeps the source text.
                <template v-if="qualified">Under current rules, it may also use its own
                  knowledge, with a short private justification.</template>
                <template v-else>It must search instead of relying on memory.</template>
              </p>
              <p>
                <strong>Reviewer and Judge:</strong> the subject, the question, and the Oracle’s
                numbered evidence. They cannot search the web or see earlier answers or the game
                history. <template v-if="qualified">Any difference, even Yes versus Rather yes,
                  goes to the Judge.</template>
              </p>
              <p v-if="qualified">
                In current runs, the Reviewer and Judge may also use their own knowledge, with a
                short private justification. An earlier accepted version limited the Reviewer
                to the supplied evidence and let the Judge use its own knowledge only in
                limited cases. Each run records its rules and prompt versions.
              </p>
              <p v-else>
                For narrow, settled facts, the Reviewer and Judge may use their own knowledge
                when the evidence is not enough.
              </p>
              <p>
                <strong>Guess Validator:</strong> only the subject and the guess, with no web
                access.
              </p>
              <p>
                If a required check fails, the round counts as a test system failure; the
                Oracle’s answer is never used on its own.
              </p>
              <p>
                The Guesser never sees sources, other models’ instructions, checking
                decisions, logs, or private files. Its own instructions and format reminder
                contain nothing about the subject.
              </p>
            </MethodDetails>
            <MethodDetails title="When an earlier answer is reused" anchor="answer-reuse">
              <p>
                Benchmark runs reuse answers by default. A question that matches an earlier
                one can reuse its fully checked answer, from an earlier compatible round or
                from the same game. The run’s recorded rules decide which answers qualify.
              </p>
              <p>
                A reused answer keeps its original evidence, time, and source label. No new
                search or check runs. The question still counts, but adds no answer-checking
                cost. The Guesser sees only the final answer. Compare runs only if they use the
                same reuse rules and answer history.
              </p>
            </MethodDetails>
          </div>
        </div>
      </section>

      <section id="scoring" class="content-section scoring-section">
        <div class="content-inner editorial-copy">
          <div><p class="eyebrow">03 · The score</p></div>
          <div>
            <h2>Fewer questions means a better score.</h2>
            <p class="lead">
              Each round gets a score. Average the rounds for each subject, then average the
              subjects. Every subject has equal weight. The result is the model’s question score.
            </p>
            <dl class="score-rules" aria-label="Round scoring">
              <div><dt>Each question</dt><dd>+1</dd></div>
              <div><dt>Each wrong guess</dt><dd>+1, play continues</dd></div>
              <div><dt>Each reply in the wrong format</dt><dd>+1, play continues; an invalid final guess ends the round instead</dd></div>
              <div><dt>Correct guess</dt><dd>Not counted; the round ends</dd></div>
              <div><dt>Subject not found</dt><dd>The round scores {{ penalty }}</dd></div>
              <div><dt>Test system failure</dt><dd>Not scored; the run stays incomplete until the round is rerun</dd></div>
            </dl>
            <p>
              For example, 12 questions, one wrong guess, and one reply in the wrong format
              before the correct guess score 14.
            </p>
            <p>
              Each score has a <strong>95% confidence interval</strong> (CI). It estimates how
              much the average could change if the same subjects were played again. A narrower
              interval means more consistent results, even if the score itself is poor. It does
              not describe performance on new subjects.
            </p>
            <p>
              The <RouterLink :to="editionRoute('results-reliability')">Stability view</RouterLink>
              ranks models by this interval’s width. Cost and time are reported separately
              and do not change the question score.
            </p>
            <p>{{ questionScoreRankingRule }} This tie-breaker is a ranking rule, not a test
              of whether one model is significantly better.</p>
            <MethodDetails title="Format errors and failed rounds" anchor="reliability">
              <p>
                Each Guesser reply must be one valid ASK or GUESS action. Before the question
                limit, an invalid reply uses one counted turn and gets a fixed FORMAT_ERROR
                reminder. The reminder says nothing about what went wrong, whether the model
                was right, or the subject. Too many invalid replies in a row end the round as a
                scored failure. An invalid final guess ends the round with no retry and no
                extra counted turn.
              </p>
              <p>
                A later correct guess does not erase earlier format errors. Result pages show
                the share of valid replies, the number of errors, and the affected rounds. The
                used turn is already in the question score; there is no second penalty.
              </p>
            </MethodDetails>
            <MethodDetails title="Scoring formulas and uncertainty" anchor="score-details">
              <p>Score policy: {{ manifest.score_policy.version }}.</p>
            <div class="formula" aria-label="Question score formula">
              <div>
                <span>Round score</span>
                <strong>questions used · failed round = {{ penalty }}</strong>
              </div>
              <div>
                <span>Subject average</span>
                <strong class="math-expression score-average-formula">
                  <math
                    display="block"
                    aria-label="One divided by R, times the sum of round scores from round one through round R"
                  >
                    <mrow>
                      <mfrac>
                        <mn>1</mn>
                        <mi>R</mi>
                      </mfrac>
                      <munderover>
                        <mo>∑</mo>
                        <mrow>
                          <mi>r</mi>
                          <mo>=</mo>
                          <mn>1</mn>
                        </mrow>
                        <mi>R</mi>
                      </munderover>
                      <msub>
                        <mtext>round score</mtext>
                        <mi>r</mi>
                      </msub>
                    </mrow>
                  </math>
                  <small class="math-key"><i>R</i> = number of rounds for the subject</small>
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
              <h3>How the interval is calculated</h3>
              <p>
                Estimate the variation between rounds separately for each subject, divide by
                that subject’s round count, then combine the estimates with equal subject
                weights. A Welch-Satterthwaite t interval allows different variation for each subject.
              </p>
            <div class="formula" aria-label="Question score confidence interval formula">
              <div class="standard-error-formula">
                <span>Standard error</span>
                <strong class="math-expression">
                  <math
                    display="block"
                    aria-label="Standard error equals one divided by the number of subjects, times the square root of the sum across subjects of each subject's sample variance of round scores divided by its round count"
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
                    <i>S</i> = subjects · <i>n<sub>s</sub></i> = rounds for subject <i>s</i> ·
                    <i>σ̂<sup>2</sup><sub>s</sub></i> = sample variance of round scores for subject <i>s</i>
                  </small>
                </strong>
              </div>
              <div>
                <span>95% interval</span>
                <strong>model score ± t critical value × standard error</strong>
              </div>
            </div>
              <p>
                The interval describes uncertainty in the average, not the range of single
                rounds. It also does not cover changes to models, providers, or editions.
                Comparing two models’ intervals is not a significance test.
              </p>
              <p>
                The interval assumes that rounds on the same subject are independent. Different
                seeds support this but do not prove it, and reused answers can link rounds. The
                interval does not adjust for this or estimate how new web research might change
                answers.
              </p>
            </MethodDetails>
          </div>
        </div>
      </section>

      <section id="repetition" class="content-section repetition-section">
        <div class="content-inner editorial-copy">
          <div><p class="eyebrow">04 · Comparisons</p></div>
          <div>
            <h2>Repeat the game on the same subjects.</h2>
            <p class="lead">
              In this edition, each model plays {{ manifest.active_cohort.target_ids.length }} subjects
              {{ manifest.active_cohort.iterations }} times each: {{ totalTrials }} rounds in total.
              Every round starts a fresh Guesser conversation. Repetition shows how much results vary.
            </p>
            <p>
              Only complete runs with accepted settings enter the leaderboard. If several runs
              qualify for a model, the newest one counts, never the best one.
            </p>
            <p v-if="qualified">
              Edition 1.1 accepts a few reviewed versions of the answer-checking prompts and
              subject descriptions, so runs may differ in more than the Guesser. These
              differences can affect scores. Each run shows its settings.
            </p>
            <aside class="scope-note">
              <h3>What a comparison can tell you</h3>
              <p>
                These results describe a small, fixed set of subjects. They do not rank general
                intelligence or predict performance on unseen subjects. Repetition does not make
                the subjects more representative. Public subjects and transcripts may also have
                appeared in a later model’s training data; we cannot rule out an advantage from this.
              </p>
            </aside>
            <MethodDetails title="Subjects, repeated rounds, and future editions" anchor="subject-design">
              <p>
                Each subject has a main name, accepted alternative names, a clear description,
                and a public reference. Every model in an edition plays the same list, shown with
                categories in each run. The selection is not random, balanced, or representative.
                Cost limits its size: each added subject needs repeated model turns and answer checks.
              </p>
              <p>
                A round cannot see another round’s transcript, evidence, or private data. Each
                round starts with a code made from the base seed and the round number. It is the
                same for every model and subject and reveals nothing about the subject. Base seed:
                {{ manifest.active_cohort.base_seed }}.
              </p>
              <p>
                Future editions should include more subjects and kinds, such as places and
                objects. Subjects and selection rules will be fixed before testing. Any change
                to subjects or game rules starts a new edition with separate results.
              </p>
            </MethodDetails>
            <MethodDetails title="Requirements for a published run" anchor="eligibility">
              <p v-if="qualified">
                Edition 1.1 fixes the subjects, rounds per subject, question limit, game rules,
                and scoring rules. A run must also match one accepted release in full: prompt
                versions, subjects, seed, game rules, answer-checking model settings, and saved
                check records. Other versions and incomplete test runs do not qualify. Published
                runs keep their experiment label if they have one.
              </p>
              <p v-else>
                Only the Guesser changes between runs. The subjects, game rules, Oracle,
                Reviewer, Judge, Guess Validator, round count, and scoring rules stay the same.
              </p>
              <ul>
                <li>Signed run files must pass integrity checks. Any invalid file stops the site
                  build.</li>
                <li>The run must be finished, with every round of every subject complete.</li>
                <li>Rounds the model failed count as scored. A run with missing rounds or test
                  system failures stays out until those rounds are rerun.</li>
                <li>For a rerun round, only the final attempt counts toward scores and cost
                  comparisons. Earlier attempts stay in the records and the total spend.</li>
              </ul>
            </MethodDetails>
          </div>
        </div>
      </section>

      <section id="publication" class="content-section publication-section">
        <div class="content-inner editorial-copy">
          <div><p class="eyebrow">05 · Explore results</p></div>
          <div>
            <h2>Follow a score back to the game.</h2>
            <p class="lead">
              Open a model’s run to see its subjects and rounds. Each round shows the questions,
              answers, guesses, and supporting evidence, along with format errors, usage, cost,
              and timing.
            </p>
            <p>
              Answers are checked by models, not independently verified. The transcripts let
              you check the evidence and spot mistakes.
            </p>
            <div class="button-row">
              <RouterLink class="button button-primary" :to="editionRoute('results')">
                Explore the results →
              </RouterLink>
              <RouterLink class="button button-secondary" :to="editionRoute('data')">
                Download the data
              </RouterLink>
            </div>
            <p class="build-story">
              For background on how it was built,
              <a
                href="https://medium.com/@patrick.heusser/i-built-an-llm-benchmark-around-twenty-questions-the-hard-part-wasnt-the-game-e743c0683da8"
                target="_blank" rel="noreferrer"
              >read the story on Medium ↗</a>.
            </p>
          </div>
        </div>
      </section>

      <EditionComparison />
    </template>
  </div>
</template>

<style scoped>
.page-hero {
  padding-block: clamp(2.5rem, 5vw, 4rem);
}

.page-hero h1 {
  max-width: 20ch;
  font-size: clamp(2.75rem, 5vw, 5rem);
}

.method-nav-shell {
  border-bottom: var(--rule-default);
  background: var(--paper-bright);
}

.method-nav {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  border-inline: var(--rule-default);
}

.method-nav a {
  padding: 1rem clamp(0.6rem, 1.2vw, 1rem);
  border-right: var(--rule-default);
  font-size: var(--text-ui);
  font-weight: var(--font-weight-bold);
  text-decoration: none;
}

.method-nav a:last-child {
  border-right: 0;
}

.editorial-copy h2 {
  max-width: 22ch;
}

.editorial-copy h3 {
  font-family: var(--font-display);
  font-size: var(--text-card-title);
  font-weight: var(--font-weight-medium);
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
  margin: 1.75rem 0;
  padding: var(--method-round-padding);
  background: var(--ink);
}

.answer-guide {
  margin-block: 1.75rem;
}

.answer-meanings > div,
.score-rules > div {
  display: grid;
  grid-template-columns: 7rem minmax(0, 1fr);
  gap: 1rem;
  padding-block: 0.75rem;
  border-bottom: var(--rule-default);
}

.answer-meanings dt,
.score-rules dt {
  font-weight: var(--font-weight-semibold);
}

.answer-meanings dd,
.score-rules dd {
  margin: 0;
  color: var(--text-secondary);
}

.score-rules {
  margin-block: 1.75rem;
}

.score-rules > div {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.answer-checks-section,
.repetition-section {
  background: var(--paper-bright);
}

.answer-roles {
  margin-block: 1.5rem;
  padding-left: 1.5rem;
}

.answer-roles li {
  padding: 0.75rem 0 0.75rem 0.5rem;
  border-bottom: var(--rule-default);
}

.answer-roles li::marker {
  color: var(--blue-ink);
  font-weight: var(--font-weight-semibold);
}

.answer-roles h3 {
  margin: 0 0 0.4rem;
  font-size: 1.25rem;
}

.answer-roles p {
  margin: 0;
}

.isolation-callout,
.scope-note {
  margin-block: 1.75rem;
  padding: 1.25rem;
  border-left: 3px solid var(--blue);
  background: var(--surface-rail);
}

.isolation-callout h3,
.scope-note h3 {
  margin: 0 0 0.75rem;
  font-size: 1.25rem;
}

.isolation-callout p,
.scope-note p {
  margin: 0;
}

.formula {
  margin: 1.5rem 0;
  border: var(--rule-default);
}

.formula > div {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: var(--rule-default);
}

.formula > div:last-child {
  border-bottom: 0;
  background: var(--surface-rail);
}

.formula span {
  color: var(--text-secondary);
  font-size: var(--text-small);
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

.math-expression .math-key {
  color: var(--text-secondary);
  font: var(--font-weight-medium) var(--text-caption)/1.5 var(--font-sans);
  text-wrap: balance;
}

.publication-section {
  background: var(--surface-rail);
}

.build-story {
  margin-top: 1.5rem;
  font-size: var(--text-small);
}

@media (max-width: 760px) {
  .method-nav-shell {
    padding-inline: 0;
  }

  .method-nav {
    grid-template-columns: 1fr 1fr;
    border-inline: 0;
  }

  .method-nav a {
    border-bottom: var(--rule-muted);
  }

  .method-nav a:nth-child(even) {
    border-right: 0;
  }

  .method-nav a:last-child {
    grid-column: 1 / -1;
    border-bottom: 0;
  }

  .formula > div {
    align-items: flex-start;
    flex-direction: column;
  }

  .formula strong {
    text-align: left;
  }

  .formula .math-expression {
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .answer-meanings > div {
    grid-template-columns: 6rem minmax(0, 1fr);
    gap: 0.75rem;
  }

  .score-rules > div {
    grid-template-columns: 1fr;
    gap: 0.35rem;
  }
}
</style>
