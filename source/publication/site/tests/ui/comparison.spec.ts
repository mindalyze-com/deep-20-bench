import { readFileSync } from "node:fs";
import path from "node:path";
import type { ComparisonDocument } from "../../src/lib/types";
import { expect, test } from "./support/fixture";
import { expectMinimumSize, expectNoViewportOverflow, modelPath, waitForPublication } from "./support/publication";

const document = JSON.parse(readFileSync(path.resolve(
  "tests/fixtures/publication/data/editions/1.0/compare.json"), "utf8")) as ComparisonDocument;
const selected = document.models.slice(0, 2);
const modelIds = selected.map(model => model.result.model.model_id);
const firstSubject = selected[0]!.subjects[0]!;

test("compare loads one bundle and shares model, metric, reference and expanded-round state", { tag: ["@both", "@smoke"] }, async ({ page }) => {
  const dataRequests: string[] = [];
  page.on("request", request => { if (new URL(request.url()).pathname.includes("/data/")) dataRequests.push(request.url()); });
  await page.goto("results/");
  await waitForPublication(page);
  dataRequests.length = 0;
  await page.locator(".results-nav").getByRole("link", { name: "Compare", exact: true }).click();
  await expect(page.getByLabel("Add model", { exact: true })).toBeVisible();
  for (const id of modelIds) await page.getByLabel("Add model", { exact: true }).selectOption(id);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect(page.locator('[data-metric="score"] td')).toHaveCount(2);
  await page.getByRole("button", { name: `Expand rounds for ${firstSubject.display_name}`, exact: true }).click();
  await expect(page.locator(`[data-subject="${firstSubject.target_id}"] .compare-round-row`)).toHaveCount(document.iterations);
  await page.getByLabel("Metric", { exact: true }).selectOption("cost");
  await page.getByLabel("Show differences from").selectOption(modelIds[0]!);
  await page.getByLabel("Sort subjects").selectOption("gap");
  await expect(page).toHaveURL(/models=.*metric=cost/);
  expect(dataRequests.filter(url => url.endsWith("/compare.json"))).toHaveLength(1);
  expect(dataRequests.filter(url => url.includes("/data/runs/") || /\/data\/editions\/[^/]+\/models\//.test(url))).toHaveLength(0);
  await expectNoViewportOverflow(page);

  await page.evaluate(() => {
    Object.defineProperty(navigator, "share", { configurable: true, value: undefined });
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: async (value: string) => { sessionStorage.setItem("copied-comparison", value); } },
    });
  });
  await page.getByRole("button", { name: "Share", exact: true }).click();
  await page.getByRole("button", { name: "Copy comparison link", exact: true }).click();
  await expect(page.locator(".compare-status")).toHaveText("Link copied.");
  expect(await page.evaluate(() => sessionStorage.getItem("copied-comparison"))).toBe(page.url());

  const shared = page.url();
  await page.reload();
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect(page.getByLabel("Metric", { exact: true })).toHaveValue("cost");
  await expect(page.getByLabel("Show differences from")).toHaveValue(modelIds[0]!);
  await expect(page.locator(`[data-subject="${firstSubject.target_id}"] .compare-round-row`)).toHaveCount(document.iterations);
  expect(page.url()).toBe(shared);
  await expect(page.locator(".compare-scroll").last()).toBeVisible();
  const scroll = page.locator(".compare-scroll").last();
  await scroll.evaluate(element => { element.scrollLeft = element.scrollWidth; });
  const label = scroll.locator("thead th").first();
  const bounds = await label.boundingBox(); const container = await scroll.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(container!.x);
  expect(bounds!.x).toBeLessThan(container!.x + 4);
  await expectNoViewportOverflow(page);
});

test("model picker marks chosen models, rejects repeat selections and allows re-adding removed models", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await page.locator(".compare-model-picker > summary").click();
  const picker = page.getByLabel("Add model", { exact: true });
  const original = page.url();
  for (const model of selected) {
    const option = picker.locator(`option[value="${model.result.model.model_id}"]`);
    await expect(option).toHaveCount(1);
    await expect(option).toHaveJSProperty("disabled", true);
    await expect(option).toHaveText(`${model.result.model.display_name} - selected`);
  }
  // A native picker can deliver a choice made before its options refreshed.
  await picker.evaluate(async (element: HTMLSelectElement, id) => {
    element.value = id;
    element.dispatchEvent(new Event("change", { bubbles: true }));
    await new Promise<void>(resolve => requestAnimationFrame(() => resolve()));
  }, modelIds[0]!);
  await expect(picker).toHaveValue("");
  await expect(page).toHaveURL(original);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect(page.locator('[data-metric="score"] td')).toHaveCount(2);
  await page.getByRole("button", { name: `Remove ${selected[0]!.result.model.display_name}`, exact: true }).click();
  const removed = picker.locator(`option[value="${modelIds[0]}"]`);
  await expect(removed).toHaveJSProperty("disabled", false);
  await expect(removed).toHaveText(selected[0]!.result.model.display_name);
  await picker.selectOption(modelIds[0]!);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect(removed).toHaveJSProperty("disabled", true);
  await expect(picker).toHaveValue("");
  await expect(page.locator('[data-metric="score"] td')).toHaveCount(2);
  await expectNoViewportOverflow(page);
});

