import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import type { ComparisonDocument, EditionsDocument } from "../../src/lib/types";
import { expect, test } from "./support/fixture";

const data = resolve("tests/fixtures/publication/data");
const index = JSON.parse(readFileSync(resolve(data, "editions.json"), "utf8")) as EditionsDocument;
const comparison = JSON.parse(readFileSync(resolve(data, "editions/1.0/compare.json"), "utf8")) as ComparisonDocument;
const added = comparison.models[0]!.result;
const oldIndex: EditionsDocument = { ...index, editions: index.editions.map(edition => ({
  ...edition,
  runs: edition.runs.filter(run => run.execution_id !== added.execution_id),
  models: edition.models.filter(model => model.model_id !== added.model.model_id),
})) };

test("an older cached index recovers comparison navigation automatically", {
  tag: ["@both", "@smoke", "@editions"],
}, async ({ page }) => {
  let indexRequests = 0;
  let comparisonRequests = 0;
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("request", request => {
    if (new URL(request.url()).pathname.endsWith("/compare.json")) comparisonRequests++;
  });
  await page.route("**/data/editions.json", async route => {
    indexRequests++;
    await route.fulfill({ json: indexRequests === 1 ? oldIndex : index });
  });
  await page.goto("editions/1.0/results/");
  await page.locator(".results-nav").getByRole("link", { name: "Compare", exact: true }).click();
  await expect(page.getByLabel("Add model", { exact: true })).toBeVisible();
  expect(indexRequests).toBe(2);
  expect(comparisonRequests).toBe(2);
  await expect(page.locator(".error-state")).toHaveCount(0);
  await page.getByLabel("Add model", { exact: true }).selectOption(added.model.model_id);
  await expect(page.locator(".compare-selections li")).toHaveCount(1);
  await expect(page.locator('[data-metric="score"] td')).toHaveCount(1);
  await page.getByLabel("Metric", { exact: true }).selectOption("cost");
  await expect(page).toHaveURL(new RegExp(`models=${added.model.model_id}.*metric=cost`));
  expect(indexRequests).toBe(2);
  expect(comparisonRequests).toBe(2);
  expect(errors).toEqual([]);
});

test("automatic refresh preserves the selected models, reference, metric and expanded rounds", {
  tag: ["@both", "@smoke", "@editions"],
}, async ({ page }) => {
  let indexRequests = 0;
  const ids = comparison.models.slice(0, 2).map(model => model.result.model.model_id);
  const subject = comparison.target_ids[0]!;
  await page.route("**/data/editions.json", async route => {
    indexRequests++;
    await route.fulfill({ json: indexRequests === 1 ? oldIndex : index });
  });
  const query = `models=${ids.join(",")}&baseline=${ids[0]}&metric=cost&expanded=${subject}`;
  await page.goto(`editions/1.0/results/compare/?${query}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect(page.getByLabel("Metric", { exact: true })).toHaveValue("cost");
  await expect(page.getByLabel("Show differences from", { exact: true })).toHaveValue(ids[0]!);
  await expect(page.locator(`[data-subject="${subject}"] .compare-round-row`)).toHaveCount(comparison.iterations);
  expect(new URL(page.url()).search.slice(1)).toBe(query);
  expect(indexRequests).toBe(2);
  await expect(page.locator(".error-state")).toHaveCount(0);
});

test("a comparison that still conflicts after one refresh shows an error without looping", {
  tag: ["@both", "@smoke", "@editions"],
}, async ({ page }) => {
  let indexRequests = 0;
  let comparisonRequests = 0;
  page.on("request", request => {
    if (new URL(request.url()).pathname.endsWith("/compare.json")) comparisonRequests++;
  });
  await page.route("**/data/editions.json", async route => {
    indexRequests++;
    await route.fulfill({ json: oldIndex });
  });
  await page.goto(`editions/1.0/results/compare/?models=${added.model.model_id}&metric=cost`);
  await expect(page.getByRole("alert")).toContainText("Comparison results belong to a different edition.");
  await expect(page.getByRole("button", { name: "Try again", exact: true })).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`models=${added.model.model_id}&metric=cost`));
  expect(indexRequests).toBe(2);
  expect(comparisonRequests).toBe(2);
});
