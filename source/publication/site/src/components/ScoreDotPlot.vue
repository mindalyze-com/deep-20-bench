<script setup lang="ts">
import { BarChart, ScatterChart } from "echarts/charts";
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
import { useRouter, type RouteLocationRaw } from "vue-router";

import { chartTooltipStyle, readChartTheme } from "@/lib/chart-theme";
import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  chartTextSize,
  chartValueDomain,
  escapeHtml,
  useResponsiveEChart,
} from "@/lib/use-responsive-echart";

echarts.use([
  BarChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  AriaComponent,
  SVGRenderer,
]);

export interface ScoreDot {
  label: string;
  value: number;
  display: string;
  link?: RouteLocationRaw;
}

const props = defineProps<{
  items: ScoreDot[];
}>();

const router = useRouter();
const chartHeight = computed(() =>
  Math.max(410, props.items.length * 43 + 82),
);
const scoreValues = computed(() =>
  props.items
    .map((item) => item.value)
    .filter((value) => Number.isFinite(value)),
);
const scoreDomain = computed(() => chartValueDomain(scoreValues.value));

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item =
    parameter === undefined ? undefined : props.items[parameter.dataIndex];
  if (item === undefined) return "";
  const theme = readChartTheme();
  return [
    '<div style="min-width:180px;padding:3px 2px">',
    `<strong style="display:block;color:${theme.ink};font:700 .82rem/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.55rem">${escapeHtml(item.display)} questions</span>`,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">Lower is better</span>`,
    item.link === undefined
      ? ""
      : `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight:700;text-transform:uppercase">View full run →</span>`,
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const theme = readChartTheme();
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const valueFontSize = chartTextSize(width, 11, 14);
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    animationEasing: "cubicOut",
    aria: {
      enabled: true,
      description: `Official question scores. Lower is better. The horizontal axis runs from ${scoreDomain.value.minimum} to ${scoreDomain.value.maximum}. ${props.items
        .map((item, index) => `${index + 1}. ${item.label}, ${item.display}`)
        .join(". ")}.`,
    },
    grid: {
      top: 18,
      right: mobile ? 54 : 76,
      bottom: 48,
      left: mobile ? 132 : 218,
    },
    tooltip: {
      ...chartTooltipStyle(theme, 11),
      trigger: "item",
      confine: true,
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      scale: true,
      min: scoreDomain.value.minimum,
      max: scoreDomain.value.maximum,
      splitNumber: mobile ? 3 : 5,
      name: "Question score · lower is better",
      nameLocation: "middle",
      nameGap: 33,
      nameTextStyle: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        fontWeight: 700,
      },
      axisLine: {
        show: true,
        lineStyle: { color: theme.border, width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        margin: 9,
        formatter: (value: number): string =>
          value.toLocaleString("en-US", { maximumFractionDigits: 1 }),
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine, width: 1 },
      },
    },
    yAxis: {
      type: "category",
      inverse: true,
      triggerEvent: true,
      data: props.items.map((item) => item.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        interval: 0,
        align: "right",
        color: theme.inkSoft,
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        fontWeight: 650,
        width: mobile ? 112 : 194,
        overflow: "truncate",
        ellipsis: "…",
        margin: mobile ? 12 : 18,
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine, width: 2 },
      },
    },
    series: [
      {
        name: "View full run",
        type: "bar",
        barWidth: mobile ? 38 : 42,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        data: props.items.map(() => scoreDomain.value.maximum),
        itemStyle: {
          color: "rgb(12 17 27 / 0.1%)",
        },
        emphasis: {
          itemStyle: {
            color: "rgba(78,100,255,0.06)",
          },
        },
        label: { show: false },
        z: 2,
      },
      {
        name: "Question score",
        type: "scatter",
        data: props.items.map((item) => ({
          name: item.label,
          value: [item.value, item.label],
        })),
        symbolSize: mobile ? 14 : 16,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        itemStyle: {
          color: theme.roles.guesser,
          borderColor: theme.ink,
          borderWidth: 1.5,
        },
        label: {
          show: true,
          position: "right",
          distance: mobile ? 6 : 8,
          color: theme.ink,
          fontFamily: chartDisplayFont,
          fontSize: valueFontSize,
          fontWeight: 650,
          formatter: (parameters: CallbackDataParams): string =>
            props.items[parameters.dataIndex]?.display ?? "",
        },
        emphasis: {
          scale: 1.25,
          itemStyle: {
            shadowBlur: 10,
            shadowColor: theme.gridLine,
          },
        },
        z: 3,
      },
    ],
  };
};

const handleClick = (parameters: CallbackDataParams): void => {
  const item =
    parameters.componentType === "yAxis"
      ? props.items.find((candidate) => candidate.label === String(parameters.value))
      : props.items[parameters.dataIndex];
  if (item?.link !== undefined) void router.push(item.link);
};

const { chartElement, refresh } = useResponsiveEChart({
  height: chartHeight,
  initialize: (element) =>
    echarts.init(element, undefined, { renderer: "svg" }),
  option: chartOption,
  onClick: handleClick,
  pointerCursor: (parameters) =>
    parameters.componentType === "yAxis" &&
    props.items.some(
      (item) =>
        item.label === String(parameters.value) && item.link !== undefined,
    ),
});

watch(() => [chartElement.value, props.items] as const, refresh, {
  deep: true,
});
</script>

<template>
  <figure class="score-dot-plot">
    <figcaption>Select a model row to view its full run.</figcaption>
    <div
      ref="chartElement"
      class="score-dot-plot-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ol class="visually-hidden" aria-label="Official question scores">
      <li v-for="(item, index) in items" :key="item.label">
        {{ index + 1 }}. {{ item.label }}: {{ item.display }} questions.
        <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
          View full run for {{ item.label }}
        </RouterLink>
      </li>
    </ol>
  </figure>
</template>

<style scoped>
.score-dot-plot {
  margin: 0;
}

.score-dot-plot figcaption {
  margin: 0;
  padding: 0.75rem 0.5rem 0;
  color: var(--muted);
  font-size: var(--text-micro);
  line-height: 1.4;
  text-align: right;
}

.score-dot-plot-canvas {
  width: 100%;
  min-width: 0;
}
</style>
