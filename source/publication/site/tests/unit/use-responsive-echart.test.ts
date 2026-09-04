// @vitest-environment jsdom

import { mount, type VueWrapper } from "@vue/test-utils";
import { defineComponent, h, KeepAlive, nextTick, ref } from "vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useResponsiveEChart, type ResponsiveChart } from "@/lib/use-responsive-echart";

const chart = vi.hoisted(() => ({
  setOption: vi.fn(), resize: vi.fn(), on: vi.fn(), off: vi.fn(), dispose: vi.fn(),
}));
const init = vi.hoisted(() => vi.fn(() => chart));
vi.mock("echarts/core", () => ({ init }));

let width = 640;
let visibility: Array<(visible: boolean) => void>;
let resize: Array<(width: number) => void>;
let wrapper: VueWrapper | undefined;

beforeEach(() => {
  vi.clearAllMocks();
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
    expect(option).not.toHaveBeenCalled();

    visibility[0]?.(true);
    await nextTick();
    expect(init).toHaveBeenCalledExactlyOnceWith(expect.any(HTMLElement), undefined, {
      renderer: "svg", width: 640, height: 300,
    });
    expect(chart.setOption).toHaveBeenCalledOnce();
    expect(chart.resize).not.toHaveBeenCalled();

    resize[0]?.(640);
    visibility[0]?.(true);
    await nextTick();
    expect(chart.setOption).toHaveBeenCalledOnce();
    expect(chart.resize).not.toHaveBeenCalled();
  });

  it("coalesces data updates and only resizes when dimensions change", async () => {
    const { api, value, height } = mountChart();
    await nextTick();
    visibility[0]?.(true);
    await nextTick();
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
    await nextTick();
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
    await nextTick();
    expect(init).toHaveBeenCalledOnce();
  });
});
