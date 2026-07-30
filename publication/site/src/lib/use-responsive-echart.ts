import type {
  DefaultLabelFormatterCallbackParams as CallbackDataParams,
  EChartsOption,
} from "echarts";
import type { EChartsType } from "echarts/core";
import {
  nextTick,
  onActivated,
  onBeforeUnmount,
  onDeactivated,
  onMounted,
  ref,
  watch,
  type Ref,
} from "vue";

interface ResponsiveChartOptions {
  height: Readonly<Ref<number>>;
  initialize: (element: HTMLDivElement) => EChartsType;
  option: (width: number) => EChartsOption;
  onClick?: (parameters: CallbackDataParams) => void;
}

interface ResponsiveChart {
  chartElement: Ref<HTMLDivElement | null>;
  refresh: () => void;
}

export const chartFont =
  'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
export const chartDisplayFont =
  '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif';

export const escapeHtml = (value: string): string =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

export const chartAnimationEnabled = (): boolean =>
  !window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
  !window.matchMedia("(max-width: 760px)").matches;

export const chartTextSize = (
  width: number,
  mobileSize: number,
  desktopSize: number,
): number => {
  if (width < 620) return mobileSize;
  const rootSize = Number.parseFloat(
    window.getComputedStyle(document.documentElement).fontSize,
  );
  const scale = Number.isFinite(rootSize)
    ? Math.min(1.125, Math.max(1, rootSize / 16))
    : 1;
  return Math.round(desktopSize * scale * 10) / 10;
};

export const useResponsiveEChart = (
  options: ResponsiveChartOptions,
): ResponsiveChart => {
  const chartElement = ref<HTMLDivElement | null>(null);
  let chart: EChartsType | null = null;
  let resizeObserver: ResizeObserver | null = null;
  let observedWidth = 0;
  let refreshPending = false;

  const render = (): void => {
    const element = chartElement.value;
    if (element === null || chart === null || element.clientWidth < 1) return;
    const width = element.clientWidth;
    observedWidth = width;
    chart.setOption(options.option(width), true);
    chart.resize({ width, height: options.height.value });
  };

  const observe = (element: HTMLDivElement): void => {
    if (resizeObserver !== null) return;
    resizeObserver = new ResizeObserver(([entry]) => {
      if (
        entry === undefined ||
        Math.abs(entry.contentRect.width - observedWidth) < 1
      ) {
        return;
      }
      render();
    });
    resizeObserver.observe(element);
  };

  const ensure = (): void => {
    const element = chartElement.value;
    if (element === null || element.clientWidth < 1 || element.clientHeight < 1) {
      return;
    }
    if (chart === null) {
      chart = options.initialize(element);
      if (options.onClick !== undefined) chart.on("click", options.onClick);
    }
    observe(element);
  };

  const refresh = (): void => {
    if (refreshPending) return;
    refreshPending = true;
    void nextTick(() => {
      refreshPending = false;
      ensure();
      render();
    });
  };

  onMounted(refresh);
  onActivated(refresh);
  watch(options.height, refresh);

  onDeactivated(() => {
    resizeObserver?.disconnect();
    resizeObserver = null;
  });

  onBeforeUnmount(() => {
    resizeObserver?.disconnect();
    resizeObserver = null;
    if (options.onClick !== undefined) chart?.off("click", options.onClick);
    chart?.dispose();
    chart = null;
  });

  return { chartElement, refresh };
};
