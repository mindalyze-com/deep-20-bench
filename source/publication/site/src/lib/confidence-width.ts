export type ConfidenceWidthBand = "tight" | "middle" | "wide";

export interface ConfidenceWidthObservation {
  key: string;
  width: number;
}

export interface ConfidenceWidthScale {
  maximum: number;
  lowerThreshold: number;
  upperThreshold: number;
  bands: ReadonlyMap<string, ConfidenceWidthBand | null>;
}

export const confidenceIntervalWidth = (
  lower: number,
  upper: number,
): number | null => {
  if (!Number.isFinite(lower) || !Number.isFinite(upper) || upper < lower) {
    return null;
  }
  return upper - lower;
};

const confidenceWidthAxisMaximum = (maximum: number): number =>
  Math.max(3, Math.ceil(maximum / 3) * 3);

export const confidenceWidthScale = (
  observations: readonly ConfidenceWidthObservation[],
): ConfidenceWidthScale => {
  const valid = observations.filter(
    (observation) =>
      Number.isFinite(observation.width) && observation.width >= 0,
  );
  const maximum = confidenceWidthAxisMaximum(
    Math.max(0, ...valid.map((observation) => observation.width)),
  );
  const lowerThreshold = maximum / 3;
  const upperThreshold = (maximum * 2) / 3;
  const bands = new Map<string, ConfidenceWidthBand | null>();

  const allEqual = valid.every(
    (observation) => observation.width === valid[0]?.width,
  );
  if (valid.length <= 1 || allEqual) {
    for (const observation of valid) bands.set(observation.key, null);
    return { maximum, lowerThreshold, upperThreshold, bands };
  }

  for (const observation of valid) {
    const band: ConfidenceWidthBand =
      observation.width < lowerThreshold
        ? "tight"
        : observation.width < upperThreshold
          ? "middle"
          : "wide";
    bands.set(observation.key, band);
  }

  return { maximum, lowerThreshold, upperThreshold, bands };
};

export const classifyConfidenceWidths = (
  observations: readonly ConfidenceWidthObservation[],
): ReadonlyMap<string, ConfidenceWidthBand | null> =>
  confidenceWidthScale(observations).bands;
