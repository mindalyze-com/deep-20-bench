import type {
  ECElementEvent,
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
  onClick?: (parameters: ECElementEvent) => void;
  pointerCursor?: (parameters: ECElementEvent) => boolean;
}

interface ResponsiveChart {
  chartElement: Ref<HTMLDivElement | null>;
  refresh: () => void;
}

export interface ChartValueDomain {
  minimum: number;
  maximum: number;
}

export const chartFont =
  'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
export const chartDisplayFont =
  '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif';

export const chartValueDomain = (
  values: readonly number[],
  paddingRatio = 0.08,
): ChartValueDomain => {
  const finiteValues = values.filter((value) => Number.isFinite(value));
  if (finiteValues.length === 0) return { minimum: 0, maximum: 1 };

  const dataMinimum = Math.min(...finiteValues);
  const dataMaximum = Math.max(...finiteValues);
  const span = dataMaximum - dataMinimum;
  const magnitude = Math.max(Math.abs(dataMinimum), Math.abs(dataMaximum), 1);
  const rangePadding = (span > 0 ? span : magnitude) * paddingRatio;
  const padding =
    dataMinimum > 0
      ? Math.min(rangePadding, dataMinimum / 2)
      : dataMaximum < 0
        ? Math.min(rangePadding, Math.abs(dataMaximum) / 2)
        : rangePadding;
  const paddedMinimum = dataMinimum - padding;
  const paddedMaximum = dataMaximum + padding;
  const paddedSpan = paddedMaximum - paddedMinimum;
  const roundingStep =
    10 ** Math.floor(Math.log10(paddedSpan > 0 ? paddedSpan : 1)) / 10;
  const roundedMinimum = Number(
    (Math.floor(paddedMinimum / roundingStep) * roundingStep).toPrecision(12),
  );
  const roundedMaximum = Number(
    (Math.ceil(paddedMaximum / roundingStep) * roundingStep).toPrecision(12),
  );

  return {
    minimum:
      dataMinimum > 0 && roundedMinimum <= 0
        ? paddedMinimum
        : dataMinimum >= 0 && roundedMinimum < 0
          ? 0
          : roundedMinimum,
    maximum:
      dataMaximum < 0 && roundedMaximum >= 0
        ? paddedMaximum
        : dataMaximum <= 0 && roundedMaximum > 0
          ? 0
          : roundedMaximum,
  };
};

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

  const updatePointerCursor = (parameters: ECElementEvent): void => {
    const element = chartElement.value;
    if (element !== null) {
      element.style.cursor =
        options.pointerCursor?.(parameters) === true ? "pointer" : "";
    }
  };

  const resetPointerCursor = (): void => {
    chartElement.value?.style.removeProperty("cursor");
  };

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
      if (options.pointerCursor !== undefined) {
        chart.on("mouseover", updatePointerCursor);
        chart.on("mouseout", resetPointerCursor);
      }
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
    if (options.pointerCursor !== undefined) {
      chart?.off("mouseover", updatePointerCursor);
      chart?.off("mouseout", resetPointerCursor);
    }
    chart?.dispose();
    chart = null;
  });

  return { chartElement, refresh };
};
