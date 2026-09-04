import { expect, test } from "@playwright/test";

test(
  "homepage charts render near the viewport and survive resize and cached navigation",
  { tag: ["@performance", "@desktop", "@smoke"] },
  async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("http://127.0.0.1:4174/", { waitUntil: "networkidle" });
    const canvases = page.locator(".score-dot-plot-canvas");
    await expect(canvases).toHaveCount(2);
    await expect(canvases.locator("svg")).toHaveCount(0);
    await expect(page.locator(".ranking-table tbody tr").first()).toBeAttached();

    await canvases.first().scrollIntoViewIfNeeded();
    await expect(canvases.locator("svg")).toHaveCount(2);
    const firstLabel = canvases.first().locator("svg text").first();
    await expect(firstLabel).toBeVisible();
    await page.setViewportSize({ width: 1100, height: 720 });
    await expect.poll(async () => canvases.first().evaluate((element) => {
      const svg = element.querySelector("svg");
      return Number(svg?.getAttribute("width")) === element.clientWidth;
    })).toBe(true);

    await page.getByRole("navigation", { name: "Primary navigation", exact: true })
      .getByRole("link", { name: "Method", exact: true }).click();
    await expect(page).toHaveURL(/\/methodology\/$/);
    await page.goBack();
    await expect(page).toHaveURL("http://127.0.0.1:4174/");
    await canvases.first().scrollIntoViewIfNeeded();
    await expect(canvases.locator("svg")).toHaveCount(2);
    await expect(firstLabel).toBeVisible();
    expect(errors).toEqual([]);
  },
);
