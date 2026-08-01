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
import { useRouter } from "vue-router";

import { chartTooltipStyle, readChartTheme } from "@/lib/chart-theme";
import { moneyEpisode } from "@/lib/format";
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
  link?: string;
}

const props = defineProps<{
  items: EfficiencyPoint[];
}>();

const router = useRouter();
const chartHeight = computed(() => 430);
const costDomain = computed(() =>
  chartValueDomain(props.items.map((item) => item.cost)),
);
const scoreDomain = computed(() =>
  chartValueDomain(props.items.map((item) => item.score)),
);

const pointData = () => {
  const maximumCost = Math.max(...props.items.map((item) => item.cost));
  return props.items.map((item) => ({
    name: item.label,
    value: [item.cost, item.score],
    rank: item.rank,
    label: {
      position:
        item.cost === maximumCost ? ("left" as const) : ("right" as const),
    },
  }));
};

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item = props.items.find((candidate) => candidate.label === parameter?.name);
  if (item === undefined) return "";
  const theme = readChartTheme();
  return [
    '<div style="min-width:190px;padding:3px 2px">',
    `<strong style="display:block;color:${theme.ink};font:700 .82rem/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.45rem">${escapeHtml(item.scoreDisplay)} questions</span>`,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">${escapeHtml(item.costDisplay)} Guesser cost per episode</span>`,
    `<span style="display:block;margin-top:4px;color:${theme.muted};font-size:.75rem">Efficiency rank ${item.rank}</span>`,
    item.link === undefined
      ? ""
      : `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight:700;text-transform:uppercase">View full run →</span>`,
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const theme = readChartTheme();
  const axisFontSize = chartTextSize(width, 9, 11);
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 480,
    aria: {
      enabled: true,
      description: `Cost and question-score trade-off. Lower and further left is better. ${props.items
        .map(
          (item) =>
            `${item.label}, ${item.scoreDisplay} questions, ${item.costDisplay} per episode`,
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
      ...chartTooltipStyle(theme, 10),
      trigger: "item",
      confine: true,
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      scale: true,
      min: costDomain.value.minimum,
      max: costDomain.value.maximum,
      name: "Guesser cost / episode · lower is better",
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
        formatter: moneyEpisode,
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine },
      },
    },
    yAxis: {
      type: "value",
      scale: true,
      min: scoreDomain.value.minimum,
      max: scoreDomain.value.maximum,
      name: "Question score",
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
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine },
      },
    },
    series: [
      {
        name: "Models",
        type: "scatter",
        data: pointData(),
        symbolSize: mobile ? 14 : 17,
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
          fontWeight: 650,
          width: 148,
          overflow: "truncate",
          ellipsis: "…",
          formatter: (parameters: CallbackDataParams): string => parameters.name,
        },
        labelLayout: {
          hideOverlap: false,
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
  <figure class="efficiency-scatter">
    <figcaption>
      <span>Lower-left is better</span>
      <span>Select a model point to view its full run</span>
    </figcaption>
    <div
      ref="chartElement"
      class="efficiency-scatter-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ul class="mobile-model-key" aria-label="Models in the chart">
      <li v-for="item in items" :key="item.label">
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
  font-weight: 760;
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

  .mobile-model-key a,
  .mobile-model-key strong {
    overflow: hidden;
    color: var(--ink);
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mobile-model-key span {
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }
}
</style>
