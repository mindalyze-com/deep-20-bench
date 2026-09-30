import { expect, test, type Page } from "@playwright/test";

import { waitForPublication } from "./support/publication";

const staticBase = "http://127.0.0.1:4174/";
const trackerUrl = "https://umami.me.mindalyze.com/script.js";
const visitorIdStorageKey = "deep20bench.visitor-id.v1";

interface Pageview {
  url: string;
  title: string;
  referrer: string;
  id: string;
}

// A local transport checks the application's integration without external analytics calls.
// An enabled automatic initial page view deliberately exposes a missing opt-out attribute.
const trackerScript = `(() => {
  const script = document.currentScript;
  window.__pageviews = [];
  window.__analyticsCalls = [];
  let id;
  window.umami = {
    identify: value => { id = value; window.__analyticsCalls.push('identify'); },
    track: payload => {
      window.__analyticsCalls.push('pageview');
      const defaults = { url: location.href, title: document.title, referrer: document.referrer, id };
      window.__pageviews.push(typeof payload === 'function' ? payload(defaults) : defaults);
    }
  };
  if (script.dataset.autoPageview !== 'false') window.umami.track();
})();`;

const views = (page: Page) => page.evaluate(() =>
  (window as Window & { __pageviews?: Pageview[] }).__pageviews ?? []);
const paths = async (page: Page) => (await views(page)).map(view => new URL(view.url).pathname);
const navigate = async (page: Page, name: string): Promise<void> => {
  const menu = page.locator(".mobile-navigation > summary");
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("link", { name, exact: true }).filter({ visible: true }).click();
};

test.beforeEach(async ({ context }) => {
  await context.route("https://umami.me.mindalyze.com/**", route => route.abort());
});

for (const timing of ["early", "late"] as const) {
  test(`one settled page view with ${timing} tracker loading`, { tag: ["@analytics", "@both"] }, async ({ page }) => {
    let release: () => void = () => undefined;
    const ready = new Promise<void>(resolve => { release = resolve; });
    await page.route(trackerUrl, async route => {
      if (timing === "late") await ready;
      await route.fulfill({ contentType: "text/javascript", body: trackerScript });
    });
    await page.goto(staticBase, { waitUntil: "domcontentloaded" });
    await waitForPublication(page);
    await expect(page).toHaveURL(`${staticBase}editions/1.1/`);
    release();
    await expect.poll(() => paths(page)).toEqual(["/editions/1.1/"]);
    await page.waitForTimeout(750);
    expect(await paths(page)).toEqual(["/editions/1.1/"]);
    await navigate(page, "Method");
    await expect.poll(() => paths(page)).toEqual(["/editions/1.1/", "/editions/1.1/methodology/"]);
    const captured = await views(page);
    expect(captured[1]?.referrer).toBe(captured[0]?.url);
    expect(captured[1]?.title).toContain("Method");
    await page.goBack();
    await expect.poll(() => paths(page)).toEqual(["/editions/1.1/", "/editions/1.1/methodology/", "/editions/1.1/"]);
    await page.goForward();
    await expect.poll(() => paths(page)).toEqual(["/editions/1.1/", "/editions/1.1/methodology/",
      "/editions/1.1/", "/editions/1.1/methodology/"]);
    await page.locator(".skip-link").evaluate((link: HTMLAnchorElement) => link.click());
    await page.waitForTimeout(400);
    expect(await views(page)).toHaveLength(4);
  });
}

test("a late tracker retains visits made before its script arrives", { tag: ["@analytics", "@both"] }, async ({ page }) => {
  let release: () => void = () => undefined;
  const ready = new Promise<void>(resolve => { release = resolve; });
  await page.route(trackerUrl, async route => {
    await ready;
    await route.fulfill({ contentType: "text/javascript", body: trackerScript });
  });
  await page.goto(staticBase, { waitUntil: "domcontentloaded" });
  await waitForPublication(page);
  await navigate(page, "About");
  await expect(page).toHaveURL(`${staticBase}editions/1.1/about/`);
  release();
  await expect.poll(() => paths(page)).toEqual(["/editions/1.1/", "/editions/1.1/about/"]);
  expect((await views(page))[0]?.title).toContain("Twenty Questions");
  expect((await views(page))[1]?.title).toBe(await page.title());
});

test("non-content routes explicitly opt out", { tag: ["@analytics", "@both"] }, async ({ page }) => {
  await page.route(trackerUrl, route => route.fulfill({ contentType: "text/javascript", body: trackerScript }));
  for (const path of ["not-a-published-page/", "editions/unknown/", "publication-unavailable/"]) {
    await page.goto(new URL(path, staticBase).href);
    await waitForPublication(page);
    expect(await views(page)).toEqual([]);
    expect(await page.evaluate(key => localStorage.getItem(key), visitorIdStorageKey)).toBeNull();
  }
});

