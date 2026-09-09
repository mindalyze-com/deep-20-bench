import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { docsRoot, derivePublicationPaths, expectNoViewportOverflow } from "./support/publication";
import { readFileSync } from "node:fs";
import path from "node:path";
import type { EditionsDocument } from "../../src/lib/types";

const base = "http://127.0.0.1:4174/";
const editions = JSON.parse(readFileSync(path.join(docsRoot, "data/editions.json"), "utf8")) as EditionsDocument;
const switchEdition = async (page: Page, id: string) => {
  if (await page.locator(".edition-picker").getAttribute("open") === null) {
    await page.locator(".edition-trigger").click();
  }
  await page.locator(".edition-links a").filter({ hasText: id === "1.1" ? "Current" : "Previous" }).click();
};

test("default edition, metric navigation, browser history and downloads stay scoped", { tag: ["@editions", "@both", "@smoke"] }, async ({ page }) => {
  await page.goto(new URL("results/cost/", base).href);
  await expect(page).toHaveURL(/editions\/1\.1\/results\/cost\/$/);
  await expect(page.locator(".edition-empty")).toHaveCount(0);
  await expect(page.locator(".results-nav a.active")).toHaveText("Cost");
  await expect(page.locator(".edition-summary")).toContainText("3 rounds per subject");
  await expect(page.locator(".edition-summary")).toContainText("Rather yes");
  await switchEdition(page, "1.0");
  await expect(page).toHaveURL(/editions\/1\.0\/results\/cost\/$/);
  await expect(page.locator(".edition-summary")).toContainText("5 rounds per subject");
  await expect(page.locator(".edition-empty")).toHaveCount(0);
  await expect(page.locator(".results-nav a.active")).toHaveText("Cost");
  await page.goBack();
  await expect(page).toHaveURL(/editions\/1\.1\/results\/cost\/$/);
  await expect(page.locator(".edition-empty")).toHaveCount(0);
  await page.goto(new URL("editions/1.1/data/", base).href);
  await expect(page.getByRole("link", { name: "Download JSON" })).toHaveAttribute("href", /data\/editions\/1.1\/deep20bench-v10.json$/);
  await expect(page.getByRole("link", { name: "v9 dataset" })).toHaveAttribute("href", /data\/deep20bench-v9.json$/);
  await switchEdition(page, "1.0");
  await expect(page.getByRole("link", { name: "Download JSON" })).toHaveAttribute("href", /data\/editions\/1.0\/deep20bench-v10.json$/);
  await expectNoViewportOverflow(page);
});

test("old deep links identify edition 1 and explain missing counterparts", { tag: ["@editions", "@both"] }, async ({ page }) => {
  const currentModels = new Set(editions.editions.find(edition => edition.edition_id === "1.1")!.runs.map(run => run.model_id));
  const missingRun = editions.editions.find(edition => edition.edition_id === "1.0")!.runs.find(run => !currentModels.has(run.model_id));
  expect(missingRun).toBeDefined();
  const paths = derivePublicationPaths(path.join(docsRoot, "data"), missingRun!.execution_id);
  await page.goto(new URL(paths.episodePath, base).href);
  await expect(page.locator(".episode-tabs")).toBeVisible();
  await expect(page.locator(".edition-links [aria-current]")).toHaveText(/v\.1\.0\s*Previous/);
  await switchEdition(page, "1.1");
  await expect(page).toHaveURL(/editions\/1.1\/results\/\?editionNotice=missing-model$/);
  await expect(page.getByRole("status").filter({ hasText: "This model has no complete result" })).toBeVisible();
  await expect(page.locator(".ranking-table tbody tr")).not.toHaveCount(0);
});

test("edition comparison remains accessible on narrow screens", { tag: ["@editions", "@both"] }, async ({ page }) => {
  await page.goto(new URL("editions/1.1/methodology/#editions", base).href);
  await expect(page.locator("#editions")).toContainText("What changed in 1.1");
  await expect(page.locator("#editions")).toContainText("Version 1.1");
  await expect(page.locator("#editions")).toContainText("Version 1");
  await expectNoViewportOverflow(page);
  await page.locator(".edition-trigger").click();
  const audit = await new AxeBuilder({ page }).include(".edition-bar").include("#editions")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(audit.violations).toEqual([]);
});

