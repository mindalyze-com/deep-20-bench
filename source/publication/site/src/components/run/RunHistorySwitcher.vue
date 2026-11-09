<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import type { RouteLocationRaw } from "vue-router";

import { editionsIndex, getLeaderboard, peekLeaderboard } from "@/lib/api";
import { dateTime, number } from "@/lib/format";
import { comparisonRoute, episodeRoute, runRoute, subjectRoute } from "@/lib/route-location";
import { runDate } from "@/lib/run-selection";
import type { PublicRunSummary } from "@/lib/types";
import { useKeyedPublicationLoad } from "@/lib/use-keyed-publication-load";

const props = withDefaults(defineProps<{
  run: PublicRunSummary;
  editionId: string;
  dark?: boolean;
  heading?: string;
}>(), { dark: false, heading: "Test runs" });
const emit = defineEmits<{ navigate: [] }>();

const route = useRoute();
const references = computed(() =>
  editionsIndex.value?.editions.find(item => item.edition_id === props.editionId)?.runs
    .filter(item => item.model_id === props.run.model_id && item.classification === "official") ?? [],
);
const { document } = useKeyedPublicationLoad({
  parameters: (): [string] => [references.value.length > 1 ? props.editionId : ""],
  load: getLeaderboard,
  initial: () => peekLeaderboard(props.editionId),
  fallbackError: "Run history could not be loaded.",
  clearBeforeLoad: true,
});

const runs = computed(() => {
  const results = document.value?.runs ?? document.value?.leaderboard ?? [];
  return references.value
    .map(item => ({
      executionId: item.execution_id,
      completedAt: item.completed_at ?? null,
      score: results.find(row => row.execution_id === item.execution_id)?.question_score ??
        (item.execution_id === props.run.execution_id ? props.run.question_score : null),
    }))
    .sort((left, right) => (right.completedAt ?? "").localeCompare(left.completedAt ?? "") ||
      right.executionId.localeCompare(left.executionId));
});

const compareTo = computed(() => {
  const other = runs.value.find(item => item.executionId !== props.run.execution_id);
  return comparisonRoute(other ? [props.run.execution_id, other.executionId] : [], props.editionId);
});

const dateLabel = (completedAt: string | null): string => {
  const label = runDate(completedAt);
  return completedAt && runs.value.filter(item => runDate(item.completedAt) === label).length > 1
    ? dateTime(completedAt) : label;
};

const runTo = (executionId: string): RouteLocationRaw => {
  const targetId = route.params.targetId;
  const trialId = route.params.trialId;
  if (route.name === "episode" && typeof targetId === "string" && typeof trialId === "string") {
    return episodeRoute(executionId, targetId, trialId, route.query);
  }
  if (route.name === "subject" && typeof targetId === "string") {
    return subjectRoute(executionId, targetId, route.query);
  }
  return runRoute(executionId, route.query);
};
</script>

<template>
  <section v-if="runs.length > 1" class="run-history-switcher" :class="{ dark }" aria-label="Dated test runs">
    <div class="history-heading">
      <span>{{ heading }}</span>
      <RouterLink class="history-compare" :to="compareTo" @click="emit('navigate')">Compare runs <span aria-hidden="true">↗</span></RouterLink>
    </div>
    <nav class="history-dates" :aria-label="`Test runs for ${run.model_name}`">
      <RouterLink
        v-for="(item, index) in runs"
        :key="item.executionId"
        class="history-date"
        :to="runTo(item.executionId)"
        :aria-current="item.executionId === run.execution_id ? 'page' : undefined"
        :aria-label="`${dateLabel(item.completedAt)}, ${index === 0 ? 'latest' : 'earlier'} run, question score ${number(item.score)}`"
        @click="emit('navigate')"
      >
        <span class="history-status">{{ index === 0 ? "Latest" : "Earlier" }}<span class="history-check" aria-hidden="true">{{ item.executionId === run.execution_id ? "✓" : "" }}</span></span>
        <time :datetime="item.completedAt ?? undefined">{{ dateLabel(item.completedAt) }}</time>
        <span class="history-score"><strong>{{ number(item.score) }}</strong> questions</span>
      </RouterLink>
    </nav>
  </section>
</template>

<style scoped>
.run-history-switcher {
  --history-text: var(--text-primary);
  --history-muted: var(--text-secondary);
  --history-border: var(--border-default);
  --history-accent: var(--blue-ink);
  --history-active: var(--surface-accent-soft);
  --history-hover: var(--surface-rail);
  margin-top: 0.55rem;
  color: var(--history-text);
}

.run-history-switcher.dark {
  --history-text: var(--text-inverse);
  --history-muted: var(--text-inverse-muted);
  --history-border: var(--border-inverse);
  --history-accent: var(--acid);
  --history-active: rgb(214 255 38 / 7%);
  --history-hover: rgb(255 255 255 / 8%);
}

.history-heading {
  display: flex;
  flex-wrap: wrap;
  gap: 0 0.6rem;
  align-items: center;
  justify-content: space-between;
  color: var(--history-muted);
  font-size: var(--text-caption);
}

.history-compare {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  gap: 0.3rem;
  color: var(--history-muted);
  text-decoration: none;
}

.history-compare:hover { color: var(--history-text); }

.history-dates {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.4rem;
  max-height: 15rem;
  overflow-y: auto;
  padding: 3px;
  margin: -3px;
  white-space: normal;
}

.history-date {
  display: grid;
  align-content: start;
  gap: 0.35rem;
  padding: 0.6rem 0.55rem;
  border: 1px solid var(--history-border);
  border-radius: 5px;
  color: var(--history-text);
  text-decoration: none;
}

.history-date:hover { background: var(--history-hover); }

.history-date[aria-current="page"] {
  border-color: var(--history-accent);
  background: var(--history-active);
}

.history-date:focus-visible,
.history-compare:focus-visible {
  outline: 2px solid var(--history-accent);
  outline-offset: 2px;
}

.history-status {
  display: flex;
  justify-content: space-between;
  gap: 0.3rem;
  color: var(--history-muted);
  font-size: 0.65rem;
  line-height: 1.2;
}

.history-check { color: var(--history-accent); }

.history-date time {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  line-height: 1.4;
}

.history-score {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.15rem 0.25rem;
  color: var(--history-muted);
  font-size: 0.65rem;
  line-height: 1.3;
}

.history-score strong {
  color: var(--history-text);
  font-size: 0.85rem;
  font-weight: var(--font-weight-bold);
  font-variant-numeric: tabular-nums;
}
</style>
