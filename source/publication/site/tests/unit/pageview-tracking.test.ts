// @vitest-environment jsdom

import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { installPageviewTracking } from "../../src/lib/pageview-tracking";
import { createVisitorIdReader, VISITOR_ID_STORAGE_KEY } from "../../src/lib/visitor-id";

type TrackPayload = Parameters<NonNullable<Window["umami"]>["track"]>[0];
type Pageview = ReturnType<TrackPayload>;

let delivered: Pageview[];
let stop: (() => void) | undefined;
const defaults = { url: "https://stale.example/", title: "Stale", referrer: "",
  website: "fixture-website", hostname: "localhost", screen: "1280x720", language: "en" };
const track = vi.fn((payload: TrackPayload): void => { delivered.push(payload(defaults)); });
const identify = vi.fn((_id: string): void => undefined);

beforeEach(() => {
  window.localStorage.clear();
  document.head.innerHTML = '<script id="deep20-analytics"></script>';
  delivered = [];
  track.mockReset();
  track.mockImplementation(payload => { delivered.push(payload(defaults)); });
  identify.mockReset();
  delete window.umami;
});

afterEach(() => {
  stop?.();
  stop = undefined;
  delete window.umami;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

const setup = async () => {
  const component = { template: "<p>Content</p>" };
  const router = createRouter({
    history: createMemoryHistory("/preview/"),
    routes: [
      { path: "/", redirect: "/editions/1.1/" },
      { path: "/editions/1.1/", component },
      { path: "/new-page/", component },
      { path: "/episode/", component },
      { path: "/excluded/", component, meta: { trackPageview: false } },
      { path: "/blocked/", component },
    ],
  });
  router.afterEach(to => { document.title = `Page ${to.path}`; });
  await router.push("/");
  await router.isReady();
  stop = installPageviewTracking(router);
  return router;
};

const pathname = (view: Pageview): string => new URL(view.url).pathname;

test("an early tracker records only the settled initial URL and covers new routes by default", async () => {
  window.umami = { track, identify };
  const router = await setup();
  expect(delivered.map(pathname)).toEqual(["/preview/editions/1.1/"]);
  expect(delivered[0]).toMatchObject({ title: "Page /editions/1.1/", website: "fixture-website" });
  await router.push("/new-page/");
  expect(delivered.map(pathname)).toEqual(["/preview/editions/1.1/", "/preview/new-page/"]);
  expect(delivered[1]?.referrer).toBe(delivered[0]?.url);
  const id = window.localStorage.getItem(VISITOR_ID_STORAGE_KEY);
  expect(id).toBeTruthy();
  expect(delivered.map(view => view.id)).toEqual([id, id]);
  expect(identify).toHaveBeenCalledExactlyOnceWith(id);
  expect(identify.mock.invocationCallOrder[0]).toBeLessThan(track.mock.invocationCallOrder[0]!);
});

test("late script loading preserves each visit's URL, title, and referrer without duplication", async () => {
  const router = await setup();
  await router.push("/new-page/?utm_source=fixture#section");
  expect(track).not.toHaveBeenCalled();
  window.umami = { track, identify };
  document.getElementById("deep20-analytics")!.dispatchEvent(new Event("load"));
  document.getElementById("deep20-analytics")!.dispatchEvent(new Event("load"));
  expect(delivered.map(pathname)).toEqual(["/preview/editions/1.1/", "/preview/new-page/"]);
  expect(delivered[0]?.title).toBe("Page /editions/1.1/");
  expect(delivered[1]).toMatchObject({ title: "Page /new-page/", referrer: delivered[0]?.url });
  expect(new URL(delivered[1]!.url).search).toBe("?utm_source=fixture");
  expect(new URL(delivered[1]!.url).hash).toBe("");
  expect(identify).toHaveBeenCalledTimes(1);
  expect(delivered[0]?.id).toBe(delivered[1]?.id);
});

test("same-page query, hash, slash, and duplicate updates do not add views", async () => {
  window.umami = { track };
  const router = await setup();
  await router.push("/editions/1.1/?notice=one");
  await router.push("/editions/1.1/?notice=one#section");
  await router.replace("/editions/1.1");
  await router.push("/editions/1.1");
  expect(track).toHaveBeenCalledTimes(1);
});

test("explicit exclusions and aborted navigation do not count; returning to content does", async () => {
  window.umami = { track };
  const router = await setup();
  router.beforeEach(to => to.path === "/blocked/" ? false : undefined);
  await router.push("/blocked/");
  await router.push("/excluded/");
  expect(track).toHaveBeenCalledTimes(1);
  await router.push("/editions/1.1/");
  expect(track).toHaveBeenCalledTimes(2);
  expect(new URL(delivered[1]!.referrer).pathname).toBe("/preview/excluded/");
});

test("browser history and content marked noindex remain tracked", async () => {
  window.umami = { track };
  const router = await setup();
  document.head.insertAdjacentHTML("beforeend", '<meta name="robots" content="noindex, follow">');
  await router.push("/episode/");
  router.back();
  await vi.waitFor(() => expect(track).toHaveBeenCalledTimes(3));
  router.forward();
  await vi.waitFor(() => expect(track).toHaveBeenCalledTimes(4));
  expect(delivered.map(pathname)).toEqual(["/preview/editions/1.1/", "/preview/episode/",
    "/preview/editions/1.1/", "/preview/episode/"]);
});

test("a blocked tracker or failed event never breaks navigation", async () => {
  const router = await setup();
  document.getElementById("deep20-analytics")!.dispatchEvent(new Event("error"));
  await router.push("/new-page/");
  window.umami = { track };
  document.getElementById("deep20-analytics")!.dispatchEvent(new Event("load"));
  expect(track).not.toHaveBeenCalled();
  expect(window.localStorage.getItem(VISITOR_ID_STORAGE_KEY)).toBeNull();
  expect(router.currentRoute.value.path).toBe("/new-page/");
});

test("synchronous and asynchronous tracker failures stay isolated", async () => {
  window.umami = { track: () => { throw new Error("Blocked event"); } };
  const router = await setup();
  window.umami = { track: () => Promise.reject(new Error("Failed event")) };
  await router.push("/new-page/");
  await Promise.resolve();
  expect(router.currentRoute.value.path).toBe("/new-page/");
});

test("a saved crypto UUID is reused when the application starts again", async () => {
  const id = "12b15d68-c61b-4826-93ae-9370928ba2a8";
  const randomUUID = vi.spyOn(window.crypto, "randomUUID").mockReturnValue(id);
  window.umami = { track, identify };
  await setup();
  stop?.();
  await setup();
  expect(randomUUID).toHaveBeenCalledTimes(1);
  expect(identify.mock.calls).toEqual([[id], [id]]);
  expect(delivered.map(view => view.id)).toEqual([id, id]);
});

test.each(["missing", "throws"])("ordinary random fallback persists when crypto %s", mode => {
  if (mode === "missing") vi.stubGlobal("crypto", {});
  else vi.spyOn(window.crypto, "randomUUID").mockImplementation(() => { throw new Error("Denied"); });
  const random = vi.spyOn(Math, "random").mockReturnValue(0.5);
  const getVisitorId = createVisitorIdReader();
  const id = getVisitorId();
  expect(id).toBe("88888888-8888-4888-8888-888888888888");
  expect(getVisitorId()).toBe(id);
  expect(window.localStorage.getItem(VISITOR_ID_STORAGE_KEY)).toBe(id);
  expect(random).toHaveBeenCalledTimes(31);
});

test("invalid saved identifiers are replaced with a random UUID", () => {
  window.localStorage.setItem(VISITOR_ID_STORAGE_KEY, "unexpected-identifying-value");
  const id = createVisitorIdReader()();
  expect(id).toMatch(/^[0-9a-f-]{36}$/);
  expect(window.localStorage.getItem(VISITOR_ID_STORAGE_KEY)).toBe(id);
});

test.each(["reads and writes", "writes only"])("denied storage %s retain one ID across navigation", async mode => {
  if (mode === "reads and writes") {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("Denied"); });
  }
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Denied"); });
  window.umami = { track, identify };
  const router = await setup();
  await router.push("/new-page/");
  expect(delivered).toHaveLength(2);
  expect(delivered[0]?.id).toBeTruthy();
  expect(delivered[0]?.id).toBe(delivered[1]?.id);
  expect(identify).toHaveBeenCalledTimes(1);
});

