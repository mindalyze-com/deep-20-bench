import type { ChartTheme } from "./chart-theme";
import { chartFont } from "./use-responsive-echart";

export const chartValueAxis = (
  theme: ChartTheme,
  fontSize: number,
  name: string,
  nameGap: number,
  formatter?: (value: number) => string,
) => ({
  type: "value" as const,
  name,
  nameLocation: "middle" as const,
  nameGap,
  nameTextStyle: {
    color: theme.muted,
    fontFamily: chartFont,
    fontSize,
  },
  axisLine: { show: true, lineStyle: { color: theme.border } },
  axisTick: { show: false },
  axisLabel: {
    color: theme.muted,
    fontFamily: chartFont,
    fontSize,
    ...(formatter === undefined ? {} : { formatter }),
  },
  splitLine: {
    show: true,
    lineStyle: { color: theme.gridLine },
  },
});

export interface NiceAxis {
  min: number;
  max: number;
  interval: number;
}

const round = (value: number): number => Number(value.toPrecision(12));

/**
 * Axis bounds that land on round tick values (for example 10–40 by 5, not 10–36),
 * so the first and last labels never crowd an odd end value.
 */
export const niceAxis = (minimum: number, maximum: number, targetTicks = 5): NiceAxis => {
  const low = Number.isFinite(minimum) ? minimum : 0;
  const high = Number.isFinite(maximum) && maximum > low ? maximum : low + 1;
  const rough = (high - low) / Math.max(1, targetTicks);
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const step =
    [1, 2, 2.5, 5, 10].map((factor) => factor * magnitude).find((candidate) => candidate >= rough)
    ?? 10 * magnitude;
  return {
    min: round(Math.floor(low / step) * step),
    max: round(Math.ceil(high / step) * step),
    interval: round(step),
  };
};

const durationSteps = [
  1_000, 2_000, 5_000, 10_000, 15_000, 30_000,
  60_000, 120_000, 300_000, 600_000, 900_000, 1_800_000,
  3_600_000, 7_200_000, 10_800_000, 21_600_000, 43_200_000,
];

/** Zero-based duration axis with whole-unit ticks (30m, 1h, 1h 30m) instead of 33m or 67m. */
export const niceDurationAxis = (maximumMs: number, targetTicks = 5): NiceAxis => {
  const high = Number.isFinite(maximumMs) && maximumMs > 0 ? maximumMs : 1_000;
  const rough = high / Math.max(1, targetTicks);
  const step = durationSteps.find((candidate) => candidate >= rough) ?? 86_400_000;
  return { min: 0, max: Math.ceil(high / step) * step, interval: step };
};

export const durationAxisLabel = (milliseconds: number): string => {
  if (milliseconds === 0) return "0";
  const minutes = Math.round(milliseconds / 60_000);
  if (milliseconds >= 3_600_000) {
    const hours = Math.floor(minutes / 60);
    return minutes % 60 === 0 ? `${hours}h` : `${hours}h ${minutes % 60}m`;
  }
  if (milliseconds >= 60_000) return `${minutes}m`;
  return `${Math.round(milliseconds / 1_000)}s`;
};
