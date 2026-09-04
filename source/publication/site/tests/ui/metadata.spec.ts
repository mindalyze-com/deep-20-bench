import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { parseRouteMetadata } from "../../src/lib/route-metadata";
import { docsRoot, staticPaths, waitForPublication } from "./support/publication";

const staticBase = "http://127.0.0.1:4174/";
const routes = parseRouteMetadata(JSON.parse(
  readFileSync(path.join(docsRoot, "data", "routes.json"), "utf8"),
) as unknown);
const subjects = routes.filter((entry) => /\/subjects\/[^/]+$/.test(entry.route));
const firstSubject = subjects[0];
const secondSubject = subjects.find((entry) =>
  entry.route !== firstSubject?.route &&
  entry.route.split("/subjects/")[1] === firstSubject?.route.split("/subjects/")[1],
);
if (firstSubject === undefined || secondSubject === undefined) {
  throw new Error("Metadata tests require the same subject in two model runs.");
}
const episode = routes.find((entry) => entry.route.startsWith(`${firstSubject.route}/episodes/`));
if (episode === undefined) throw new Error("Metadata tests require a public episode.");

const readHead = (page: Page) => page.evaluate(() => ({
  title: document.title,
  description: document.querySelector('meta[name="description"]')?.getAttribute("content") ?? null,
  canonical: document.querySelector('link[rel="canonical"]')?.getAttribute("href") ?? null,
  robots: document.querySelector('meta[name="robots"]')?.getAttribute("content") ?? null,
  ogTitle: document.querySelector('meta[property="og:title"]')?.getAttribute("content") ?? null,
  ogSiteName: document.querySelector('meta[property="og:site_name"]')?.getAttribute("content") ?? null,
  ogDescription: document.querySelector('meta[property="og:description"]')?.getAttribute("content") ?? null,
  ogUrl: document.querySelector('meta[property="og:url"]')?.getAttribute("content") ?? null,
  twitterTitle: document.querySelector('meta[name="twitter:title"]')?.getAttribute("content") ?? null,
  twitterDescription: document.querySelector('meta[name="twitter:description"]')?.getAttribute("content") ?? null,
}));

test("initial SEO metadata survives hydration", { tag: ["@metadata", "@desktop"] }, async ({ browser, page }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const initial = await context.newPage();
  try {
    const paths = [
      ...staticPaths,
      "story/",
      `${firstSubject.route.split("/subjects/")[0]}/`,
      `${firstSubject.route}/`,
      `${secondSubject.route}/`,
      `${episode.route}/`,
    ];
    for (const route of paths) {
      const url = new URL(route, staticBase).href;
      await initial.goto(url);
      const expected = await readHead(initial);
      await page.goto(url);
      await waitForPublication(page);
      await expect.poll(() => readHead(page), { message: route || "homepage" }).toEqual(expected);
    }
  } finally {
    await context.close();
  }
});

test("client navigation keeps full metadata and restores indexing after an episode", { tag: ["@metadata", "@desktop"] }, async ({ page }) => {
  await page.goto(staticBase);
  await waitForPublication(page);
  const paths = [
    "results",
    firstSubject.route.split("/subjects/")[0]!,
    firstSubject.route,
    episode.route,
    firstSubject.route,
    "results",
    secondSubject.route.split("/subjects/")[0]!,
    secondSubject.route,
    "",
  ];
  for (const route of paths) {
    const href = `/${route === "" ? "" : `${route}/`}`;
    await page.locator(`a[href="${href}"]:not([tabindex="-1"])`).filter({ visible: true }).first().click();
    await expect(page).toHaveURL(new URL(href, staticBase).href);
    await waitForPublication(page);
    const expected = routes.find((entry) => entry.route === route);
    if (expected === undefined) throw new Error(`Missing metadata for ${route}.`);
    const head = await readHead(page);
    expect(head.title).toBe(expected.browser_title);
    expect(head.description).toBe(expected.description);
    expect(head.ogTitle).toBe(expected.browser_title);
    expect(head.ogSiteName).toBe("Deep20Bench");
    expect(head.twitterTitle).toBe(expected.browser_title);
    expect(head.robots).toBe(expected.indexable ? null : "noindex, follow");
  }
});
