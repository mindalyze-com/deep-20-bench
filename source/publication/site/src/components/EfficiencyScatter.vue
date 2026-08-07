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
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { chartTooltipStyle, readChartTheme } from "@/lib/chart-theme";
import { moneyEpisode, number } from "@/lib/format";
import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  chartFontWeightSemibold,
  chartTextSize,
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
  normalizedCost: number;
  normalizedScore: number;
  distanceDisplay: string;
  paretoEfficient: boolean;
  link?: string;
}

const props = withDefaults(
  defineProps<{
    items: EfficiencyPoint[];
    expanded?: boolean;
  }>(),
  { expanded: false },
);

const router = useRouter();
const figureElement = ref<HTMLElement | null>(null);
const chartWidth = ref(0);
const viewportWidth = ref(window.innerWidth);
const viewportHeight = ref(window.innerHeight);
let figureResizeObserver: ResizeObserver | null = null;

const updateViewport = (): void => {
  viewportWidth.value = window.innerWidth;
  viewportHeight.value = window.innerHeight;
};

onMounted(() => {
  window.addEventListener("resize", updateViewport);
  figureResizeObserver = new ResizeObserver(([entry]) => {
    if (entry !== undefined) chartWidth.value = Math.round(entry.contentRect.width);
  });
  if (figureElement.value !== null) {
    figureResizeObserver.observe(figureElement.value);
  }
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", updateViewport);
  figureResizeObserver?.disconnect();
});

const desktopChartHeight = (): number => {
  const width =
    chartWidth.value > 0
      ? chartWidth.value
      : Math.min(viewportWidth.value, props.expanded ? 1040 : 780);
  const plotSize = Math.max(
    220,
    Math.min(props.expanded ? 720 : 620, width - 160),
  );
  return plotSize + (props.expanded ? 48 : 76);
};

const chartHeight = computed(() => {
  if (props.expanded) {
    return viewportWidth.value <= 760
      ? Math.max(
          280,
          Math.min(
            560,
            viewportWidth.value + 70,
            viewportHeight.value - 120,
          ),
        )
      : Math.max(
          420,
          Math.min(900, viewportHeight.value - 80, desktopChartHeight()),
        );
  }
  if (viewportWidth.value <= 760) return 480;
  return desktopChartHeight();
});

const pointData = (mobile: boolean) => {
  const maximumCost = Math.max(...props.items.map((item) => item.normalizedCost));
  return props.items.map((item) => ({
    name: item.label,
    value: [item.normalizedCost, item.normalizedScore],
    rank: item.rank,
    symbol: item.paretoEfficient ? "diamond" : "circle",
    symbolSize: item.paretoEfficient ? (mobile ? 17 : 21) : mobile ? 13 : 16,
    label: {
      position:
        item.normalizedCost === maximumCost ? ("left" as const) : ("right" as const),
    },
  }));
};

