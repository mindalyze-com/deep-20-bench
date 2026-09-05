**Local SEO fixes - 5 September 2026**

Implemented the concrete source and generated-site fixes from the [SEO audit](../seo-audit-20260905/README.md). At the end of this local implementation pass, all changes remained in the working tree. No commit, push, pull request, release, deployment, GitHub setting change, Search Console submission, or hosting change had been made. A later publication request is a separate step.

- Removed the manually maintained model count from the README and linked to the generated current results.
- Shortened all 126 subject-page titles while retaining the full model name, reasoning setting, subject, and site name. Titles still come from the route manifest during static rendering, hydration, and navigation.
- Added model identity to each subject page's H1. All 153 indexable pages now have distinct H1s, titles, and descriptions. Titles longer than 65 characters fell from 122 to one; this is a presentation measure, not a search-engine limit.
- Added the canonical CC BY 4.0 license URL and a stable Dataset ID to homepage JSON-LD. The Data page explains attribution and distinguishes result-data licensing from the software's source-available license. License links and software wording share one definition.
- Deferred the ECharts download and evaluation until a chart approaches the viewport. Static results, accessible data, links, and reserved chart dimensions remain available. A failed download shows a reload notice. Delayed downloads respect page deactivation and unmounting.
- Preloaded the two local normal Latin fonts used above the fold. Vite produces the correct content-hashed asset URLs for the configured base path.
- Fixed delayed scroll restoration overriding a position the visitor has already changed. This surfaced during mobile checks after initial loading became faster.
- Regenerated the complete `docs/` tree and updated publication documentation.

The local publication still contains 18 official models, 153 indexable pages, and 630 episode pages. The v9 compatibility URL and schema remain present. The v9 dataset is unchanged except for `/provenance/built_at`; no benchmark results, transcripts, scoring, model requests, or Guesser-visible state changed. Existing unrelated working-tree changes were retained.

**Validation**

- 69 publication compiler tests passed.
- 21 frontend unit tests passed, including deferred loading, download failure, unmounting, and cached-route activation.
- 111 desktop and mobile functional browser tests passed, including accessibility, responsive layouts, no-JavaScript content, chart interactions, canonical metadata, and episode indexability.
- Python lint, strict Python typing, and Vue/TypeScript checks passed.
- All 153 sitemap pages have one H1, unique titles and descriptions, the expected canonical, and no unintended noindex. All are reachable through static links within two steps of the homepage.
- All 630 episode pages retain `noindex, follow`. No missing linked local targets or HTML-referenced assets were found.
- A fresh `deep20-publication build --check` matched the complete generated `docs/` tree exactly.
- `git diff --check` passed.

**Local performance measurements**

Three alternating cold runs per snapshot used Lighthouse 13.4.1, default mobile simulated throttling, and identical local gzip compression. Both snapshots contain the same 18-model cohort. The table shows medians.

| Metric | Before | After |
| --- | ---: | ---: |
| Lighthouse performance | 84 | 96 |
| Lighthouse SEO | 100 | 100 |
| First contentful paint | 2.33 s | 1.65 s |
| Largest contentful paint | 4.06 s | 2.72 s |
| Total blocking time | 0 ms | 0 ms |
| Cumulative layout shift | 0.00065 | 0 |
| Initial total transfer | 409.4 KiB | 221.9 KiB |
| Initial JavaScript transfer | 271.4 KiB | 83.4 KiB |

Initial JavaScript transfer fell by 69.3%, and total transfer fell by 45.8%. No renderer chunk was requested initially in the final build. The browser test confirms that it downloads once near the viewport and is reused after navigation. Font preloads did not introduce additional font requests.

These local results demonstrate a loading improvement under the measured conditions. They are not live PageSpeed scores or field Core Web Vitals. The final median mobile lab LCP remains above 2.5 seconds. Performance after release still needs a live measurement. The deferred renderer is about 598 kB minified / 203 kB gzip and triggers Vite's existing 550 kB chunk warning when built; it is downloaded when a chart is needed.

Full per-run metrics and representative network inventories are retained in [performance.json](performance.json).

**Actions left outside this local change**

The repository's public homepage setting, Google Search Console migration checks and indexing requests, sitemap submission, live deployment, and host cache headers were left untouched as requested. Search rankings, Google-selected canonical URLs, field Core Web Vitals, and Google's licensing summary cannot be verified or changed by a local build.

The audit's future options for retaining superseded-run URLs and publishing an original comparison article remain separate publication work. The current crawl found no broken run URLs. Archiving superseded runs needs an explicit historical-publication policy; this change preserves the current selected-official-run contract.

Evidence: [local checks](local-checks.json). The initial audit remains an unchanged record of the live site before these local fixes.
