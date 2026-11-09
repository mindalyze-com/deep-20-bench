import { expect, test } from "vitest";
import { runDate, runLabel } from "../../src/lib/run-selection";

test("run dates use the same UTC date as history, static HTML and transcripts", () => {
  const timestamp = "2026-09-26T23:33:57.298552Z";
  expect(runDate(timestamp)).toBe("26 Sep 2026");
  expect(runLabel("Opus 5.5", timestamp)).toBe("Opus 5.5 · 26 Sep 2026");
});
