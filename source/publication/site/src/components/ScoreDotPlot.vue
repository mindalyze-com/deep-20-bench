<script setup lang="ts">
import { BarChart, CustomChart, ScatterChart } from "echarts/charts";
import {
  AriaComponent,
  GridComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  CustomSeriesRenderItem,
  ECElementEvent,
  EChartsOption,
} from "echarts";
import { SVGRenderer } from "echarts/renderers";
import { computed, ref, useId, watch } from "vue";
import { useRouter, type RouteLocationRaw } from "vue-router";

import { chartTooltipStyle, readChartTheme } from "@/lib/chart-theme";
import type { PublicRepeatAverage } from "@/lib/types";
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
  CustomChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  AriaComponent,
  SVGRenderer,
]);

export interface ScoreDot {
  modelId: string;
  label: string;
  value: number;
  display: string;
  confidenceLower?: number;
  confidenceUpper?: number;
  confidenceDisplay?: string;
  detail?: string;
  link?: RouteLocationRaw;
}

interface RepeatAverageGroup {
  modelId: string;
  label: string;
  value: number;
  averages: PublicRepeatAverage[];
}

const props = withDefaults(
  defineProps<{
    items: ScoreDot[];
    repeatAverages?: PublicRepeatAverage[] | null;
    repeatAveragesLoading?: boolean;
    repeatAveragesError?: string | null;
  }>(),
  {
    repeatAverages: null,
    repeatAveragesLoading: false,
    repeatAveragesError: null,
  },
);

const emit = defineEmits<{
  requestRepeatAverages: [];
}>();

const router = useRouter();
const showRepeatAverages = ref(false);
// The repeat-average overlay remains implemented but is intentionally not exposed for now.
const repeatAverageControlEnabled = false;
const repeatSwitchId = `repeat-average-switch-${useId()}`;
const chartHeight = computed(() =>
  Math.max(410, props.items.length * 43 + 82),
);
const summaryScoreValues = computed(() =>
  props.items
    .flatMap((item) => [
      item.value,
      item.confidenceLower ?? item.value,
      item.confidenceUpper ?? item.value,
    ])
    .filter((value) => Number.isFinite(value)),
);
const repeatAverageGroups = computed<RepeatAverageGroup[]>(() => {
  if (props.repeatAverages === null) return [];
  const itemsByModel = new Map(props.items.map((item) => [item.modelId, item]));
  const groups = new Map<string, RepeatAverageGroup>();
  for (const average of props.repeatAverages) {
    const item = itemsByModel.get(average.model_id);
    if (item === undefined) continue;
    const value = Number(average.average_questions);
    if (!Number.isFinite(value)) continue;
    const key = `${average.model_id}\u0000${average.average_questions}`;
    const existing = groups.get(key);
    if (existing === undefined) {
      groups.set(key, {
        modelId: average.model_id,
        label: item.label,
        value,
        averages: [average],
      });
    } else {
      existing.averages.push(average);
    }
  }
  const itemOrder = new Map(props.items.map((item, index) => [item.modelId, index]));
  return [...groups.values()]
    .map((group) => ({
      ...group,
      averages: [...group.averages].sort(
        (left, right) => left.trial_number - right.trial_number,
      ),
    }))
    .sort(
      (left, right) =>
        (itemOrder.get(left.modelId) ?? Number.MAX_SAFE_INTEGER) -
          (itemOrder.get(right.modelId) ?? Number.MAX_SAFE_INTEGER) ||
        left.value - right.value,
    );
});
const scoreDomain = computed(() =>
  chartValueDomain([
    ...summaryScoreValues.value,
    ...(showRepeatAverages.value
      ? repeatAverageGroups.value.map((group) => group.value)
      : []),
  ]),
);
const repeatCountLabel = computed(() => {
  if (props.repeatAveragesLoading) return "Loading repeat averages…";
  if (props.repeatAverages === null) return "Five cohort-wide repeats";
  const counts = new Map<string, number>();
  for (const average of props.repeatAverages) {
    counts.set(average.model_id, (counts.get(average.model_id) ?? 0) + 1);
  }
  const values = [...counts.values()];
  return values.length > 0 && values.every((value) => value === values[0])
    ? `${values[0]} per model`
    : `${props.repeatAverages.length} total`;
});

const handleRepeatToggle = (event: Event): void => {
  const target = event.currentTarget;
  if (!(target instanceof HTMLInputElement)) return;
  showRepeatAverages.value = target.checked;
  if (target.checked && props.repeatAverages === null) {
    emit("requestRepeatAverages");
  }
};

const summaryTooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item =
    parameter === undefined ? undefined : props.items[parameter.dataIndex];
  if (item === undefined) return "";
  const theme = readChartTheme();
  const confidence =
    item.confidenceDisplay === undefined
      ? ""
      : `<span style="display:block;margin-top:7px;color:${theme.muted};font-size:.78rem;font-weight:620">95% CI of average ${escapeHtml(item.confidenceDisplay)} questions</span>`;
  const detail =
    item.detail === undefined
      ? ""
      : `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">${escapeHtml(item.detail)}</span>`;
  return [
    '<div style="min-width:180px;padding:3px 2px">',
    `<strong style="display:block;color:${theme.ink};font:700 .82rem/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.55rem">${escapeHtml(item.display)} questions</span>`,
    confidence,
    detail,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">Lower is better</span>`,
    item.link === undefined
      ? ""
      : `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight:700;text-transform:uppercase">View full run →</span>`,
    "</div>",
  ].join("");
};

const repeatNumbers = (averages: PublicRepeatAverage[]): string => {
  const values = averages.map((average) => average.trial_number);
  if (values.length === 1) return `Repeat ${values[0]}`;
  if (values.length === 2) return `Repeats ${values[0]} and ${values[1]}`;
  return `Repeats ${values.slice(0, -1).join(", ")}, and ${values.at(-1)}`;
};

const repeatTooltip = (parameter: CallbackDataParams): string => {
  const group = repeatAverageGroups.value[parameter.dataIndex];
  if (group === undefined) return "";
  const theme = readChartTheme();
  const subjectCount = group.averages[0]?.subject_count ?? 0;
  const successful = group.averages.reduce(
    (total, average) => total + average.successful,
    0,
  );
  const modelFailed = group.averages.reduce(
    (total, average) => total + average.model_failed,
    0,
  );
  const total = successful + modelFailed;
  const cohort =
    group.averages.length === 1
      ? `${subjectCount} subjects`
      : `${subjectCount} subjects each`;
  const outcomes =
    modelFailed === 0
      ? `${successful}/${total} successful subject trials`
      : `${successful} successful · ${modelFailed} model failures`;
  return [
    '<div style="min-width:205px;padding:3px 2px">',
    `<strong style="display:block;color:${theme.ink};font:700 .82rem/1.35 ${chartFont}">${escapeHtml(group.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.55rem">${group.value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} questions</span>`,
    `<span style="display:block;margin-top:6px;color:${theme.inkSoft};font-size:.78rem;font-weight:650">${escapeHtml(repeatNumbers(group.averages))} · ${cohort}</span>`,
    `<span style="display:block;margin-top:4px;color:${theme.muted};font-size:.75rem">${escapeHtml(outcomes)}</span>`,
    `<span style="display:block;margin-top:7px;color:${theme.muted};font-size:.75rem">Average of the same trial number across the fixed subject cohort</span>`,
    `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight:700;text-transform:uppercase">View full run →</span>`,
    "</div>",
  ].join("");
};

const tooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  return parameter?.seriesName === "Repeat averages"
    ? repeatTooltip(parameter)
    : summaryTooltip(parameters);
};

