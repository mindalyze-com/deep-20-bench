<script setup lang="ts">
import { BarChart, CustomChart, ScatterChart } from "echarts/charts";
import {
  AriaComponent,
  GridComponent,
  MarkAreaComponent,
  MarkLineComponent,
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

import {
  chartTooltipStyle,
  readChartTheme,
  type ChartTheme,
} from "@/lib/chart-theme";
import {
  confidenceIntervalWidth,
  confidenceWidthScale,
  type ConfidenceWidthBand,
} from "@/lib/confidence-width";
import { number } from "@/lib/format";
import type { PublicRepeatAverage } from "@/lib/types";
import {
  chartAnimationEnabled,
  chartDisplayFont,
  chartFont,
  chartFontWeightSemibold,
  chartFontWeightBold,
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
  MarkAreaComponent,
  MarkLineComponent,
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

interface ConfidenceWidthDetail {
  width: number;
  display: string;
  band: ConfidenceWidthBand | null;
}

interface ModelAxisLabel {
  name: string;
  effort: string | null;
}

const confidenceBandLegend: readonly {
  band: ConfidenceWidthBand;
  label: string;
}[] = [
  { band: "tight", label: "Tighter" },
  { band: "middle", label: "Middle" },
  { band: "wide", label: "Wider" },
];

const confidenceBandColor = (
  theme: ChartTheme,
  band: ConfidenceWidthBand | null,
): string =>
  band === null ? theme.confidenceWidth.neutral : theme.confidenceWidth[band];

const confidenceBandFill = (
  theme: ChartTheme,
  band: ConfidenceWidthBand,
): string =>
  band === "tight"
    ? theme.confidenceWidth.tightFill
    : band === "middle"
      ? theme.confidenceWidth.middleFill
      : theme.confidenceWidth.wideFill;

const confidenceBandLongLabel = (
  band: ConfidenceWidthBand | null,
): string =>
  band === null
    ? "not grouped"
    : band === "tight"
      ? "tighter band"
      : band === "middle"
        ? "middle band"
        : "wider band";

const splitModelAxisLabel = (label: string): ModelAxisLabel => {
  const match = /^(.*)\s+\((high|medium|low|non-thinking)\)$/i.exec(label);
  return match === null
    ? { name: label, effort: null }
    : { name: match[1] ?? label, effort: match[2]?.toLowerCase() ?? null };
};

const formatModelAxisLabel = (label: string, stacked: boolean): string => {
  if (!stacked) return `{model|${label}}`;
  const parts = splitModelAxisLabel(label);
  const name =
    parts.name.length <= 19
      ? parts.name
      : `${parts.name.slice(0, 18).trimEnd()}…`;
  return parts.effort === null
    ? `{model|${name}}`
    : `{model|${name}}\n{effort|${parts.effort}}`;
};

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
  Math.max(430, props.items.length * 52 + 88),
);
const confidenceObservations = computed(() =>
  props.items.flatMap((item) => {
    if (
      item.confidenceLower === undefined ||
      item.confidenceUpper === undefined
    ) {
      return [];
    }
    const width = confidenceIntervalWidth(
      item.confidenceLower,
      item.confidenceUpper,
    );
    return width === null ? [] : [{ key: item.modelId, width }];
  }),
);
const confidenceScale = computed(() =>
  confidenceWidthScale(confidenceObservations.value),
);
const confidenceDetails = computed<ReadonlyMap<string, ConfidenceWidthDetail>>(() => {
  const bands = confidenceScale.value.bands;
  return new Map(
    confidenceObservations.value.map((observation) => [
      observation.key,
      {
        width: observation.width,
        display: number(observation.width, 2),
        band: bands.get(observation.key) ?? null,
      },
    ]),
  );
});

const confidenceDetailFor = (
  item: ScoreDot,
): ConfidenceWidthDetail | undefined => confidenceDetails.value.get(item.modelId);

const bestScoreModelIds = computed<ReadonlySet<string>>(() => {
  const finiteItems = props.items.filter((item) => Number.isFinite(item.value));
  const bestValue = Math.min(...finiteItems.map((item) => item.value));
  return new Set(
    finiteItems
      .filter((item) => item.value === bestValue)
      .map((item) => item.modelId),
  );
});

const tightestConfidenceModelIds = computed<ReadonlySet<string>>(() => {
  const details = [...confidenceDetails.value.entries()];
  const tightestWidth = Math.min(...details.map(([, detail]) => detail.width));
  return new Set(
    details
      .filter(([, detail]) => detail.width === tightestWidth)
      .map(([modelId]) => modelId),
  );
});

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

const summaryTooltipForItem = (item: ScoreDot): string => {
  const theme = readChartTheme();
  const confidence =
    item.confidenceDisplay === undefined
      ? ""
      : `<span style="display:block;margin-top:7px;color:${theme.muted};font-size:.78rem;font-weight: var(--font-weight-semibold)">95% CI of average ${escapeHtml(item.confidenceDisplay)} questions</span>`;
  const confidenceWidth = confidenceDetailFor(item);
  const width =
    confidenceWidth === undefined
      ? ""
      : `<span style="display:block;margin-top:5px;color:${confidenceBandColor(theme, confidenceWidth.band)};font-size:.78rem;font-weight: var(--font-weight-bold)">CI width ${escapeHtml(confidenceWidth.display)} questions · ${escapeHtml(confidenceBandLongLabel(confidenceWidth.band))} on the displayed scale</span>`;
  const detail =
    item.detail === undefined
      ? ""
      : `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">${escapeHtml(item.detail)}</span>`;
  return [
    '<div style="min-width:180px;padding:3px 2px">',
    `<strong style="display:block;color:${theme.ink};font: var(--font-weight-bold) .82rem/1.35 ${chartFont}">${escapeHtml(item.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.55rem">${escapeHtml(item.display)} questions</span>`,
    confidence,
    width,
    detail,
    `<span style="display:block;margin-top:5px;color:${theme.muted};font-size:.75rem">Lower is better</span>`,
    item.link === undefined
      ? ""
      : `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight: var(--font-weight-bold);text-transform:uppercase">View full run →</span>`,
    "</div>",
  ].join("");
};

const summaryTooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item =
    parameter === undefined ? undefined : props.items[parameter.dataIndex];
  return item === undefined ? "" : summaryTooltipForItem(item);
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
    `<strong style="display:block;color:${theme.ink};font: var(--font-weight-bold) .82rem/1.35 ${chartFont}">${escapeHtml(group.label)}</strong>`,
    `<span style="display:block;margin-top:8px;color:${theme.ink};font-family:${chartDisplayFont};font-size:1.55rem">${group.value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} questions</span>`,
    `<span style="display:block;margin-top:6px;color:${theme.inkSoft};font-size:.78rem;font-weight: var(--font-weight-semibold)">${escapeHtml(repeatNumbers(group.averages))} · ${cohort}</span>`,
    `<span style="display:block;margin-top:4px;color:${theme.muted};font-size:.75rem">${escapeHtml(outcomes)}</span>`,
    `<span style="display:block;margin-top:7px;color:${theme.muted};font-size:.75rem">Average of the same trial number across the fixed subject cohort</span>`,
    `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight: var(--font-weight-bold);text-transform:uppercase">View full run →</span>`,
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

const scoreChartOption = (width: number): EChartsOption => {
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
    const item = props.items[categoryIndex];
    const detail = item === undefined ? undefined : confidenceDetailFor(item);
    const stroke = confidenceBandColor(theme, detail?.band ?? null);
    return {
      type: "group",
      children: [
        {
          type: "line",
          shape: { x1: lowerX, y1: lowerY, x2: upperX, y2: upperY },
          style: { stroke, lineWidth: 2.6, opacity: 0.92 },
        },
        {
          type: "line",
          shape: { x1: lowerX, y1: lowerY - cap, x2: lowerX, y2: lowerY + cap },
          style: { stroke, lineWidth: 2, opacity: 0.92 },
        },
        {
          type: "line",
          shape: { x1: upperX, y1: upperY - cap, x2: upperX, y2: upperY + cap },
          style: { stroke, lineWidth: 2, opacity: 0.92 },
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
      description: `Official question scores. Each solid blue marker is the average question score, where lower is better. Each colored line is the 95 percent confidence interval of that average. Its color matches the three-band CI width companion plot.${showRepeatAverages.value ? " Grey diamonds show averages for each trial number across the fixed subject cohort; darker diamonds indicate equal repeat averages." : ""} The horizontal axis runs from ${scoreDomain.value.minimum} to ${scoreDomain.value.maximum}. ${props.items
        .map(
          (item, index) => {
            const detail = confidenceDetailFor(item);
            return `${index + 1}. ${item.label}, ${item.display}${
              item.confidenceDisplay === undefined
                ? ""
                : `, 95 percent confidence interval ${item.confidenceDisplay}`
            }${
              detail === undefined
                ? ""
                : `, width ${detail.display}, ${confidenceBandLongLabel(detail.band)}`
            }${bestScoreModelIds.value.has(item.modelId) ? ", best score" : ""}${
              tightestConfidenceModelIds.value.has(item.modelId)
                ? ", smallest CI width"
                : ""
            }`;
          },
        )
        .join(". ")}.`,
    },
    grid: {
      top: 18,
      right: mobile ? 32 : 76,
      bottom: 48,
      left: mobile ? 130 : 238,
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
        fontWeight: chartFontWeightBold,
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
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        width: mobile ? 110 : 212,
        overflow: "truncate",
        ellipsis: "…",
        margin: mobile ? 10 : 18,
        formatter: (value: string): string => formatModelAxisLabel(value, mobile),
        rich: {
          model: {
            color: theme.ink,
            fontFamily: chartFont,
            fontSize: categoryFontSize,
            fontWeight: chartFontWeightBold,
            lineHeight: mobile ? 13 : 16,
            width: mobile ? 110 : 212,
            align: "right",
          },
          effort: {
            color: theme.muted,
            fontFamily: chartFont,
            fontSize: Math.max(8, categoryFontSize - 2),
            fontWeight: chartFontWeightSemibold,
            lineHeight: 11,
            width: 110,
            align: "right",
          },
        },
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
          fontWeight: chartFontWeightSemibold,
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
      {
        name: "Score award",
        type: "scatter",
        silent: true,
        symbolSize: 0,
        data: props.items
          .filter((item) => bestScoreModelIds.value.has(item.modelId))
          .map((item) => [item.confidenceUpper ?? item.value, item.label]),
        label: {
          show: true,
          position: "right",
          distance: 10,
          formatter: "Best score",
          color: theme.inkSoft,
          backgroundColor: theme.surface,
          borderColor: theme.borderStrong,
          borderWidth: 1,
          borderRadius: 2,
          padding: [1, 4],
          fontFamily: chartFont,
          fontSize: 9,
          fontWeight: chartFontWeightBold,
        },
        tooltip: { show: false },
        z: 5,
      },
    ],
  };
};

const widthTooltip = (
  parameters: CallbackDataParams | CallbackDataParams[],
): string => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  const item = props.items.find(
    (candidate) => candidate.modelId === parameter?.name,
  );
  return item === undefined ? "" : summaryTooltipForItem(item);
};

const widthChartOption = (width: number): EChartsOption => {
  const stacked = window.matchMedia("(max-width: 780px)").matches;
  const theme = readChartTheme();
  const axisFontSize = chartTextSize(width, 10, 11);
  const categoryFontSize = chartTextSize(width, 10, 12);
  const maximum = confidenceScale.value.maximum;
  const lowerThreshold = confidenceScale.value.lowerThreshold;
  const upperThreshold = confidenceScale.value.upperThreshold;

  return {
    animation: chartAnimationEnabled(),
    animationDuration: 420,
    animationEasing: "cubicOut",
    aria: {
      enabled: true,
      description: `CI widths for the official question scores. This is the score-stability measure, and lower is better. The horizontal scale runs from zero to ${maximum} questions and is split into three equal visual bands. The bands are a guide, not fixed quality thresholds. ${props.items
        .map((item, index) => {
          const detail = confidenceDetailFor(item);
          return `${index + 1}. ${item.label}, ${
            detail === undefined
              ? "CI unavailable"
              : `${detail.display} questions, ${confidenceBandLongLabel(detail.band)}`
          }${
            tightestConfidenceModelIds.value.has(item.modelId)
              ? ", smallest CI width"
              : ""
          }`;
        })
        .join(". ")}.`,
    },
    grid: {
      top: 18,
      right: stacked ? 32 : 44,
      bottom: 48,
      left: stacked ? 130 : 14,
    },
    tooltip: {
      ...chartTooltipStyle(theme, 11),
      trigger: "item",
      confine: true,
      formatter: widthTooltip,
    },
    xAxis: {
      type: "value",
      min: 0,
      max: maximum,
      interval: maximum / 3,
      name: "CI width · tighter ←  → wider",
      nameLocation: "middle",
      nameGap: 33,
      nameTextStyle: {
        color: theme.inkSoft,
        fontFamily: chartFont,
        fontSize: axisFontSize,
        fontWeight: chartFontWeightBold,
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
      splitLine: { show: false },
    },
    yAxis: {
      type: "category",
      inverse: true,
      triggerEvent: stacked,
      data: props.items.map((item) => item.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        show: stacked,
        interval: 0,
        align: "right",
        fontFamily: chartFont,
        fontSize: categoryFontSize,
        width: 110,
        overflow: "truncate",
        ellipsis: "…",
        margin: 10,
        formatter: (value: string): string => formatModelAxisLabel(value, stacked),
        rich: {
          model: {
            color: theme.ink,
            fontFamily: chartFont,
            fontSize: categoryFontSize,
            fontWeight: chartFontWeightBold,
            lineHeight: 13,
            width: 110,
            align: "right",
          },
          effort: {
            color: theme.muted,
            fontFamily: chartFont,
            fontSize: Math.max(8, categoryFontSize - 2),
            fontWeight: chartFontWeightSemibold,
            lineHeight: 11,
            width: 110,
            align: "right",
          },
        },
      },
      splitLine: {
        show: true,
        lineStyle: { color: theme.gridLine, width: 1 },
      },
    },
    series: [
      {
        name: "CI width",
        type: "scatter",
        data: props.items.flatMap((item) => {
          const detail = confidenceDetailFor(item);
          if (detail === undefined) return [];
          return [
            {
              name: item.modelId,
              value: [detail.width, item.label],
              itemStyle: {
                color: confidenceBandColor(theme, detail.band),
                borderColor: theme.surface,
                borderWidth: 2,
              },
              label: {
                position: detail.width >= maximum * 0.78 ? "left" : "right",
              },
            },
          ];
        }),
        encode: { x: 0, y: 1 },
        symbolSize: stacked ? 15 : 16,
        cursor: props.items.some((item) => item.link !== undefined)
          ? "pointer"
          : "default",
        label: {
          show: true,
          distance: 7,
          color: theme.ink,
          fontFamily: chartDisplayFont,
          fontSize: chartTextSize(width, 11, 13),
          fontWeight: chartFontWeightSemibold,
          formatter: (parameters: CallbackDataParams): string => {
            const item = props.items.find(
              (candidate) => candidate.modelId === parameters.name,
            );
            if (item === undefined) return "";
            const display = confidenceDetailFor(item)?.display ?? "";
            return tightestConfidenceModelIds.value.has(item.modelId)
              ? `${display}    {award|Smallest CI width}`
              : display;
          },
          rich: {
            award: {
              color: theme.inkSoft,
              backgroundColor: theme.surface,
              borderColor: theme.borderStrong,
              borderWidth: 1,
              borderRadius: 2,
              padding: [1, 4],
              fontFamily: chartFont,
              fontSize: 9,
              fontWeight: chartFontWeightBold,
            },
          },
        },
        emphasis: {
          scale: 1.25,
          itemStyle: {
            borderColor: theme.ink,
            shadowBlur: 8,
            shadowColor: theme.gridLine,
          },
        },
        markArea: {
          silent: true,
          label: { show: false },
          data: [
            [
              {
                xAxis: 0,
                itemStyle: { color: confidenceBandFill(theme, "tight") },
              },
              { xAxis: lowerThreshold },
            ],
            [
              {
                xAxis: lowerThreshold,
                itemStyle: { color: confidenceBandFill(theme, "middle") },
              },
              { xAxis: upperThreshold },
            ],
            [
              {
                xAxis: upperThreshold,
                itemStyle: { color: confidenceBandFill(theme, "wide") },
              },
              { xAxis: maximum },
            ],
          ],
        },
        markLine: {
          silent: true,
          z: 2,
          symbol: "none",
          label: { show: false },
          lineStyle: {
            color: theme.border,
            type: "dashed",
            width: 1,
          },
          data: [{ xAxis: lowerThreshold }, { xAxis: upperThreshold }],
        },
        z: 3,
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

const handleWidthClick = (parameters: ECElementEvent): void => {
  const item =
    parameters.componentType === "yAxis"
      ? props.items.find(
          (candidate) => candidate.label === String(parameters.value),
        )
      : props.items.find((candidate) => candidate.modelId === parameters.name);
  if (item?.link !== undefined) void router.push(item.link);
};

const { chartElement: scoreChartElement, refresh: refreshScoreChart } =
  useResponsiveEChart({
    height: chartHeight,
    initialize: (element) =>
      echarts.init(element, undefined, { renderer: "svg" }),
    option: scoreChartOption,
    onClick: handleClick,
    pointerCursor: (parameters) =>
      parameters.componentType === "yAxis" &&
      props.items.some(
        (item) =>
          item.label === String(parameters.value) && item.link !== undefined,
      ),
  });

const { chartElement: widthChartElement, refresh: refreshWidthChart } =
  useResponsiveEChart({
    height: chartHeight,
    initialize: (element) =>
      echarts.init(element, undefined, { renderer: "svg" }),
    option: widthChartOption,
    onClick: handleWidthClick,
    pointerCursor: (parameters) =>
      parameters.componentType === "yAxis" &&
      props.items.some(
        (item) =>
          item.label === String(parameters.value) && item.link !== undefined,
      ),
  });

const refreshCharts = (): void => {
  refreshScoreChart();
  refreshWidthChart();
};

watch(
  () => [scoreChartElement.value, widthChartElement.value, props.items] as const,
  refreshCharts,
  {
    deep: true,
  },
);
watch(
  () =>
    [
      props.repeatAverages,
      props.repeatAveragesLoading,
      showRepeatAverages.value,
    ] as const,
  refreshCharts,
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
    <p v-if="repeatAveragesError !== null" class="repeat-average-error" role="alert">
      {{ repeatAveragesError }}
    </p>
    <div class="score-dot-plot-grid">
      <figcaption class="score-dot-plot-caption">
        <span class="score-dot-plot-legend">
          <span class="score-dot-plot-legend-item score-dot-plot-legend-item--primary">
            <i class="score-dot-plot-legend-marker" aria-hidden="true"></i>
            <strong>Question score</strong>
            <small>lower is better</small>
          </span>
          <span class="score-dot-plot-confidence-legend">
            <strong>95% CI · color = CI width</strong>
            <span
              v-for="entry in confidenceBandLegend"
              :key="entry.band"
              class="score-dot-plot-confidence-band"
            >
              <i :data-confidence-band="entry.band" aria-hidden="true"></i>
              <span>{{ entry.label }}</span>
            </span>
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
      <div class="confidence-width-caption">
        <strong>CI width <span aria-hidden="true">·</span> stability</strong>
        <small>lower is better</small>
      </div>
      <div
        ref="scoreChartElement"
        class="score-dot-plot-canvas score-dot-plot-canvas--score"
        tabindex="0"
        :style="{ height: `${chartHeight}px` }"
      ></div>
      <div
        ref="widthChartElement"
        class="score-dot-plot-canvas score-dot-plot-canvas--width"
        tabindex="0"
        :style="{ height: `${chartHeight}px` }"
      ></div>
    </div>
    <ol class="visually-hidden" aria-label="Official question scores">
      <li
        v-for="(item, index) in items"
        :key="item.label"
        :data-model-id="item.modelId"
        :data-confidence-band="confidenceDetailFor(item)?.band ?? 'neutral'"
      >
        {{ index + 1 }}. {{ item.label }}: {{ item.display }} questions.
        <span v-if="bestScoreModelIds.has(item.modelId)">Best score.</span>
        <span v-if="item.confidenceDisplay">
          95% confidence interval of the average: {{ item.confidenceDisplay }} questions.
        </span>
        <span v-if="confidenceDetailFor(item)">
          CI width: {{ confidenceDetailFor(item)?.display }} questions;
          {{ confidenceBandLongLabel(confidenceDetailFor(item)?.band ?? null) }} on the
          displayed scale.
        </span>
        <span v-if="tightestConfidenceModelIds.has(item.modelId)">
          Smallest CI width.
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

.score-dot-plot-grid {
  display: grid;
  grid-template-areas:
    "score-caption width-caption"
    "score-canvas width-canvas";
  grid-template-columns: minmax(0, 1.75fr) minmax(18rem, 0.85fr);
  grid-template-rows: auto auto;
  column-gap: 1.25rem;
  width: 100%;
  min-width: 0;
}

.score-dot-plot-caption {
  grid-area: score-caption;
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

.confidence-width-caption {
  display: flex;
  grid-area: width-caption;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0.55rem 0.5rem 0;
  color: var(--text-primary);
  line-height: 1.25;
  text-align: center;
}

.confidence-width-caption strong {
  font-size: var(--text-small);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.confidence-width-caption small {
  margin-top: 0.12rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-semibold);
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
  font-weight: var(--font-weight-bold);
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

.score-dot-plot-confidence-legend,
.score-dot-plot-confidence-band {
  display: inline-flex;
  align-items: center;
}

.score-dot-plot-confidence-legend {
  flex-wrap: wrap;
  gap: 0.35rem 0.75rem;
}

.score-dot-plot-confidence-legend > strong {
  color: var(--text-primary);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
}

.score-dot-plot-confidence-band {
  gap: 0.32rem;
  text-transform: capitalize;
}

.score-dot-plot-confidence-band i {
  display: inline-block;
  width: 1.35rem;
  height: 2px;
  background: var(--confidence-neutral);
}

.score-dot-plot-confidence-band i[data-confidence-band="tight"] {
  background: var(--confidence-tight);
}

.score-dot-plot-confidence-band i[data-confidence-band="middle"] {
  background: var(--confidence-middle);
}

.score-dot-plot-confidence-band i[data-confidence-band="wide"] {
  background: var(--confidence-wide);
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
  font-weight: var(--font-weight-bold);
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

.score-dot-plot-canvas--score {
  grid-area: score-canvas;
}

.score-dot-plot-canvas--width {
  grid-area: width-canvas;
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

@media (max-width: 780px) {
  .score-dot-plot-grid {
    grid-template-areas:
      "score-caption"
      "score-canvas"
      "width-caption"
      "width-canvas";
    grid-template-columns: minmax(0, 1fr);
    row-gap: 0;
  }

  .confidence-width-caption {
    min-height: 64px;
    margin-top: 0.75rem;
    padding-top: 1rem;
    border-top: var(--rule-subtle);
  }
}

@media (max-width: 620px) {
  .score-dot-plot-caption {
    align-items: stretch;
    padding-top: 0.7rem;
    flex-direction: column;
  }

  .score-dot-plot-confidence-legend {
    display: grid;
    grid-template-columns: repeat(2, max-content);
  }

  .score-dot-plot-confidence-legend > strong {
    grid-column: 1 / -1;
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
