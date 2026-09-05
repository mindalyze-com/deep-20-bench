// @vitest-environment jsdom

import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { defineComponent, h, KeepAlive, nextTick, ref } from "vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useResponsiveEChart, type ResponsiveChart } from "@/lib/use-responsive-echart";
import type { ChartRenderer } from "@/lib/chart-loader";

const chart = vi.hoisted(() => ({
  setOption: vi.fn(), resize: vi.fn(), on: vi.fn(), off: vi.fn(), dispose: vi.fn(),
}));
const init = vi.hoisted(() => vi.fn(() => chart));
const loadChartRenderer = vi.hoisted(() => vi.fn());
vi.mock("@/lib/chart-loader", () => ({ loadChartRenderer }));

let width = 640;
let visibility: Array<(visible: boolean) => void>;
let resize: Array<(width: number) => void>;
let wrapper: VueWrapper | undefined;

beforeEach(() => {
  vi.clearAllMocks();
  loadChartRenderer.mockReset().mockResolvedValue(init);
  width = 640;
  visibility = [];
  resize = [];
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockImplementation(() => width);
  vi.stubGlobal("IntersectionObserver", class {
    constructor(callback: IntersectionObserverCallback) {
      visibility.push((visible) => callback(
        [{ isIntersecting: visible } as IntersectionObserverEntry],
        this as unknown as IntersectionObserver,
      ));
    }
    observe = vi.fn();
    disconnect = vi.fn();
  });
  vi.stubGlobal("ResizeObserver", class {
    constructor(callback: ResizeObserverCallback) {
      resize.push((newWidth) => callback(
        [{ contentRect: { width: newWidth } } as ResizeObserverEntry],
        this as unknown as ResizeObserver,
      ));
    }
    observe = vi.fn();
    disconnect = vi.fn();
  });
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  vi.unstubAllGlobals();
});

const mountChart = () => {
  const height = ref(300);
  const shown = ref(true);
  const value = ref(1);
  const option = vi.fn((chartWidth: number) => ({
    title: { text: `${value.value}:${chartWidth}` },
  }));
  let api: ResponsiveChart | undefined;
  const Chart = defineComponent({
    setup() {
      api = useResponsiveEChart({ height, option });
      return () => h("div", { ref: api?.chartElement });
    },
  });
  wrapper = mount(defineComponent({
    setup: () => () => h(KeepAlive, null, {
      default: () => shown.value ? h(Chart) : h("span"),
    }),
  }));
  if (api === undefined) throw new Error("Chart did not mount");
  return { api, height, shown, value, option };
};

