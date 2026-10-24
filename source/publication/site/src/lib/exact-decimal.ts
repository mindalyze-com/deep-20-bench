/** Exact finite decimal operations for published values; round only when formatting. */
interface DecimalParts { coefficient: bigint; scale: number }

const parts = (value: string): DecimalParts => {
  const match = /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(value);
  if (match === null || value.length > 160) throw new Error("Invalid comparison decimal.");
  const exponent = Number(match[4] ?? 0);
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 100) {
    throw new Error("Invalid comparison decimal exponent.");
  }
  const fraction = match[3] ?? "";
  let coefficient = BigInt(`${match[1]}${match[2]}${fraction}`);
  let scale = fraction.length - exponent;
  if (scale < 0) { coefficient *= 10n ** BigInt(-scale); scale = 0; }
  return { coefficient, scale };
};

export const isDecimal = (value: unknown): value is string => {
  if (typeof value !== "string") return false;
  try { parts(value); return true; } catch { return false; }
};

const align = (left: string, right: string): { left: bigint; right: bigint; scale: number } => {
  const a = parts(left); const b = parts(right);
  const scale = Math.max(a.scale, b.scale);
  return { left: a.coefficient * 10n ** BigInt(scale - a.scale),
    right: b.coefficient * 10n ** BigInt(scale - b.scale), scale };
};

const serialize = (coefficient: bigint, scale: number): string => {
  const sign = coefficient < 0n ? "-" : "";
  const digits = (coefficient < 0n ? -coefficient : coefficient).toString().padStart(scale + 1, "0");
  return scale === 0 ? `${sign}${digits}`
    : `${sign}${digits.slice(0, -scale)}.${digits.slice(-scale)}`;
};

export const compareDecimal = (left: string, right: string): number => {
  const value = align(left, right);
  return value.left < value.right ? -1 : value.left > value.right ? 1 : 0;
};

export const subtractDecimal = (left: string, right: string): string => {
  const value = align(left, right);
  return serialize(value.left - value.right, value.scale);
};

export const addDecimal = (left: string, right: string): string => {
  const value = align(left, right);
  return serialize(value.left + value.right, value.scale);
};

/** Equal-count subject comparisons can rank the exact sum, formatting its mean separately. */
export const sumDecimals = (values: readonly string[]): string => values.reduce(addDecimal, "0");

export const multiplyInteger = (value: string, multiplier: number): string => {
  if (!Number.isSafeInteger(multiplier)) throw new Error("Invalid decimal multiplier.");
  const parsed = parts(value);
  return serialize(parsed.coefficient * BigInt(multiplier), parsed.scale);
};
