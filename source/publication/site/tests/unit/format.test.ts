import { describe, expect, test } from "vitest";

import {
  contractPercent,
  formatCount,
  moneyEpisode,
  reasoningEffortLabel,
  staticDateTimeLabel,
} from "../../src/lib/format";
import { splitModelName } from "../../src/lib/model-name";

describe("publication formatting", () => {
  test("keeps meaningful contract and episode precision", () => {
    expect(contractPercent("1", 0)).toBe("100%");
    expect(contractPercent("0.9984", 1)).toBe(">99%");
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

  test("renders publication timestamps consistently across server and browser time zones", () => {
    expect(staticDateTimeLabel("2026-08-05T18:13:13.469638Z")).toBe(
      "Aug 5, 2026, 6:13:13 PM",
    );
  });
});