test("model-page entry preselects its model and comparison links open real rounds", { tag: ["@both"] }, async ({ page }) => {
  await page.goto(modelPath);
  await waitForPublication(page);
  const link = page.getByRole("link", { name: "Compare this model", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  await expect(page.locator(".compare-selections li")).toHaveCount(1);
  await expect(page.locator('.compare-table td[data-state="best"], .compare-table td[data-state="worst"]')).toHaveCount(0);
  const button = page.getByRole("button", { name: `Expand rounds for ${firstSubject.display_name}`, exact: true });
  await button.click();
  await page.locator(".compare-round-link").first().click();
  await expect(page).toHaveURL(/\/runs\/[^/]+\/subjects\/T-\d+\/episodes\/trial-\d+\//);
  await expect(page.locator(".episode-hero")).toBeVisible();
});

test("unavailable models are explained and a failed bundle request can be retried", { tag: ["@both"] }, async ({ page }) => {
  await page.route("**/compare.json", route => route.fulfill({ status: 503, body: "Unavailable" }));
  await page.goto(`editions/1.0/results/compare/?models=${modelIds[0]},M-9999`);
  await expect(page.getByRole("button", { name: "Try again", exact: true })).toBeVisible();
  await page.unroute("**/compare.json");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.locator(".compare-selections li")).toHaveCount(1);
  await expect(page.locator(".compare-notice")).toContainText("M-9999");
  await expectNoViewportOverflow(page);
});

test("sharing offers copying and can close by button, toggle or Escape", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await page.evaluate(() => {
    Object.defineProperty(navigator, "share", { configurable: true, value: undefined });
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: undefined });
    window.document.execCommand = () => false;
  });
  const share = page.getByRole("button", { name: "Share", exact: true });
  const panel = page.getByRole("region", { name: "Share comparison", exact: true });
  await share.click();
  await expect(share).toHaveAttribute("aria-expanded", "true");
  const field = page.getByLabel("Comparison link", { exact: true });
  await expect(field).toHaveValue(page.url());
  expect(await field.evaluate((input: HTMLInputElement) =>
    input.selectionStart === 0 && input.selectionEnd === input.value.length)).toBe(true);
  const copy = page.getByRole("button", { name: "Copy comparison link", exact: true });
  await expectMinimumSize(copy, 44);
  await copy.click();
  await expect(page.locator(".compare-status")).toContainText("Select the link and copy it");
  await expect(field).toBeFocused();
  await page.evaluate(() => {
    window.document.execCommand = command => {
      const input = window.document.activeElement as HTMLInputElement;
      if (command !== "copy" || input.selectionStart !== 0 || input.selectionEnd !== input.value.length) return false;
      sessionStorage.setItem("copied-comparison", input.value);
      return true;
    };
  });
  await copy.click();
  expect(await page.evaluate(() => sessionStorage.getItem("copied-comparison"))).toBe(page.url());
  await expect(page.locator(".compare-status")).toHaveText("Link copied.");
  await expect(copy).toHaveText("Copied");
  await expect(copy).toBeFocused();
  await expect(panel).toBeVisible();
  await share.click();
  await expect(panel).toHaveCount(0);
  await expect(share).toBeFocused();
  await share.click();
  await page.keyboard.press("Escape");
  await expect(panel).toHaveCount(0);
  await expect(share).toBeFocused();
  await share.click();
  const close = panel.getByRole("button", { name: "Close", exact: true });
  await expectMinimumSize(close, 44);
  await close.click();
  await expect(panel).toHaveCount(0);
  await expect(share).toBeFocused();
  await expectNoViewportOverflow(page);
});

