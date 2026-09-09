// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { mount } from "@vue/test-utils";
import type { RouteLocationNormalizedLoaded } from "vue-router";

import {
  getLeaderboard, parsePublicationDocument, resetPublicationData, seedPublicationData,
  selectedEditionId,
} from "../../src/lib/api";
import { editionDestination } from "../../src/lib/use-edition-context";
import type { EditionsDocument, EpisodeDocument, LeaderboardDocument, ManifestDocument } from "../../src/lib/types";
import EpisodeTranscriptPanel from "../../src/components/episode/EpisodeTranscriptPanel.vue";

const fixture = (path: string): unknown => JSON.parse(readFileSync(resolve(
  "tests/fixtures/publication/data", path), "utf8"));
const previous = parsePublicationDocument(fixture("manifest.json")) as ManifestDocument;
const leaderboard = parsePublicationDocument(fixture("leaderboard.json")) as LeaderboardDocument;
const previousIndex = parsePublicationDocument(fixture("editions.json")) as EditionsDocument;
const previousEdition = previousIndex.editions[0]!;
const currentEdition = {
  ...previousEdition, edition_id: "1.1", label: "1.1", status: "current" as const,
  runs: previousEdition.runs.slice(0, 1).map(run => ({ ...run, execution_id: "BX-current", target_ids: ["T-0001"] })),
};
const index: EditionsDocument = {
  ...previousIndex, default_edition_id: "1.1", editions: [currentEdition, previousEdition],
};

beforeEach(resetPublicationData);
afterEach(() => vi.unstubAllGlobals());

test("edition caches remain independent when requests complete out of order", async () => {
  let release: (response: Response) => void = () => {};
  const slow = new Promise<Response>(resolve => { release = resolve; });
  const fetch = vi.fn((url: string) => url.includes("1.0") ? slow : Promise.resolve(
    Response.json({ ...leaderboard, edition_id: "1.1", leaderboard: [] }),
  ));
  vi.stubGlobal("fetch", fetch);
  const old = getLeaderboard("1.0");
  const current = await getLeaderboard("1.1");
  selectedEditionId.value = "1.1";
  release(Response.json(leaderboard));
  expect((await old).edition_id).toBe("1.0");
  expect(await getLeaderboard()).toBe(current);
  expect(current.leaderboard).toEqual([]);
  expect(fetch).toHaveBeenCalledTimes(2);
});

test("a mismatched edition response is rejected and can be retried", async () => {
  const fetch = vi.fn().mockResolvedValueOnce(Response.json(leaderboard))
    .mockResolvedValueOnce(Response.json({ ...leaderboard, edition_id: "1.1", leaderboard: [] }));
  vi.stubGlobal("fetch", fetch);
  await expect(getLeaderboard("1.1")).rejects.toThrow();
  expect((await getLeaderboard("1.1")).edition_id).toBe("1.1");
});

test("duplicate run ownership is rejected", () => {
  expect(() => parsePublicationDocument({ ...index, editions: [previousEdition,
    { ...currentEdition, runs: previousEdition.runs }],
  })).toThrow(/ownership/);
});

const route = (name: string, params: Record<string, string>) => ({
  name, params, fullPath: "/example/", query: {}, hash: "",
}) as RouteLocationNormalizedLoaded;

test("switching an episode preserves model and subject but never assumes a paired round", () => {
  seedPublicationData([index, previous]);
  const source = previousEdition.runs[0]!;
  const target = editionDestination(route("episode", {
    executionId: source.execution_id, targetId: "T-0001", trialId: "trial-003",
  }), currentEdition);
  expect(target).toEqual({ name: "subject", params: { executionId: "BX-current", targetId: "T-0001" },
    query: { editionNotice: "episode-scope" } });
  expect(editionDestination(route("subject", { executionId: source.execution_id, targetId: "T-0002" }), currentEdition))
    .toEqual({ name: "run", params: { executionId: "BX-current" }, query: { editionNotice: "missing-subject" } });
  expect(editionDestination(route("run", { executionId: previousEdition.runs[1]!.execution_id }), currentEdition))
    .toEqual({ name: "results", params: { editionId: "1.1" }, query: { editionNotice: "missing-model" } });
  expect(editionDestination(route("episode", { executionId: source.execution_id }), previousEdition))
    .toBe("/example/");
});

test("qualified transcript tokens are restricted to question answers and their edition", () => {
  const run = previousEdition.runs[0]!;
  const episode = parsePublicationDocument(fixture(
    `runs/${run.execution_id}/subjects/T-0001/episodes/trial-001.json`,
  )) as EpisodeDocument;
  const payload = structuredClone(episode);
  const turn = payload.episode.turns.find(turn => turn.turn_type === "action");
  if (turn === undefined || turn.turn_type !== "action") throw new Error("Missing fixture action");
  turn.answer = "RATHER_YES";
  turn.action = "GUESS";
  expect(() => parsePublicationDocument(payload)).toThrow(/answer/);
  turn.action = "ASK";
  expect(() => seedPublicationData([index, previous, payload])).toThrow(/Standard edition/);
  resetPublicationData();
  payload.edition_id = "1.1";
  expect(() => seedPublicationData([index, payload])).toThrow(/different edition/);
});

test("qualified question tokens retain their labels and never count as format violations", () => {
  const run = previousEdition.runs[0]!;
  const document = parsePublicationDocument(fixture(
    `runs/${run.execution_id}/subjects/T-0001/episodes/trial-001.json`,
  )) as EpisodeDocument;
  const episode = structuredClone(document.episode);
  const questions = episode.turns.filter(turn => turn.turn_type === "action" && turn.action === "ASK");
  for (const [index, answer] of ["RATHER_YES", "RATHER_NO"].entries()) {
    const turn = questions[index];
    if (turn === undefined || turn.turn_type !== "action") throw new Error("Missing question");
    turn.answer = answer as "RATHER_YES" | "RATHER_NO";
  }
  const wrapper = mount(EpisodeTranscriptPanel, { props: { episode } });
  expect(wrapper.get(".turn-map").text()).toContain("Rather yes");
  expect(wrapper.get(".turn-map").text()).toContain("Rather no");
  expect(wrapper.get(".turn-map").text()).not.toContain("FORMAT");
  expect(wrapper.findAll(".answer").map(answer => answer.text())).toEqual(
    expect.arrayContaining([expect.stringContaining("Rather yes"), expect.stringContaining("Rather no")]),
  );
  wrapper.unmount();
});