const chartOption = (width: number): EChartsOption => {
  const mobile = width < 620;
  const theme = readChartTheme();
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const valueFontSize = chartTextSize(width, 11, 14);
  const renderConfidenceInterval: CustomSeriesRenderItem = (_parameters, api) => {
    const categoryIndex = Number(api.value(2));
    const lower = api.coord([Number(api.value(0)), categoryIndex]);
    const upper = api.coord([Number(api.value(1)), categoryIndex]);
    const lowerX = lower[0] ?? 0;
    const lowerY = lower[1] ?? 0;
    const upperX = upper[0] ?? 0;
    const upperY = upper[1] ?? 0;
    const cap = mobile ? 5 : 6;
    return {
      type: "group",
      children: [
        {
          type: "line",
          shape: { x1: lowerX, y1: lowerY, x2: upperX, y2: upperY },
          style: { stroke: theme.roles.guesser, lineWidth: 2, opacity: 0.55 },
        },
        {
          type: "line",
          shape: { x1: lowerX, y1: lowerY - cap, x2: lowerX, y2: lowerY + cap },
          style: { stroke: theme.roles.guesser, lineWidth: 1.5, opacity: 0.55 },
        },
        {
          type: "line",
          shape: { x1: upperX, y1: upperY - cap, x2: upperX, y2: upperY + cap },
          style: { stroke: theme.roles.guesser, lineWidth: 1.5, opacity: 0.55 },
        },
      ],
    };
  };
  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    animationEasing: "cubicOut",
    aria: {
      enabled: true,
      description: `Official question scores. Each solid blue marker is the average question score, where lower is better. Each blue line is the 95 percent confidence interval of that average.${showRepeatAverages.value ? " Grey diamonds show averages for each trial number across the fixed subject cohort; darker diamonds indicate equal repeat averages." : ""} The horizontal axis runs from ${scoreDomain.value.minimum} to ${scoreDomain.value.maximum}. ${props.items
        .map(
          (item, index) =>
            `${index + 1}. ${item.label}, ${item.display}${
              item.confidenceDisplay === undefined
                ? ""
                : `, 95 percent confidence interval ${item.confidenceDisplay}`
            }`,
        )
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
        color: theme.inkSoft,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        fontWeight: 760,
      },
      axisLine: {
        show: true,
        lineStyle: { color: theme.borderStrong, width: 1 },
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
        color: theme.ink,
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        fontWeight: 700,
        width: mobile ? 112 : 194,
        overflow: "truncate",
        ellipsis: "…",
        margin: mobile ? 12 : 18,
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine, width: 1 },
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
        z: 1,
      },
      ...(showRepeatAverages.value
        ? [
            {
              name: "Repeat averages",
              type: "scatter" as const,
              data: repeatAverageGroups.value.map((group) => ({
                name: `${group.label}: ${group.value}`,
                value: [group.value, group.label],
                itemStyle: {
                  color: theme.muted,
                  opacity: 1 - (1 - 0.22) ** group.averages.length,
                },
              })),
              symbol: "diamond",
              symbolOffset: [0, 13],
              symbolSize: mobile ? 10 : 9,
              cursor: "pointer",
              emphasis: {
                scale: 1.45,
                itemStyle: {
                  borderColor: theme.ink,
                  borderWidth: 1,
                },
              },
              z: 2,
            },
          ]
        : []),
      {
        name: "95% CI of average",
        type: "custom",
        renderItem: renderConfidenceInterval,
        encode: { x: [0, 1], y: 2 },
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        data: props.items.map((item, index) => [
          item.confidenceLower ?? item.value,
          item.confidenceUpper ?? item.value,
          index,
        ]),
        z: 3,
      },
      {
        name: "Question score",
        type: "scatter",
        data: props.items.map((item) => ({
          name: item.label,
          value: [item.value, item.label],
        })),
        symbolSize: mobile ? 17 : 19,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        itemStyle: {
          color: theme.roles.guesser,
          borderColor: theme.surface,
          borderWidth: 3,
        },
        label: {
          show: true,
          position: "top",
          distance: mobile ? 5 : 6,
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
            borderColor: theme.ink,
            shadowBlur: 8,
            shadowColor: theme.gridLine,
          },
        },
        z: 4,
      },
    ],
  };
};

const handleClick = (parameters: ECElementEvent): void => {
  const item =
    parameters.seriesName === "Repeat averages"
      ? props.items.find(
          (candidate) =>
            candidate.modelId ===
            repeatAverageGroups.value[parameters.dataIndex]?.modelId,
        )
      : parameters.componentType === "yAxis"
        ? props.items.find(
            (candidate) => candidate.label === String(parameters.value),
          )
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
watch(
  () =>
    [
      props.repeatAverages,
      props.repeatAveragesLoading,
      showRepeatAverages.value,
    ] as const,
  refresh,
  { deep: true },
);
watch(
  () => props.repeatAveragesError,
  (error) => {
    if (error !== null) showRepeatAverages.value = false;
  },
);
</script>

<template>
  <figure class="score-dot-plot">
    <figcaption class="score-dot-plot-caption">
      <span class="score-dot-plot-legend">
        <span class="score-dot-plot-legend-item score-dot-plot-legend-item--primary">
          <i class="score-dot-plot-legend-marker" aria-hidden="true"></i>
          <strong>Question score</strong>
          <small>lower is better</small>
        </span>
        <span class="score-dot-plot-legend-item">
          <i class="score-dot-plot-legend-interval" aria-hidden="true"></i>
          <span>95% CI of average</span>
        </span>
        <span v-if="showRepeatAverages" class="score-dot-plot-legend-item">
          <span>Grey diamond: repeat average</span>
        </span>
      </span>
      <label
        v-if="repeatAverageControlEnabled"
        class="repeat-average-switch"
        :for="repeatSwitchId"
      >
        <span class="repeat-average-switch-copy">
          <strong>Show repeat averages</strong>
          <small :id="`${repeatSwitchId}-description`">{{ repeatCountLabel }}</small>
        </span>
        <input
          :id="repeatSwitchId"
          type="checkbox"
          role="switch"
          :checked="showRepeatAverages"
          :disabled="repeatAveragesLoading"
          :aria-describedby="`${repeatSwitchId}-description`"
          @change="handleRepeatToggle"
        />
        <span class="repeat-average-switch-track" aria-hidden="true">
          <span></span>
        </span>
      </label>
    </figcaption>
    <p v-if="repeatAveragesError !== null" class="repeat-average-error" role="alert">
      {{ repeatAveragesError }}
    </p>
    <div
      ref="chartElement"
      class="score-dot-plot-canvas"
      tabindex="0"
      :style="{ height: `${chartHeight}px` }"
    ></div>
    <ol class="visually-hidden" aria-label="Official question scores">
      <li v-for="(item, index) in items" :key="item.label">
        {{ index + 1 }}. {{ item.label }}: {{ item.display }} questions.
        <span v-if="item.confidenceDisplay">
          95% confidence interval of the average: {{ item.confidenceDisplay }} questions.
        </span>
        <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
          View full run for {{ item.label }}
        </RouterLink>
      </li>
    </ol>
    <ol
      v-if="showRepeatAverages"
      class="visually-hidden"
      aria-label="Repeat averages"
    >
      <li
        v-for="average in repeatAverages ?? []"
        :key="`${average.execution_id}-${average.trial_number}`"
      >
        {{ items.find((item) => item.modelId === average.model_id)?.label }},
        repeat {{ average.trial_number }}: {{ average.average_questions }} questions,
        averaged across {{ average.subject_count }} subjects.
      </li>
    </ol>
  </figure>
</template>

<style scoped>
.score-dot-plot {
  width: 100%;
  min-width: 0;
  margin: 0;
  overflow: hidden;
}

.score-dot-plot-caption {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  min-height: 44px;
  margin: 0;
  padding: 0.55rem 0.5rem 0;
  color: var(--muted);
  font-size: var(--text-micro);
  line-height: 1.4;
}

.score-dot-plot-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 1.1rem;
  align-items: center;
  min-width: 0;
}

.score-dot-plot-legend-item {
  display: inline-flex;
  gap: 0.42rem;
  align-items: center;
  min-height: 1.5rem;
}

.score-dot-plot-legend-item--primary strong {
  color: var(--text-primary);
  font-size: var(--text-small);
  font-weight: 760;
}

.score-dot-plot-legend-item small {
  color: var(--muted);
  font-size: var(--text-micro);
}

.score-dot-plot-legend-marker {
  width: 0.72rem;
  height: 0.72rem;
  border: 2px solid var(--paper-bright);
  border-radius: 50%;
  background: var(--blue);
  box-shadow: 0 0 0 1px var(--blue);
}

.score-dot-plot-legend-interval {
  width: 1.45rem;
  height: 1px;
  background: var(--blue);
  opacity: 0.55;
}

.repeat-average-switch {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
  gap: 0.7rem;
  align-items: center;
  justify-content: flex-end;
  min-height: 44px;
  color: var(--ink);
  cursor: pointer;
}

.repeat-average-switch-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.25;
}

.repeat-average-switch-copy strong {
  font-size: var(--text-small);
  font-weight: 720;
}

.repeat-average-switch-copy small {
  margin-top: 0.1rem;
  color: var(--muted);
  font-size: var(--text-micro);
}

.repeat-average-switch input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.repeat-average-switch-track {
  display: flex;
  width: 2.7rem;
  height: 1.55rem;
  padding: 0.18rem;
  border: var(--rule-default);
  border-radius: 999px;
  background: var(--paper);
  transition:
    border-color 150ms ease,
    background 150ms ease;
}

.repeat-average-switch-track span {
  width: 1.05rem;
  height: 1.05rem;
  border-radius: 50%;
  background: var(--muted);
  transition:
    background 150ms ease,
    transform 150ms ease;
}

.repeat-average-switch input:checked + .repeat-average-switch-track {
  border-color: var(--blue);
  background: color-mix(in srgb, var(--blue) 18%, var(--paper-bright));
}

.repeat-average-switch input:checked + .repeat-average-switch-track span {
  background: var(--blue);
  transform: translateX(1.15rem);
}

.repeat-average-switch input:focus-visible + .repeat-average-switch-track {
  outline: 2px solid var(--blue);
  outline-offset: 3px;
}

.repeat-average-switch:has(input:disabled) {
  cursor: wait;
  opacity: 0.68;
}

.repeat-average-error {
  margin: 0.25rem 0.5rem 0;
  color: var(--coral);
  font-size: var(--text-small);
  text-align: right;
}

.score-dot-plot-canvas {
  width: 100%;
  min-width: 0;
}

.score-dot-plot-canvas:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: -2px;
}

@media (prefers-reduced-motion: reduce) {
  .repeat-average-switch-track,
  .repeat-average-switch-track span {
    transition: none;
  }
}

@media (max-width: 620px) {
  .score-dot-plot-caption {
    align-items: stretch;
    padding-top: 0.7rem;
    flex-direction: column;
  }

  .repeat-average-switch {
    justify-content: space-between;
    padding-top: 0.4rem;
    border-top: var(--rule-subtle);
  }

  .repeat-average-switch-copy {
    align-items: flex-start;
  }

  .repeat-average-error {
    text-align: left;
  }
}
</style>
