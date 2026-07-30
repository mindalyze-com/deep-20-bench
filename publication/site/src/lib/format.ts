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
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

export const number = (
  value: string | number | null | undefined,
  digits = 2,
): string =>
  value === null || value === undefined
    ? "—"
    : new Intl.NumberFormat("en", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(Number(value));

export const integer = (value: number): string =>
  new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value);

export const percent = (value: string | null | undefined): string =>
  value === null || value === undefined
    ? "—"
    : new Intl.NumberFormat("en", {
        style: "percent",
        maximumFractionDigits: 0,
      }).format(Number(value));

export const money = (value: string | number | null | undefined): string =>
  value === null || value === undefined
    ? "—"
    : usd.format(Number(value));

export const moneyEpisode = (
  value: string | number | null | undefined,
): string => {
  if (value === null || value === undefined) return "—";
  const amount = Number(value);
  return (Math.abs(amount) >= 1 ? usd : usdEpisode).format(amount);
};

export const date = (value: string | null): string =>
  value === null
    ? "—"
    : new Intl.DateTimeFormat("en", {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      }).format(new Date(value));

export const dateTime = (value: string): string =>
  new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(value));

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
