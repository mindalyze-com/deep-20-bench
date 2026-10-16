import { dataLicenseResource } from "./site-resources";
import type {
  LeaderboardDocument,
  ManifestDocument,
  ModelDocument,
  ModelIndexDocument,
  RunDocument,
} from "./types";

type StructuredData = Record<string, unknown>;

/** Pages with JSON-LD; prerendering and browser navigation share this description. */
export type StructuredDataPage =
  | { kind: "home" | "data"; manifest: ManifestDocument; leaderboard: LeaderboardDocument }
  | { kind: "model"; manifest: ManifestDocument; model: ModelDocument }
  | { kind: "model-index"; manifest: ManifestDocument; index: ModelIndexDocument }
  | { kind: "run"; manifest: ManifestDocument; run: RunDocument }
  | { kind: "subject"; manifest: ManifestDocument; run: RunDocument; targetId: string }
  | {
    kind: "episode";
    manifest: ManifestDocument;
    run: RunDocument;
    targetId: string;
    trialId: string;
  };

const editionDataset = (
  manifest: ManifestDocument,
  leaderboard: LeaderboardDocument,
  canonicalBase: string,
): StructuredData => {
  const editionId = manifest.edition_id;
  const cohort = manifest.active_cohort;
  const editionUrl = new URL(`editions/${editionId}/`, canonicalBase).href;
  const evaluated = leaderboard.leaderboard.filter((row) => row.status === "evaluated");
  return {
    "@context": "https://schema.org",
    "@type": "Dataset",
    // The edition page keeps the stable identity; the data page is the landing page.
    "@id": new URL("#dataset", editionUrl).href,
    name: `${manifest.site.title} ${cohort.edition_label}`,
    version: cohort.edition_label,
    alternateName: ["Deep20 Bench", "D20B"],
    description:
      `Results of ${manifest.site.title} edition ${cohort.edition_label}, a Twenty Questions ` +
      `AI benchmark for large language models: ${evaluated.length} evaluated models, ` +
      `${cohort.target_ids.length} hidden subjects, and ${cohort.iterations} rounds per subject. ` +
      "Includes the leaderboard, question scores, success rates, format errors, costs, " +
      "runtimes, and every round transcript with its questions, answers, and evidence.",
    url: new URL(`editions/${editionId}/data/`, canonicalBase).href,
    creator: { "@type": "Person", name: manifest.site.creator_name },
    dateModified: manifest.provenance.built_at,
    isAccessibleForFree: true,
    license: dataLicenseResource.href,
    keywords: [
      "Deep20Bench", "Deep20 Bench", "Deep20 benchmark", "large language models",
      "large language model benchmark", "LLM benchmark", "AI benchmark", "AI model benchmark",
      "Twenty Questions", "question strategy", "state tracking",
    ],
    variableMeasured: ["question score", "success rate", "format compliance", "cost", "runtime"],
    measurementTechnique: `${cohort.target_ids.length} subjects, ${cohort.iterations} rounds per subject, ${evaluated.length} evaluated models`,
    distribution: [
      {
        "@type": "DataDownload",
        encodingFormat: "text/csv",
        contentUrl: new URL(`data/editions/${editionId}/leaderboard.csv`, canonicalBase).href,
      },
      {
        "@type": "DataDownload",
        encodingFormat: "application/json",
        contentUrl: new URL(`data/editions/${editionId}/deep20bench-v10.json`, canonicalBase).href,
      },
    ],
  };
};

const breadcrumbs = (
  items: readonly { name: string; route: string }[],
  canonicalBase: string,
): StructuredData => ({
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: items.map((item, index) => ({
    "@type": "ListItem",
    position: index + 1,
    name: item.name,
    item: new URL(item.route, canonicalBase).href,
  })),
});

const evidenceBreadcrumbs = (
  page: Extract<StructuredDataPage, { run: RunDocument }>,
  canonicalBase: string,
): StructuredData => {
  const { manifest, run } = page;
  const editionRoute = `editions/${manifest.edition_id}/`;
  const runRoute = `runs/${run.run.execution_id}/`;
  const items = [
    { name: `${manifest.site.title} ${manifest.active_cohort.edition_label}`, route: editionRoute },
    { name: "Results", route: `${editionRoute}results/` },
    { name: run.run.model_name, route: runRoute },
  ];
  if (page.kind !== "run") {
    const subject = run.subjects.find((summary) => summary.target_id === page.targetId);
    if (subject === undefined) throw new Error("Structured data subject is missing from its run.");
    const subjectRoute = `${runRoute}subjects/${page.targetId}/`;
    items.push({ name: subject.display_name, route: subjectRoute });
    if (page.kind === "episode") {
      items.push({
        name: `Round ${Number(page.trialId.replace(/^trial-/, ""))}`,
        route: `${subjectRoute}episodes/${page.trialId}/`,
      });
    }
  }
  return breadcrumbs(items, canonicalBase);
};

