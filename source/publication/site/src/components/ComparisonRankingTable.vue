<script setup lang="ts">
import { computed } from "vue";

import SortButton from "@/components/SortButton.vue";
import type { SortDirection } from "@/lib/use-table-sort";

type ComparisonRankingTableVariant = "home" | "results-overview";

interface ComparisonColumn {
  key: string;
  labels: readonly string[];
  className: string;
  numeric: boolean;
  width: number;
}

const props = defineProps<{
  variant: ComparisonRankingTableVariant;
  label: string;
  /** When given, column headers become sort buttons; the parent sorts its rows. */
  sortDirection?: (key: string) => SortDirection | "none";
}>();
defineEmits<{ sort: [key: string] }>();

const compactWidth = 4;
const modelWidth = 24;
const metricWidth = (100 - compactWidth - modelWidth) / 5;

const sharedColumns = [
  {
    key: "rank",
    labels: ["Rank"],
    className: "rank-column",
    numeric: false,
    width: compactWidth,
  },
  {
    key: "model",
    labels: ["Model"],
    className: "model-column",
    numeric: false,
    width: modelWidth,
  },
  {
    key: "score",
    labels: ["Question score", "95% CI"],
    className: "primary-metric-column",
    numeric: true,
    width: metricWidth,
  },
] as const satisfies readonly ComparisonColumn[];

const variantColumns: Record<ComparisonRankingTableVariant, readonly ComparisonColumn[]> = {
  home: [
    {
      key: "reasoning",
      labels: ["Reasoning"],
      className: "reasoning-column",
      numeric: true,
      width: metricWidth,
    },
    {
      key: "success",
      labels: ["Solved"],
      className: "success-column",
      numeric: true,
      width: metricWidth,
    },
    {
      key: "contract",
      labels: ["Valid", "format"],
      className: "contract-column",
      numeric: true,
      width: metricWidth,
    },
    {
      key: "cost",
      labels: ["Benchmark", "run cost"],
      className: "cost-column",
      numeric: true,
      width: metricWidth,
    },
  ],
  "results-overview": [
    {
      key: "success",
      labels: ["Solved"],
      className: "success-column",
      numeric: true,
      width: metricWidth,
    },
    {
      key: "contract",
      labels: ["Valid", "format"],
      className: "contract-column",
      numeric: true,
      width: metricWidth,
    },
    {
      key: "cost",
      labels: ["Guesser cost", "per round"],
      className: "cost-column",
      numeric: true,
      width: metricWidth,
    },
    {
      key: "time",
      labels: ["Model time", "per round"],
      className: "time-column",
      numeric: true,
      width: metricWidth,
    },
  ],
};

const columns = computed<readonly ComparisonColumn[]>(() => [
  ...sharedColumns,
  ...variantColumns[props.variant],
]);
const tableClasses = computed(() => [
  "data-table",
  "ranking-table",
  "comparison-ranking-table",
  ...(props.variant === "home"
    ? ["ranking-table--home"]
    : ["results-table", "results-table--overview"]),
]);
</script>

<template>
  <div
    class="table-wrap ranking-table-wrap comparison-ranking-table-wrap"
    :aria-label="label"
  >
    <table :class="tableClasses">
      <caption class="visually-hidden">{{ label }}</caption>
      <colgroup>
        <col
          v-for="column in columns"
          :key="column.key"
          :class="column.className"
          :style="{ width: `${column.width}%` }"
        />
      </colgroup>
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="column.className"
            :data-numeric="column.numeric ? '' : undefined"
            :aria-sort="sortDirection && column.key !== 'rank' ? sortDirection(column.key) : undefined"
          >
            <template v-if="column.key === 'rank'">
              <span aria-hidden="true">#</span>
              <span class="visually-hidden">Rank</span>
            </template>
            <SortButton
              v-else-if="sortDirection"
              :labels="column.labels"
              :direction="sortDirection(column.key)"
              @sort="$emit('sort', column.key)"
            />
            <span v-else-if="column.labels.length > 1" class="table-header-stack">
              <span v-for="label in column.labels" :key="label">{{ label }}</span>
            </span>
            <template v-else>{{ column.labels[0] }}</template>
          </th>
        </tr>
      </thead>
      <slot />
    </table>
  </div>
</template>
