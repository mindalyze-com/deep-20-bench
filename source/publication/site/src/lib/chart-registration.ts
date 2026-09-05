import {
  BarChart,
  CustomChart,
  LineChart,
  PieChart,
  ScatterChart,
} from "echarts/charts";
import {
  AriaComponent,
  GridComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
} from "echarts/components";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

export { init } from "echarts/core";

// This module is loaded only when a chart approaches the viewport.
use([
  BarChart,
  CustomChart,
  LineChart,
  PieChart,
  ScatterChart,
  GridComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
  AriaComponent,
  SVGRenderer,
]);
