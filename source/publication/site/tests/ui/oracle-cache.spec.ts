import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "./support/fixture";
import { episodePath, expectNoViewportOverflow, waitForPublication } from "./support/publication";
import type { PublicEpisodeDetail } from "../../src/lib/types";

test("historical answer source is visible and expandable @both @smoke", async ({ page }) => {
  const documentPath = `${episodePath.replace(/\/$/, "")}.json`;
  const fixture = JSON.parse(readFileSync(path.resolve("tests/fixtures/publication/data", documentPath), "utf8")) as { episode: PublicEpisodeDetail };
  const turn = fixture.episode.turns.find((value) => value.turn_type === "action" && value.action === "ASK");
  if (!turn || turn.turn_type !== "action") throw new Error("Missing ASK fixture");
  turn.oracle_cache = {
    execution_id: "BX-earlier-response-source", model_id: "M-0002", benchmark_id: "B-0001",
    target_id: "T-0001", trial_id: "trial-002", episode_id: `EP-${"a".repeat(32)}`,
    turn_number: 7, question: "The original historical question?",
    answered_at: "2026-07-26T10:00:00+00:00",
  };
  await page.route(`**/data/${documentPath}`, route => route.fulfill({ json: fixture }));
  await page.goto(episodePath);
  await waitForPublication(page);
  await page.getByRole("tab", { name: /Transcript/i }).click();
  const source = page.getByRole("complementary", { name: "Historical answer source" });
  await expect(source.getByText("Answer from an earlier test")).toBeVisible();
  await source.getByText("View original response").click();
  await expect(source.getByText("BX-earlier-response-source")).toBeVisible();
  await expect(source.getByText("The original historical question?")).toBeVisible();
  await expectNoViewportOverflow(page);
});

test("same-game answer links back to its original turn @both @smoke", async ({ page }) => {
  const documentPath = `${episodePath.replace(/\/$/, "")}.json`;
  const fixture = JSON.parse(readFileSync(path.resolve("tests/fixtures/publication/data", documentPath), "utf8")) as { episode: PublicEpisodeDetail };
  const asks = fixture.episode.turns.filter(value => value.turn_type === "action" && value.action === "ASK");
  const original = asks[0];
  const repeated = asks[1];
  if (!original || !repeated || original.turn_type !== "action" || repeated.turn_type !== "action") throw new Error("Missing ASK fixtures");
  repeated.oracle_cache = {
    scope: "same_episode", target_id: "T-0007", episode_id: fixture.episode.episode_id,
    turn_number: original.turn_number, question: original.question!, answered_at: "2026-09-07T00:00:00Z",
  };
  await page.route(`**/data/${documentPath}`, route => route.fulfill({ json: fixture }));
  await page.goto(episodePath);
  await waitForPublication(page);
  await page.getByRole("tab", { name: /Transcript/i }).click();
  const source = page.getByRole("complementary", { name: "Earlier turn answer source" });
  await expect(source.getByText(`Answer reused from turn ${original.turn_number} of this game`)).toBeVisible();
  await source.getByText("View original response").click();
  await source.getByRole("button", { name: `Go to turn ${original.turn_number}` }).click();
  await expect(page.locator(`#turn-${original.turn_number}`)).toBeFocused();
  await expectNoViewportOverflow(page);
});
