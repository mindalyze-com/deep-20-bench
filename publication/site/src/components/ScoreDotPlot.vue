<script setup lang="ts">
import { ScatterChart } from "echarts/charts";
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

import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  escapeHtml,
  useResponsiveEChart,
} from "@/lib/use-responsive-echart";

echarts.use([
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
const scoreDomain = computed(() => {
  if (scoreValues.value.length === 0) return { minimum: 0, maximum: 1 };
  const dataMinimum = Math.min(...scoreValues.value);
  const dataMaximum = Math.max(...scoreValues.value);
  const span = dataMaximum - dataMinimum;
  const padding = Math.max(0.5, span * 0.08);
  return {
    minimum: Math.max(0, Math.floor((dataMinimum - padding) * 2) / 2),
    maximum: Math.ceil((dataMaximum + padding) * 2) / 2,
  };
});

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item =
    parameter === undefined ? undefined : props.items[parameter.dataIndex];
  if (item === undefined) return "";
  return [
    '<div style="min-width:180px;padding:3px 2px">',
    `<strong style="display:block;color:#11131c;font:700 12px/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:#11131c;font-family:${chartDisplayFont};font-size:25px">${escapeHtml(item.display)} questions</span>`,
    '<span style="display:block;margin-top:5px;color:#5f626a;font-size:11px">Lower is better</span>',
    item.link === undefined
      ? ""
      : '<span style="display:block;margin-top:9px;color:#2539bd;font-size:10px;font-weight:700;text-transform:uppercase">Open model details →</span>',
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
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
      trigger: "item",
      confine: true,
      backgroundColor: "#fbfaf6",
      borderColor: "#c9c7bf",
      borderWidth: 1,
      padding: 11,
      extraCssText: "box-shadow:0 12px 30px rgba(17,19,28,.15);",
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      min: scoreDomain.value.minimum,
      max: scoreDomain.value.maximum,
      splitNumber: mobile ? 3 : 5,
      name: "Question score · lower is better",
      nameLocation: "middle",
      nameGap: 33,
      nameTextStyle: {
        color: "#5f626a",
        fontFamily: chartFont,
        fontSize: 10,
        fontWeight: 700,
      },
      axisLine: {
        show: true,
        lineStyle: { color: "#8f8d86", width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: "#5f626a",
        fontFamily: chartFont,
        fontSize: 10,
        margin: 9,
        formatter: (value: number): string =>
          value.toLocaleString("en-US", { maximumFractionDigits: 1 }),
      },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(17,19,28,.08)", width: 1 },
      },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: props.items.map((item) => item.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        interval: 0,
        align: "right",
        color: "#252833",
        fontFamily: chartFont,
        fontSize: mobile ? 10 : 11,
        fontWeight: 650,
        width: mobile ? 112 : 194,
        overflow: "truncate",
        ellipsis: "…",
        margin: mobile ? 12 : 18,
      },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(17,19,28,.16)", width: 2 },
      },
    },
    series: [
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
          color: "#4e64ff",
          borderColor: "#11131c",
          borderWidth: 1.5,
        },
        label: {
          show: true,
          position: "right",
          distance: mobile ? 6 : 8,
          color: "#11131c",
          fontFamily: chartDisplayFont,
          fontSize: mobile ? 11 : 13,
          fontWeight: 650,
          formatter: (parameters: CallbackDataParams): string =>
            props.items[parameters.dataIndex]?.display ?? "",
        },
        emphasis: {
          scale: 1.25,
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(17,19,28,.2)",
          },
        },
        z: 3,
      },
    ],
  };
};

const handleClick = (parameters: CallbackDataParams): void => {
  const item = props.items[parameters.dataIndex];
  if (item?.link !== undefined) void router.push(item.link);
};

const { chartElement, refresh } = useResponsiveEChart({
  height: chartHeight,
  initialize: (element) =>
    echarts.init(element, undefined, { renderer: "svg" }),
  option: chartOption,
  onClick: handleClick,
});

watch(() => [chartElement.value, props.items] as const, refresh, {
  deep: true,
});
</script>

<template>
  <figure class="score-dot-plot">
    <div
      ref="chartElement"
      class="score-dot-plot-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ol class="visually-hidden" aria-label="Official question scores">
      <li v-for="(item, index) in items" :key="item.label">
        {{ index + 1 }}. {{ item.label }}: {{ item.display }} questions.
        <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
          Open full details for {{ item.label }}
        </RouterLink>
      </li>
    </ol>
  </figure>
</template>

<style scoped>
.score-dot-plot {
  margin: 0;
}

.score-dot-plot-canvas {
  width: 100%;
  min-width: 0;
}
</style>
