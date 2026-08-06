<script setup lang="ts">
import { illustrativeRound } from "@/lib/illustrative-round";

const questionCount = illustrativeRound.turns.filter((turn) => turn.kind === "question").length;
</script>

<template>
  <aside
    class="round-example"
    :aria-label="
      `Illustrative round: ${illustrativeRound.subject} identified with a trial score of ${questionCount}`
    "
  >
    <div class="round-card">
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
        <li
          v-for="(turn, index) in illustrativeRound.turns"
          :key="turn.prompt"
          :class="{ 'round-guess': turn.kind === 'guess' }"
        >
          <span :class="{ 'round-guess-label': turn.kind === 'guess' }">
            {{ turn.kind === "guess" ? "Guess" : String(index + 1).padStart(2, "0") }}
          </span>
          <p>
            <span :class="{ 'round-guess-name': turn.kind === 'guess' }">
              {{ turn.prompt }}
            </span>
            <span v-if="turn.kind === 'guess'" class="round-not-counted">Not counted</span>
          </p>
          <strong>
            {{ turn.kind === "guess" ? `${turn.prompt} - ${turn.answer}` : turn.answer }}
          </strong>
        </li>
      </ol>
    </div>
    <div class="round-score-connector" aria-hidden="true">
      <span></span>
    </div>
    <div class="round-score-card">
      <span class="round-score-label">Question score (single round)</span>
      <div class="round-score-content">
        <strong class="round-score-number">{{ questionCount }}</strong>
        <div class="round-score-copy">
          <p class="round-score-summary">
            <strong>{{ questionCount }} questions counted.</strong>
            <span>The correct guess is excluded.</span>
          </p>
          <p class="round-score-direction">
            <strong>Lower is better</strong>
            <span>Fewer questions → better score</span>
          </p>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.round-example {
  position: relative;
  width: min(100%, var(--round-example-max));
  color: white;
  font-family: var(--font-sans);
  line-height: 1.5;
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
  font-weight: var(--font-weight-semibold);
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
  color: inherit;
  line-height: 1.5;
}

.round-card li p {
  margin: 0;
  color: inherit;
  font-size: var(--text-small);
  line-height: 1.5;
}

.round-card li strong {
  color: var(--acid);
  font-size: var(--text-micro);
  letter-spacing: 0.02em;
  line-height: 1.5;
  text-align: right;
  text-transform: uppercase;
}

.round-card li:last-child {
  border-bottom: 0;
}

.round-card li.round-guess {
  grid-template-columns: 3rem minmax(0, 1fr) auto;
  gap: 0.5rem;
  min-height: 4.5rem;
  border-top: 1px dashed rgb(255 255 255 / 18%);
  background: transparent;
}

.round-card li:nth-last-child(2) {
  border-bottom: 0;
}

.round-guess-label {
  color: rgb(255 255 255 / 55%);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.round-guess p {
  display: flex;
  gap: 0.65rem;
  align-items: center;
  min-width: 0;
}

.round-guess-name {
  border-bottom: 1px dotted rgb(255 255 255 / 62%);
  line-height: 1.25;
}

.round-not-counted {
  flex: 0 0 auto;
  padding: 0.2rem 0.42rem;
  border: var(--rule-inverse);
  border-radius: 2px;
  color: rgb(255 255 255 / 52%);
  font-size: 0.625rem;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.04em;
  line-height: 1.2;
  text-transform: uppercase;
}

.round-card li.round-guess > strong {
  max-width: 7rem;
  line-height: 1.3;
}

.round-score-connector {
  --connector-source: 6.75rem;
  --connector-target: 3.1rem;

  position: relative;
  height: 1.75rem;
  color: var(--acid);
}

.round-score-connector::before {
  position: absolute;
  top: 0;
  left: var(--connector-target);
  width: calc(var(--connector-source) - var(--connector-target));
  height: 0.85rem;
  border-right: 1px solid rgb(214 255 38 / 90%);
  border-bottom: 1px solid rgb(214 255 38 / 90%);
  content: "";
}

.round-score-connector > span {
  position: absolute;
  top: 0.85rem;
  left: var(--connector-target);
  width: 1px;
  height: calc(100% - 0.85rem);
  background: rgb(214 255 38 / 90%);
  transform: translateX(-0.5px);
}

.round-score-connector > span::before,
.round-score-connector > span::after {
  position: absolute;
  bottom: 0;
  width: 0.44rem;
  height: 1px;
  background: rgb(214 255 38 / 90%);
  content: "";
}

.round-score-connector > span::before {
  right: 50%;
  transform: rotate(45deg);
  transform-origin: right center;
}

.round-score-connector > span::after {
  left: 50%;
  transform: rotate(-45deg);
  transform-origin: left center;
}

.round-score-card {
  display: grid;
  grid-template-rows: auto auto;
  row-gap: 1rem;
  align-items: start;
  min-height: 8.9rem;
  padding: 1rem;
  border: 1px solid rgb(214 255 38 / 68%);
  background: rgb(255 255 255 / 2%);
  color: white;
}

.round-score-label {
  color: var(--acid);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.07em;
  line-height: 1.2;
  text-transform: uppercase;
}

.round-score-content {
  display: grid;
  grid-template-columns: 6.75rem minmax(0, 1fr);
  column-gap: 1rem;
  align-items: start;
}

.round-score-number {
  position: relative;
  top: 0.22rem;
  display: block;
  align-self: start;
  justify-self: center;
  color: var(--acid);
  font-family: var(--font-display);
  font-size: 5rem;
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.07em;
  line-height: 1;
}

.round-score-copy,
.round-score-direction {
  display: grid;
}

.round-score-copy {
  gap: 0.45rem;
}

.round-score-copy p {
  margin: 0;
  color: inherit;
}

.round-score-summary {
  display: grid;
  gap: 0.08rem;
  font-size: var(--text-small);
  line-height: 1.35;
}

.round-score-summary > strong {
  font-weight: var(--font-weight-semibold);
}

.round-score-summary > span,
.round-score-direction > span {
  color: rgb(255 255 255 / 56%);
  line-height: 1.4;
}

.round-score-summary > span {
  font-size: var(--text-small);
}

.round-score-direction > span {
  font-size: var(--text-micro);
}

.round-score-direction {
  gap: 0.05rem;
  margin-top: 0.1rem;
}

.round-score-direction > strong {
  color: var(--acid);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.05em;
  line-height: 1.3;
  text-transform: uppercase;
}

@media (max-width: 620px) {
  .round-card li strong {
    max-width: 8rem;
  }

  .round-score-card {
    min-height: 9.1rem;
    padding: 0.95rem;
  }

  .round-score-content {
    grid-template-columns: 6.75rem minmax(0, 1fr);
    column-gap: 0.7rem;
  }

  .round-score-number {
    font-size: 4.65rem;
  }
}
</style>
