// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeEach, describe, expect, test } from "vitest";
import type { RouteLocationNormalizedLoaded } from "vue-router";

import {
  modelSlug,
  parsePublicationDocument,
  resetPublicationData,
  seedPublicationData,
  selectedEditionId,
} from "../../src/lib/api";
import { modelSummaryRoute } from "../../src/lib/route-location";
import { pageStructuredData } from "../../src/lib/structured-data";
import type {
  EditionsDocument,
  ManifestDocument,
  ModelDocument,
  ModelIndexDocument,
} from "../../src/lib/types";
import { editionDestination } from "../../src/lib/use-edition-context";

const fixture = (path: string): unknown => JSON.parse(readFileSync(resolve(
  "tests/fixtures/publication/data", path), "utf8"));
const index = parsePublicationDocument(fixture("editions.json")) as EditionsDocument;
const manifest = parsePublicationDocument(fixture("editions/1.0/manifest.json")) as ManifestDocument;
const modelIndex = parsePublicationDocument(fixture("editions/1.0/models.json")) as ModelIndexDocument;
const firstEntry = modelIndex.models[0]!;
const model = parsePublicationDocument(
  fixture(`editions/1.0/models/${firstEntry.slug}.json`),
) as ModelDocument;
const canonicalBase = "https://example.org/";

beforeEach(() => {
  resetPublicationData();
  seedPublicationData([index, manifest, modelIndex, model]);
  selectedEditionId.value = "1.0";
});

describe("model pages", () => {
  test("link a model to its stable page, or to its run before slugs are known", () => {
    const { model_id: modelId } = model.result.model;
    expect(modelSlug(modelId)).toBe(model.slug);
    expect(modelSummaryRoute(modelId, "BX-unused")).toEqual({
      name: "model", params: { editionId: "1.0", slug: model.slug },
    });
    expect(modelSummaryRoute("M-9999", "BX-fallback")).toEqual({
      name: "run", params: { executionId: "BX-fallback" },
    });
  });

  test("observations cite rounds that the subjects table publishes", () => {
    const rounds = new Set(model.subjects.flatMap((subject) =>
      subject.rounds.map((item) => `${item.target_id}/${item.trial_id}`)));
    expect(model.observations.length).toBeGreaterThan(0);
    for (const observation of model.observations) {
      for (const reference of observation.rounds) {
        expect(rounds.has(`${reference.target_id}/${reference.trial_id}`)).toBe(true);
      }
    }
  });

  test("describe a model page as a web page inside the edition dataset", () => {
    const [page, crumbs] = pageStructuredData({ kind: "model", manifest, model }, canonicalBase);
    const url = `${canonicalBase}editions/1.0/models/${model.slug}/`;
    expect(page).toMatchObject({
      "@type": "WebPage",
      "@id": `${url}#webpage`,
      url,
      isPartOf: { "@id": `${canonicalBase}#website` },
      about: { "@id": `${canonicalBase}editions/1.0/#dataset` },
    });
    expect(String(page?.description)).toContain(model.result.model.display_name);
    expect(crumbs?.["@type"]).toBe("BreadcrumbList");
    const items = crumbs?.itemListElement as { item: string }[];
    expect(items.map((item) => item.item)).toEqual([
      `${canonicalBase}editions/1.0/`,
      `${canonicalBase}editions/1.0/models/`,
      url,
    ]);
    expect(JSON.stringify(page)).not.toMatch(/AggregateRating|Review|Product/);
  });

  test("list every model on the index page", () => {
    const [page] = pageStructuredData({ kind: "model-index", manifest, index: modelIndex }, canonicalBase);
    const list = page?.mainEntity as { numberOfItems: number; itemListElement: { url: string }[] };
    expect(page?.["@type"]).toBe("CollectionPage");
    expect(list.numberOfItems).toBe(modelIndex.models.length);
    expect(list.itemListElement[0]?.url).toBe(
      `${canonicalBase}editions/1.0/models/${firstEntry.slug}/`,
    );
  });

  test("switch editions to the same model, or to the model list when it is missing", () => {
    const route = {
      name: "model", params: { editionId: "1.0", slug: model.slug }, fullPath: "/", query: {}, hash: "",
    } as unknown as RouteLocationNormalizedLoaded;
    const edition = index.editions[0]!;
    const other = { ...edition, edition_id: "1.1", models: [{ model_id: model.result.model.model_id, slug: "renamed" }] };
    expect(editionDestination(route, other)).toEqual({
      name: "model", params: { editionId: "1.1", slug: "renamed" },
    });
    expect(editionDestination(route, { ...other, models: [] })).toEqual({
      name: "models", params: { editionId: "1.1" }, query: { editionNotice: "missing-model-page" },
    });
  });

  test("reject an edition index without model pages", () => {
    const legacy = { ...index, editions: index.editions.map(({ models: _models, ...edition }) => edition) };
    expect(() => parsePublicationDocument(legacy)).toThrow("Publication edition index is invalid.");
  });
});
