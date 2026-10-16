import { readFileSync } from "node:fs";

import { describe, expect, test } from "vitest";

import { pageStructuredData } from "../../src/lib/structured-data";
import type { LeaderboardDocument, ManifestDocument, RunDocument } from "../../src/lib/types";

const fixture = <T>(path: string): T =>
  JSON.parse(readFileSync(new URL(`../fixtures/publication/data/${path}`, import.meta.url), "utf8")) as T;

const at = <T>(items: readonly T[], index: number): T => {
  const item = items[index];
  if (item === undefined) throw new Error(`Missing test item ${index}.`);
  return item;
};

const canonicalBase = "https://example.org/";
const manifest = fixture<ManifestDocument>("manifest.json");
const leaderboard = fixture<LeaderboardDocument>("leaderboard.json");
const run = fixture<RunDocument>("runs/BX-20260728-official-M0001-010.json");
const subject = at(run.subjects, 0);

describe("page structured data", () => {
  test("describes the same dataset on the homepage and the data page", () => {
    const homeDataset = at(pageStructuredData({ kind: "home", manifest, leaderboard }, canonicalBase), 0);
    const dataPage = pageStructuredData({ kind: "data", manifest, leaderboard }, canonicalBase);
    const dataDataset = at(dataPage, 0);
    const crumbs = at(dataPage, 1);

    expect(dataDataset).toEqual(homeDataset);
    expect(dataDataset["@id"]).toBe(`${canonicalBase}editions/${manifest.edition_id}/#dataset`);
    expect(dataDataset.url).toBe(`${canonicalBase}editions/${manifest.edition_id}/data/`);
    expect(String(dataDataset.description)).not.toContain("prototype");
    expect(crumbs["@type"]).toBe("BreadcrumbList");
  });

  test("links an episode to its edition, results, run, and subject", () => {
    const crumbs = at(pageStructuredData({
      kind: "episode",
      manifest,
      run,
      targetId: subject.target_id,
      trialId: "trial-002",
    }, canonicalBase), 0);
    const runUrl = `${canonicalBase}runs/${run.run.execution_id}/`;
    const subjectUrl = `${runUrl}subjects/${subject.target_id}/`;

    expect(crumbs.itemListElement).toEqual([
      expect.objectContaining({ position: 1, item: `${canonicalBase}editions/${manifest.edition_id}/` }),
      expect.objectContaining({ position: 2, name: "Results" }),
      expect.objectContaining({ position: 3, name: run.run.model_name, item: runUrl }),
      expect.objectContaining({ position: 4, name: subject.display_name, item: subjectUrl }),
      expect.objectContaining({
        position: 5,
        name: "Round 2",
        item: `${subjectUrl}episodes/trial-002/`,
      }),
    ]);
  });

  test("rejects a subject that is not part of the run", () => {
    expect(() => pageStructuredData(
      { kind: "subject", manifest, run, targetId: "T-9999" },
      canonicalBase,
    )).toThrow("missing");
  });
});
