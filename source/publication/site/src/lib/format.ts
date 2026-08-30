const decimal = new Intl.NumberFormat("en", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const usd = new Intl.NumberFormat("en", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const usdEpisode = new Intl.NumberFormat("en", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
});

const userDate = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
});

const userDateTime = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "medium",
});

const staticDate = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeZone: "UTC",
});

const staticDateAndTime = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "medium",
  timeZone: "UTC",
});

export const number = (
  value: string | number | null | undefined,
  digits = 2,
): string =>
  value === null || value === undefined
    ? "-"
    : new Intl.NumberFormat("en", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(Number(value));

export interface ConfidenceIntervalBounds {
  lower: string | number;
  upper: string | number;
}

export const confidenceIntervalLabel = (
  interval: ConfidenceIntervalBounds | null | undefined,
  digits = 2,
): string =>
  interval === null || interval === undefined
    ? "-"
    : `${number(interval.lower, digits)}–${number(interval.upper, digits)}`;

export const integer = (value: number): string =>
  new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value);

export const percent = (value: string | null | undefined): string =>
  value === null || value === undefined
    ? "-"
    : new Intl.NumberFormat("en", {
        style: "percent",
        maximumFractionDigits: 0,
      }).format(Number(value));

export const contractPercent = (
  value: string | null | undefined,
  violations: number,
): string => {
  const formatted = percent(value);
  return violations > 0 && formatted === "100%" ? ">99%" : formatted;
};

export const plural = (
  count: number,
  singular: string,
  pluralForm = `${singular}s`,
): string => (count === 1 ? singular : pluralForm);

export const formatCount = (
  count: number,
  singular: string,
  pluralForm = `${singular}s`,
): string => `${integer(count)} ${plural(count, singular, pluralForm)}`;

const countWords: Readonly<Record<number, string>> = { 5: "five", 7: "seven" };

export const countWord = (value: number): string =>
  countWords[value] ?? String(value);

export const money = (value: string | number | null | undefined): string =>
  value === null || value === undefined
    ? "-"
    : usd.format(Number(value));

export const moneyEpisode = (
  value: string | number | null | undefined,
): string =>
  value === null || value === undefined
    ? "-"
    : usdEpisode.format(Number(value));

export const date = (value: string | null): string =>
  value === null ? "-" : userDate.format(new Date(value));

export const dateTime = (value: string): string =>
  userDateTime.format(new Date(value));

export const staticDateLabel = (value: string): string =>
  staticDate.format(new Date(value));

export const staticDateTimeLabel = (value: string): string =>
  staticDateAndTime.format(new Date(value));

export const isoDateTime = (value: string): string =>
  new Date(value).toISOString().replace(/\.\d{3}Z$/, "Z");

export const duration = (milliseconds: number): string => {
  const seconds = milliseconds / 1_000;
  if (seconds < 60) return `${number(seconds, 1)} s`;
  if (seconds < 3_600) {
    return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  }
  return `${Math.floor(seconds / 3_600)}h ${Math.round((seconds % 3_600) / 60)}m`;
};

export const seconds = (milliseconds: number): string =>
  decimal.format(milliseconds / 1_000);

const reasoningLabels: Record<string, string> = {
  none: "None",
  minimal: "Minimal",
  low: "Low",
  medium: "Medium",
  high: "High",
  "extra-high": "Extra high",
  xhigh: "Extra high",
  max: "Maximum",
  default: "Default",
};

export const reasoningEffortLabel = (value: string): string => {
  const normalized = value.trim().toLowerCase().replaceAll("_", "-");
  return (
    reasoningLabels[normalized] ??
    normalized.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
  );
};

export const statusLabel = (value: string): string =>
  value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
