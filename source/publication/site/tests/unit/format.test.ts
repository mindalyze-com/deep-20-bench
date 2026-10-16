import { describe, expect, test } from "vitest";

import {
  contractPercent,
  formatCount,
  moneyEpisode,
  number,
  reasoningEffortLabel,
  date,
  dateTime,
} from "../../src/lib/format";
import { splitModelName } from "../../src/lib/model-name";

describe("publication formatting", () => {
  test("keeps decimal precision independent across repeated formats", () => {
    expect(number("1234.5678", 1)).toBe("1,234.6");
    expect(number("1234.5678", 4)).toBe("1,234.5678");
    expect(number("1234.5678", 1)).toBe("1,234.6");
    expect(number("1234.5678")).toBe("1,234.57");
    expect(number(null, 4)).toBe("-");
  });

  test("keeps meaningful contract and episode precision", () => {
    expect(contractPercent("1", 0)).toBe("100%");
    expect(contractPercent("0.9984", 1)).toBe("99.8%");
    expect(contractPercent("0.99932", 3)).toBe("99.9%");
    expect(contractPercent("0.9997", 1)).toBe(">99.9%");
    expect(contractPercent(null, 1)).toBe("-");
    expect(formatCount(1, "violation")).toBe("1 violation");
    expect(formatCount(2, "invalid output")).toBe("2 invalid outputs");
    expect(moneyEpisode("0.114")).toBe("$0.1140");
    expect(moneyEpisode("1.4")).toBe("$1.4000");
  });

  test("normalizes reasoning-effort labels and model suffixes", () => {
    expect(reasoningEffortLabel("extra_high")).toBe("Extra high");
    expect(splitModelName("Claude Opus 5 (high)")).toEqual({
      displayName: "Claude Opus 5",
      reasoningEffort: "high",
    });
    expect(splitModelName("Model without suffix")).toEqual({
      displayName: "Model without suffix",
      reasoningEffort: null,
    });
  });

  test("renders publication timestamps in one UTC format", () => {
    expect(dateTime("2026-08-05T18:13:13.469638Z")).toBe("5 Aug 2026, 18:13 UTC");
    expect(dateTime("2026-09-06T02:00:00+02:00")).toBe("6 Sep 2026, 00:00 UTC");
    expect(dateTime("2026-09-06T12:05:09Z")).toBe("6 Sep 2026, 12:05 UTC");
    expect(date("2026-01-01T00:30:00+01:00")).toBe("31 Dec 2025");
    expect(date(null)).toBe("-");
  });
});
