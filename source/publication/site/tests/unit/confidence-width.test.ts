import { describe, expect, test } from "vitest";

import {
  classifyConfidenceWidths,
  confidenceIntervalWidth,
  confidenceWidthScale,
} from "../../src/lib/confidence-width";

describe("confidence width classification", () => {
  test("divides the displayed scale into three bands", () => {
    const scale = confidenceWidthScale([
      { key: "tight", width: 2 },
      { key: "middle", width: 6 },
      { key: "wide", width: 10 },
    ]);

    expect(scale.maximum).toBe(12);
    expect(scale.lowerThreshold).toBe(4);
    expect(scale.upperThreshold).toBe(8);
    expect([...scale.bands.entries()]).toEqual([
      ["tight", "tight"],
      ["middle", "middle"],
      ["wide", "wide"],
    ]);
  });

  test("keeps equal widths together and omits meaningless bands", () => {
    const tied = classifyConfidenceWidths([
      { key: "a", width: 1 },
      { key: "b", width: 2 },
      { key: "c", width: 2 },
      { key: "d", width: 2 },
      { key: "e", width: 3 },
      { key: "f", width: 4 },
      { key: "g", width: 5 },
      { key: "h", width: 6 },
    ]);

    expect(tied.get("b")).toBe("middle");
    expect(tied.get("c")).toBe(tied.get("b"));
    expect(tied.get("d")).toBe(tied.get("b"));
    expect(classifyConfidenceWidths([{ key: "only", width: 2 }]).get("only"))
      .toBeNull();
    expect(
      [...classifyConfidenceWidths([
        { key: "one", width: 2 },
        { key: "two", width: 2 },
      ]).values()],
    ).toEqual([null, null]);
  });

  test("rejects invalid intervals", () => {
    expect(confidenceIntervalWidth(2, 5)).toBe(3);
    expect(confidenceIntervalWidth(Number.NaN, 2)).toBeNull();
    expect(confidenceIntervalWidth(3, 2)).toBeNull();
  });
});