test("blocked analytics leaves ordinary navigation working", { tag: ["@analytics", "@both"] }, async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(staticBase);
  await waitForPublication(page);
  await navigate(page, "Data");
  await expect(page).toHaveURL(`${staticBase}editions/1.1/data/`);
  await waitForPublication(page);
  expect(errors).toEqual([]);
});

test("visitor ID survives navigation, reloads, and tabs while separate profiles get different IDs",
  { tag: ["@analytics", "@both"] }, async ({ page, context, browser }) => {
    await context.route(trackerUrl, route => route.fulfill({ contentType: "text/javascript", body: trackerScript }));
    await page.goto(staticBase);
    await expect.poll(() => views(page)).toHaveLength(1);
    const id = (await views(page))[0]!.id;
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    await navigate(page, "Method");
    expect((await views(page)).map(view => view.id)).toEqual([id, id]);
    expect(await page.evaluate(() =>
      (window as Window & { __analyticsCalls?: string[] }).__analyticsCalls)).toEqual(["identify", "pageview", "pageview"]);
    await page.reload();
    await expect.poll(() => views(page)).toHaveLength(1);
    expect((await views(page))[0]?.id).toBe(id);
    expect(await page.evaluate(key => localStorage.getItem(key), visitorIdStorageKey)).toBe(id);

    const otherTab = await context.newPage();
    await otherTab.goto(staticBase);
    await expect.poll(() => views(otherTab)).toHaveLength(1);
    expect((await views(otherTab))[0]?.id).toBe(id);
    await otherTab.close();

    const otherProfile = await browser.newContext();
    try {
      await otherProfile.route("https://umami.me.mindalyze.com/**", route => route.abort());
      await otherProfile.route(trackerUrl, route => route.fulfill({ contentType: "text/javascript", body: trackerScript }));
      const otherPage = await otherProfile.newPage();
      await otherPage.goto(staticBase);
      await expect.poll(() => views(otherPage)).toHaveLength(1);
      expect((await views(otherPage))[0]?.id).not.toBe(id);
    } finally {
      await otherProfile.close();
    }

    const changedId = "ce2cd05e-eb34-42a8-ae24-e2abccfb8832";
    await page.evaluate(({ key, value }) => localStorage.setItem(key, value), { key: visitorIdStorageKey, value: changedId });
    await navigate(page, "Data");
    await expect.poll(() => views(page)).toHaveLength(2);
    expect((await views(page))[1]?.id).toBe(changedId);

    await page.evaluate(key => localStorage.removeItem(key), visitorIdStorageKey);
    await navigate(page, "About");
    await expect.poll(() => views(page)).toHaveLength(3);
    const newId = (await views(page))[2]!.id;
    expect(newId).not.toBe(changedId);
    expect(await page.evaluate(key => localStorage.getItem(key), visitorIdStorageKey)).toBe(newId);
    await page.reload();
    await expect.poll(() => views(page)).toHaveLength(1);
    expect((await views(page))[0]?.id).toBe(newId);
  });

test("ordinary random visitor IDs persist when crypto is unavailable", { tag: ["@analytics", "@both"] }, async ({ page }) => {
  await page.addInitScript(() => { Object.defineProperty(window, "crypto", { value: undefined }); });
  await page.route(trackerUrl, route => route.fulfill({ contentType: "text/javascript", body: trackerScript }));
  await page.goto(staticBase);
  await expect.poll(() => views(page)).toHaveLength(1);
  const id = (await views(page))[0]!.id;
  expect(id).toMatch(/^[0-9a-f-]{36}$/);
  await page.reload();
  await expect.poll(() => views(page)).toHaveLength(1);
  expect((await views(page))[0]?.id).toBe(id);
});

test("denied storage keeps a visitor ID for the page session", { tag: ["@analytics", "@both"] }, async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => { throw new Error("Storage denied"); };
    Storage.prototype.setItem = () => { throw new Error("Storage denied"); };
  });
  await page.route(trackerUrl, route => route.fulfill({ contentType: "text/javascript", body: trackerScript }));
  await page.goto(staticBase);
  await expect.poll(() => views(page)).toHaveLength(1);
  const id = (await views(page))[0]!.id;
  expect(id).toBeTruthy();
  await navigate(page, "Data");
  expect((await views(page)).map(view => view.id)).toEqual([id, id]);
  await page.reload();
  await expect.poll(() => views(page)).toHaveLength(1);
  expect((await views(page))[0]?.id).not.toBe(id);
  expect(errors).toEqual([]);
});
