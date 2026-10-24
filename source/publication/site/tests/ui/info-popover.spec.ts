import type { Locator, Page } from "@playwright/test";
import { expect, test } from "./support/fixture";
import { expectMinimumSize, expectNoViewportOverflow, runPath, waitForPublication } from "./support/publication";

const expectAnchored = async (page: Page, trigger: Locator, panel: Locator): Promise<void> => {
  await expect(panel).toBeVisible();
  await expect(panel).toHaveClass(/info-popover-panel--positioned/);
  await expect.poll(async () => {
    const anchor = (await trigger.boundingBox())!;
    const box = (await panel.boundingBox())!;
    const placement = await panel.getAttribute("data-placement");
    return placement === "below" ? Math.abs(box.y - anchor.y - anchor.height - 8)
      : placement === "above" ? Math.abs(anchor.y - box.y - box.height - 8) : 0;
  }).toBeLessThanOrEqual(2);
  const box = (await panel.boundingBox())!;
  const viewport = await page.evaluate(() => ({
    left: window.visualViewport?.offsetLeft ?? 0,
    top: window.visualViewport?.offsetTop ?? 0,
    width: window.visualViewport?.width ?? window.document.documentElement.clientWidth,
    height: window.visualViewport?.height ?? window.innerHeight,
  }));
  expect(box.x).toBeGreaterThanOrEqual(viewport.left + 11);
  expect(box.y).toBeGreaterThanOrEqual(viewport.top + 11);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.left + viewport.width - 11);
  expect(box.y + box.height).toBeLessThanOrEqual(viewport.top + viewport.height - 11);
  await expectMinimumSize(panel.getByRole("button", { name: "Close explanation", exact: true }), 44);
};

test("shared explanations stay anchored across all result views and run scores", { tag: ["@both", "@smoke", "@editions"] }, async ({ page, browserName }) => {
  test.setTimeout(60_000);
  for (const route of ["results/", "results/cost/", "results/time/", "results/reliability/", "results/efficiency/", "results/compare/", runPath]) {
    await page.goto(route);
    await waitForPublication(page);
    if (route === "results/compare/") await page.getByLabel("Add model", { exact: true }).selectOption({ index: 1 });
    // Allow the app's initial document scroll restoration to settle before
    // Playwright scrolls off-screen explanation buttons into view.
    await page.waitForTimeout(250);
    const triggers = await page.locator(".info-popover-trigger:visible").all();
    expect(triggers.length, route).toBeGreaterThan(0);
    for (const trigger of triggers) {
      await trigger.click();
      const panel = page.locator(`[id="${await trigger.getAttribute("aria-controls")}"]`);
      await expectAnchored(page, trigger, panel);
      await expect(trigger).toBeFocused();
      await expect(trigger).toHaveAttribute("aria-expanded", "true");
      // WebKit on macOS uses Option-Tab to include buttons in keyboard navigation.
      await page.keyboard.press(browserName === "webkit" ? "Alt+Tab" : "Tab");
      await expect(panel.getByRole("button", { name: "Close explanation", exact: true })).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(panel).not.toBeVisible();
      await expect(trigger).toHaveAttribute("aria-expanded", "false");
      await expect(trigger).toBeFocused();
    }
    await expectNoViewportOverflow(page);
  }
});

test("edge placement follows scrolling and resizing without leaving detached panels", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("results/cost/");
  await waitForPublication(page);
  await page.waitForTimeout(250);
  const trigger = page.getByRole("button", { name: "How this page is ordered", exact: true });
  const panel = page.getByRole("dialog", { name: "How this page is ordered", exact: true });
  const placements = new Set<string>();
  for (const size of [{ width: 320, height: 568 }, { width: 430, height: 740 }, { width: 768, height: 1024 }, { width: 1280, height: 720 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(size);
    await trigger.evaluate(element => window.scrollTo({ top: window.scrollY + element.getBoundingClientRect().bottom - window.innerHeight + 24 }));
    await trigger.click();
    await expectAnchored(page, trigger, panel);
    placements.add((await panel.getAttribute("data-placement"))!);
    await page.evaluate(() => window.scrollBy(0, 40));
    await expectAnchored(page, trigger, panel);
    await page.setViewportSize({ ...size, height: size.height + 90 });
    await expectAnchored(page, trigger, panel);
    await page.getByRole("button", { name: "Close explanation", exact: true }).click();
    await expect(panel).not.toBeVisible();
    await expect(trigger).toBeFocused();
  }
  expect([...placements]).toEqual(expect.arrayContaining(["above", "below"]));
  await trigger.click();
  await expect(panel).toBeVisible();
  await page.evaluate(() => window.scrollTo({ top: window.document.documentElement.scrollHeight }));
  await expect(panel).not.toBeVisible();
  await expect.poll(() => page.evaluate(() => Math.abs(window.document.documentElement.scrollHeight - window.innerHeight - window.scrollY))).toBeLessThanOrEqual(2);
});

test("explanations toggle, dismiss outside, and replace the previous open panel", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.goto("results/cost/");
  await waitForPublication(page);
  await page.waitForTimeout(250);
  const first = page.getByRole("button", { name: "Per round", exact: true });
  const second = page.getByRole("button", { name: "Rerun rounds", exact: true });
  await first.click();
  await expect(page.getByRole("dialog", { name: "Per round", exact: true })).toBeVisible();
  await second.press("Enter");
  await expect(page.getByRole("dialog")).toHaveCount(1);
  await expect(page.getByRole("dialog", { name: "Rerun rounds", exact: true })).toBeVisible();
  await expect(first).toHaveAttribute("aria-expanded", "false");
  await second.press("Enter");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await first.click();
  await expect(page.getByRole("dialog")).toHaveCount(1);
  await page.mouse.click(5, 5);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expectNoViewportOverflow(page);
});

test("long metric explanations keep their close control visible while the text scrolls", { tag: ["@both", "@smoke", "@editions"] }, async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 480 });
  await page.goto("results/compare/");
  await waitForPublication(page);
  await page.getByLabel("Add model", { exact: true }).selectOption({ index: 1 });
  await page.waitForTimeout(250);
  const trigger = page.getByRole("button", { name: "About metrics", exact: true });
  await trigger.click();
  const panel = page.getByRole("dialog", { name: "About metrics", exact: true });
  await expectAnchored(page, trigger, panel);
  const close = panel.getByRole("button", { name: "Close explanation", exact: true });
  const top = (await close.boundingBox())!.y;
  const body = panel.locator(".info-popover-body");
  expect(await body.evaluate(element => element.scrollHeight > element.clientHeight)).toBe(true);
  await body.evaluate(element => { element.scrollTop = element.scrollHeight; });
  expect(Math.abs((await close.boundingBox())!.y - top)).toBeLessThanOrEqual(1);
  await expect(close).toBeInViewport();
  await close.click();
  await expect(trigger).toBeFocused();
});