const distanceGuideData = (distance: number): number[][] =>
  Array.from({ length: 81 }, (_, index) => {
    const angle = (index / 80) * (Math.PI / 2);
    return [distance * Math.cos(angle), distance * Math.sin(angle)];
  }).filter(([cost, score]) => (cost ?? 2) <= 1 && (score ?? 2) <= 1);

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item = props.items.find((candidate) => candidate.label === parameter?.name);
  if (item === undefined) return "";
  const theme = readChartTheme();
  return [
    '<div style="min-width:190px;padding:3px 2px">',
    `<strong style="display:block;color:${theme.ink};font: var(--font-weight-bold) .82rem/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.45rem">${escapeHtml(item.scoreDisplay)} questions</span>`,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">${escapeHtml(item.costDisplay)} Guesser cost per episode</span>`,
    `<span style="display:block;margin-top:4px;color:${theme.muted};font-size:.75rem">Ideal distance ${escapeHtml(item.distanceDisplay)} · rank ${item.rank}</span>`,
    item.paretoEfficient
      ? `<span style="display:block;margin-top:4px;color:${theme.results.efficiency};font-size:.75rem;font-weight: var(--font-weight-bold)">Pareto-efficient</span>`
      : "",
    item.link === undefined
      ? ""
      : `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight: var(--font-weight-bold);text-transform:uppercase">View full run →</span>`,
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 760;
  const theme = readChartTheme();
  const axisFontSize = chartTextSize(width, 9, 11);
  const plotSize = Math.max(
    220,
    Math.min(
      props.expanded ? 720 : 620,
      width - (mobile ? (props.expanded ? 80 : 96) : 160),
      chartHeight.value - (props.expanded ? 48 : mobile ? 96 : 76),
    ),
  );
  const plotLeft = Math.round((width - plotSize) / 2);
  const guideDistances = [0.25, 0.5, 0.75, 1, 1.25];
  const rawCosts = props.items.map((item) => item.cost);
  const rawScores = props.items.map((item) => item.score);
  const costMinimum = Math.min(...rawCosts);
  const costMaximum = Math.max(...rawCosts);
  const scoreMinimum = Math.min(...rawScores);
  const scoreMaximum = Math.max(...rawScores);
  const rawValueAt = (normalized: number, minimum: number, maximum: number): number =>
    minimum + normalized * (maximum - minimum);
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 480,
    aria: {
      enabled: true,
      description: `Normalized cost and question-score trade-off. Lower and further left is better. Curves show equal ideal distance and diamonds mark Pareto-efficient models. ${props.items
        .map(
          (item) =>
            `${item.label}, ideal distance ${item.distanceDisplay}, rank ${item.rank}, ${item.scoreDisplay} questions, ${item.costDisplay} per episode${item.paretoEfficient ? ", Pareto-efficient" : ""}`,
        )
        .join(". ")}.`,
    },
    grid: {
      top: 34,
      left: plotLeft,
      width: plotSize,
      height: plotSize,
    },
    tooltip: {
      ...chartTooltipStyle(theme, 10),
      trigger: "item",
      confine: true,
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      min: 0,
      max: 1,
      boundaryGap: [0, 0],
      interval: 0.25,
      name: "Guesser cost per episode · normalized position",
      nameLocation: "middle",
      nameGap: mobile ? 43 : 48,
      nameTextStyle: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
      },
      axisLine: { show: true, lineStyle: { color: theme.border } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        formatter: (value: number): string =>
          moneyEpisode(rawValueAt(value, costMinimum, costMaximum)),
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine },
      },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 1,
      boundaryGap: [0, 0],
      interval: 0.25,
      name: "Question score · normalized position",
      nameLocation: "middle",
      nameGap: mobile ? 40 : 51,
      nameTextStyle: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
      },
      axisLine: { show: true, lineStyle: { color: theme.border } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        formatter: (value: number): string =>
          number(rawValueAt(value, scoreMinimum, scoreMaximum), 2),
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine },
      },
    },
    series: [
      ...guideDistances.map((distance) => ({
        name: `Distance ${number(distance, 2)}`,
        type: "line" as const,
        data: distanceGuideData(distance),
        silent: true,
        symbol: "none",
        lineStyle: {
          color: theme.border,
          type: "dashed" as const,
          width: 1,
          opacity: distance > 1 ? 0.45 : 0.9,
        },
        emphasis: { disabled: true },
        tooltip: { show: false },
        z: 1,
      })),
      {
        name: "Distance labels",
        type: "scatter",
        data: guideDistances.map((distance) => ({
          name: `Distance ${number(distance, 2)}`,
          value: [distance / Math.SQRT2, distance / Math.SQRT2],
          label: {
            show: true,
            position: "top" as const,
            formatter: number(distance, 2),
            color: distance > 1 ? theme.border : theme.muted,
            fontFamily: chartFont,
            fontSize: chartTextSize(width, 8, 10),
            backgroundColor: theme.surface,
            padding: [1, 3],
          },
        })),
        silent: true,
        symbolSize: 1,
        itemStyle: { color: "transparent" },
        tooltip: { show: false },
        z: 1,
      },
      {
        name: "Models",
        type: "scatter",
        clip: false,
        data: pointData(mobile),
        cursor: "pointer",
        itemStyle: {
          color: theme.results.efficiency,
          borderColor: theme.ink,
          borderWidth: 2,
        },
        label: {
          show: !mobile,
          distance: 7,
          color: theme.inkSoft,
          fontFamily: chartFont,
          fontSize: chartTextSize(width, 8, 11),
          fontWeight: chartFontWeightSemibold,
          width: 148,
          overflow: "truncate",
          ellipsis: "…",
          formatter: (parameters: CallbackDataParams): string => parameters.name,
        },
        labelLayout: {
          hideOverlap: true,
          moveOverlap: "shiftY",
        },
        emphasis: {
          scale: 1.35,
          itemStyle: {
            shadowBlur: 10,
            shadowColor: theme.gridLine,
          },
        },
        z: 2,
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
  <figure
    ref="figureElement"
    class="efficiency-scatter"
    :class="{ 'efficiency-scatter--expanded': expanded }"
  >
    <figcaption v-if="!expanded">
      <span>Lower-left is better</span>
      <span>Curves show equal ideal distance</span>
    </figcaption>
    <div
      ref="chartElement"
      class="efficiency-scatter-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ul class="mobile-model-key" aria-label="Models in the chart">
      <li v-for="item in items" :key="item.label">
        <i :class="{ 'is-pareto': item.paretoEfficient }" aria-hidden="true"></i>
        <RouterLink v-if="item.link" :to="item.link">{{ item.label }}</RouterLink>
        <strong v-else>{{ item.label }}</strong>
        <span>
          {{ item.distanceDisplay }} distance{{ item.paretoEfficient ? " · Pareto-efficient" : "" }}
        </span>
      </li>
    </ul>
    <ol class="visually-hidden" aria-label="Cost and question-score data">
      <li v-for="item in items" :key="item.label">
        {{ item.label }}: {{ item.scoreDisplay }} questions,
        {{ item.costDisplay }} Guesser cost per episode, ideal distance
        {{ item.distanceDisplay }}, rank {{ item.rank }}.
        <span v-if="item.paretoEfficient">Pareto-efficient.</span>
        <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
          View full run for {{ item.label }}
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

.efficiency-scatter--expanded {
  padding-block: 0.5rem;
}

figcaption {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem 1.2rem;
  align-items: center;
  color: var(--muted);
  font-size: var(--text-micro);
}

figcaption > span:first-child {
  margin-right: auto;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.efficiency-scatter-canvas {
  width: 100%;
  min-width: 0;
}

.mobile-model-key {
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

  .mobile-model-key {
    display: grid;
    margin: 0.2rem 0.5rem 0;
    padding: 0;
    border-top: var(--rule-subtle);
    list-style: none;
  }

  .mobile-model-key li {
    display: grid;
    grid-template-columns: 0.55rem minmax(0, 1fr) auto;
    gap: 0.5rem;
    align-items: center;
    min-height: 2.4rem;
    border-bottom: var(--rule-subtle);
    font-size: var(--text-micro);
  }

  .mobile-model-key i {
    width: 0.55rem;
    height: 0.55rem;
    border: var(--rule-strong);
    border-radius: 50%;
    background: var(--result-efficiency);
  }

  .mobile-model-key i.is-pareto {
    border-radius: 0;
    transform: rotate(45deg);
  }

  .mobile-model-key a,
  .mobile-model-key strong {
    overflow: hidden;
    color: var(--ink);
    font-weight: var(--font-weight-bold);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mobile-model-key span {
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }

  .efficiency-scatter--expanded .mobile-model-key {
    display: none;
  }
}
</style>
