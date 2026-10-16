import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import type { LeaderboardDocument, ManifestDocument } from "../../src/lib/types";
import { test as fixtureTest } from "./support/fixture";
import { docsRoot, expectNoViewportOverflow, waitForPublication } from "./support/publication";

const staticBase = "http://127.0.0.1:4174/";
const document = JSON.parse(readFileSync(
  path.join(docsRoot, "data/editions/1.1/leaderboard.json"), "utf8",
)) as LeaderboardDocument;
const first = document.leaderboard.find((row) => row.rank === 1);
if (first === undefined) throw new Error("The current edition needs a ranked result.");
const leaders = document.leaderboard.filter((row) => row.question_score === first.question_score);

test(
  "score ranks and subtle badges agree across the homepage, results and runs",
  { tag: ["@score-ranking", "@both", "@smoke"] },
  async ({ page }, testInfo) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(new URL("editions/1.1/", staticBase).href);
    await waitForPublication(page);
    const card = page.locator(".winner-card");
    await expect(card).toContainText(/over \d+ rounds/);
    for (const row of leaders) {
      await expect(card.locator(`[data-rank="${row.rank}"]`))
        .toHaveCount(leaders.filter((other) => other.rank === row.rank).length);
      await expect(card).toContainText(row.model.display_name);
    }
    if (leaders.length > 1) {
      if (leaders.filter((row) => row.rank === 1).length > 1) {
        await expect(card.locator("h3")).toHaveText("Tied for first place");
        const badges = card.locator(".winner-list [data-rank]");
        for (const badge of await badges.all()) await expect(badge).toHaveAttribute("data-rank", "1");
      } else {
        await expect(card.locator("h3")).toContainText(first.model.display_name);
        await expect(card).toContainText("Same average score as");
        await expect(card.locator('[data-rank="1"]')).toHaveAttribute("title", /narrower 95% CI/);
      }
    }
    await expect(card.locator(".score-confidence")).toContainText("95% CI");
    await expectNoViewportOverflow(page);
    await card.scrollIntoViewIfNeeded();
    await card.screenshot({ path: testInfo.outputPath("rank-card.png") });

    await page.goto(new URL("editions/1.1/results/", staticBase).href);
    await waitForPublication(page);
    await expect(page.locator(".score-ranking-note")).toContainText("then by narrower 95%");
    for (const row of leaders) {
      const visibleRow = page.locator("tbody tr, .mobile-result-card")
        .filter({ hasText: row.model.display_name }).filter({ visible: true });
      await expect(visibleRow.locator(`[data-rank="${row.rank}"]`))
        .toBeVisible();
    }

    for (const row of leaders) {
      await page.goto(new URL(`runs/${row.execution_id}/`, staticBase).href);
      await waitForPublication(page);
      await expect(page.locator(".run-search-facts")
        .locator(`[data-rank="${row.rank}"]`)).toBeVisible();
    }
    await page.goto(new URL("editions/1.0/", staticBase).href);
    await waitForPublication(page);
    await expect(page.locator(".score-ranking-note")).toHaveCount(0);
    expect(errors).toEqual([]);
  },
);

fixtureTest(
  "a wider-CI model stays outside the shared first-place list",
  { tag: ["@score-ranking", "@both", "@smoke"] },
  async ({ page }) => {
    const fixtureRoot = path.resolve("tests/fixtures/publication/data/editions/1.0");
    const leaderboard = JSON.parse(readFileSync(path.join(fixtureRoot, "leaderboard.json"), "utf8")) as LeaderboardDocument;
    const manifest = JSON.parse(readFileSync(path.join(fixtureRoot, "manifest.json"), "utf8")) as ManifestDocument;
    const contenders = leaderboard.leaderboard.slice(0, 3);
    for (const [index, row] of contenders.entries()) {
      row.rank = index < 2 ? 1 : 3;
      row.question_score = "12";
      if (row.question_score_confidence_interval === null) throw new Error("The fixture needs CIs.");
      row.question_score_confidence_interval.estimate = "12";
      row.question_score_confidence_interval.lower = index < 2 ? "11" : "10";
      row.question_score_confidence_interval.upper = index < 2 ? "13" : "14";
    }
    manifest.winner = {
      model_ids: contenders.slice(0, 2).map((row) => row.model.model_id),
      display_names: contenders.slice(0, 2).map((row) => row.model.display_name),
      question_score: "12", joint: true,
    };
    await page.route("**/deep-20-bench/data/editions/1.0/leaderboard.json", (route) =>
      route.fulfill({ json: leaderboard }));
    await page.route("**/deep-20-bench/data/editions/1.0/manifest.json", (route) =>
      route.fulfill({ json: manifest }));
    await page.goto("editions/1.0/");
    await waitForPublication(page);
    const card = page.locator(".winner-card");
    await expect(card.locator("h3")).toHaveText("Tied for first place");
    const list = card.locator(".winner-list");
    await expect(list.locator('[data-rank="1"][data-rank-tied="true"]')).toHaveCount(2);
    await expect(list).toContainText(contenders[0]!.model.display_name);
    await expect(list).toContainText(contenders[1]!.model.display_name);
    await expect(list).not.toContainText(contenders[2]!.model.display_name);
    await expect(card.locator(".winner-comparison")).toContainText(contenders[2]!.model.display_name);
    await expect(card.locator(".winner-comparison [data-rank]")).toHaveAttribute("data-rank", "3");
    await expect(card.locator(".score-confidence")).toContainText("95% CI");
    await expectNoViewportOverflow(page);
  },
);
