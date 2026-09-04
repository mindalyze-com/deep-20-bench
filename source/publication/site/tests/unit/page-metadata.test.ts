// @vitest-environment jsdom

import { beforeEach, describe, expect, test } from "vitest";

import { applyPageMetadata } from "../../src/lib/page-metadata";
import { parseRouteMetadata, type RouteMetadata } from "../../src/lib/route-metadata";

const canonicalBase = "https://example.org/benchmark/";
const subject: RouteMetadata = {
  route: "runs/model-a/subjects/person",
  canonical_route: "runs/model-a/subjects/person",
  browser_title: "Model A on Person - Twenty Questions Results | Deep20Bench",
  description: "Model A solved all five trials for Person.",
  indexable: true,
};

beforeEach(() => {
  document.head.innerHTML = "";
});

describe("publication page metadata", () => {
  test("keeps model identity when two runs have the same subject", () => {
    applyPageMetadata(subject, canonicalBase);
    const firstTitle = document.title;
    const second = {
      ...subject,
      route: "runs/model-b/subjects/person",
      canonical_route: "runs/model-b/subjects/person",
      browser_title: "Model B on Person - Twenty Questions Results | Deep20Bench",
      description: "Model B solved three of five trials for Person.",
    };
    applyPageMetadata(second, canonicalBase);

    expect(document.title).toBe(second.browser_title);
    expect(document.title).not.toBe(firstTitle);
    expect(document.querySelector('meta[name="description"]')?.getAttribute("content"))
      .toBe(second.description);
    expect(document.querySelector('meta[property="og:title"]')?.getAttribute("content"))
      .toBe(second.browser_title);
    expect(document.querySelector('meta[name="twitter:description"]')?.getAttribute("content"))
      .toBe(second.description);
    expect(document.querySelectorAll('link[rel="canonical"]')).toHaveLength(1);
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute("href"))
      .toBe(`${canonicalBase}${second.canonical_route}/`);
  });

  test("restores indexability when leaving an episode and resolves an alias", () => {
    applyPageMetadata({ ...subject, indexable: false }, canonicalBase);
    expect(document.querySelector('meta[name="robots"]')?.getAttribute("content"))
      .toBe("noindex, follow");

    applyPageMetadata({ ...subject, route: "legacy-subject" }, canonicalBase);
    expect(document.querySelector('meta[name="robots"]')).toBeNull();
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute("href"))
      .toBe(`${canonicalBase}${subject.canonical_route}/`);

    applyPageMetadata(undefined, canonicalBase);
    expect(document.querySelector('link[rel="canonical"]')).toBeNull();
    expect(document.querySelector('meta[property="og:url"]')).toBeNull();
    expect(document.querySelector('meta[name="robots"]')?.getAttribute("content"))
      .toBe("noindex, follow");
  });

  test("rejects malformed manifests and duplicate routes at the build boundary", () => {
    expect(() => parseRouteMetadata({ schema_version: 1, routes: [subject] })).toThrow();
    expect(() => parseRouteMetadata({
      schema_version: 2, routes: [{ ...subject, indexable: "false" }],
    })).toThrow();
    expect(() => parseRouteMetadata({ schema_version: 2, routes: [subject, subject] }))
      .toThrow(/duplicate/);
    expect(parseRouteMetadata({ schema_version: 2, routes: [subject] })).toEqual([subject]);
  });
});
