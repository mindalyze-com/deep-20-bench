<script setup lang="ts">
import { LineChart, ScatterChart } from "echarts/charts";
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

import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  escapeHtml,
  useResponsiveEChart,
} from "@/lib/use-responsive-echart";

echarts.use([
  LineChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  AriaComponent,
  SVGRenderer,
]);

export interface EfficiencyPoint {
  label: string;
  rank: number;
  cost: number;
  costDisplay: string;
  score: number;
  scoreDisplay: string;
  frontier: boolean;
  link?: string;
}

const props = defineProps<{
  items: EfficiencyPoint[];
}>();

const router = useRouter();
const chartHeight = computed(() => 430);
const frontier = computed(() =>
  props.items
    .filter((item) => item.frontier)
    .sort((left, right) => left.cost - right.cost),
);
const scoreMinimum = computed(() =>
  Math.max(
    0,
    Math.floor(Math.min(...props.items.map((item) => item.score)) - 2),
  ),
);
const scoreMaximum = computed(() =>
  Math.ceil(Math.max(...props.items.map((item) => item.score), 1) + 2),
);
const costMaximum = computed(
  () => Math.max(...props.items.map((item) => item.cost), 1) * 1.08,
);

const pointData = (frontierOnly: boolean) =>
  props.items
    .filter((item) => item.frontier === frontierOnly)
    .map((item) => ({
      name: item.label,
      value: [item.cost, item.score],
      rank: item.rank,
    }));

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item = props.items.find((candidate) => candidate.label === parameter?.name);
  if (item === undefined) return "";
  return [
    '<div style="min-width:190px;padding:3px 2px">',
    `<strong style="display:block;color:#11131c;font:700 12px/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:#11131c;font-family:${chartDisplayFont};font-size:23px">${escapeHtml(item.scoreDisplay)} questions</span>`,
    `<span style="display:block;margin-top:5px;color:#5f626a;font-size:11px">${escapeHtml(item.costDisplay)} Guesser cost per episode</span>`,
    `<span style="display:block;margin-top:4px;color:#5f626a;font-size:11px">${item.frontier ? "Pareto frontier" : "Ranked model"} · efficiency rank ${item.rank}</span>`,
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
    animationDuration: 480,
    aria: {
      enabled: true,
      description: `Cost and question-score trade-off. Lower and further left is better. ${props.items
        .map(
          (item) =>
            `${item.label}, ${item.scoreDisplay} questions, ${item.costDisplay} per episode${item.frontier ? ", Pareto frontier" : ""}`,
        )
        .join(". ")}.`,
    },
    grid: {
      top: mobile ? 26 : 34,
      right: mobile ? 18 : 42,
      bottom: mobile ? 64 : 70,
      left: mobile ? 58 : 76,
    },
    tooltip: {
      trigger: "item",
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
      max: costMaximum.value,
      name: "Guesser cost / episode · lower is better",
      nameLocation: "middle",
      nameGap: mobile ? 43 : 48,
      nameTextStyle: {
        color: "#5f626a",
        fontFamily: chartFont,
        fontSize: mobile ? 9 : 10,
      },
      axisLine: { show: true, lineStyle: { color: "#a8a69f" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#6d7078",
        fontFamily: chartFont,
        fontSize: 9,
        formatter: (value: number): string =>
          `$${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`,
      },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(17,19,28,.10)" },
      },
    },
    yAxis: {
      type: "value",
      min: scoreMinimum.value,
      max: scoreMaximum.value,
      name: "Question score",
      nameLocation: "middle",
      nameGap: mobile ? 40 : 51,
      nameTextStyle: {
        color: "#5f626a",
        fontFamily: chartFont,
        fontSize: mobile ? 9 : 10,
      },
      axisLine: { show: true, lineStyle: { color: "#a8a69f" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#6d7078",
        fontFamily: chartFont,
        fontSize: 9,
      },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(17,19,28,.10)" },
      },
    },
    series: [
      {
        name: "Pareto frontier guide",
        type: "line",
        data: frontier.value.map((item) => [item.cost, item.score]),
        symbol: "none",
        silent: true,
        lineStyle: {
          color: "#849f18",
          width: 2,
          type: "dashed",
        },
        z: 1,
      },
      {
        name: "Other ranked models",
        type: "scatter",
        data: pointData(false),
        symbolSize: mobile ? 12 : 14,
        cursor: "pointer",
        itemStyle: {
          color: "#fbfaf6",
          borderColor: "#4e64ff",
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: { scale: 1.35 },
        z: 2,
      },
      {
        name: "Pareto frontier",
        type: "scatter",
        data: pointData(true),
        symbolSize: mobile ? 17 : 20,
        cursor: "pointer",
        itemStyle: {
          color: "#d6ff3f",
          borderColor: "#667d0d",
          borderWidth: 2,
        },
        label: {
          show: !mobile,
          position: "right",
          distance: 7,
          color: "#252833",
          fontFamily: chartFont,
          fontSize: mobile ? 8 : 10,
          fontWeight: 650,
          width: mobile ? 76 : 145,
          overflow: "truncate",
          ellipsis: "…",
          formatter: (parameters: CallbackDataParams): string => parameters.name,
        },
        emphasis: { scale: 1.25 },
        z: 3,
      },
    ],
  };
};

