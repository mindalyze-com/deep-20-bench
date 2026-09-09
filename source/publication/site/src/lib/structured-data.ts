import { dataLicenseResource } from "./site-resources";
import type { LeaderboardDocument, ManifestDocument } from "./types";

/** The same edition-specific markup is used by prerendering and browser navigation. */
export const homepageStructuredData = (
  manifest: ManifestDocument,
  leaderboard: LeaderboardDocument,
  canonicalBase: string,
) => {
  const editionId = manifest.edition_id;
  const editionUrl = new URL(`editions/${editionId}/`, canonicalBase).href;
  const evaluated = leaderboard.leaderboard.filter((row) => row.status === "evaluated");
  return [
    {
      "@context": "https://schema.org",
      "@type": "Dataset",
      "@id": new URL("#dataset", editionUrl).href,
      name: `${manifest.site.title} ${manifest.active_cohort.edition_label}`,
      version: manifest.active_cohort.edition_label,
      alternateName: ["Deep20 Bench", "D20B"],
      description: manifest.site.description,
      url: editionUrl,
      creator: { "@type": "Person", name: manifest.site.creator_name },
      dateModified: manifest.provenance.built_at,
      isAccessibleForFree: true,
      license: dataLicenseResource.href,
      keywords: [
        "Deep20Bench", "Deep20 Bench", "Deep20 benchmark", "large language models",
        "large language model benchmark", "LLM benchmark", "Twenty Questions",
        "question strategy", "state tracking",
      ],
      variableMeasured: ["question score", "success rate", "contract compliance", "cost", "runtime"],
      measurementTechnique: `${manifest.active_cohort.target_ids.length} subjects, ${manifest.active_cohort.iterations} repeated trials per subject, ${evaluated.length} evaluated models`,
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
    },
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "@id": new URL("#website", canonicalBase).href,
      name: manifest.site.title,
      alternateName: manifest.site.short_title,
      url: canonicalBase,
    },
  ];
};

export const applyStructuredData = (
  data: ReturnType<typeof homepageStructuredData>,
): void => {
  if (typeof document === "undefined") return;
  document.querySelectorAll('script[type="application/ld+json"]').forEach((script) => script.remove());
  for (const item of data) {
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(item);
    document.head.append(script);
  }
};