test("the phone edition picker stays readable and large enough to tap", { tag: ["@editions", "@mobile"] }, async ({ page }) => {
  for (const width of [320, 390, 480]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(new URL("editions/1.1/results/", base).href);
    const trigger = page.locator(".edition-trigger");
    await expect(trigger).toBeVisible();
    expect((await trigger.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await expect(page.locator(".edition-summary")).toBeHidden();
    await trigger.tap();
    await expect(page.locator(".edition-summary")).toBeVisible();
    await expect(page.locator(".edition-summary")).toContainText("10 subjects");
    for (const link of await page.locator(".edition-panel a").all()) {
      expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }
    const panel = (await page.locator(".edition-panel").boundingBox())!;
    expect(panel.x).toBeGreaterThanOrEqual(0);
    expect(panel.x + panel.width).toBeLessThanOrEqual(width);
    await page.locator(".edition-changes").tap();
    await expect(page).toHaveURL(/methodology\/#editions$/);
    await expect(page.locator(".edition-panel")).toBeHidden();
    await expectNoViewportOverflow(page);
  }
});

test("edition hover and keyboard focus preview settings without switching", { tag: ["@editions", "@desktop"] }, async ({ page }) => {
  await page.goto(new URL("editions/1.1/", base).href);
  const trigger = page.locator(".edition-trigger");
  const summary = page.locator(".edition-summary");
  const previous = page.locator(".edition-links a").filter({ hasText: "Previous" });
  await trigger.click();
  await previous.hover();
  await expect(summary.locator(".edition-label")).toHaveText("Edition 1.0 settings");
  await expect(summary).toContainText("7 subjects");
  await expect(summary).toContainText("5 rounds per subject");
  await expect(summary).toContainText("50 question limit");
  await expect(summary).not.toContainText("Rather yes");
  await expect(page).toHaveURL(/editions\/1\.1\/$/);
  await expect(trigger).toContainText("v.1.1");
  await expect(page.locator(".edition-links [aria-current]")).toContainText("v.1.1");
  await summary.hover();
  await expect(summary.locator(".edition-label")).toHaveText("Edition 1.0 settings");
  await page.locator(".wordmark").hover();
  await expect(summary.locator(".edition-label")).toHaveText("Edition 1.1 settings");
  await expect(summary).toContainText("Rather yes");

  await page.keyboard.press("Escape");
  await page.keyboard.press("Enter");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await expect(previous).toBeFocused();
  await expect(summary.locator(".edition-label")).toHaveText("Edition 1.0 settings");
  await page.keyboard.press("Escape");
  await page.keyboard.press("Enter");
  await expect(summary.locator(".edition-label")).toHaveText("Edition 1.1 settings");
  await previous.hover();
  await summary.locator(".edition-changes").click();
  await expect(page).toHaveURL(/editions\/1\.0\/methodology\/#editions$/);
});

test("late edition preview responses cannot replace newer settings", { tag: ["@editions", "@desktop"] }, async ({ page }) => {
  let release = (): void => {};
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/data/editions/1.0/manifest.json", async route => {
    await pending;
    await route.continue();
  });
  try {
    await page.goto(new URL("editions/1.1/", base).href);
    await page.locator(".edition-trigger").click();
    const summary = page.locator(".edition-summary");
    await page.locator(".edition-links a").filter({ hasText: "Previous" }).hover();
    await expect(summary).toContainText("Loading settings");
    await page.locator(".edition-links a").filter({ hasText: "Current" }).hover();
    await expect(summary.locator(".edition-label")).toHaveText("Edition 1.1 settings");
    const response = page.waitForResponse("**/data/editions/1.0/manifest.json");
    release();
    await (await response).finished();
    await expect(summary).toContainText("10 subjects");
    await expect(summary).toContainText("3 rounds per subject");
    await expect(summary).toContainText("Rather yes");
    await expect(page.locator(".edition-trigger")).toContainText("v.1.1");
  } finally { release(); }
});

test("failed edition previews keep the active edition usable", { tag: ["@editions", "@desktop"] }, async ({ page }) => {
  await page.route("**/data/editions/1.0/manifest.json", route => route.fulfill({ status: 503 }));
  await page.goto(new URL("editions/1.1/", base).href);
  await page.locator(".edition-trigger").click();
  const summary = page.locator(".edition-summary");
  await page.locator(".edition-links a").filter({ hasText: "Previous" }).hover();
  await expect(summary).toContainText("Settings could not be loaded.");
  await expect(summary.locator(".edition-facts")).toHaveCount(0);
  await expect(page).toHaveURL(/editions\/1\.1\/$/);
  await page.locator(".edition-links a").filter({ hasText: "Current" }).hover();
  await expect(summary).toContainText("10 subjects");
  await expect(summary).toContainText("Rather yes");
});

test("unavailable edition settings show an error with a working retry", { tag: ["@editions", "@desktop"] }, async ({ page }) => {
  await page.route("**/data/editions/1.1/manifest.json", route => route.fulfill({ status: 503 }));
  await page.goto(new URL("editions/1.0/results/", base).href);
  await expect(page.locator(".ranking-table tbody tr")).not.toHaveCount(0);
  await switchEdition(page, "1.1");
  await expect(page.getByRole("alert")).toContainText("edition settings could not be loaded");
  await page.unroute("**/data/editions/1.1/manifest.json");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page).toHaveURL(/editions\/1\.1\/results\/$/);
  await expect(page.locator(".ranking-table tbody tr")).not.toHaveCount(0);
});

test("both editions can be selected without JavaScript", { tag: ["@editions", "@both"] }, async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 800 } });
  try {
    const page = await context.newPage();
    await page.goto(base);
    await expect(page.locator(".edition-trigger")).toContainText("v.1.1");
    await switchEdition(page, "1.0");
    await expect(page.locator(".edition-trigger")).toContainText("v.1.0");
    await (await primaryLink(page, "About")).click();
    await expect(page).toHaveURL(/editions\/1.0\/about\/$/);
    await expect(page.locator(".edition-links [aria-current]")).toHaveText(/v\.1\.0\s*Previous/);
    await (await primaryLink(page, "Results")).click();
    await expect(page).toHaveURL(/editions\/1.0\/results\/$/);
    await expect(page.locator(".edition-empty")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  } finally { await context.close(); }
});