const handleClick = (parameters: CallbackDataParams): void => {
  const item = props.items.find((candidate) => candidate.label === parameters.name);
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
  <figure class="efficiency-scatter">
    <figcaption>
      <span>Lower-left is better</span>
      <span><i class="frontier-key" aria-hidden="true"></i>Pareto frontier</span>
      <span><i aria-hidden="true"></i>Other ranked model</span>
    </figcaption>
    <div
      ref="chartElement"
      class="efficiency-scatter-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ul class="mobile-frontier-key" aria-label="Pareto frontier models">
      <li v-for="item in frontier" :key="item.label">
        <i aria-hidden="true"></i>
        <RouterLink v-if="item.link" :to="item.link">{{ item.label }}</RouterLink>
        <strong v-else>{{ item.label }}</strong>
        <span>{{ item.scoreDisplay }} q · {{ item.costDisplay }}</span>
      </li>
    </ul>
    <ol class="visually-hidden" aria-label="Cost and question-score data">
      <li v-for="item in items" :key="item.label">
        {{ item.label }}: {{ item.scoreDisplay }} questions,
        {{ item.costDisplay }} Guesser cost per episode.
        <span v-if="item.frontier">Pareto frontier.</span>
        <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
          Open full details for {{ item.label }}
        </RouterLink>
      </li>
    </ol>
  </figure>
</template>

<style scoped>
.efficiency-scatter {
  margin: 0;
  padding: 1rem clamp(0.8rem, 2vw, 1.5rem) 1.2rem;
  background:
    linear-gradient(rgb(17 19 28 / 2%) 1px, transparent 1px) 0 0 / 100% 52px,
    var(--paper-bright);
}

figcaption {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem 1.2rem;
  align-items: center;
  color: var(--muted);
  font-size: 0.62rem;
}

figcaption > span:first-child {
  margin-right: auto;
  font-weight: 760;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

figcaption span:not(:first-child) {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

figcaption i {
  width: 0.65rem;
  height: 0.65rem;
  border: 2px solid var(--blue);
  border-radius: 50%;
  background: var(--paper-bright);
}

figcaption .frontier-key {
  border-color: #667d0d;
  background: var(--acid);
}

.efficiency-scatter-canvas {
  width: 100%;
  min-width: 0;
}

.mobile-frontier-key {
  display: none;
}

@media (max-width: 620px) {
  .efficiency-scatter {
    padding-inline: 0.4rem;
  }

  figcaption {
    padding-inline: 0.5rem;
  }

  figcaption > span:first-child {
    flex-basis: 100%;
  }

  .mobile-frontier-key {
    display: grid;
    margin: 0.2rem 0.5rem 0;
    padding: 0;
    border-top: 1px solid var(--line-soft);
    list-style: none;
  }

  .mobile-frontier-key li {
    display: grid;
    grid-template-columns: 0.55rem minmax(0, 1fr) auto;
    gap: 0.5rem;
    align-items: center;
    min-height: 2.4rem;
    border-bottom: 1px solid var(--line-soft);
    font-size: 0.65rem;
  }

  .mobile-frontier-key i {
    width: 0.55rem;
    height: 0.55rem;
    border: 2px solid #667d0d;
    border-radius: 50%;
    background: var(--acid);
  }

  .mobile-frontier-key a,
  .mobile-frontier-key strong {
    overflow: hidden;
    color: var(--ink);
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mobile-frontier-key span {
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }
}
</style>
