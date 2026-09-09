// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { mount } from "@vue/test-utils";
import { describe, expect, test } from "vitest";
import EpisodeTranscriptPanel from "../../src/components/episode/EpisodeTranscriptPanel.vue";
import type { PublicEpisodeDetail } from "../../src/lib/types";

const fixture = JSON.parse(readFileSync("tests/fixtures/publication/data/runs/BX-20260728-official-M0001-010/subjects/T-0007/episodes/trial-001.json", "utf8")) as { episode: PublicEpisodeDetail };

describe("historical Oracle answers", () => {
  test("labels reuse across games within this benchmark run", () => {
    const episode = structuredClone(fixture.episode);
    const turn = episode.turns.find((value) => value.turn_type === "action" && value.action === "ASK");
    if (!turn || turn.turn_type !== "action") throw new Error("Missing ASK fixture");
    turn.oracle_cache = {
      scope: "same_execution", execution_id: "BX-current", model_id: "M-0001",
      benchmark_id: "B-0001", target_id: "T-0007", trial_id: "trial-001",
      episode_id: "EP-original", turn_number: 7, question: "Original question?",
      answered_at: "2026-09-08T10:00:00Z",
    };
    const wrapper = mount(EpisodeTranscriptPanel, { props: { episode } });
    const source = wrapper.get('[aria-label="Earlier game answer source"]');
    expect(source.text()).toContain("Answer reused from an earlier game in this benchmark run");
    expect(source.text()).toContain("trial-001 / 7");
    expect(source.find("button").exists()).toBe(false);
    for (const evidence of turn.evidence) expect(wrapper.text()).toContain(evidence.excerpt);
  });
  test("keeps long source summaries labelled and outside quotation blocks", () => {
    const episode = structuredClone(fixture.episode);
    const turn = episode.turns.find((value) => value.turn_type === "action" && value.action === "ASK");
    if (!turn || turn.turn_type !== "action") throw new Error("Missing ASK fixture");
    const context = "Source context with material qualifications. ".repeat(30);
    turn.evidence = [{ source_url: "https://example.test/summary", excerpt: context,
      validation: "model_reported", kind: "source_summary" }];
    const wrapper = mount(EpisodeTranscriptPanel, { props: { episode } });
    const article = wrapper.findAll(".evidence-list article").find((item) => item.text().includes(context.trim()));
    expect(article).toBeDefined();
    expect(article?.text()).toContain("Source summary (model-reported)");
    expect(article?.find("blockquote").exists()).toBe(false);
  });
  test("discloses source and retains evidence", () => {
    const episode = structuredClone(fixture.episode);
    const turn = episode.turns.find((value) => value.turn_type === "action" && value.action === "ASK");
    if (!turn || turn.turn_type !== "action") throw new Error("Missing ASK fixture");
    turn.oracle_cache = {
      execution_id: "BX-earlier-source", model_id: "M-0002", benchmark_id: "B-0001",
      target_id: "T-0007", trial_id: "trial-002", episode_id: "EP-original", turn_number: 7,
      question: "The ORIGINAL question?", answered_at: "2026-07-26T10:00:00+00:00",
    };
    const wrapper = mount(EpisodeTranscriptPanel, { props: { episode } });
    const source = wrapper.get('[aria-label="Historical answer source"]');
    expect(source.text()).toContain("Answer from an earlier test");
    expect(source.text()).toContain("BX-earlier-source");
    expect(source.text()).toContain("trial-002 / 7");
    expect(source.text()).toContain("The ORIGINAL question?");
    expect(source.find("details summary").text()).toBe("View original response");
    expect(source.get("time").attributes("datetime")).toBe(turn.oracle_cache.answered_at);
    for (const evidence of turn.evidence) expect(wrapper.text()).toContain(evidence.excerpt);
  });
  test("labels an answer from this game with its original turn", () => {
    const episode = structuredClone(fixture.episode);
    const turn = episode.turns.find((value) => value.turn_type === "action" && value.action === "ASK");
    if (!turn || turn.turn_type !== "action") throw new Error("Missing ASK fixture");
    turn.oracle_cache = {
      scope: "same_episode", target_id: "T-0007", episode_id: episode.episode_id,
      turn_number: 1, question: "The original live question?", answered_at: "2026-09-07T00:00:00Z",
    };
    const wrapper = mount(EpisodeTranscriptPanel, { props: { episode } });
    const source = wrapper.get('[aria-label="Earlier turn answer source"]');
    expect(source.text()).toContain("Answer reused from turn 1 of this game");
    expect(source.text()).toContain("The original live question?");
    expect(source.get("button").text()).toBe("Go to turn 1");
    expect(source.text()).not.toContain("earlier test");
    for (const evidence of turn.evidence) expect(wrapper.text()).toContain(evidence.excerpt);
  });
  test("leaves fresh historical transcripts unmarked", () => {
    const wrapper = mount(EpisodeTranscriptPanel, { props: { episode: fixture.episode } });
    expect(wrapper.find('[aria-label="Historical answer source"]').exists()).toBe(false);
  });
});
