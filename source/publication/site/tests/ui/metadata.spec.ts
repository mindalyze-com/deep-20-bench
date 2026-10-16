import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { parseRouteMetadata } from "../../src/lib/route-metadata";
import { docsRoot, staticPaths, waitForPublication } from "./support/publication";

const staticBase = "http://127.0.0.1:4174/";
test.beforeEach(async ({ page }) => {
  await page.route("https://**/*", (route) => route.abort());
});

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

// Results link each model's stable page; the run is one step further.
const editionsIndex = JSON.parse(readFileSync(path.join(docsRoot, "data", "editions.json"), "utf8")) as {
  editions: { edition_id: string; models: { model_id: string; slug: string }[] }[];
};
const modelRouteForRun = (runRoute: string): string => {
  const run = JSON.parse(readFileSync(path.join(docsRoot, "data", `${runRoute}.json`), "utf8")) as {
    edition_id: string; run: { model_id: string };
  };
  const slug = editionsIndex.editions.find((edition) => edition.edition_id === run.edition_id)
    ?.models.find((model) => model.model_id === run.run.model_id)?.slug;
  if (slug === undefined) throw new Error(`Run ${runRoute} has no model page.`);
  return `editions/${run.edition_id}/models/${slug}`;
};

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
  structuredData: [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map((script) => JSON.parse(script.textContent ?? "null") as unknown),
}));

test("initial SEO metadata survives hydration", { tag: ["@metadata", "@desktop"] }, async ({ browser, page }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const initial = await context.newPage();
  try {
    const paths = [
      ...staticPaths,
      ...routes.filter((entry) => /^editions\/[^/]+(?:\/[^/]+)*$/.test(entry.route))
        .map((entry) => `${entry.route}/`),
      "story/",
      `${firstSubject.route.split("/subjects/")[0]}/`,
      `${firstSubject.route}/`,
      `${secondSubject.route}/`,
      `${episode.route}/`,
    ];
    // Every edition page is checked, including one page per model, so allow time per page.
    test.setTimeout(Math.max(30_000, paths.length * 1_000));
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

test("client navigation keeps full metadata and permits indexing on every page", { tag: ["@metadata", "@desktop"] }, async ({ page }) => {
  const owner = JSON.parse(readFileSync(path.join(
    docsRoot, "data", `${firstSubject.route.split("/subjects/")[0]}.json`,
  ), "utf8")) as { edition_id: string };
  const editionHome = `editions/${owner.edition_id}`;
  await page.goto(new URL(`${editionHome}/`, staticBase).href);
  await waitForPublication(page);
  const firstRun = firstSubject.route.split("/subjects/")[0]!;
  const secondRun = secondSubject.route.split("/subjects/")[0]!;
  const paths = [
    `${editionHome}/results`,
    modelRouteForRun(firstRun),
    firstRun,
    firstSubject.route,
    episode.route,
    firstSubject.route,
    `${editionHome}/results`,
    modelRouteForRun(secondRun),
    secondRun,
    secondSubject.route,
    editionHome,
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
    expect(head.robots).toBeNull();
  }
});

test("edition switching keeps dataset markup aligned with the page", { tag: ["@metadata", "@desktop"] }, async ({ browser, page }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const initial = await context.newPage();
  const homes = routes.filter((entry) => /^editions\/[^/]+$/.test(entry.route));
  try {
    await page.goto(new URL(`${homes[0]!.route}/`, staticBase).href);
    await waitForPublication(page);
    for (const home of [...homes.slice(1), homes[0]!]) {
      await initial.goto(new URL(`${home.route}/`, staticBase).href);
      const expected = await readHead(initial);
      await page.locator(".edition-trigger").click();
      await page.locator(`.edition-links a[href="/${home.route}/"]`).click();
      await expect.poll(() => readHead(page)).toEqual(expected);

      const resultsPath = `${home.route}/results/`;
      await initial.goto(new URL(resultsPath, staticBase).href);
      const resultsHead = await readHead(initial);
      await page.locator(`.primary-navigation a[href="/${resultsPath}"]`).click();
      await expect.poll(() => readHead(page)).toEqual(resultsHead);

      await page.locator(`.wordmark[href="/${home.route}/"]`).click();
      await expect.poll(() => readHead(page)).toEqual(expected);
    }
  } finally {
    await context.close();
  }
});