describe("responsive chart rendering", () => {
  it("keeps offscreen charts out of hydration and renders once near the viewport", async () => {
    const { api, option } = mountChart();
    await nextTick();
    api.refresh();
    await nextTick();
    expect(init).not.toHaveBeenCalled();
    expect(loadChartRenderer).not.toHaveBeenCalled();
    expect(option).not.toHaveBeenCalled();

    visibility[0]?.(true);
    await flushPromises();
    expect(init).toHaveBeenCalledExactlyOnceWith(expect.any(HTMLElement), undefined, {
      renderer: "svg", width: 640, height: 300,
    });
    expect(chart.setOption).toHaveBeenCalledOnce();
    expect(chart.resize).not.toHaveBeenCalled();

    resize[0]?.(640);
    visibility[0]?.(true);
    await flushPromises();
    expect(chart.setOption).toHaveBeenCalledOnce();
    expect(chart.resize).not.toHaveBeenCalled();
  });

  it("coalesces data updates and only resizes when dimensions change", async () => {
    const { api, value, height } = mountChart();
    await nextTick();
    visibility[0]?.(true);
    await flushPromises();
    value.value = 2;
    api.refresh();
    api.refresh();
    await nextTick();
    expect(chart.setOption).toHaveBeenCalledTimes(2);
    expect(chart.setOption).toHaveBeenLastCalledWith({ title: { text: "2:640" } }, true);
    expect(chart.resize).not.toHaveBeenCalled();

    visibility[0]?.(false);
    width = 480;
    resize[0]?.(480);
    await nextTick();
    expect(chart.resize).toHaveBeenCalledExactlyOnceWith({ width: 480, height: 300 });
    expect(chart.setOption).toHaveBeenLastCalledWith({ title: { text: "2:480" } }, true);

    height.value = 400;
    await nextTick();
    await nextTick();
    expect(chart.resize).toHaveBeenLastCalledWith({ width: 480, height: 400 });
  });

  it("retains offscreen updates and resumes cached routes without recreating charts", async () => {
    const { api, value, shown } = mountChart();
    await nextTick();
    visibility[0]?.(true);
    await flushPromises();
    visibility[0]?.(false);
    value.value = 3;
    api.refresh();
    await nextTick();
    expect(chart.setOption).toHaveBeenCalledOnce();

    shown.value = false;
    await nextTick();
    visibility[0]?.(true);
    api.refresh();
    await nextTick();
    expect(chart.setOption).toHaveBeenCalledOnce();
    shown.value = true;
    await nextTick();
    await nextTick();
    expect(chart.setOption).toHaveBeenCalledOnce();
    visibility.at(-1)?.(true);
    await nextTick();
    expect(init).toHaveBeenCalledOnce();
    expect(chart.setOption).toHaveBeenLastCalledWith({ title: { text: "3:640" } }, true);
  });

  it("does not initialize after unmount and supports browsers without IntersectionObserver", async () => {
    mountChart();
    await nextTick();
    wrapper?.unmount();
    wrapper = undefined;
    visibility[0]?.(true);
    await nextTick();
    expect(init).not.toHaveBeenCalled();

    vi.stubGlobal("IntersectionObserver", undefined);
    mountChart();
    await flushPromises();
    expect(init).toHaveBeenCalledOnce();
  });

  it("waits for activation and uses current data after a delayed download", async () => {
    let resolveRenderer: ((renderer: ChartRenderer) => void) | undefined;
    loadChartRenderer.mockImplementation(() => new Promise<ChartRenderer>((resolve) => {
      resolveRenderer = resolve;
    }));
    const { api, shown, value, height } = mountChart();
    await nextTick();
    visibility[0]?.(true);
    await nextTick();
    expect(loadChartRenderer).toHaveBeenCalledOnce();
    expect(init).not.toHaveBeenCalled();

    value.value = 4;
    width = 480;
    height.value = 400;
    api.refresh();
    shown.value = false;
    await nextTick();
    resolveRenderer?.(init as unknown as ChartRenderer);
    await flushPromises();
    expect(init).not.toHaveBeenCalled();

    shown.value = true;
    await flushPromises();
    expect(init).not.toHaveBeenCalled();
    visibility.at(-1)?.(true);
    await flushPromises();
    expect(loadChartRenderer).toHaveBeenCalledOnce();
    expect(init).toHaveBeenCalledExactlyOnceWith(expect.any(HTMLElement), undefined, {
      renderer: "svg", width: 480, height: 400,
    });
    expect(chart.setOption).toHaveBeenCalledExactlyOnceWith({ title: { text: "4:480" } }, true);
  });

  it("ignores a download that finishes after unmount", async () => {
    let resolveRenderer: ((renderer: ChartRenderer) => void) | undefined;
    loadChartRenderer.mockImplementation(() => new Promise<ChartRenderer>((resolve) => {
      resolveRenderer = resolve;
    }));
    mountChart();
    await nextTick();
    visibility[0]?.(true);
    await nextTick();
    expect(loadChartRenderer).toHaveBeenCalledOnce();
    wrapper?.unmount();
    wrapper = undefined;
    resolveRenderer?.(init as unknown as ChartRenderer);
    await flushPromises();
    expect(init).not.toHaveBeenCalled();
  });

  it("reports a failed download without retrying on every resize", async () => {
    loadChartRenderer.mockRejectedValue(new Error("Download failed"));
    const { api } = mountChart();
    await nextTick();
    visibility[0]?.(true);
    await flushPromises();
    expect(api.loadError.value).toBe(true);
    api.refresh();
    width = 480;
    resize[0]?.(480);
    await flushPromises();
    expect(loadChartRenderer).toHaveBeenCalledOnce();
    expect(init).not.toHaveBeenCalled();
  });
});
