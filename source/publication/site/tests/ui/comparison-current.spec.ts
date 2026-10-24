import { readFileSync } from "node:fs";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { ComparisonDocument } from "../../src/lib/types";
import { docsRoot, expectMinimumSize, expectNoViewportOverflow } from "./support/publication";

const comparison = (edition: string) => JSON.parse(readFileSync(path.join(
  docsRoot, "data/editions", edition, "compare.json"), "utf8")) as ComparisonDocument;
const current = comparison("1.1"); const previous = comparison("1.0");
const firstFive = current.models.slice(0, 5);
const ids = firstFive.map(model => model.result.model.model_id);
const equalBestScores = firstFive.filter(model =>
  model.result.question_score === firstFive[0]!.result.question_score).length;
const staticBase = "http://127.0.0.1:4174/";

test("uneven model names keep reasoning labels and run controls aligned as columns resize", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  const long = current.models.find(model => model.result.model.display_name === "Muse Spark 1.3 Contributor (high)")!;
  const short = current.models.find(model => model.result.model.display_name === "GPT-6 Luna (high)")!;
  const shortId = short.result.model.model_id;
  await page.goto(`${staticBase}editions/1.1/results/compare/?models=${shortId},${long.result.model.model_id}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  for (const width of [390, 320, 430, 768, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    for (const label of ["Main metric comparison", "Subject and round comparison"]) {
      const region = page.getByRole("region", { name: label, exact: true });
      await expect.poll(() => region.locator("thead .model-name-effort").evaluateAll(elements => {
        const tops = elements.map(element => element.getBoundingClientRect().top);
        return Math.max(...tops) - Math.min(...tops);
      })).toBeLessThanOrEqual(1);
      await expect.poll(() => region.locator("..").locator(".comparison-pinned-header .model-name-effort").evaluateAll(elements => {
        const tops = elements.map(element => element.getBoundingClientRect().top);
        return Math.max(...tops) - Math.min(...tops);
      })).toBeLessThanOrEqual(1);
      if (label === "Main metric comparison") {
        await expect.poll(() => region.locator(".compare-run summary").evaluateAll(elements => {
          const tops = elements.map(element => element.getBoundingClientRect().top);
          return Math.max(...tops) - Math.min(...tops);
        })).toBeLessThanOrEqual(1);
      }
    }
    await page.getByLabel("Show differences from", { exact: true }).selectOption(shortId);
    await expect.poll(() => page.locator(".compare-main-table .compare-run summary").evaluateAll(elements => {
      const tops = elements.map(element => element.getBoundingClientRect().top);
      return Math.max(...tops) - Math.min(...tops);
    })).toBeLessThanOrEqual(1);
    await page.getByLabel("Show differences from", { exact: true }).selectOption("");
    await expect(page.locator(".compare-main-table .model-name-variant").last()).toHaveText("Spark 1.3 Contributor");
    expect(await page.locator(".compare-main-table .model-name-variant").last().evaluate(element => {
      const range = window.document.createRange();
      const start = element.textContent!.indexOf("Contributor");
      range.setStart(element.firstChild!, start);
      range.setEnd(element.firstChild!, start + "Contributor".length);
      return range.getClientRects().length;
    })).toBe(1);
    await expectNoViewportOverflow(page);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  const title = page.locator(".compare-main-table .model-name").first();
  await expect.poll(async () => (await title.boundingBox())!.height).toBeGreaterThan(60);
  const tall = (await title.boundingBox())!.height;
  await page.locator(".compare-model-picker > summary").click();
  await page.getByRole("button", { name: `Remove ${long.result.model.display_name}`, exact: true }).click();
  const replacement = current.models.find(model => model.result.model.display_name === "Claude Haiku 5.5 (high)")!;
  await page.getByLabel("Add model", { exact: true }).selectOption(replacement.result.model.model_id);
  await expect.poll(async () => (await title.boundingBox())!.height).toBeLessThan(tall - 1);
  await expectNoViewportOverflow(page);
});

test("two model columns fit portrait phones and wider headers return to inline names", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.goto(`${staticBase}editions/1.1/results/compare/?models=${ids.slice(0, 2).join(',')}&expanded=T-0005`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  for (const width of [390, 430, 320]) {
    await page.setViewportSize({ width, height: 844 });
    for (const label of ["Main metric comparison", "Subject and round comparison"]) {
      const table = page.getByRole("region", { name: label, exact: true });
      await expect.poll(() => table.evaluate(element => element.scrollWidth - element.clientWidth)).toBeLessThanOrEqual(1);
      const bounds = (await table.boundingBox())!;
      const cells = table.locator("tbody tr").first().locator("td");
      for (const cell of await cells.all()) {
        const value = (await cell.locator("strong").boundingBox())!;
        expect(value.x).toBeGreaterThan(bounds.x);
        expect(value.x + value.width).toBeLessThanOrEqual(bounds.x + bounds.width);
      }
      const model = table.locator("thead .model-name").first();
      const family = (await model.locator(".model-name-family").boundingBox())!;
      const variant = (await model.locator(".model-name-variant").boundingBox())!;
      const effort = (await model.locator(".model-name-effort").boundingBox())!;
      expect(variant.y).toBeGreaterThanOrEqual(family.y + family.height - 1);
      expect(effort.y).toBeGreaterThanOrEqual(variant.y + variant.height - 1);
      await expect(model.locator(".model-name-label")).toHaveText(firstFive[0]!.result.model.display_name.replace(/ \([^)]+\)$/, ''));
    }
    await expect(page.locator(".compare-mobile-hint")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  }
  await page.locator(".compare-model-picker > summary").click();
  await page.getByLabel("Add model", { exact: true }).selectOption(ids[2]!);
  await expect(page.locator(".compare-selections li")).toHaveCount(3);
  await expect(page.locator(".compare-mobile-hint")).toHaveCount(2);
  await page.setViewportSize({ width: 1280, height: 844 });
  const model = page.getByRole("region", { name: "Main metric comparison", exact: true }).locator("thead .model-name").first();
  const family = (await model.locator(".model-name-family").boundingBox())!;
  const variant = (await model.locator(".model-name-variant").boundingBox())!;
  expect(Math.abs(family.y - variant.y)).toBeLessThanOrEqual(1);
  await expectNoViewportOverflow(page);
});

test("five-model static comparisons hydrate without extra result requests and fit narrow phones", { tag: ["@both", "@smoke"] }, async ({ page }, testInfo) => {
  const errors: string[] = []; const resultRequests: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (/hydration|mismatch/i.test(message.text())) errors.push(message.text()); });
  page.on("request", request => { if (/\/data\/(?:runs\/|editions\/[^/]+\/(?:compare|leaderboard|models))/.test(request.url())) resultRequests.push(request.url()); });
  await page.goto(`${staticBase}editions/1.1/results/compare/?models=${ids.join(',')}&expanded=T-0005`);
  await expect(page.locator(".compare-selections li")).toHaveCount(5);
  await expect(page.getByLabel("Add model", { exact: true })).toBeDisabled();
  await expect(page.locator('[data-metric="score"] td[data-state="best"]')).toHaveCount(equalBestScores === firstFive.length ? 0 : equalBestScores);
  await expect(page.locator('[data-subject="T-0005"] .compare-round-row')).toHaveCount(current.iterations);
  expect(resultRequests).toEqual([]);
  expect(errors).toEqual([]);
  await expectNoViewportOverflow(page);
  const aboutMetrics = page.getByRole("button", { name: "About metrics", exact: true });
  await expectMinimumSize(aboutMetrics, 44);
  await aboutMetrics.click();
  await expect(page.getByRole("dialog", { name: "About metrics", exact: true })).toContainText("Smaller means more consistent results across rounds.");
  await page.keyboard.press("Escape");
  await expect(aboutMetrics).toBeFocused();
  await page.locator(".compare-model-picker > summary").click();
  for (const button of await page.locator(".compare-selections button").all()) {
    await expectMinimumSize(button, 44);
  }
  for (const control of await page.locator(".compare-view select, .compare-view input").all()) {
    await expectMinimumSize(control, 44);
  }
  if (testInfo.project.name.startsWith("mobile")) {
    await page.setViewportSize({ width: 320, height: 720 });
    await expectNoViewportOverflow(page);
    const table = await page.getByRole("region", { name: "Main metric comparison", exact: true }).boundingBox();
    const firstScore = await page.locator('[data-metric="score"] td strong').first().boundingBox();
    expect(firstScore!.x + firstScore!.width).toBeLessThanOrEqual(table!.x + table!.width);
  }
  const result = await new AxeBuilder({ page }).include(".compare-view")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(result.violations).toEqual([]);
  await page.getByRole("button", { name: `Remove ${firstFive[4]!.result.model.display_name}`, exact: true }).click();
  await expect(page.locator(".compare-selections li")).toHaveCount(4);
  await expect(page.getByLabel("Add model", { exact: true })).toBeEnabled();
});

test("edition switches keep shared model identities and use destination round counts", { tag: ["@both", "@editions"] }, async ({ page }) => {
  const shared = current.models.find(model => previous.models.some(old => old.result.model.model_id === model.result.model.model_id))!;
  const missing = current.models.find(model => !previous.models.some(old => old.result.model.model_id === model.result.model.model_id))!;
  await page.goto(`${staticBase}editions/1.1/results/compare/?models=${shared.result.model.model_id},${missing.result.model.model_id}&expanded=T-0001`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await page.locator(".edition-trigger").click();
  await page.locator(".edition-links a").filter({ hasText: "v1.0" }).click();
  await expect(page).toHaveURL(/\/editions\/1.0\/results\/compare\//);
  await expect(page.locator(".compare-selections li")).toHaveCount(1);
  await expect(page.locator(".compare-notice")).toContainText("not in this edition");
  await expect(page.locator('[data-subject="T-0001"] .compare-round-row')).toHaveCount(previous.iterations);
  await expectNoViewportOverflow(page);
});
