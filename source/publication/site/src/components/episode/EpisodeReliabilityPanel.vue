<script setup lang="ts">
import { computed } from "vue";

import ContractMetrics from "@/components/ContractMetrics.vue";
import { contractViolationDetails } from "@/lib/contract-violation-copy";
import type {
  PublicContractViolationTurn,
  PublicEpisodeDetail,
} from "@/lib/types";

const props = defineProps<{
  episode: PublicEpisodeDetail;
}>();

const violationTurns = computed(() =>
  props.episode.turns.filter(
    (turn): turn is PublicContractViolationTurn =>
      turn.turn_type === "contract_violation",
  ),
);
</script>

<template>
  <section
    id="reliability"
    class="content-section episode-panel reliability"
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
      <ContractMetrics class="reliability-grid" :contract="episode.contract" />
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
            <strong>{{ contractViolationDetails[turn.violation_kind].label }}</strong>
            <p>{{ contractViolationDetails[turn.violation_kind].description }}</p>
            <small>
              {{ turn.counted ? `Counted as Q${turn.counted_questions}` : "No turn charge" }}
              · {{ turn.feedback_event ?? "No retry" }}
            </small>
          </li>
        </ol>
      </section>
    </div>
  </section>
</template>

<style scoped>
.reliability {
  border-top: var(--border-emphasis-width) solid var(--state-danger);
  background: var(--surface-danger-soft);
}

.reliability-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0 0 1.5rem;
  border: var(--rule-strong);
}

.reliability-grid :deep(div) {
  padding: 1rem;
  border-right: var(--rule-strong);
  border-bottom: var(--rule-strong);
}

.reliability-grid :deep(div:nth-child(3n)) {
  border-right: 0;
}

.reliability-grid :deep(div:nth-last-child(-n + 3)) {
  border-bottom: 0;
}

.reliability-grid :deep(dt) {
  color: var(--text-secondary);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.reliability-grid :deep(dd) {
  margin: 0.4rem 0 0;
  font-family: var(--font-display);
  font-size: 1.8rem;
}

.violation-summary {
  border: var(--rule-default);
  border-top: var(--border-emphasis-width) solid var(--state-danger);
  background: var(--surface-raised);
}

.violation-summary > header {
  padding: 1.25rem;
  border-bottom: var(--rule-default);
}

.violation-summary h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 3vw, 3rem);
  font-weight: var(--font-weight-medium);
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
  border-bottom: var(--rule-subtle);
}

.violation-summary li:last-child {
  border-bottom: 0;
}

.violation-summary li > span,
.violation-summary li > small {
  color: var(--text-secondary);
  font-size: var(--text-caption);
}

.violation-summary li > strong {
  font-size: var(--text-micro);
}

.violation-summary li > p {
  margin: 0;
  font-size: var(--text-caption);
  line-height: 1.5;
}

@media (max-width: 780px) {
  .reliability-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .reliability-grid :deep(div:nth-child(3n)) {
    border-right: var(--rule-strong);
  }

  .reliability-grid :deep(div:nth-child(even)) {
    border-right: 0;
  }

  .reliability-grid :deep(div:nth-last-child(-n + 3)) {
    border-bottom: var(--rule-strong);
  }

  .reliability-grid :deep(div:nth-last-child(-n + 2)) {
    border-bottom: 0;
  }
}

@media (max-width: 560px) {
  .reliability-grid {
    grid-template-columns: 1fr;
  }

  .reliability-grid :deep(div),
  .reliability-grid :deep(div:nth-child(3n)),
  .reliability-grid :deep(div:nth-child(even)),
  .reliability-grid :deep(div:nth-last-child(-n + 2)) {
    border-right: 0;
    border-bottom: var(--rule-strong);
  }

  .reliability-grid :deep(div:last-child) {
    border-bottom: 0;
  }

  .violation-summary li {
    grid-template-columns: 1fr;
    gap: 0.4rem;
  }
}
</style>
