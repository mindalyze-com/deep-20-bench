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

import { loadChartRenderer, type ChartRenderer } from "./chart-loader";

export { escapeHtml } from "./html";

interface ResponsiveChartOptions {
  height: Readonly<Ref<number>>;
  option: (width: number) => EChartsOption;
  onClick?: (parameters: ECElementEvent) => void;
  pointerCursor?: (parameters: ECElementEvent) => boolean;
}

export interface ResponsiveChart {
  chartElement: Ref<HTMLDivElement | null>;
  loadError: Ref<boolean>;
  refresh: () => void;
}

export interface ChartValueDomain {
  minimum: number;
  maximum: number;
}

const readTypographyToken = (name: string, fallback: string): string =>
  typeof window === "undefined" || typeof document === "undefined"
    ? fallback
    : window.getComputedStyle(document.documentElement).getPropertyValue(name).trim() ||
      fallback;

const readTypographyWeight = (name: string, fallback: number): number => {
  const value = Number.parseInt(readTypographyToken(name, String(fallback)), 10);
  return Number.isFinite(value) ? value : fallback;
};

export const chartFont = readTypographyToken("--font-sans", "sans-serif");
export const chartDisplayFont = readTypographyToken("--font-display", "serif");
export const chartFontWeightSemibold = readTypographyWeight(
  "--font-weight-semibold",
  600,
);
export const chartFontWeightBold = readTypographyWeight(
  "--font-weight-bold",
  700,
);

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

export const chartAnimationEnabled = (): boolean =>
  typeof window !== "undefined" &&
  !window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
  !window.matchMedia("(max-width: 760px)").matches;

export const chartTextSize = (
  width: number,
  mobileSize: number,
  desktopSize: number,
): number => {
  if (width < 620) return mobileSize;
  if (typeof window === "undefined" || typeof document === "undefined") {
    return desktopSize;
  }
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
  const loadError = ref(false);
  let renderer: ChartRenderer | null = null;
  let rendererLoading = false;
  let chart: EChartsType | null = null;
  let resizeObserver: ResizeObserver | null = null;
  let visibilityObserver: IntersectionObserver | null = null;
  let observedWidth = 0;
  let observedHeight = 0;
  let visible = false;
  let active = true;
  let disposed = false;
  let optionDirty = true;
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
    if (element === null || !active || disposed || (!visible && chart === null)) return;
    const width = element.clientWidth;
    const height = options.height.value;
    if (width < 1 || height < 1) return;
    const dimensionsChanged = width !== observedWidth || height !== observedHeight;
    // Already-rendered SVGs must follow viewport resizes even when offscreen,
    // otherwise their fixed pixel width can overflow the narrower container.
    if (!visible && !dimensionsChanged) return;

    if (chart === null) {
      if (renderer === null) {
        if (!rendererLoading && !loadError.value) {
          rendererLoading = true;
          void loadChartRenderer().then((loaded) => {
            rendererLoading = false;
            if (disposed) return;
            renderer = loaded;
            // Read visibility, dimensions and data again after the download.
            schedule();
          }, () => {
            rendererLoading = false;
            if (!disposed) loadError.value = true;
          });
        }
        return;
      }
      // Explicit dimensions avoid another layout read inside ECharts initialization.
      chart = renderer(element, undefined, { renderer: "svg", width, height });
      if (options.onClick !== undefined) chart.on("click", options.onClick);
      if (options.pointerCursor !== undefined) {
        chart.on("mouseover", updatePointerCursor);
        chart.on("mouseout", resetPointerCursor);
      }
    } else if (dimensionsChanged) {
      chart.resize({ width, height });
    }
    if (width !== observedWidth) optionDirty = true;
    observedWidth = width;
    observedHeight = height;
    if (optionDirty) {
      chart.setOption(options.option(width), true);
      optionDirty = false;
    }
  };

  const observe = (element: HTMLDivElement): void => {
    if (visibilityObserver === null && typeof IntersectionObserver !== "undefined") {
      // Keep below-the-fold chart layout out of hydration. The reserved container
      // and static text remain present, and rendering starts before scrolling reaches it.
      visibilityObserver = new IntersectionObserver(([entry]) => {
        if (!active || disposed) return;
        visible = entry?.isIntersecting === true;
        if (visible) schedule();
      }, { rootMargin: "300px" });
      visibilityObserver.observe(element);
    } else if (typeof IntersectionObserver === "undefined") {
      visible = true;
    }
    if (resizeObserver === null) {
      resizeObserver = new ResizeObserver(([entry]) => {
        if (entry !== undefined && Math.abs(entry.contentRect.width - observedWidth) >= 1) {
          schedule();
        }
      });
      resizeObserver.observe(element);
    }
  };

  const schedule = (): void => {
    if (refreshPending || !active || disposed) return;
    refreshPending = true;
    void nextTick(() => {
      refreshPending = false;
      const element = chartElement.value;
      if (element === null || !active || disposed) return;
      observe(element);
      render();
    });
  };

  const refresh = (): void => {
    optionDirty = true;
    schedule();
  };

  onMounted(refresh);
  onActivated(() => {
    active = true;
    schedule();
  });
  watch(options.height, refresh);

  const disconnect = (): void => {
    resizeObserver?.disconnect();
    resizeObserver = null;
    visibilityObserver?.disconnect();
    visibilityObserver = null;
    visible = false;
  };

  onDeactivated(() => {
    active = false;
    disconnect();
  });

  onBeforeUnmount(() => {
    disposed = true;
    disconnect();
    if (options.onClick !== undefined) chart?.off("click", options.onClick);
    if (options.pointerCursor !== undefined) {
      chart?.off("mouseover", updatePointerCursor);
      chart?.off("mouseout", resetPointerCursor);
    }
    chart?.dispose();
    chart = null;
  });

  return { chartElement, loadError, refresh };
};
