<script setup lang="ts">
import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  EChartsOption,
} from "echarts";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import ChartAccessibleData, {
  type ChartAccessibleItem,
} from "@/components/ChartAccessibleData.vue";
import ChartModelKey, {
  type ChartModelKeyItem,
} from "@/components/ChartModelKey.vue";
import { chartValueAxis } from "@/lib/chart-axis";
import ChartLoadNotice from "@/components/ChartLoadNotice.vue";
import { scatterSeriesPresentation } from "@/lib/chart-series";
import { chartTooltipStyle, readChartTheme } from "@/lib/chart-theme";
import {
  chartTooltipItem,
  chartTooltipPrimary,
  chartTooltipRunLink,
  chartTooltipTitle,
} from "@/lib/chart-tooltip";
import { moneyEpisode, number } from "@/lib/format";
import {
  chartAnimationEnabled,
  chartFont,
  chartTextSize,
  escapeHtml,
} from "@/lib/use-responsive-echart";
import { useLinkedEChart } from "@/lib/use-linked-echart";

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

const figureElement = ref<HTMLElement | null>(null);
const chartWidth = ref(0);
const viewportWidth = ref(typeof window === "undefined" ? 1280 : window.innerWidth);
const viewportHeight = ref(typeof window === "undefined" ? 720 : window.innerHeight);
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
const modelKeyItems = computed<ChartModelKeyItem[]>(() =>
  props.items.map((item) => ({
    key: item.label,
    label: item.label,
    detail: `${item.distanceDisplay} distance${
      item.paretoEfficient ? " · Pareto-efficient" : ""
    }`,
    link: item.link,
    marker: item.paretoEfficient ? "diamond" : "circle",
  })),
);
const accessibleItems = computed<ChartAccessibleItem[]>(() =>
  props.items.map((item) => ({
    key: item.label,
    label: item.label,
    description: `${item.label}: ${item.scoreDisplay} questions, ${item.costDisplay} Guesser cost per episode, ideal distance ${item.distanceDisplay}, rank ${item.rank}.${item.paretoEfficient ? " Pareto-efficient." : ""}`,
    link: item.link,
  })),
);

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
  const item = chartTooltipItem(parameters, props.items);
  if (item === undefined) return "";
  const theme = readChartTheme();
  return [
    '<div style="min-width:190px;padding:3px 2px">',
    chartTooltipTitle(theme, item.label),
    chartTooltipPrimary(theme, `${item.scoreDisplay} questions`),
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">${escapeHtml(item.costDisplay)} Guesser cost per episode</span>`,
    `<span style="display:block;margin-top:4px;color:${theme.muted};font-size:.75rem">Ideal distance ${escapeHtml(item.distanceDisplay)} · rank ${item.rank}</span>`,
    item.paretoEfficient
      ? `<span style="display:block;margin-top:4px;color:${theme.results.efficiency};font-size:.75rem;font-weight: var(--font-weight-bold)">Pareto-efficient</span>`
      : "",
    chartTooltipRunLink(theme, item.link !== undefined),
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
      ...chartValueAxis(
        theme,
        axisFontSize,
        "Guesser cost per episode · normalized position",
        mobile ? 43 : 48,
        (value) => moneyEpisode(rawValueAt(value, costMinimum, costMaximum)),
      ),
      min: 0,
      max: 1,
      boundaryGap: [0, 0],
      interval: 0.25,
    },
    yAxis: {
      ...chartValueAxis(
        theme,
        axisFontSize,
        "Question score · normalized position",
        mobile ? 40 : 51,
        (value) => number(rawValueAt(value, scoreMinimum, scoreMaximum), 2),
      ),
      min: 0,
      max: 1,
      boundaryGap: [0, 0],
      interval: 0.25,
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
        ...scatterSeriesPresentation(
          theme,
          width,
          mobile,
          theme.results.efficiency,
          true,
          (parameters) => parameters.name,
        ),
      },
    ],
  };
};

const { chartElement, loadError } = useLinkedEChart({
  height: chartHeight,
  items: () => props.items,
  option: chartOption,
});
void chartElement;
</script>

<template>
  <figure
    ref="figureElement"
    class="scatter-chart efficiency-scatter"
    :class="{ 'efficiency-scatter--expanded': expanded }"
  >
    <figcaption v-if="!expanded" class="scatter-chart-caption">
      <span>Lower-left is better</span>
      <span>Curves show equal ideal distance</span>
    </figcaption>
    <ChartLoadNotice v-if="loadError" />
    <div
      ref="chartElement"
      class="scatter-chart-canvas efficiency-scatter-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ChartModelKey
      v-if="!expanded"
      :items="modelKeyItems"
      color="var(--result-efficiency)"
    />
    <ChartAccessibleData
      label="Cost and question-score data"
      :items="accessibleItems"
    />
  </figure>
</template>

<style scoped>
.efficiency-scatter--expanded {
  padding-block: 0.5rem;
}
</style>
