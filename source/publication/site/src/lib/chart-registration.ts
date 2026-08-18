import {
  AriaComponent,
  GridComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

export { echarts };

export const standardChartComponents = [
  GridComponent,
  TooltipComponent,
  AriaComponent,
  SVGRenderer,
];
