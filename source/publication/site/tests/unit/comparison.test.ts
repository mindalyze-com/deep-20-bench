import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import type { RouteLocationNormalizedLoaded } from "vue-router";
import { getComparison, parsePublicationDocument, resetPublicationData, seedPublicationData } from "../../src/lib/api";
import { comparisonState, compareValue, formatValue, mainComparisonMetrics, roundValue, scalar, subjectValue, valueMark } from "../../src/lib/comparison";
import { compareDecimal, subtractDecimal } from "../../src/lib/exact-decimal";
import { editionDestination } from "../../src/lib/use-edition-context";
import type { ComparisonDocument, EditionsDocument } from "../../src/lib/types";

const fixture = (path: string): unknown => JSON.parse(readFileSync(resolve("tests/fixtures/publication/data", path), "utf8"));
const document = parsePublicationDocument(fixture("editions/1.0/compare.json")) as ComparisonDocument;
const editions = parsePublicationDocument(fixture("editions.json")) as EditionsDocument;

beforeEach(resetPublicationData);
afterEach(() => vi.unstubAllGlobals());

test("score ties and differences retain precision beyond JavaScript numbers", () => {
  expect(compareDecimal("13.66666666666666666666666667", "13.66666666666666666666666667")).toBe(0);
  expect(compareDecimal("1.00000000000000000001", "1")).toBe(1);
  expect(subtractDecimal("14.00000000000000000001", "13.00000000000000000000")).toBe("1.00000000000000000001");
  expect(compareDecimal("1E-8", "0.00000001")).toBe(0);
  expect(compareValue({ numerator: "10", denominator: 3 }, { numerator: "20", denominator: 6 })).toBe(0);
  const values = [scalar("13.66666666666666666666666667"), scalar("13.66666666666666666666666667"), scalar("15")];
  expect(values.map(value => valueMark(value, values))).toEqual(["best", "best", "worst"]);
  expect(valueMark(scalar("13"), [scalar("13"), scalar("13")])).toBe("tie");
  expect(valueMark(scalar("13"), [scalar("13"), null])).toBe(null);
  expect(valueMark(null, [scalar("13"), scalar("15")])).toBe(null);
  expect(valueMark(scalar("1"), [scalar("1"), scalar("2")], true)).toBe("worst");
});

test("failed rounds use their penalty while other metrics keep their recorded units", () => {
  const subject = document.models.flatMap(model => model.subjects).find(subject =>
    subject.rounds.some(round => round.status === "model_failure"))!;
  const failed = subject.rounds.find(round => round.status === "model_failure")!;
  expect(roundValue(failed, "questions")).toEqual(scalar(document.max_questions + 1));
  expect(roundValue(failed, "cost")).toEqual(scalar(failed.cost_usd));
  expect(roundValue(failed, "duration")).toEqual(scalar(failed.duration_ms));
  expect(subjectValue(subject, "questions")).toEqual(scalar(subject.average_questions));
  expect(roundValue(undefined, "questions")).toBe(null);
});

test("per-round cost comparisons keep sub-cent values and differences visible", () => {
  for (const key of ["model-cost", "full-cost"]) {
    const metric = mainComparisonMetrics.find(metric => metric.key === key)!;
    expect(formatValue(scalar("0.0046"), metric.format)).toBe("$0.0046");
    expect(formatValue(scalar("0.0015"), metric.format)).toBe("$0.0015");
    expect(formatValue(scalar("0"), metric.format)).toBe("$0.0000");
    expect(formatValue(null, metric.format)).toBe("Unavailable");
  }
});

test("URL selection preserves order, bounds the selection, and reads shared view settings", () => {
  expect(comparisonState({ models: ["M-0006,M-0001,M-0006", "M-0014"],
    expanded: "T-0005,T-0001", baseline: "M-0001", metric: "cost", sort: "gap" })).toEqual({
    modelIds: ["M-0006", "M-0001", "M-0014"], expanded: ["T-0005", "T-0001"],
    baseline: "M-0001", metric: "cost", sort: "gap",
  });
  expect(comparisonState({ models: "M-0001,M-0002,M-0003,M-0004,M-0005,M-0006", metric: "wrong", baseline: "M-0006" }))
    .toMatchObject({ modelIds: ["M-0001", "M-0002", "M-0003", "M-0004", "M-0005"], metric: "questions", baseline: "" });
});

test("comparison JSON rejects wrong penalties, duplicate runs, malformed metrics and missing rounds", () => {
  const badPenalty = structuredClone(document);
  badPenalty.models[0]!.subjects[0]!.rounds[0]!.penalized_questions = "-1";
  expect(() => parsePublicationDocument(badPenalty)).toThrow(/Comparison data/);
  const duplicate = { ...document, models: [document.models[0], document.models[0]] };
  expect(() => parsePublicationDocument(duplicate)).toThrow(/Comparison data/);
  const malformed = structuredClone(document);
  malformed.models[0]!.result.question_score = "NaN";
  expect(() => parsePublicationDocument(malformed)).toThrow(/Comparison data/);
  const incomplete = structuredClone(document);
  incomplete.models[0]!.subjects[0]!.rounds.pop();
  expect(() => parsePublicationDocument(incomplete)).toThrow(/Comparison data/);
});

test("one fetched bundle is reused and wrong edition ownership is rejected", async () => {
  seedPublicationData([editions]);
  const fetch = vi.fn().mockResolvedValue(Response.json(document));
  vi.stubGlobal("fetch", fetch);
  expect(await getComparison("1.0")).toEqual(document);
  expect(await getComparison("1.0")).toEqual(document);
  expect(fetch).toHaveBeenCalledTimes(1);
  const wrong = structuredClone(document);
  wrong.models[0]!.result.execution_id = "BX-not-published";
  expect(() => seedPublicationData([wrong])).toThrow(/different edition/);
});

test("edition switching matches model IDs and removes unavailable models and subjects", () => {
  seedPublicationData([editions]);
  const source = editions.editions[0]!;
  const first = document.models[0]!.result.model.model_id;
  const second = document.models[1]!.result.model.model_id;
  const target = { ...source, edition_id: "1.1", models: source.models.filter(model => model.model_id === first),
    runs: source.runs.filter(run => run.model_id === first).map(run => ({ ...run, target_ids: ["T-0001"] })) };
  const route = { name: "results-compare", params: { editionId: "1.0" }, fullPath: "/",
    query: { models: `${first},${second}`, baseline: second, expanded: "T-0001,T-0002", metric: "cost" }, hash: "",
  } as unknown as RouteLocationNormalizedLoaded;
  expect(editionDestination(route, target)).toEqual({ name: "results-compare", params: { editionId: "1.1" },
    query: { models: first, baseline: undefined, expanded: "T-0001", metric: "cost", comparisonNotice: "missing-models" } });
});
