const decimal = new Intl.NumberFormat("en", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const decimalFormats = new Map<number, Intl.NumberFormat>([[2, decimal]]);
const decimalFormat = (digits: number): Intl.NumberFormat => {
  let format = decimalFormats.get(digits);
  if (format === undefined) {
    format = new Intl.NumberFormat("en", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
    decimalFormats.set(digits, format);
  }
  return format;
};

const wholeNumber = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });
const percentage = new Intl.NumberFormat("en", {
  style: "percent",
  maximumFractionDigits: 0,
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

// One fixed UTC format keeps initial HTML, hydration, and every page in agreement
// (for example "9 Sep 2026" and "9 Sep 2026, 10:31 UTC"), matching run page titles.
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dayLabel = (timestamp: Date): string => {
  if (Number.isNaN(timestamp.getTime())) throw new RangeError("Invalid time value");
  return `${timestamp.getUTCDate()} ${months[timestamp.getUTCMonth()]} ${timestamp.getUTCFullYear()}`;
};

export const number = (
  value: string | number | null | undefined,
  digits = 2,
): string =>
  value === null || value === undefined
    ? "-"
    : decimalFormat(digits).format(Number(value));

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
  wholeNumber.format(value);

export const percent = (value: string | null | undefined): string =>
  value === null || value === undefined
    ? "-"
    : percentage.format(Number(value));

const percentOneDecimal = new Intl.NumberFormat("en", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

// Any violation shows one decimal so small differences stay visible (99.3% vs 99.6%);
// a rate that would still round to 100% shows as ">99.9%".
export const contractPercent = (
  value: string | null | undefined,
  violations: number,
): string => {
  if (value === null || value === undefined || violations === 0) return percent(value);
  const formatted = percentOneDecimal.format(Number(value));
  return formatted === "100.0%" ? ">99.9%" : formatted;
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
  value === null ? "-" : dayLabel(new Date(value));

export const dateTime = (value: string): string => {
  const timestamp = new Date(value);
  const hours = String(timestamp.getUTCHours()).padStart(2, "0");
  const minutes = String(timestamp.getUTCMinutes()).padStart(2, "0");
  return `${dayLabel(timestamp)}, ${hours}:${minutes} UTC`;
};

export const isoDateTime = (value: string): string =>
  new Date(value).toISOString().replace(/\.\d{3}Z$/, "Z");

export const duration = (milliseconds: number): string => {
  const seconds = milliseconds / 1_000;
  if (seconds < 10) return `${number(seconds, 1)}s`;
  const whole = Math.round(seconds);
  if (whole < 60) return `${whole}s`;
  if (whole < 3_600) return `${Math.floor(whole / 60)}m ${whole % 60}s`;
  const minutes = Math.round(whole / 60);
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
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

const outcomeLabels: Readonly<Record<string, string>> = {
  success: "Solved",
  model_failure: "Not found",
  infrastructure_failure: "Test system failure",
  limit_exhausted: "Question limit reached",
  guesser_protocol_failure: "Too many format errors",
  validator_unknown: "Guess not confirmed",
};
export const outcomeLabel = (value: string): string =>
  outcomeLabels[value] ?? statusLabel(value);

const contractStatusLabels: Readonly<Record<string, string>> = {
  clean: "No errors",
  breached: "Errors found",
  not_evaluable: "Not checked",
};
export const contractStatusLabel = (value: string): string =>
  contractStatusLabels[value] ?? statusLabel(value);
