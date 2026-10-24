import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";
import type { ComparisonDocument, ModelIndexDocument } from "../../src/lib/types";
import { splitModelName } from "../../src/lib/model-name";

import {
  derivePublicationPaths,
  docsRoot,
  expectNoViewportOverflow,
  waitForPublication,
} from "./support/publication";

const { episodePath, runPath, subjectPath } = derivePublicationPaths(
  path.join(docsRoot, "data"),
);

test("every current model opens from the model index and returns to it", {
  tag: ["@current-data", "@both", "@smoke"],
}, async ({ page }) => {
  test.setTimeout(90_000);
  const index = JSON.parse(readFileSync(path.join(
    docsRoot, "data/editions/1.1/models.json"), "utf8")) as ModelIndexDocument;
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("http://127.0.0.1:4174/editions/1.1/models/");
  await expect(page.locator(".model-index-table tbody tr")).toHaveCount(index.models.length);
  for (const entry of index.models) {
    await page.locator(`.model-index-table a[href$="/models/${entry.slug}/"]`).click();
    await expect(page.locator(".model-page h1")).toContainText(splitModelName(entry.model.display_name).displayName);
    await expect(page.locator(".model-page .run-callout")).toHaveAttribute("href", `/runs/${entry.execution_id}/`);
    await expectNoViewportOverflow(page);
    await page.getByRole("link", { name: "All models", exact: true }).click();
    await expect(page.locator(".model-index-table tbody tr")).toHaveCount(index.models.length);
  }
  expect(errors).toEqual([]);
});

test("comparison keeps sub-cent per-round costs visible on narrow phones and desktop", {
  tag: ["@current-data", "@both", "@smoke"],
}, async ({ page }, testInfo) => {
  const comparison = JSON.parse(readFileSync(path.join(
    docsRoot, "data/editions/1.1/compare.json"), "utf8")) as ComparisonDocument;
  const cheap = comparison.models.find(model => {
    const cost = Number(model.result.guesser_cost_per_episode_usd);
    return cost >= 0.0001 && cost < 0.005;
  });
  if (cheap === undefined) throw new Error("A published sub-cent model cost is required.");
  const other = comparison.models.find(model => model !== cheap)!;
  await page.goto(`http://127.0.0.1:4174/editions/1.1/results/compare/?models=${other.result.model.model_id},${cheap.result.model.model_id}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  const cost = page.locator('[data-metric="model-cost"] td strong').last();
  await expect(cost).toHaveText(`$${Number(cheap.result.guesser_cost_per_episode_usd).toFixed(4)}`);
  for (const width of [320, 390, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    const table = page.getByRole("region", { name: "Main metric comparison", exact: true });
    await expect.poll(() => table.evaluate(element => element.scrollWidth - element.clientWidth)).toBeLessThanOrEqual(1);
    const bounds = (await table.boundingBox())!;
    const value = (await cost.boundingBox())!;
    expect(value.x).toBeGreaterThan(bounds.x);
    expect(value.x + value.width).toBeLessThanOrEqual(bounds.x + bounds.width);
    await expectNoViewportOverflow(page);
  }
  if (testInfo.project.name.startsWith("mobile")) await page.setViewportSize({ width: 390, height: 844 });
  await page.locator(".compare-main-table").screenshot({ path: testInfo.outputPath("comparison-costs.png") });
  await page.locator('[data-metric="model-cost"]').screenshot({ path: testInfo.outputPath("comparison-cost-row.png") });
});

test(
  "the generated publication loads each dynamic page template",
  { tag: ["@current-data", "@desktop", "@smoke"] },
  async ({ page }) => {
    const browserErrors: string[] = [];
    const failedResponses: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("pageerror", (error) => browserErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) {
        failedResponses.push(`${response.status()} ${response.url()}`);
      }
    });

    for (const routePath of ["", "results/", runPath, subjectPath, episodePath]) {
      await page.goto(routePath);
      await waitForPublication(page);
      await expect(page.locator("h1").first()).toBeVisible();
    }

    expect(browserErrors).toEqual([]);
    expect(failedResponses).toEqual([]);
  },
);
