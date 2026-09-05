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

export interface MetricBar {
  label: string;
  value: number;
  display: string;
  detail?: string;
  link?: string;
}

const props = withDefaults(
  defineProps<{
    items: MetricBar[];
    directionLabel?: string;
    color?: "blue" | "acid" | "coral" | "efficiency";
    valueFormat?: "number" | "currency" | "duration";
  }>(),
  {
    directionLabel: "Lower is better",
    color: "blue",
    valueFormat: "number",
  },
);

const router = useRouter();

const chartHeight = computed(() =>
  Math.max(370, props.items.length * 48 + 86),
);

const axisValue = (value: number): string => {
  if (props.valueFormat === "currency") return money(value);
  if (props.valueFormat === "duration") {
    if (value >= 60_000) return `${number(value / 60_000, 0)}m`;
    return `${number(value / 1_000, 0)}s`;
  }
  return number(value, value < 10 ? 2 : 0);
};

const number = (value: number, digits: number): string =>
  value.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  });

const tooltip = (parameters: CallbackDataParams | CallbackDataParams[]): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item =
    parameter === undefined ? undefined : props.items[parameter.dataIndex];
  if (item === undefined) return "";
  const theme = readChartTheme();
  const detail =
    item.detail === undefined
      ? ""
      : `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem;line-height:1.45">${escapeHtml(item.detail)}</span>`;
  return [
    '<div style="min-width:180px;max-width:280px;padding:3px 2px">',
    chartTooltipTitle(theme, item.label),
    chartTooltipPrimary(theme, item.display, "1.55rem"),
    detail,
    chartTooltipRunLink(theme, item.link !== undefined, true),
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const theme = readChartTheme();
  const colors = {
    blue: theme.roles.guesser,
    acid: theme.acid,
    coral: theme.coral,
    efficiency: theme.results.efficiency,
  };
  const color = colors[props.color];
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const valueFontSize = chartTextSize(width, 11, 14);
  const maximum = Math.max(
    1,
    ...props.items
      .map((item) => item.value)
      .filter((value) => Number.isFinite(value) && value >= 0),
  );
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    animationEasing: "cubicOut",
    aria: {
      enabled: true,
      description: `${props.directionLabel}. The value axis starts at zero. ${props.items
        .map((item, index) => `${index + 1}. ${item.label}, ${item.display}`)
        .join(". ")}.`,
    },
    grid: {
      top: 18,
      right: mobile ? 56 : 82,
      bottom: 42,
      left: mobile ? 132 : 210,
    },
    tooltip: {
      ...chartTooltipStyle(theme, 11),
      trigger: "item",
      confine: true,
      formatter: tooltip,
    },
    xAxis: {
      type: "value",
      min: 0,
      splitNumber: mobile ? 3 : 5,
      axisLine: {
        show: true,
        lineStyle: { color: theme.border, width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: theme.muted,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        margin: 10,
        formatter: axisValue,
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
        fontWeight: chartFontWeightSemibold,
        width: mobile ? 112 : 186,
        overflow: "truncate",
        ellipsis: "…",
        margin: mobile ? 12 : 18,
      },
    },
    series: [
      {
        name: props.directionLabel,
        type: "bar",
        barWidth: mobile ? 15 : 18,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        data: props.items.map((item, index) => ({
          value: item.value,
          itemStyle: {
            color,
            opacity: index === 0 ? 1 : Math.max(0.58, 0.92 - index * 0.035),
            borderRadius: [0, 3, 3, 0],
          },
        })),
        label: {
          show: true,
          position: "right",
          distance: mobile ? 6 : 10,
          color: theme.ink,
          fontFamily: chartDisplayFont,
          fontSize: valueFontSize,
          fontWeight: chartFontWeightSemibold,
          formatter: (parameters: CallbackDataParams): string =>
            props.items[parameters.dataIndex]?.display ?? "",
        },
        emphasis: {
          itemStyle: {
            opacity: 1,
            shadowBlur: 10,
            shadowColor: theme.gridLine,
          },
        },
      },
      {
        name: "View full run",
        type: "bar",
        barGap: "-100%",
        barWidth: mobile ? 38 : 42,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        data: props.items.map(() => maximum),
        itemStyle: {
          color: "rgb(12 17 27 / 0.1%)",
        },
        emphasis: {
          itemStyle: {
            color: "rgb(79 93 255 / 6%)",
          },
        },
        label: { show: false },
        z: 10,
      },
    ],
  };
};

const handleChartClick = (parameters: CallbackDataParams): void => {
  const item =
    parameters.componentType === "yAxis"
      ? props.items.find((candidate) => candidate.label === String(parameters.value))
      : props.items[parameters.dataIndex];
  if (item?.link !== undefined) void router.push(item.link);
};

const { chartElement, loadError, refresh } = useResponsiveEChart({
  height: chartHeight,
  option: chartOption,
  onClick: handleChartClick,
  pointerCursor: (parameters) =>
    parameters.componentType === "yAxis" &&
    props.items.some(
      (item) =>
        item.label === String(parameters.value) && item.link !== undefined,
    ),
});

watch(
  () => [
    chartElement.value,
    props.items,
    props.directionLabel,
    props.color,
    props.valueFormat,
  ] as const,
  refresh,
  { deep: true },
);
</script>

<template>
  <figure class="metric-chart" :class="`metric-chart--${color}`">
    <figcaption>
      <span>{{ directionLabel }}</span>
      <small><i aria-hidden="true"></i>Select a model row to view its full run</small>
    </figcaption>
    <ChartLoadNotice v-if="loadError" />
    <div
      ref="chartElement"
      class="metric-chart-canvas"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ol class="visually-hidden" aria-label="Chart data and model detail links">
      <li v-for="(item, index) in items" :key="item.label">
        {{ index + 1 }}. {{ item.label }}: {{ item.display }}.
        <span v-if="item.detail">{{ item.detail }}.</span>
        <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
          View full run for {{ item.label }}
        </RouterLink>
      </li>
    </ol>
  </figure>
</template>

<style scoped>
.metric-chart {
  margin: 0;
  padding: clamp(1.2rem, 3vw, 2.5rem);
  background:
    linear-gradient(rgb(17 19 28 / 2%) 1px, transparent 1px) 0 0 / 100% 48px,
    var(--paper-bright);
}

figcaption {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.3rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

figcaption small {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.04em;
}

figcaption i {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--blue);
}

.metric-chart--acid figcaption i {
  background: var(--chart-acid);
}

.metric-chart--coral figcaption i {
  background: var(--coral);
}

.metric-chart--efficiency figcaption i {
  background: var(--result-efficiency);
}

.metric-chart-canvas {
  width: 100%;
  min-width: 0;
}

@media (max-width: 620px) {
  .metric-chart {
    padding: 1rem 0.75rem 1.1rem;
  }

  figcaption {
    align-items: flex-start;
    padding-inline: 0.25rem;
  }

  figcaption small {
    display: none;
  }
}
</style>
