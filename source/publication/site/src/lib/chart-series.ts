import type { DefaultLabelFormatterCallbackParams as CallbackDataParams } from "echarts";

import type { ChartTheme } from "./chart-theme";
import {
  chartFont,
  chartFontWeightSemibold,
  chartTextSize,
} from "./use-responsive-echart";

export const scatterSeriesPresentation = (
  theme: ChartTheme,
  width: number,
  mobile: boolean,
  color: string,
  hideOverlap: boolean,
  formatter: (parameters: CallbackDataParams) => string,
) => ({
  itemStyle: {
    color,
    borderColor: theme.ink,
    borderWidth: 2,
  },
  label: {
    show: !mobile,
    distance: 7,
    color: theme.inkSoft,
    fontFamily: chartFont,
    fontSize: chartTextSize(width, 8, 11),
    fontWeight: chartFontWeightSemibold,
    width: 148,
    overflow: "truncate" as const,
    ellipsis: "…",
    formatter,
  },
  labelLayout: {
    hideOverlap,
    moveOverlap: "shiftY" as const,
  },
  emphasis: {
    scale: 1.35,
    itemStyle: {
      shadowBlur: 10,
      shadowColor: theme.gridLine,
    },
  },
  z: 2,
});
