<script setup lang="ts">
import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  EChartsOption,
} from "echarts";
import { computed } from "vue";

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
import type { ReliabilityChartItem } from "@/lib/reliability-chart";
import {
  chartAnimationEnabled,
  chartTextSize,
  chartValueDomain,
  escapeHtml,
} from "@/lib/use-responsive-echart";
import { useLinkedEChart } from "@/lib/use-linked-echart";

const props = defineProps<{
  items: ReliabilityChartItem[];
}>();

const chartHeight = computed(() => 430);
const widthDomain = computed(() =>
  chartValueDomain(props.items.map((item) => item.intervalWidth)),
);
const scoreDomain = computed(() =>
  chartValueDomain(props.items.map((item) => item.score)),
);
const modelKeyItems = computed<ChartModelKeyItem[]>(() =>
  props.items.map((item) => ({
    key: item.label,
    label: item.label,
    detail: `${item.scoreDisplay} q · CI width ${item.intervalWidthDisplay}`,
    link: item.link,
  })),
);
const accessibleItems = computed<ChartAccessibleItem[]>(() =>
  props.items.map((item) => ({
    key: item.label,
    label: item.label,
    description: `${item.label}: score ${item.scoreDisplay} questions; CI width ${item.intervalWidthDisplay} questions; stability rank ${item.reliabilityRank}.`,
    link: item.link,
  })),
);

const chartLabel = (label: string): string =>
  label.replace(/\s+\([^)]*\)$/, "");

const labelPosition = (
  item: ReliabilityChartItem,
  maximumWidth: number,
): "top" | "right" | "bottom" | "left" => {
  if (item.intervalWidth === maximumWidth) return "left";
  if ([2, 5].includes(item.reliabilityRank)) return "left";
  if ([3, 7].includes(item.reliabilityRank)) return "top";
  if ([4, 8].includes(item.reliabilityRank)) return "bottom";
  return "right";
};

const pointData = () => {
  const maximumWidth = Math.max(
    ...props.items.map((item) => item.intervalWidth),
  );
  return props.items.map((item) => ({
    name: item.label,
    value: [item.intervalWidth, item.score],
    label: {
      position: labelPosition(item, maximumWidth),
    },
  }));
};

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const item = chartTooltipItem(parameters, props.items);
  if (item === undefined) return "";
  const theme = readChartTheme();
  return [
    '<div style="min-width:200px;max-width:290px;padding:3px 2px">',
    chartTooltipTitle(theme, item.label),
    chartTooltipPrimary(theme, `${item.scoreDisplay} questions`),
    `<span style="display:block;margin-top:6px;color:${theme.inkSoft};font-size:.78rem;font-weight: var(--font-weight-semibold)">CI width ${escapeHtml(item.intervalWidthDisplay)} questions</span>`,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">95% CI ${escapeHtml(item.confidenceDisplay)} · stability rank ${item.reliabilityRank}</span>`,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">Lower-left is better</span>`,
    chartTooltipRunLink(theme, item.link !== undefined),
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
      description: `Question score and repeated-trial stability on the fixed subjects. Lower-left is better: lower question score and smaller CI width. ${props.items
        .map(
          (item) =>
            `${item.label}, score ${item.scoreDisplay}, CI width ${item.intervalWidthDisplay}`,
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
      ...chartValueAxis(
        theme,
        axisFontSize,
        "CI width · lower is better",
        mobile ? 43 : 48,
        (value) =>
          value.toLocaleString("en-US", { maximumFractionDigits: 1 }),
      ),
      scale: true,
      min: widthDomain.value.minimum,
      max: widthDomain.value.maximum,
    },
    yAxis: {
      ...chartValueAxis(
        theme,
        axisFontSize,
        "Question score",
        mobile ? 40 : 51,
      ),
      scale: true,
      min: scoreDomain.value.minimum,
      max: scoreDomain.value.maximum,
    },
    series: [
      {
        name: "Models",
        type: "scatter",
        data: pointData(),
        symbolSize: mobile ? 14 : 17,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        ...scatterSeriesPresentation(
          theme,
          width,
          mobile,
          theme.results.stability,
          false,
          (parameters) => chartLabel(parameters.name),
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
  <figure class="scatter-chart reliability-scatter">
    <figcaption class="scatter-chart-caption">
      <span>Lower-left is better</span>
      <span>Select a model point to view its full run</span>
    </figcaption>
    <ChartLoadNotice v-if="loadError" />
    <div
      ref="chartElement"
      class="scatter-chart-canvas reliability-scatter-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ChartModelKey :items="modelKeyItems" color="var(--result-stability)" />
    <ChartAccessibleData
      label="Question score and stability data"
      :items="accessibleItems"
    />
  </figure>
</template>
