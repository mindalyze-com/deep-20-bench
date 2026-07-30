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
  chartValueDomain,
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
    color?: "blue" | "acid" | "coral";
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

const colors = {
  blue: "#4e64ff",
  acid: "#8cad12",
  coral: "#ef5435",
} as const;

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
  const detail =
    item.detail === undefined
      ? ""
      : `<span style="display:block;margin-top:5px;color:#5f626a;font-size:.72rem;line-height:1.45">${escapeHtml(item.detail)}</span>`;
  return [
    '<div style="min-width:180px;max-width:280px;padding:3px 2px">',
    `<strong style="display:block;color:#11131c;font-size:.82rem;line-height:1.35">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:#11131c;font-family:Iowan Old Style,Palatino Linotype,Georgia,serif;font-size:1.55rem;line-height:1">${escapeHtml(item.display)}</span>`,
    detail,
    item.link === undefined
      ? ""
      : '<span style="display:block;margin-top:9px;color:#2539bd;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase">View full run →</span>',
    "</div>",
  ].join("");
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const color = colors[props.color];
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const valueFontSize = chartTextSize(width, 11, 14);
  const domain = chartValueDomain(props.items.map((item) => item.value));
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    animationEasing: "cubicOut",
    aria: {
      enabled: true,
      description: `${props.directionLabel}. ${props.items
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
      scale: true,
      min: domain.minimum,
      max: domain.maximum,
      splitNumber: mobile ? 3 : 5,
      axisLine: {
        show: true,
        lineStyle: { color: "#a8a69f", width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: "#6d7078",
        fontFamily: chartFont,
        fontSize: axisFontSize,
        margin: 10,
        formatter: axisValue,
      },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(17,19,28,.10)", width: 1 },
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
        color: "#252833",
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        fontWeight: 650,
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
          color: "#11131c",
          fontFamily: chartDisplayFont,
          fontSize: valueFontSize,
          fontWeight: 600,
          formatter: (parameters: CallbackDataParams): string =>
            props.items[parameters.dataIndex]?.display ?? "",
        },
        emphasis: {
          itemStyle: {
            opacity: 1,
            shadowBlur: 10,
            shadowColor: "rgba(17,19,28,.18)",
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
        data: props.items.map(() => domain.maximum),
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

const handleChartClick = (parameters: CallbackDataParams): void => {
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
  font-weight: 760;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

figcaption small {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-micro);
  font-weight: 700;
  letter-spacing: 0.04em;
}

figcaption i {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--blue);
}

.metric-chart--acid figcaption i {
  background: #8cad12;
}

.metric-chart--coral figcaption i {
  background: var(--coral);
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
