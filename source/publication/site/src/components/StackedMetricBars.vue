<script setup lang="ts">
import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  EChartsOption,
} from "echarts";
import { computed, watch } from "vue";
import { useRouter } from "vue-router";

import ChartLoadNotice from "@/components/ChartLoadNotice.vue";
import { chartTooltipStyle, readChartTheme } from "@/lib/chart-theme";
import {
  chartTooltipPrimary,
  chartTooltipRunLink,
  chartTooltipTitle,
} from "@/lib/chart-tooltip";
import { money } from "@/lib/format";
import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  chartFontWeightSemibold,
  chartTextSize,
  escapeHtml,
  useResponsiveEChart,
} from "@/lib/use-responsive-echart";

export interface StackedBarSegment {
  label: string;
  color: string;
}

export interface StackedBarBreakdown {
  label: string;
  display: string;
}

export interface StackedBarRow {
  label: string;
  display: string;
  values: number[];
  details: string[];
  breakdown?: StackedBarBreakdown[];
  link?: string;
}

const props = defineProps<{
  rows: StackedBarRow[];
  segments: StackedBarSegment[];
  directionLabel: string;
}>();

const router = useRouter();
const chartHeight = computed(() => Math.max(380, props.rows.length * 48 + 84));
const breakdownLabels = computed(() =>
  props.rows.find((row) => (row.breakdown?.length ?? 0) > 0)?.breakdown?.map(
    (entry) => entry.label,
  ) ?? [],
);

const breakdownDisplay = (row: StackedBarRow, label: string): string =>
  row.breakdown?.find((entry) => entry.label === label)?.display ?? "-";

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const row =
    parameter === undefined ? undefined : props.rows[parameter.dataIndex];
  if (row === undefined) return "";
  const theme = readChartTheme();
  const detail = props.segments
    .map((segment, index) => {
      const display = row.details[index] ?? money(row.values[index] ?? 0);
      return `<span style="display:grid;grid-template-columns:8px 1fr auto;gap:7px;align-items:center;margin-top:5px;color:${theme.muted};font-size:.75rem"><i style="width:8px;height:8px;border-radius:50%;background:${segment.color}"></i><span>${escapeHtml(segment.label)}</span><strong style="color:${theme.inkSoft}">${escapeHtml(display)}</strong></span>`;
    })
    .join("");
  const breakdown =
    row.breakdown === undefined || row.breakdown.length === 0
      ? ""
      : [
          `<span style="display:block;margin-top:9px;padding-top:7px;border-top:1px solid ${theme.border};color:${theme.inkSoft};font-size:.72rem;font-weight: var(--font-weight-bold);text-transform:uppercase">Adjudication breakdown</span>`,
          ...row.breakdown.map(
            (entry) =>
              `<span style="display:grid;grid-template-columns:1fr auto;gap:7px;margin-top:4px;color:${theme.muted};font-size:.75rem"><span>${escapeHtml(entry.label)}</span><strong style="color:${theme.inkSoft}">${escapeHtml(entry.display)}</strong></span>`,
          ),
        ].join("");
  return [
    '<div style="min-width:205px;max-width:280px;padding:3px 2px">',
    chartTooltipTitle(theme, row.label),
    chartTooltipPrimary(theme, row.display, "1.45rem", 7),
    detail,
    breakdown,
    chartTooltipRunLink(theme, row.link !== undefined),
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const theme = readChartTheme();
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const valueFontSize = chartTextSize(width, 11, 14);
  const totals = props.rows.map((row) =>
    row.values.reduce((sum, value) => sum + value, 0),
  );
  const maximum = Math.max(
    1,
    ...totals.filter((value) => Number.isFinite(value) && value >= 0),
  );
  const lastSeries = props.segments.length - 1;
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    aria: {
      enabled: true,
      description: `${props.directionLabel}. The value axis starts at zero. ${props.rows
        .map((row) => `${row.label}, ${row.display}`)
        .join(". ")}.`,
    },
    grid: {
      top: 18,
      right: mobile ? 54 : 82,
      bottom: 42,
      left: mobile ? 128 : 205,
    },
    tooltip: {
      ...chartTooltipStyle(theme, 10),
      trigger: "axis",
      axisPointer: { type: "shadow" },
      confine: true,
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      min: 0,
      splitNumber: mobile ? 3 : 5,
      axisLine: { show: true, lineStyle: { color: theme.border } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        formatter: money,
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine },
      },
    },
    yAxis: {
      type: "category",
      inverse: true,
      triggerEvent: true,
      data: props.rows.map((row) => row.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        interval: 0,
        color: theme.inkSoft,
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        fontWeight: chartFontWeightSemibold,
        width: mobile ? 108 : 180,
        overflow: "truncate",
        ellipsis: "…",
        margin: mobile ? 12 : 18,
      },
    },
    series: [
      ...props.segments.map((segment, segmentIndex) => ({
        name: segment.label,
        type: "bar" as const,
        stack: "full-cost",
        barWidth: mobile ? 15 : 18,
        cursor: props.rows.some((row) => row.link !== undefined)
          ? "pointer"
          : "default",
        itemStyle: {
          color: segment.color,
          borderRadius:
            segmentIndex === 0
              ? [3, 0, 0, 3]
              : segmentIndex === lastSeries
                ? [0, 3, 3, 0]
                : 0,
        },
        data: props.rows.map((row) => row.values[segmentIndex] ?? 0),
        label:
          segmentIndex === lastSeries
            ? {
                show: true,
                position: "right" as const,
                distance: mobile ? 6 : 10,
                color: theme.ink,
                fontFamily: chartDisplayFont,
                fontSize: valueFontSize,
                fontWeight: chartFontWeightSemibold,
                formatter: (parameters: CallbackDataParams): string =>
                  props.rows[parameters.dataIndex]?.display ?? "",
              }
            : { show: false },
        emphasis: {
          focus: "series" as const,
        },
      })),
      {
        name: "View full run",
        type: "bar",
        barGap: "-100%",
        barWidth: mobile ? 38 : 42,
        cursor: props.rows.some((row) => row.link !== undefined)
          ? "pointer"
          : "default",
        data: props.rows.map(() => maximum),
        itemStyle: {
          color: "rgb(12 17 27 / 0.1%)",
        },
        emphasis: {
          itemStyle: {
            color: "rgba(78,100,255,0.06)",
          },
        },
        label: { show: false },
        z: 10,
      },
    ],
  };
};