test("an unknown edition stays unavailable instead of showing another edition's scores", { tag: ["@editions", "@desktop"] }, async ({ page }) => {
  await page.goto(new URL("editions/9.9/", base).href);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("unavailable");
  await expect(page.locator(".ranking-table")).toHaveCount(0);
  await expect(page.locator("#route-content a")).toHaveCount(2);
});

test("an older embedded schema is replaced with current edition data", { tag: ["@editions", "@desktop"] }, async ({ page }) => {
  await page.route("**/editions/1.1/", async route => {
    const response = await route.fetch();
    const body = (await response.text()).replace(
      /(<script id="deep20-page-state" type="application\/json">)[\s\S]*?(<\/script>)/,
      '$1{"schema_version":0,"documents":[]}$2',
    );
    expect(body).toContain('"schema_version":0,"documents":[]');
    await route.fulfill({ response, body });
  });
  await page.goto(new URL("editions/1.1/", base).href);
  await expect(page.locator(".ranking-table tbody tr")).not.toHaveCount(0);
  await switchEdition(page, "1.0");
  await expect(page.locator(".ranking-table tbody tr")).not.toHaveCount(0);
});

const primaryLink = async (page: Page, name: string) => {
  const desktop = page.getByRole("navigation", { name: "Primary navigation", exact: true });
  if (await desktop.isVisible()) return desktop.getByRole("link", { name, exact: true });
  await page.locator(".mobile-navigation summary").click();
  return page.getByRole("navigation", { name: "Mobile primary navigation", exact: true })
    .getByRole("link", { name, exact: true });
};

