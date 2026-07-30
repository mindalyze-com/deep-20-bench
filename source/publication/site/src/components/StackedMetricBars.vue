<script setup lang="ts">
import { BarChart } from "echarts/charts";
import {
  AriaComponent,
  GridComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  EChartsOption,
} from "echarts";
import { SVGRenderer } from "echarts/renderers";
import { computed, watch } from "vue";
import { useRouter } from "vue-router";

import { money } from "@/lib/format";
import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  chartTextSize,
  escapeHtml,
  useResponsiveEChart,
} from "@/lib/use-responsive-echart";

echarts.use([
  BarChart,
  GridComponent,
  TooltipComponent,
  AriaComponent,
  SVGRenderer,
]);

export interface StackedBarSegment {
  label: string;
  color: string;
}

export interface StackedBarRow {
  label: string;
  display: string;
  values: number[];
  details: string[];
  link?: string;
}

const props = defineProps<{
  rows: StackedBarRow[];
  segments: StackedBarSegment[];
  directionLabel: string;
}>();

const router = useRouter();
const chartHeight = computed(() => Math.max(380, props.rows.length * 48 + 84));

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const row =
    parameter === undefined ? undefined : props.rows[parameter.dataIndex];
  if (row === undefined) return "";
  const detail = props.segments
    .map((segment, index) => {
      const display = row.details[index] ?? money(row.values[index] ?? 0);
      return `<span style="display:grid;grid-template-columns:8px 1fr auto;gap:7px;align-items:center;margin-top:5px;color:#5f626a;font-size:.72rem"><i style="width:8px;height:8px;border-radius:50%;background:${segment.color}"></i><span>${escapeHtml(segment.label)}</span><strong style="color:#252833">${escapeHtml(display)}</strong></span>`;
    })
    .join("");
  return [
    '<div style="min-width:205px;max-width:280px;padding:3px 2px">',
    `<strong style="display:block;color:#11131c;font:700 .82rem/1.35 ${chartFont}">${escapeHtml(row.label)}</strong>`,
    `<span style="display:block;margin-top:7px;color:#11131c;font-family:${chartDisplayFont};font-size:1.45rem">${escapeHtml(row.display)}</span>`,
    detail,
    row.link === undefined
      ? ""
      : '<span style="display:block;margin-top:9px;color:#2539bd;font-size:.72rem;font-weight:700;text-transform:uppercase">Open model details →</span>',
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const valueFontSize = chartTextSize(width, 11, 14);
  const maximum = Math.max(
    ...props.rows.map((row) =>
      row.values.reduce((sum, value) => sum + value, 0),
    ),
    1,
  );
  const lastSeries = props.segments.length - 1;
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    aria: {
      enabled: true,
      description: `${props.directionLabel}. ${props.rows
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
      trigger: "axis",
      axisPointer: { type: "shadow" },
      confine: true,
      backgroundColor: "#fbfaf6",
      borderColor: "#c9c7bf",
      borderWidth: 1,
      padding: 10,
      extraCssText: "box-shadow:0 12px 30px rgba(17,19,28,.15);",
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      min: 0,
      max: maximum * 1.12,
      splitNumber: mobile ? 3 : 5,
      axisLine: { show: true, lineStyle: { color: "#a8a69f" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#6d7078",
        fontFamily: chartFont,
        fontSize: axisFontSize,
        formatter: money,
      },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(17,19,28,.10)" },
      },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: props.rows.map((row) => row.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        interval: 0,
        color: "#252833",
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        fontWeight: 650,
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
                color: "#11131c",
                fontFamily: chartDisplayFont,
                fontSize: valueFontSize,
                fontWeight: 600,
                formatter: (parameters: CallbackDataParams): string =>
                  props.rows[parameters.dataIndex]?.display ?? "",
              }
            : { show: false },
        emphasis: {
          focus: "series" as const,
        },
      })),
      {
        name: "Open model details",
        type: "bar",
        barGap: "-100%",
        barWidth: mobile ? 38 : 42,
        cursor: props.rows.some((row) => row.link !== undefined)
          ? "pointer"
          : "default",
        data: props.rows.map(() => maximum * 1.12),
        itemStyle: {
          color: "rgba(17,19,28,0.001)",
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
  const row = props.rows[parameters.dataIndex];
  if (row?.link !== undefined) void router.push(row.link);
};

const { chartElement, refresh } = useResponsiveEChart({
  height: chartHeight,
  initialize: (element) =>
    echarts.init(element, undefined, { renderer: "svg" }),
  option: chartOption,
  onClick: handleClick,
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
        <RouterLink v-if="row.link" :to="row.link" tabindex="-1">
          Open full details for {{ row.label }}
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
  font-weight: 760;
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
  font-weight: 650;
}

figcaption i {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
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
