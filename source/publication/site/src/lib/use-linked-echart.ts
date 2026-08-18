import type { ECElementEvent, EChartsOption } from "echarts";
import { watch, type Ref } from "vue";
import { useRouter, type RouteLocationRaw } from "vue-router";

import {
  useResponsiveEChart,
  type ResponsiveChart,
} from "./use-responsive-echart";

export interface LinkedChartItem {
  label: string;
  link?: RouteLocationRaw;
}

interface LinkedChartOptions {
  height: Readonly<Ref<number>>;
  items: () => readonly LinkedChartItem[];
  option: (width: number) => EChartsOption;
}

export const useLinkedEChart = (options: LinkedChartOptions): ResponsiveChart => {
  const router = useRouter();
  const handleClick = (parameters: ECElementEvent): void => {
    const item = options.items().find(
      (candidate) => candidate.label === String(parameters.name),
    );
    if (item?.link !== undefined) void router.push(item.link);
  };
  const chart = useResponsiveEChart({
    height: options.height,
    option: options.option,
    onClick: handleClick,
  });

  watch(() => [chart.chartElement.value, options.items()] as const, chart.refresh, {
    deep: true,
  });
  return chart;
};