test("native sharing receives the full comparison and cancellation stays quiet", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}&expanded=${firstSubject.target_id}&metric=cost`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await page.evaluate(() => {
    Object.defineProperty(navigator, "share", { configurable: true, value: async (data: ShareData) => {
      sessionStorage.setItem("shared-comparison", JSON.stringify(data));
    } });
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async () => {
      throw new Error("Native sharing must not also copy to the clipboard.");
    } } });
  });
  const share = page.getByRole("button", { name: "Share", exact: true });
  await share.click();
  expect(JSON.parse((await page.evaluate(() => sessionStorage.getItem("shared-comparison")))!))
    .toEqual({ title: "Deep20Bench comparison", url: page.url() });
  await expect(page.getByLabel("Comparison link", { exact: true })).toHaveCount(0);
  await page.evaluate(() => Object.defineProperty(navigator, "share", { configurable: true, value: async () => {
    throw new DOMException("Canceled", "AbortError");
  } }));
  await share.click();
  await expect(share).toBeEnabled();
  await expect(page.getByLabel("Comparison link", { exact: true })).toHaveCount(0);
  await expect(page.locator(".compare-status")).toBeEmpty();
  await page.evaluate(() => Object.defineProperty(navigator, "share", { configurable: true, value: async () => {
    throw new DOMException("Blocked", "NotAllowedError");
  } }));
  await share.click();
  await expect(page.getByLabel("Comparison link", { exact: true })).toHaveValue(page.url());
  await expect(share).toBeEnabled();
  await page.evaluate(() => { window.document.execCommand = () => false; });
  await page.getByRole("button", { name: "Copy comparison link", exact: true }).click();
  await expect(page.locator(".compare-status")).toHaveText("Could not copy automatically. Select the link and copy it.");
  await expect(page.getByLabel("Comparison link", { exact: true })).toBeFocused();
});

test("subject names and averages expand before offering explicit detail links", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}`);
  const subject = page.locator(`[data-subject="${firstSubject.target_id}"]`);
  await expect(subject.locator(".compare-round-row")).toHaveCount(0);
  await expect(subject.locator("a")).toHaveCount(0);
  await expect(subject.locator(".compare-subject-row button")).toHaveCount(1);
  const disclosure = subject.locator(".compare-expand");
  await disclosure.focus();
  await page.keyboard.press("Enter");
  await expect(disclosure).toHaveAttribute("aria-expanded", "true");
  await expect(subject.locator(".compare-round-row")).toHaveCount(document.iterations);
  await page.keyboard.press("Space");
  await expect(disclosure).toHaveAttribute("aria-expanded", "false");
  await subject.locator(".compare-average-cell").nth(1).click();
  await expect(page).toHaveURL(/results\/compare\/.*expanded=/);
  await expect(disclosure).toHaveAttribute("aria-expanded", "true");
  const link = subject.locator(".compare-subject-row .compare-subject-link").first();
  await expect(link).toContainText("Open subject");
  await expectMinimumSize(link, 44);
  await expect(link).toHaveAttribute("href", new RegExp(`/runs/${selected[0]!.result.execution_id}/subjects/${firstSubject.target_id}/\\?compare=`));
  await link.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/runs/${selected[0]!.result.execution_id}/subjects/${firstSubject.target_id}/\\?compare=`));
  await expect(page.locator(".episode-rail-heading h1")).toContainText(firstSubject.display_name);
  await page.getByRole("link", { name: "Back to comparison", exact: true }).click();
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect(disclosure).toHaveAttribute("aria-expanded", "true");
  await disclosure.focus();
  await page.keyboard.press("Space");
  await expect(disclosure).toHaveAttribute("aria-expanded", "false");
  await expect(subject.locator("a")).toHaveCount(0);
  await expectNoViewportOverflow(page);
});

test("subject and round comparison match the compact visual baseline", { tag: ["@both", "@visual"] }, async ({ page }) => {
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}&expanded=${firstSubject.target_id}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  // A full-table capture extends beyond the viewport. Cover pinned headers separately,
  // without baking viewport overlays or the skip link into the table's visual baseline.
  await page.addStyleTag({ content: ".comparison-pinned-header, .skip-link { visibility: hidden !important; }" });
  await expect(page.getByRole("region", { name: "Main metric comparison", exact: true }))
    .toHaveScreenshot("comparison-main-metrics.webp");
  await expect(page.getByRole("region", { name: "Subject and round comparison", exact: true }))
    .toHaveScreenshot("comparison-subject-rounds.webp");
});

test("compact round details keep raw counts when the scored value differs", { tag: ["@both"] }, async ({ page }) => {
  const model = document.models.find(item => item.subjects.some(subject => subject.rounds.some(round =>
    round.penalized_questions !== null && Number(round.penalized_questions) !== round.counted_questions)))!;
  const subject = model.subjects.find(item => item.rounds.some(round =>
    round.penalized_questions !== null && Number(round.penalized_questions) !== round.counted_questions))!;
  const penalized = subject.rounds.find(round => Number(round.penalized_questions) !== round.counted_questions)!;
  const solved = subject.rounds.find(round => round.status === "success" && Number(round.penalized_questions) === round.counted_questions)!;
  await page.goto(`editions/1.0/results/compare/?models=${model.result.model.model_id}&expanded=${subject.target_id}`);
  const rows = page.locator(`[data-subject="${subject.target_id}"]`);
  const penalizedCell = rows.locator(`[data-round="${penalized.trial_number}"] .compare-round-link`);
  await expect(penalizedCell.locator("strong")).toHaveText(penalized.penalized_questions!);
  await expect(penalizedCell).toContainText(`${penalized.counted_questions} counted`);
  await expect(rows.locator(`[data-round="${solved.trial_number}"] .compare-counted`)).toHaveCount(0);
});

test("subject and round links return to the comparison settings and table position", { tag: ["@both", "@smoke"] }, async ({ page }) => {
  const path = `editions/1.0/results/compare/?models=${modelIds.join(',')}&expanded=${firstSubject.target_id}&metric=cost&baseline=${modelIds[0]}&sort=gap`;
  for (const selector of [".compare-subject-link", ".compare-round-link"]) {
    await page.goto(path);
    await expect(page.locator(".compare-selections li")).toHaveCount(2);
    const origin = page.url();
    // Initial document scroll restoration retries through 220 ms. Let it settle before
    // Playwright's programmatic scrolling, which is not a real user scroll gesture.
    await page.waitForTimeout(250);
    const table = page.getByRole("region", { name: "Subject and round comparison", exact: true });
    const link = page.locator(`[data-subject="${firstSubject.target_id}"] ${selector}`).nth(1);
    await link.scrollIntoViewIfNeeded();
    const top = await page.evaluate(() => window.scrollY);
    const left = await table.evaluate(element => element.scrollLeft);
    await link.click();
    const back = page.getByRole("link", { name: "Back to comparison", exact: true });
    await expect(back).toBeVisible();
    await expectMinimumSize(back, 44);
    const originUrl = new URL(origin);
    await expect(back).toHaveAttribute("href", originUrl.pathname + originUrl.search);
    await back.click();
    await expect(page).toHaveURL(origin);
    await expect(page.locator(".compare-selections li")).toHaveCount(2);
    await expect(page.getByLabel("Metric", { exact: true })).toHaveValue("cost");
    await expect(page.getByLabel("Show differences from")).toHaveValue(modelIds[0]!);
    await expect(page.getByLabel("Sort subjects")).toHaveValue("gap");
    await expect(page.locator(`[data-subject="${firstSubject.target_id}"] .compare-round-row`)).toHaveCount(document.iterations);
    await expect.poll(() => page.evaluate(expected => Math.abs(window.scrollY - expected), top)).toBeLessThanOrEqual(2);
    await expect.poll(() => table.evaluate((element, expected) => Math.abs(element.scrollLeft - expected), left)).toBeLessThanOrEqual(2);
    await expectNoViewportOverflow(page);
  }
});

test("comparison return context survives deeper navigation and reload, and browser Back restores the table", { tag: ["@both", "@smoke"] }, async ({ page }) => {
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}&expanded=${firstSubject.target_id}&metric=duration`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  const origin = page.url();
  await page.waitForTimeout(250);
  const table = page.getByRole("region", { name: "Subject and round comparison", exact: true });
  const subjectLink = page.locator(`[data-subject="${firstSubject.target_id}"] .compare-subject-link`).nth(1);
  await subjectLink.scrollIntoViewIfNeeded();
  const originalTop = await page.evaluate(() => window.scrollY);
  const originalLeft = await table.evaluate(element => element.scrollLeft);
  await subjectLink.click();
  await expect(page.getByRole("link", { name: "Back to comparison", exact: true })).toBeVisible();
  await page.locator(".episode-list a").first().click();
  await expect(page.locator(".episode-hero")).toBeVisible();
  await page.reload();
  await page.route("**/compare.json", async route => {
    await new Promise(resolve => setTimeout(resolve, 450));
    await route.fallback();
  });
  await page.getByRole("link", { name: "Back to comparison", exact: true }).click();
  await expect(page).toHaveURL(origin);
  await expect(page.getByLabel("Metric", { exact: true })).toHaveValue("duration");
  await expect.poll(() => page.evaluate(expected => Math.abs(window.scrollY - expected), originalTop)).toBeLessThanOrEqual(2);
  await expect.poll(() => table.evaluate((element, expected) => Math.abs(element.scrollLeft - expected), originalLeft)).toBeLessThanOrEqual(2);
  await page.unroute("**/compare.json");
  await page.waitForTimeout(250);
  const link = page.locator(`[data-subject="${firstSubject.target_id}"] .compare-round-link`).nth(1);
  const action = link.locator(".compare-detail-action");
  await action.scrollIntoViewIfNeeded();
  const top = await page.evaluate(() => window.scrollY);
  await link.click();
  await expect(page.locator(".episode-hero")).toBeVisible();
  const canonical = new URL(page.url()).pathname;
  await page.goBack();
  await expect(page).toHaveURL(origin);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  await expect.poll(() => page.evaluate(expected => Math.abs(window.scrollY - expected), top)).toBeLessThanOrEqual(2);
  await page.goto(canonical);
  await expect(page.locator(".episode-hero")).toBeVisible();
  await expect(page.getByRole("link", { name: "Back to comparison", exact: true })).toHaveCount(0);
});

