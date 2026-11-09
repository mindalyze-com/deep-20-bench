<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import InfoPopover from "@/components/InfoPopover.vue";
import RunHistorySwitcher from "@/components/run/RunHistorySwitcher.vue";
import { editionsIndex } from "@/lib/api";
import { dateTime, number } from "@/lib/format";
import { runDate } from "@/lib/run-selection";
import type { PublicRunSummary } from "@/lib/types";

const props = defineProps<{ run: PublicRunSummary; editionId: string }>();
const route = useRoute();
const panel = ref<InstanceType<typeof InfoPopover> | null>(null);
const dates = computed(() => editionsIndex.value?.editions
  .find(edition => edition.edition_id === props.editionId)?.runs
  .filter(run => run.model_id === props.run.model_id && run.classification === "official") ?? []);
const date = computed(() => dates.value.filter(run => runDate(run.completed_at) === runDate(props.run.completed_at)).length > 1
  ? dateTime(props.run.completed_at) : runDate(props.run.completed_at));
const close = (): void => panel.value?.close();
watch(() => route.fullPath, close);
</script>

<template>
  <InfoPopover
    v-if="dates.length > 1"
    ref="panel"
    class="run-history-picker"
    label="Test runs"
    close-label="Close test runs"
    :show-indicator="false"
  >
    <template #trigger>
      <span class="picker-label">Test run</span>
      <time :datetime="run.completed_at">{{ date }}</time>
      <span class="picker-score">{{ number(run.question_score) }}<span class="visually-hidden"> questions</span></span>
      <svg class="picker-chevron" width="12" height="8" viewBox="0 0 12 8" aria-hidden="true"><path d="m1 1 5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>
    </template>
    <p class="picker-model">{{ run.model_name }}</p>
    <RunHistorySwitcher :run="run" :edition-id="editionId" heading="Choose a date" @navigate="close" />
  </InfoPopover>
</template>

<style scoped>
.run-history-picker { flex: 0 0 auto; }

.run-history-picker :deep(.info-popover-trigger) {
  min-height: 44px;
  gap: 0.6rem;
  padding: 0.45rem 0.65rem;
  border: var(--rule-default);
  border-radius: 6px;
  background: var(--paper-bright);
  color: var(--ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
}

.run-history-picker :deep(.info-popover-trigger:hover),
.run-history-picker :deep(.info-popover-trigger[aria-expanded="true"]) {
  border-color: var(--blue-ink);
  background: var(--surface-accent-soft);
  text-decoration: none;
}

.picker-label { color: var(--text-secondary); font-weight: 400; }
.picker-score { padding-left: 0.6rem; border-left: var(--rule-default); color: var(--blue-ink); font-variant-numeric: tabular-nums; }
.picker-chevron { flex-shrink: 0; transition: transform 140ms ease; }
.run-history-picker :deep(.info-popover-trigger[aria-expanded="true"]) .picker-chevron { transform: rotate(180deg); }
.picker-model { color: var(--ink); font-size: var(--text-small); font-weight: var(--font-weight-semibold); }
.run-history-picker :deep(.run-history-switcher) { margin-top: 0; }
.run-history-picker :deep(.history-date) { padding: 0.75rem; }
.run-history-picker :deep(.history-date time) { font-size: var(--text-small); }
.run-history-picker :deep(.history-score strong) { font-size: 1.1rem; }

@media (prefers-reduced-motion: reduce) {
  .picker-chevron { transition: none; }
}

@media (max-width: 760px) {
  .run-history-picker { display: none; }
}
</style>
