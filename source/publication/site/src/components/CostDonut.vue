<script setup lang="ts">
import { PieChart } from "echarts/charts";
import {
  AriaComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  EChartsOption,
} from "echarts";
import { SVGRenderer } from "echarts/renderers";
import { computed, watch } from "vue";

import {
  chartAnimationEnabled,
  chartFont,
  escapeHtml,
  useResponsiveEChart,
} from "@/lib/use-responsive-echart";

echarts.use([PieChart, TooltipComponent, AriaComponent, SVGRenderer]);

export interface CostDonutItem {
  label: string;
  value: number;
  display: string;
  color: string;
  primary?: boolean;
}

const props = withDefaults(
  defineProps<{
    items: CostDonutItem[];
    totalDisplay: string;
    caption?: string;
  }>(),
  {
    caption: "Share of full-run cost",
  },
);

const chartHeight = computed(() => 242);
const total = computed(() =>
  props.items.reduce((sum, item) => sum + item.value, 0),
);
const share = (value: number): string =>
  total.value <= 0
    ? "0%"
    : `${((value / total.value) * 100).toLocaleString("en-US", {
        maximumFractionDigits: 1,
      })}%`;

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item =
    parameter === undefined ? undefined : props.items[parameter.dataIndex];
  if (item === undefined) return "";
  return [
    '<div style="min-width:150px;padding:2px">',
    `<strong style="display:block;color:#11131c;font:700 12px/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:7px;color:#11131c;font-size:1.3rem">${escapeHtml(item.display)}</span>`,
    `<span style="display:block;margin-top:4px;color:#5f626a;font-size:.72rem">${share(item.value)} of full-run cost</span>`,
    "</div>",
  ].join("");
};

const chartOption = (): EChartsOption => ({
  animation: chartAnimationEnabled(),
  animationDuration: 420,
  animationEasing: "cubicOut",
  aria: {
    enabled: true,
    description: `${props.caption}. ${props.items
      .map((item) => `${item.label}, ${item.display}, ${share(item.value)}`)
      .join(". ")}.`,
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
  series: [
    {
      name: props.caption,
      type: "pie",
      radius: ["58%", "83%"],
      center: ["50%", "50%"],
      startAngle: 90,
      minAngle: 2,
      avoidLabelOverlap: true,
      itemStyle: {
        borderColor: "#fbfaf6",
        borderWidth: 3,
      },
      label: { show: false },
      labelLine: { show: false },
      emphasis: {
        scale: true,
        scaleSize: 5,
      },
      data: props.items.map((item) => ({
        name: item.label,
        value: item.value,
        itemStyle: { color: item.color },
      })),
    },
  ],
});

const { chartElement, refresh } = useResponsiveEChart({
  height: chartHeight,
  initialize: (element) =>
    echarts.init(element, undefined, { renderer: "svg" }),
  option: chartOption,
});

watch(
  () =>
    [
      chartElement.value,
      props.items,
      props.totalDisplay,
      props.caption,
    ] as const,
  refresh,
  { deep: true },
);
</script>

<template>
  <figure class="cost-donut">
    <figcaption>
      <strong>Cost composition.</strong>
      <span>{{ caption }}</span>
    </figcaption>
    <div class="cost-donut-layout">
      <div class="cost-donut-plot">
        <div
          ref="chartElement"
          class="cost-donut-canvas"
          :style="{ height: `${chartHeight}px` }"
        ></div>
        <div class="cost-donut-total" aria-hidden="true">
          <span>Full run</span>
          <strong>{{ totalDisplay }}</strong>
        </div>
      </div>
      <ol aria-label="Full-run cost by role">
        <li
          v-for="item in items"
          :key="item.label"
          :class="{ primary: item.primary }"
        >
          <i :style="{ background: item.color }" aria-hidden="true"></i>
          <span>{{ item.label }}</span>
          <small>{{ share(item.value) }}</small>
          <strong>{{ item.display }}</strong>
        </li>
      </ol>
    </div>
  </figure>
</template>

<style scoped>
.cost-donut {
  margin: 0;
  container-type: inline-size;
}

figcaption {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  margin-bottom: 0.7rem;
}

figcaption strong {
  font-size: var(--text-small);
}

figcaption span {
  color: var(--muted);
  font-size: var(--text-micro);
}

.cost-donut-layout {
  display: grid;
  grid-template-columns: minmax(9rem, 0.85fr) minmax(0, 1.15fr);
  gap: 1rem;
  align-items: center;
}

.cost-donut-plot {
  position: relative;
  min-width: 0;
}

.cost-donut-canvas {
  width: 100%;
}

.cost-donut-total {
  position: absolute;
  inset: 50% auto auto 50%;
  display: grid;
  width: 7rem;
  text-align: center;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.cost-donut-total span {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 760;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.cost-donut-total strong {
  margin-top: 0.35rem;
  font-family: var(--font-display);
  font-size: 1.55rem;
  font-weight: 600;
  letter-spacing: -0.04em;
}

ol {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}

li {
  display: grid;
  grid-template-columns: 0.55rem minmax(0, 1fr) auto auto;
  gap: 0.6rem;
  align-items: center;
  min-height: 2.3rem;
  border-bottom: 1px solid var(--line-soft);
  font-size: var(--text-small);
}

li:last-child {
  border-bottom: 0;
}

li i {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
}

li > span {
  color: var(--muted);
}

li.primary > span,
li.primary > strong {
  color: var(--ink);
  font-weight: 760;
}

li small {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

li strong {
  min-width: 4.6rem;
  text-align: right;
  font-size: var(--text-small);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 620px) {
  .cost-donut-layout {
    grid-template-columns: 1fr;
    gap: 0.2rem;
  }

  .cost-donut-plot {
    width: min(100%, 18rem);
    margin-inline: auto;
  }

  figcaption {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.25rem;
  }

  li {
    min-height: 2.55rem;
    font-size: var(--text-small);
  }
}

@container (max-width: 22rem) {
  .cost-donut-layout {
    grid-template-columns: 1fr;
    gap: 0.2rem;
  }

  .cost-donut-plot {
    width: min(100%, 18rem);
    margin-inline: auto;
  }
}
</style>
