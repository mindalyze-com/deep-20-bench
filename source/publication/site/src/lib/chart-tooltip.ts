import type { DefaultLabelFormatterCallbackParams as CallbackDataParams } from "echarts";

import type { ChartTheme } from "./chart-theme";
import { escapeHtml } from "./html";
import { chartDisplayFont, chartFont } from "./use-responsive-echart";

export const chartTooltipItem = <Item extends { label: string }>(
  parameters: CallbackDataParams | CallbackDataParams[],
  items: readonly Item[],
): Item | undefined => {
  const parameter = Array.isArray(parameters) ? parameters[0] : parameters;
  return items.find((candidate) => candidate.label === parameter?.name);
};

export const chartTooltipRunLink = (
  theme: ChartTheme,
  visible: boolean,
  spaced = false,
): string =>
  visible
    ? `<span style="display:block;margin-top:9px;color:${theme.accent};font-size:.75rem;font-weight: var(--font-weight-bold);${spaced ? "letter-spacing:.06em;" : ""}text-transform:uppercase">View full run →</span>`
    : "";

export const chartTooltipTitle = (
  theme: ChartTheme,
  value: string,
): string =>
  `<strong style="display:block;color:${theme.ink};font: var(--font-weight-bold) .82rem/1.35 ${chartFont}">${escapeHtml(value)}</strong>`;

export const chartTooltipPrimary = (
  theme: ChartTheme,
  value: string,
  fontSize = "1.45rem",
  marginTop = 8,
): string =>
  `<span style="display:block;margin-top:${marginTop}px;color:${theme.ink};font-family:${chartDisplayFont};font-size:${fontSize}">${escapeHtml(value)}</span>`;
