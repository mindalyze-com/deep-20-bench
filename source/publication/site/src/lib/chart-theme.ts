export interface ChartTheme {
  ink: string;
  inkSoft: string;
  muted: string;
  surface: string;
  border: string;
  borderStrong: string;
  gridLine: string;
  accent: string;
  acid: string;
  coral: string;
  results: {
    stability: string;
    efficiency: string;
  };
  roles: {
    guesser: string;
    oracle: string;
    reviewer: string;
    judge: string;
    validator: string;
  };
  tooltipShadow: string;
}

const customProperty = (
  styles: CSSStyleDeclaration,
  name: string,
  fallback: string,
): string => styles.getPropertyValue(name).trim() || fallback;

export const readChartTheme = (): ChartTheme => {
  const styles = window.getComputedStyle(document.documentElement);
  return {
    ink: customProperty(styles, "--text-primary", "#0c111b"),
    inkSoft: customProperty(styles, "--ink-soft", "#272b33"),
    muted: customProperty(styles, "--text-secondary", "#60636a"),
    surface: customProperty(styles, "--surface-raised", "#faf9f5"),
    border: customProperty(styles, "--border-default", "#c8c6bd"),
    borderStrong: customProperty(styles, "--muted", "#60636a"),
    gridLine: customProperty(styles, "--border-subtle", "rgb(12 17 27 / 12%)"),
    accent: customProperty(styles, "--blue-ink", "#3044d2"),
    acid: customProperty(styles, "--chart-acid", "#8cad12"),
    coral: customProperty(styles, "--coral", "#e95a3d"),
    results: {
      stability: customProperty(styles, "--result-stability", "#8266d5"),
      efficiency: customProperty(styles, "--result-efficiency", "#168c76"),
    },
    roles: {
      guesser: customProperty(styles, "--role-guesser", "#4f5dff"),
      oracle: customProperty(styles, "--role-oracle", "#e95a3d"),
      reviewer: customProperty(styles, "--role-reviewer", "#91a72b"),
      judge: customProperty(styles, "--role-judge", "#8a72cf"),
      validator: customProperty(styles, "--role-validator", "#8b8f99"),
    },
    tooltipShadow: customProperty(
      styles,
      "--shadow-chart-tooltip",
      "0 14px 34px rgb(12 17 27 / 18%)",
    ),
  };
};

export const chartTooltipStyle = (
  theme: ChartTheme,
  padding: number,
): {
  backgroundColor: string;
  borderColor: string;
  borderWidth: number;
  padding: number;
  extraCssText: string;
} => ({
  backgroundColor: theme.surface,
  borderColor: theme.border,
  borderWidth: 1,
  padding,
  extraCssText: `box-shadow:${theme.tooltipShadow};`,
});
