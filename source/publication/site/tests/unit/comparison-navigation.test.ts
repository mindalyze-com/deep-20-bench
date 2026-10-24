import { afterEach, expect, test, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { comparisonReturnPath } from "../../src/lib/comparison-navigation";

const component = { render: () => null };
const router = createRouter({ history: createMemoryHistory(), routes: [
  { path: "/editions/:editionId/results/compare/", name: "results-compare", component },
  { path: "/:pathMatch(.*)*", name: "not-found", component },
] });
afterEach(() => vi.unstubAllGlobals());

test("comparison return links retain the selected view and reject other destinations", () => {
  const origin = "/editions/1.1/results/compare/?models=M-0035,M-0028&expanded=T-0002&metric=cost&baseline=M-0035&sort=gap";
  expect(comparisonReturnPath(router, { compare: origin })).toBe(origin);
  for (const invalid of [null, [origin], "https://example.com/", "//example.com/",
    "/\\example.com/", "/editions/1.1/models/claude/", "/" + "x".repeat(4096)]) {
    expect(comparisonReturnPath(router, { compare: invalid })).toBe(null);
  }
  expect(comparisonReturnPath(router, {})).toBe(null);
});

const browserStorage = () => {
  const entries = new Map<string, string>();
  vi.stubGlobal("window", { sessionStorage: {
    getItem: (key: string) => entries.get(key) ?? null,
    setItem: (key: string, value: string) => { entries.set(key, value); },
  } });
  return entries;
};

test("tab-local positions survive a fresh module after a detail-page reload", async () => {
  vi.resetModules();
  browserStorage();
  const origin = "/editions/1.1/results/compare/?models=M-0035,M-0028";
  const before = await import("../../src/lib/comparison-navigation");
  before.rememberComparisonScroll(origin, { top: 1769, main: 210, subjects: 146 });
  vi.resetModules();
  const after = await import("../../src/lib/comparison-navigation");
  expect(after.comparisonScroll(origin)).toEqual({ top: 1769, main: 210, subjects: 146 });
});

test("saved positions are bounded and malformed storage is ignored", async () => {
  vi.resetModules();
  const storage = browserStorage();
  const navigation = await import("../../src/lib/comparison-navigation");
  for (let index = 0; index < 51; index++) {
    navigation.rememberComparisonScroll(`/compare/?model=${index}`, { top: index, main: 0, subjects: 0 });
  }
  vi.resetModules();
  const restored = await import("../../src/lib/comparison-navigation");
  expect(restored.comparisonScroll("/compare/?model=0")).toBe(null);
  expect(restored.comparisonScroll("/compare/?model=50")?.top).toBe(50);
  storage.set("deep20:comparison-scroll:v1", JSON.stringify([
    ["/bad", { top: -1, main: 0, subjects: 0 }], ["/bad-type", { top: "12", main: 0, subjects: 0 }],
    ["/valid", { top: 12, main: 0, subjects: 0 }],
  ]));
  vi.resetModules();
  const checked = await import("../../src/lib/comparison-navigation");
  expect(checked.comparisonScroll("/bad")).toBe(null);
  expect(checked.comparisonScroll("/bad-type")).toBe(null);
  expect(checked.comparisonScroll("/valid")?.top).toBe(12);
  storage.set("deep20:comparison-scroll:v1", "invalid JSON");
  vi.resetModules();
  expect((await import("../../src/lib/comparison-navigation")).comparisonScroll("/valid")).toBe(null);
});

test("denied session storage still preserves same-document return positions", async () => {
  vi.resetModules();
  vi.stubGlobal("window", { get sessionStorage() { throw new Error("Storage denied"); } });
  const navigation = await import("../../src/lib/comparison-navigation");
  navigation.rememberComparisonScroll("/compare/", { top: 1200, main: 0, subjects: 70 });
  expect(navigation.comparisonScroll("/compare/")).toEqual({ top: 1200, main: 0, subjects: 70 });
});