const handleClick = (parameters: CallbackDataParams): void => {
  const row =
    parameters.componentType === "yAxis"
      ? props.rows.find((candidate) => candidate.label === String(parameters.value))
      : props.rows[parameters.dataIndex];
  if (row?.link !== undefined) void router.push(row.link);
};

const { chartElement, loadError, refresh } = useResponsiveEChart({
  height: chartHeight,
  option: chartOption,
  onClick: handleClick,
  pointerCursor: (parameters) =>
    parameters.componentType === "yAxis" &&
    props.rows.some(
      (row) =>
        row.label === String(parameters.value) && row.link !== undefined,
    ),
});

watch(
  () =>
    [
      chartElement.value,
      props.rows,
      props.segments,
      props.directionLabel,
    ] as const,
  refresh,
  { deep: true },
);
</script>

<template>
  <figure class="stacked-chart">
    <figcaption>
      <span>{{ directionLabel }}</span>
      <ul aria-label="Cost components">
        <li v-for="segment in segments" :key="segment.label">
          <i :style="{ background: segment.color }" aria-hidden="true"></i>
          {{ segment.label }}
        </li>
      </ul>
    </figcaption>
    <ChartLoadNotice v-if="loadError" />
    <p class="chart-run-cue">Select a model row to view its full run.</p>
    <details v-if="breakdownLabels.length > 0" class="stacked-chart-breakdown">
      <summary>Exact adjudication breakdown</summary>
      <div
        class="stacked-chart-breakdown-table-wrap"
        tabindex="0"
        aria-label="Scrollable exact adjudication cost breakdown"
      >
        <table>
          <caption class="visually-hidden">
            Exact adjudication costs by model
          </caption>
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th
                v-for="label in breakdownLabels"
                :key="label"
                scope="col"
                data-numeric
              >
                {{ label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="`breakdown-${row.label}`">
              <th scope="row">{{ row.label }}</th>
              <td v-for="label in breakdownLabels" :key="label" data-numeric>
                {{ breakdownDisplay(row, label) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>
    <div
      ref="chartElement"
      class="stacked-chart-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ol class="visually-hidden" aria-label="Stacked cost chart data">
      <li v-for="row in rows" :key="row.label">
        {{ row.label }}: {{ row.display }}.
        <span v-for="(detail, index) in row.details" :key="index">
          {{ segments[index]?.label }} {{ detail }}.
        </span>
        <span v-for="entry in row.breakdown ?? []" :key="entry.label">
          {{ entry.label }} {{ entry.display }}.
        </span>
        <RouterLink v-if="row.link" :to="row.link" tabindex="-1">
          View full run for {{ row.label }}
        </RouterLink>
      </li>
    </ol>
  </figure>
</template>

<style scoped>
.stacked-chart {
  margin: 0;
  padding: clamp(1.2rem, 3vw, 2.5rem);
  background: var(--paper-bright);
}

figcaption {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.3rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

figcaption ul {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem 0.9rem;
  margin: 0;
  padding: 0;
  list-style: none;
  letter-spacing: 0;
  text-transform: none;
}

figcaption li {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: var(--text-micro);
  font-weight: var(--font-weight-semibold);
}

figcaption i {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
}

.chart-run-cue {
  margin: 0.4rem 0 0;
  color: var(--muted);
  font-size: var(--text-micro);
  line-height: 1.4;
  text-align: right;
}

.stacked-chart-breakdown {
  margin: 0.75rem 0 0.25rem;
  border-top: var(--rule-subtle);
  border-bottom: var(--rule-subtle);
}

.stacked-chart-breakdown summary {
  min-height: var(--control-min-size);
  padding: 0.75rem 0;
  color: var(--text-primary);
  font-size: var(--text-small);
  font-weight: var(--font-weight-bold);
  cursor: pointer;
}

.stacked-chart-breakdown-table-wrap {
  padding-bottom: 0.75rem;
  overflow-x: auto;
}

.stacked-chart-breakdown table {
  width: 100%;
  min-width: 36rem;
  border-collapse: collapse;
  font-size: var(--text-small);
}

.stacked-chart-breakdown th,
.stacked-chart-breakdown td {
  padding: 0.45rem 0.6rem;
  border-top: var(--rule-subtle);
  text-align: left;
}

.stacked-chart-breakdown [data-numeric] {
  text-align: right;
  white-space: nowrap;
}

.stacked-chart-breakdown tbody th {
  font-weight: var(--font-weight-semibold);
}

.stacked-chart-canvas {
  width: 100%;
  min-width: 0;
}

@media (max-width: 620px) {
  .stacked-chart {
    padding: 1rem 0.75rem 1.1rem;
  }

  figcaption {
    display: grid;
    padding-inline: 0.25rem;
  }

  figcaption ul {
    justify-content: flex-start;
  }
}
</style>