const modelBreadcrumbs = (
  manifest: ManifestDocument,
  canonicalBase: string,
  model?: ModelDocument,
): StructuredData => {
  const editionRoute = `editions/${manifest.edition_id}/`;
  const items = [
    { name: `${manifest.site.title} ${manifest.active_cohort.edition_label}`, route: editionRoute },
    { name: "Models", route: `${editionRoute}models/` },
  ];
  if (model !== undefined) {
    items.push({
      name: model.result.model.display_name,
      route: `${editionRoute}models/${model.slug}/`,
    });
  }
  return breadcrumbs(items, canonicalBase);
};

const modelPage = (
  manifest: ManifestDocument,
  model: ModelDocument,
  canonicalBase: string,
): StructuredData => {
  const editionUrl = new URL(`editions/${manifest.edition_id}/`, canonicalBase).href;
  const url = new URL(`editions/${manifest.edition_id}/models/${model.slug}/`, canonicalBase).href;
  const result = model.result;
  const name = result.model.display_name;
  const standing = result.rank === null
    ? "no ranked result"
    : `rank ${result.rank} of ${model.ranked_models}`;
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": `${url}#webpage`,
    url,
    name: `${name} Twenty Questions results`,
    description:
      `Results of ${name} in ${manifest.site.title} edition ` +
      `${manifest.active_cohort.edition_label}: ${standing}, ` +
      `${result.successful} of ${result.terminal_trials} rounds solved.`,
    inLanguage: "en",
    dateModified: manifest.provenance.latest_completed_at ?? manifest.provenance.built_at,
    isPartOf: { "@id": new URL("#website", canonicalBase).href },
    about: { "@id": new URL("#dataset", editionUrl).href },
  };
};

export const pageStructuredData = (
  page: StructuredDataPage,
  canonicalBase: string,
): StructuredData[] => {
  switch (page.kind) {
    case "home":
      return [
        editionDataset(page.manifest, page.leaderboard, canonicalBase),
        {
          "@context": "https://schema.org",
          "@type": "WebSite",
          "@id": new URL("#website", canonicalBase).href,
          name: page.manifest.site.title,
          alternateName: page.manifest.site.short_title,
          url: canonicalBase,
        },
      ];
    case "data":
      return [
        editionDataset(page.manifest, page.leaderboard, canonicalBase),
        breadcrumbs([
          {
            name: `${page.manifest.site.title} ${page.manifest.active_cohort.edition_label}`,
            route: `editions/${page.manifest.edition_id}/`,
          },
          { name: "Data", route: `editions/${page.manifest.edition_id}/data/` },
        ], canonicalBase),
      ];
    case "model":
      return [
        modelPage(page.manifest, page.model, canonicalBase),
        modelBreadcrumbs(page.manifest, canonicalBase, page.model),
      ];
    case "model-index": {
      const editionId = page.manifest.edition_id;
      const url = new URL(`editions/${editionId}/models/`, canonicalBase).href;
      return [
        {
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          "@id": `${url}#webpage`,
          url,
          name: `Models tested in ${page.manifest.site.title} ` +
            `${page.manifest.active_cohort.edition_label}`,
          inLanguage: "en",
          dateModified: page.manifest.provenance.latest_completed_at ??
            page.manifest.provenance.built_at,
          isPartOf: { "@id": new URL("#website", canonicalBase).href },
          about: { "@id": new URL("#dataset", new URL(`editions/${editionId}/`, canonicalBase)).href },
          mainEntity: {
            "@type": "ItemList",
            numberOfItems: page.index.models.length,
            itemListElement: page.index.models.map((entry, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: entry.model.display_name,
              url: new URL(`editions/${editionId}/models/${entry.slug}/`, canonicalBase).href,
            })),
          },
        },
        modelBreadcrumbs(page.manifest, canonicalBase),
      ];
    }
    default:
      return [evidenceBreadcrumbs(page, canonicalBase)];
  }
};

export const applyStructuredData = (data: readonly StructuredData[]): void => {
  if (typeof document === "undefined") return;
  document.querySelectorAll('script[type="application/ld+json"]').forEach((script) => script.remove());
  for (const item of data) {
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(item);
    document.head.append(script);
  }
};
