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