test("About preserves edition selection across navigation and reload", { tag: ["@editions", "@both", "@smoke"] }, async ({ page }) => {
  await page.goto(new URL("editions/1.0/results/", base).href);
  await (await primaryLink(page, "About")).click();
  await expect(page).toHaveURL(/editions\/1.0\/about\/$/);
  await expect(page.locator(".edition-links [aria-current]")).toHaveText(/v\.1\.0\s*Previous/);
  await page.reload();
  await expect(page.locator(".edition-links [aria-current]")).toHaveText(/v\.1\.0\s*Previous/);
  await (await primaryLink(page, "Results")).click();
  await expect(page).toHaveURL(/editions\/1.0\/results\/$/);
  await expect(page.locator(".edition-empty")).toHaveCount(0);
  await page.goBack();
  await expect(page).toHaveURL(/editions\/1.0\/about\/$/);
  await switchEdition(page, "1.1");
  await expect(page).toHaveURL(/editions\/1.1\/about\/$/);
  await expect(page.locator(".edition-links [aria-current]")).toHaveText(/v\.1\.1\s*Current/);
});

test("a slow edition switch keeps the selector consistent with the displayed data", { tag: ["@editions", "@both"] }, async ({ page }) => {
  await page.goto(new URL("editions/1.0/results/", base).href);
  let release: () => void = () => {};
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/data/editions/1.1/manifest.json", async route => {
    await gate;
    await route.continue();
  });
  try {
    await switchEdition(page, "1.1");
    await expect(page.getByRole("status").filter({ hasText: "Loading edition 1.1" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Results 1");
    await expect(page.locator(".edition-links [aria-current]")).toHaveText(/v\.1\.0\s*Previous/);
    await expect(page.locator(".edition-trigger")).toContainText("v.1.0");
    await page.locator(".edition-trigger").click();
    await expect(page.locator(".edition-links a").first()).toHaveAttribute("aria-disabled", "true");
    await page.locator(".edition-links a").first().dispatchEvent("click");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Results 1");
  } finally { release(); }
  await expect(page).toHaveURL(/editions\/1.1\/results\/$/);
  await expect(page.locator(".ranking-table tbody tr")).not.toHaveCount(0);
  await expect(page.getByRole("status").filter({ hasText: "Loading edition" })).toHaveCount(0);
  await expect(page.locator(".edition-trigger")).toContainText("v.1.1");
  await expect(page.locator(".edition-panel")).toBeHidden();
  await expect(page.locator(".edition-links [aria-disabled]")).toHaveCount(0);
});

test("desktop edition links work by keyboard and tablet controls have touch targets", { tag: ["@editions", "@desktop"] }, async ({ browser, page }) => {
  await page.goto(new URL("editions/1.1/results/", base).href);
  const trigger = page.locator(".edition-trigger");
  await trigger.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".edition-panel")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(".edition-links a").first()).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator(".edition-panel")).toBeHidden();
  await expect(trigger).toBeFocused();
  await page.keyboard.press("Space");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await expect(page.locator(".edition-links a").filter({ hasText: "Previous" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/editions\/1.0\/results\/$/);
  await trigger.click();
  await page.getByRole("heading", { level: 1 }).click();
  await expect(page.locator(".edition-panel")).toBeHidden();
  const context = await browser.newContext({ viewport: { width: 768, height: 1024 }, hasTouch: true });
  try {
    const tablet = await context.newPage();
    await tablet.goto(new URL("editions/1.0/results/", base).href);
    await tablet.locator(".edition-trigger").tap();
    const current = tablet.locator(".edition-links a").filter({ hasText: "Current" });
    expect((await current.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await current.tap();
    await expect(tablet).toHaveURL(/editions\/1.1\/results\/$/);
    await expectNoViewportOverflow(tablet);
  } finally { await context.close(); }
});
