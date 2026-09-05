import type { init } from "echarts/core";

export type ChartRenderer = typeof init;

/** Keep the renderer's download and evaluation out of initial page hydration. */
export const loadChartRenderer = async (): Promise<ChartRenderer> =>
  (await import("./chart-registration")).init;