test("ID creation waits for tracking, then each view reads the stored ID", async () => {
  const read = vi.spyOn(Storage.prototype, "getItem");
  const write = vi.spyOn(Storage.prototype, "setItem");
  const generate = vi.spyOn(window.crypto, "randomUUID");
  createVisitorIdReader();
  const router = await setup();
  await router.push("/new-page/");
  expect(read).not.toHaveBeenCalled();
  expect(write).not.toHaveBeenCalled();
  expect(generate).not.toHaveBeenCalled();
  window.umami = { track, identify };
  document.getElementById("deep20-analytics")!.dispatchEvent(new Event("load"));
  expect(read.mock.calls).toEqual([[VISITOR_ID_STORAGE_KEY], [VISITOR_ID_STORAGE_KEY]]);
  expect(write).toHaveBeenCalledTimes(1);
  expect(generate).toHaveBeenCalledTimes(1);
  expect(delivered[0]?.id).toBe(delivered[1]?.id);
});

test("each view consumes an existing ID or creates one after storage is cleared without reloading", async () => {
  const initialId = "12b15d68-c61b-4826-93ae-9370928ba2a8";
  const changedId = "ce2cd05e-eb34-42a8-ae24-e2abccfb8832";
  const newId = "d35bc7b5-0f7e-475f-91c9-52c8ae2e90cc";
  window.localStorage.setItem(VISITOR_ID_STORAGE_KEY, initialId);
  const generate = vi.spyOn(window.crypto, "randomUUID").mockReturnValue(newId);
  window.umami = { track, identify };
  const router = await setup();
  expect(generate).not.toHaveBeenCalled();
  window.localStorage.setItem(VISITOR_ID_STORAGE_KEY, changedId);
  await router.push("/new-page/");
  expect(generate).not.toHaveBeenCalled();
  window.localStorage.removeItem(VISITOR_ID_STORAGE_KEY);
  await router.push("/episode/");
  expect(generate).toHaveBeenCalledTimes(1);
  expect(window.localStorage.getItem(VISITOR_ID_STORAGE_KEY)).toBe(newId);
  expect(delivered.map(view => view.id)).toEqual([initialId, changedId, newId]);
  expect(identify.mock.calls).toEqual([[initialId], [changedId], [newId]]);
});

test.each(["sync", "async"])("%s identification failure still sends page views with the ID", async mode => {
  window.umami = { track, identify: () => {
    if (mode === "sync") throw new Error("Blocked identify");
    return Promise.reject(new Error("Failed identify"));
  } };
  const router = await setup();
  await router.push("/new-page/");
  await Promise.resolve();
  expect(delivered).toHaveLength(2);
  expect(delivered[0]?.id).toBeTruthy();
  expect(delivered[0]?.id).toBe(delivered[1]?.id);
});