test("compact model headers stay aligned while the page and tables scroll", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  const five = document.models.slice(0, 5).map(model => model.result.model.model_id);
  await page.goto(`editions/1.0/results/compare/?models=${five.join(',')}&expanded=${document.target_ids.join(',')}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(five.length);
  await page.waitForTimeout(250);
  for (const label of ["Main metric comparison", "Subject and round comparison"]) {
    const table = page.getByRole("region", { name: label, exact: true });
    const shell = table.locator("..");
    const header = shell.locator(".comparison-pinned-header");
    const headerScroll = shell.locator(".comparison-header-scroll");
    await table.evaluate(element => window.scrollTo({ top: window.scrollY + element.getBoundingClientRect().top + 200 }));
    await expect(header).toBeVisible();
    await expect.poll(async () => Math.abs((await header.boundingBox())!.y)).toBeLessThanOrEqual(1);
    await table.evaluate(element => { element.scrollLeft = element.scrollWidth - element.clientWidth; });
    await expect.poll(async () => Math.abs(await headerScroll.evaluate(element => element.scrollLeft)
      - await table.evaluate(element => element.scrollLeft))).toBeLessThanOrEqual(1);
    const positions = await shell.evaluate(element => {
      const visible = element.querySelectorAll(".comparison-pinned-header th");
      const original = element.querySelectorAll(".compare-scroll thead th");
      return [...original].map((cell, index) => Math.abs(cell.getBoundingClientRect().x - visible[index]!.getBoundingClientRect().x));
    });
    expect(Math.max(...positions)).toBeLessThanOrEqual(1);
    await headerScroll.evaluate(element => { element.scrollLeft = 0; });
    await expect.poll(() => table.evaluate(element => element.scrollLeft)).toBe(0);
    expect(await table.evaluate(element => element.scrollHeight - element.clientHeight)).toBeLessThanOrEqual(1);
    await expectNoViewportOverflow(page);
  }
  await expect(page.locator(".comparison-pinned-header").first()).not.toBeVisible();
  await page.evaluate(() => window.scrollTo({ top: 0 }));
  await expect(page.locator(".comparison-pinned-header.is-pinned")).toHaveCount(0);
});

test("mobile averages expand the shared subject and expose labeled navigation", { tag: ["@mobile", "@smoke", "@editions"] }, async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`editions/1.0/results/compare/?models=${modelIds.join(',')}`);
  await expect(page.locator(".compare-selections li")).toHaveCount(2);
  const table = page.getByRole("region", { name: "Subject and round comparison", exact: true });
  const subject = page.locator(`[data-subject="${firstSubject.target_id}"]`);
  for (const width of [390, 430, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await table.evaluate(element => { element.scrollLeft = element.scrollWidth - element.clientWidth; });
    await subject.locator(".compare-average-cell").nth(1).click();
    await expect(subject.locator(".compare-expand")).toHaveAttribute("aria-expanded", "true");
    await expect(subject.locator(".compare-subject-link")).toHaveCount(2);
    await expect(subject.locator(".compare-round-link")).toHaveCount(document.iterations * 2);
    const link = subject.locator(".compare-round-link").nth(1);
    await expect(link).toContainText("Open round");
    await expectMinimumSize(link, 44);
    await page.getByLabel("Metric", { exact: true }).selectOption("cost");
    await expect(link).toContainText("$");
    await subject.locator(".compare-average-cell strong").nth(1).click();
    await expect(subject.locator("a")).toHaveCount(0);
    await expect(subject.locator(".compare-expand")).toHaveAttribute("aria-expanded", "false");
    await page.getByLabel("Metric", { exact: true }).selectOption("questions");
    await expectNoViewportOverflow(page);
  }
});
