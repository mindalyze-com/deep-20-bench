<script setup lang="ts">
import { computed } from "vue";

import { contractViolationDetails as violationDetails } from "@/lib/contract-violation-copy";
import type { PublicEpisodeDetail } from "@/lib/types";

const props = defineProps<{
  episode: PublicEpisodeDetail;
}>();

const turnMap = computed(() =>
  props.episode.turns.map((turn) => {
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
</script>

<template>
<section
  id="transcript"
  class="content-section episode-panel episode-transcript"
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
          Valid recorded outputs are canonical structured actions. Rejected Guesser text
          is published separately without provider or call identifiers.
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
                <section class="rejected-output-comparison">
                  <header>
                    <strong>What the model returned</strong>
                    <small>Exact Guesser provider text</small>
                  </header>
                  <div v-if="turn.rejected_outputs.length" class="rejected-output-list">
                    <article
                      v-for="output in turn.rejected_outputs"
                      :key="output.attempt_number"
                    >
                      <span>
                        Attempt {{ output.attempt_number }} · finish
                        {{ output.finish_reason ?? "not reported" }}
                      </span>
                      <pre>{{ output.text }}</pre>
                    </article>
                  </div>
                  <p v-else class="missing-output">
                    The provider returned no textual completion for this call.
                  </p>
                </section>
                <section
                  v-if="episode.guesser_disclosure?.required_formats"
                  class="contract-examples"
                >
                  <header>
                    <strong>What a valid response looks like</strong>
                    <small>The same formats shown to the Guesser</small>
                  </header>
                  <div>
                    <article>
                      <span>ASK</span>
                      <pre>{{ episode.guesser_disclosure.required_formats.ask }}</pre>
                    </article>
                    <article>
                      <span>GUESS</span>
                      <pre>{{ episode.guesser_disclosure.required_formats.guess }}</pre>
                    </article>
                  </div>
                  <p class="detail-note">
                    The response must match one complete format. Active strings must be
                    non-empty. Inactive fields must be JSON <code>null</code>.
                  </p>
                </section>
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
</template>

<style scoped>
.setup-disclosure {
  margin-bottom: 2rem;
}

.setup-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: clamp(1.2rem, 3vw, 2rem);
  border-top: var(--rule-default);
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
  font-size: var(--text-caption);
  font-weight: 760;
  text-transform: uppercase;
}

pre {
  max-width: 100%;
  margin: 0;
  padding: 1rem;
  overflow: auto;
  border: var(--rule-inverse);
  background: var(--surface-code);
  color: var(--text-code);
  font: 0.72rem/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.detail-note {
  margin: 0;
  padding: 0.85rem 1rem;
  border-left: var(--border-emphasis-width) solid var(--blue);
  background: var(--surface-accent-soft);
  color: var(--ink-soft);
  font-size: 0.75rem;
  line-height: 1.55;
}

.turn-map {
  margin-bottom: 1.4rem;
  border: var(--rule-default);
  background: var(--surface-raised);
}

.turn-map > header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  padding: 1rem 1.1rem 0.9rem;
  border-bottom: var(--rule-subtle);
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
  font-size: var(--text-caption);
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
  border: var(--rule-default);
  background: var(--surface-raised);
  color: var(--ink);
  cursor: pointer;
}

.turn-map button:hover {
  border-color: var(--ink);
}

.turn-map button span {
  font-family: var(--font-mono);
  font-size: var(--text-caption);
}

.turn-map button strong {
  margin-top: 0.18rem;
  font-size: var(--text-caption);
}

.turn-map button.tone-yes {
  border-bottom: var(--border-emphasis-width) solid var(--state-clean);
}

.turn-map button.tone-no {
  border-bottom: var(--border-emphasis-width) solid var(--state-danger);
}

.turn-map button.tone-unknown {
  border-bottom: var(--border-emphasis-width) solid var(--state-warning);
}

.turn-map button.tone-format {
  border-bottom: var(--border-emphasis-width) solid var(--state-format);
}

.turn-map > footer {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 1rem;
  padding: 0.7rem 1rem;
  border-top: var(--rule-subtle);
  color: var(--muted);
  font-size: var(--text-caption);
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
  background: var(--state-clean);
}

.turn-map > footer .tone-no {
  background: var(--coral);
}

.turn-map > footer .tone-unknown {
  background: var(--state-warning);
}

.turn-map > footer .tone-format {
  background: var(--state-format);
}

.turn-list {
  border-top: var(--rule-default);
}

.turn {
  display: grid;
  grid-template-columns: 3.5rem minmax(0, 1fr) minmax(8rem, 0.25fr);
  gap: clamp(1rem, 3vw, 2.5rem);
  padding: clamp(1.4rem, 3vw, 2.5rem) 0;
  scroll-margin-top: 1rem;
  border-bottom: var(--rule-default);
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
  border: var(--rule-strong);
  background: var(--acid);
  font-size: var(--text-caption);
  font-weight: 820;
}

.turn.guess .turn-marker span {
  background: var(--ink);
  color: var(--acid);
}

.turn.violation .turn-marker span {
  background: color-mix(in srgb, var(--state-danger) 28%, var(--surface-raised));
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
  font-size: var(--text-caption);
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
  border-left: var(--border-emphasis-width) solid var(--blue);
  background: var(--surface-accent-soft);
  line-height: 1.55;
}

.validator-note strong {
  color: var(--blue-ink);
  font-size: var(--text-caption);
  text-transform: uppercase;
}

.turn-disclosure {
  margin-top: 1rem;
}

.turn-disclosure > pre,
.violation-body {
  border-top: var(--rule-default);
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
  font-size: var(--text-caption);
  font-weight: 760;
  text-transform: uppercase;
}

.evidence-list blockquote {
  margin: 0.8rem 0;
  color: var(--ink-soft);
  line-height: 1.65;
}

.evidence-list a {
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
  background: var(--surface-raised);
  text-align: center;
}

.answer span {
  color: var(--muted);
  font-size: var(--text-caption);
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
  background: var(--surface-success-soft);
}

.answer-no {
  background: var(--surface-danger-soft);
}

.answer-unknown {
  background: color-mix(in srgb, var(--state-warning) 14%, var(--surface-raised));
}

.answer-format {
  background: color-mix(in srgb, var(--state-danger) 28%, var(--surface-raised));
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
  border: var(--rule-default);
}

.violation-body dl div {
  min-width: 0;
  padding: 0.8rem;
  border-right: var(--rule-default);
  border-bottom: var(--rule-default);
}

.violation-body dd {
  margin: 0.35rem 0 0;
  overflow-wrap: anywhere;
}

.rejected-output-comparison,
.contract-examples {
  margin-top: 1rem;
  border: var(--rule-default);
  background: var(--paper-bright);
}

.rejected-output-comparison > header,
.contract-examples > header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 1rem;
  border-bottom: var(--rule-default);
}

.rejected-output-comparison > header strong,
.contract-examples > header strong {
  font-size: 0.72rem;
}

.rejected-output-comparison > header small,
.contract-examples > header small,
.rejected-output-list article > span,
.contract-examples article > span {
  color: var(--muted);
  font-size: var(--text-caption);
}

.rejected-output-list {
  display: grid;
  gap: 1px;
  background: var(--line);
}

.rejected-output-list article,
.contract-examples article {
  min-width: 0;
  padding: 0.9rem;
  background: var(--paper-bright);
}

.rejected-output-list article > span,
.contract-examples article > span {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 760;
  text-transform: uppercase;
}

.missing-output {
  margin: 0;
  padding: 1rem;
  color: var(--muted);
  line-height: 1.6;
}

.contract-examples > div {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: var(--line);
}

.contract-examples .detail-note {
  margin: 1rem;
}

@media (max-width: 780px) {
  .setup-body,
  .contract-examples > div {
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

}

@media (max-width: 560px) {
  .warning-facts,
  .violation-body dl,
  .contract-examples > div {
    grid-template-columns: 1fr;
  }

  .warning-facts div,
  .violation-body dl > div {
    grid-column: 1;
    border-right: 0;
    border-bottom: var(--rule-default);
  }

  .turn {
    gap: 0.8rem;
  }

}

.setup-disclosure {
  margin-bottom: 1.2rem;
}

.turn-list {
  border-top: var(--rule-strong);
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

@media (max-width: 760px) {
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
      font-size: var(--text-caption);
      font-weight: 800;
      letter-spacing: 0.025em;
    }

    .turn-marker {
      gap: 0;
    }

    .turn-marker span {
      width: 2.2rem;
      height: 2.2rem;
      font-size: var(--text-caption);
    }

    .turn-marker i {
      display: none;
    }

    .turn-label {
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: flex-start;
      gap: 0.3rem 0.6rem;
      font-size: var(--text-caption);
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
      font-size: var(--text-caption);
    }

    .turn-disclosure > summary small {
      font-size: var(--text-caption);
    }

    .turn-disclosure > summary > span:last-child {
      font-size: var(--text-caption);
    }

}
</style>
