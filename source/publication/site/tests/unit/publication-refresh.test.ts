import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { computed } from "vue";

import {
  editionsIndex, getComparison, getLeaderboard, peekComparison, peekLeaderboard, peekManifest,
  resetPublicationData, seedPublicationData, selectedEditionId,
} from "../../src/lib/api";
import type { ComparisonDocument, EditionsDocument, ManifestDocument } from "../../src/lib/types";

const fixture = (path: string): unknown => JSON.parse(readFileSync(resolve(
  "tests/fixtures/publication/data", path), "utf8"));
const comparison = fixture("editions/1.0/compare.json") as ComparisonDocument;
const index = fixture("editions.json") as EditionsDocument;
const manifest = fixture("manifest.json") as ManifestDocument;
const added = comparison.models[0]!.result;
const oldIndex: EditionsDocument = { ...index, editions: index.editions.map(edition => ({
  ...edition,
  runs: edition.runs.filter(run => run.execution_id !== added.execution_id),
  models: edition.models.filter(model => model.model_id !== added.model.model_id),
})) };
const oldManifest: ManifestDocument = { ...manifest,
  official_runs: manifest.official_runs.filter(run => run.execution_id !== added.execution_id),
};

const serve = (document = comparison) => vi.fn(async (url: string, _options?: RequestInit) => {
  if (url.endsWith("/compare.json")) return Response.json(document);
  if (url.endsWith("/editions.json")) return Response.json(index);
  if (url.endsWith("/manifest.json")) return Response.json(manifest);
  throw new Error(`Unexpected fixture request: ${url}`);
});

beforeEach(resetPublicationData);
afterEach(() => vi.unstubAllGlobals());

test("a new comparison refreshes an older embedded index once and shares the recovery", async () => {
  seedPublicationData([oldIndex, oldManifest]);
  const settings = computed(() => peekManifest("1.0"));
  expect(settings.value).toEqual(oldManifest);
  const fetch = serve();
  vi.stubGlobal("fetch", fetch);
  const results = await Promise.all([getComparison("1.0"), getComparison("1.0")]);
  expect(results).toEqual([comparison, comparison]);
  expect(editionsIndex.value).toEqual(index);
  expect(peekManifest("1.0")).toEqual(manifest);
  expect(settings.value).toEqual(manifest);
  expect(peekComparison("1.0")).toEqual(comparison);
  expect(selectedEditionId.value).toBe("1.0");
  expect(fetch).toHaveBeenCalledTimes(4);
  expect(fetch.mock.calls.filter(([url]) => url.endsWith("/compare.json"))).toHaveLength(2);
  for (const [, options] of fetch.mock.calls.slice(1)) expect(options?.cache).toBe("no-cache");
  await expect(getComparison("1.0")).resolves.toEqual(comparison);
  expect(fetch).toHaveBeenCalledTimes(4);
});

test("refreshed data with unpublished runs stays rejected without a retry loop", async () => {
  seedPublicationData([oldIndex, oldManifest]);
  const wrong = structuredClone(comparison);
  wrong.models[0]!.result.execution_id = "BX-not-published";
  const fetch = serve(wrong);
  vi.stubGlobal("fetch", fetch);
  await expect(getComparison("1.0")).rejects.toThrow(/different edition/);
  expect(fetch).toHaveBeenCalledTimes(4);
  expect(editionsIndex.value).toEqual(oldIndex);
  expect(peekManifest("1.0")).toEqual(oldManifest);
  expect(peekComparison("1.0")).toBeNull();
});

test("recovery does not publish a fresh index alongside an older manifest", async () => {
  seedPublicationData([oldIndex, oldManifest]);
  const fetch = serve();
  const implementation = fetch.getMockImplementation()!;
  fetch.mockImplementation((url, options) => url.endsWith("/manifest.json")
    ? Promise.resolve(Response.json(oldManifest)) : implementation(url, options));
  vi.stubGlobal("fetch", fetch);
  await expect(getComparison("1.0")).rejects.toThrow();
  expect(fetch).toHaveBeenCalledTimes(4);
  expect(editionsIndex.value).toEqual(oldIndex);
  expect(peekComparison("1.0")).toBeNull();
});

test.each(["unavailable", "malformed", "wrong-route"])(
  "an unrelated %s response does not trigger an inventory refresh", async failure => {
    seedPublicationData([index, manifest]);
    const response = failure === "unavailable" ? new Response("Unavailable", { status: 503 })
      : failure === "malformed" ? Response.json({ document_type: "comparison", schema_version: 99 })
        : Response.json({ ...comparison, edition_id: "1.1" });
    const fetch = vi.fn().mockResolvedValue(response);
    vi.stubGlobal("fetch", fetch);
    await expect(getComparison("1.0")).rejects.toThrow();
    expect(fetch).toHaveBeenCalledTimes(1);
  },
);

test("a failed refresh leaves the old state intact and a later attempt can recover", async () => {
  seedPublicationData([oldIndex, oldManifest]);
  const fetch = serve();
  const implementation = fetch.getMockImplementation()!;
  let fail = true;
  fetch.mockImplementation((url, options) => url.endsWith("/editions.json") && fail
    ? Promise.resolve(new Response("Unavailable", { status: 503 })) : implementation(url, options));
  vi.stubGlobal("fetch", fetch);
  await expect(getComparison("1.0")).rejects.toThrow();
  expect(editionsIndex.value).toEqual(oldIndex);
  expect(peekManifest("1.0")).toEqual(oldManifest);
  fail = false;
  await expect(getComparison("1.0")).resolves.toEqual(comparison);
  expect(fetch).toHaveBeenCalledTimes(8);
});

test("an older in-flight request cannot refill the cache after a publication refresh", async () => {
  seedPublicationData([oldIndex, oldManifest]);
  let release: (response: Response) => void = () => {};
  const slow = new Promise<Response>(resolve => { release = resolve; });
  const fetch = serve();
  const implementation = fetch.getMockImplementation()!;
  let leaderboardRequests = 0;
  fetch.mockImplementation((url, options) => url.endsWith("/leaderboard.json")
    ? ++leaderboardRequests === 1 ? slow : Promise.resolve(Response.json(fixture("leaderboard.json")))
    : implementation(url, options));
  vi.stubGlobal("fetch", fetch);
  const old = getLeaderboard("1.0");
  await getComparison("1.0");
  release(Response.json(fixture("leaderboard.json")));
  await old;
  expect(peekLeaderboard("1.0")).toBeNull();
  await getLeaderboard("1.0");
  expect(leaderboardRequests).toBe(2);
});
