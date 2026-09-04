**Deep20Bench Google result presentation - follow-up, 4 September 2026**

The search presentation can be improved while retaining GitHub Pages hosting. The page title, site name, snippet, and favicon are separate concerns. The existing title commit addresses only part of the problem and is not deployed.

Direct signed-out Google browser checks used `q=Deep20Bench`, `hl=en`, `pws=0`, and `gl=us` / `gl=ch`. Both displayed the homepage with the site name “GitHub Pages documentation” and the title “How well can AI models play Twenty Questions?”. The homepage was the first main organic result with the US parameter and third with the Switzerland parameter. These are observations of two result pages, not stable or universal rankings.

**Verified deployment and content**

| Check | Observed result |
| --- | --- |
| Project homepage | HTTP 200 at `https://mindalyze-com.github.io/deep-20-bench/` |
| Initial HTML title | `Deep20Bench: A Twenty Questions LLM Benchmark` |
| Main H1 | `How well can AI models play Twenty Questions?` |
| Initial description | Describes comparing 16 AI models and the benchmark's measured abilities |
| Structured data | Dataset; no WebSite node |
| Open Graph site name | Absent |
| Canonical | Existing project homepage URL |
| Favicon declaration | `/deep-20-bench/favicon.svg`; asset returns HTTP 200 |
| Host root | `https://mindalyze-com.github.io/` returns HTTP 404, with title `Site not found · GitHub Pages` |
| Root-site repository lookup | GitHub API returns 404 for `mindalyze-com/mindalyze-com.github.io`; this alone does not prove that an inaccessible private repository does not exist |
| GitHub Pages configuration | Source `main:/docs`, no custom domain, HTTPS enforced |
| Latest successful Pages build | Commit `2d9a7a4d5f99268ec40b5a8785b5f8ea00d412c9`, completed 2026-09-02 05:19:55 UTC |
| Live entry script | `index-CLk95az1.js` |
| Locally committed entry script | `index-BCTyireG.js` |
| New route manifest on live site | `/deep-20-bench/data/routes.json` returns HTTP 404 |

The phrase “GitHub Pages documentation” is absent from the live project HTML. Google selected it. The missing root identity is consistent with Google's fallback rules; the exact reason for that particular wording is not observable here.

**Site identity and the host boundary**

Google selects one site name per domain or subdomain. Its preferred signal is WebSite structured data at the root homepage; a project subdirectory cannot establish a separate name. Adding markup only under `/deep-20-bench/` therefore does not resolve this boundary. [Google site-name documentation](https://developers.google.com/search/docs/appearance/site-names).

A root homepage is possible through the separate `mindalyze-com.github.io` repository. This corrects an omission in the first audit: buying a domain is not the only potential remedy. However, `https://mindalyze-com.github.io/mtl-explorer/` also returns HTTP 200, with title `Map Thousands of GPS Tracks | MTL Explorer`. Branding this shared host exclusively as Deep20Bench would misrepresent that project. GitHub also reports Pages enabled for FineTuningTrial, but its default project URL returned 404. [GitHub site types](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

The two practical choices are a shared Mindalyze homepage or a dedicated Deep20Bench hostname. I recommend the latter if independent Deep20Bench branding is the requirement. A custom subdomain of an already-owned domain would avoid a new registration. GitHub Pages supports this through the project's Pages settings and DNS. Its CNAME target must be `mindalyze-com.github.io`, without the project path. No domain ownership or availability was checked. [GitHub custom-domain setup](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

**Page title and snippet**

The observed blue title exactly matches the live H1. Google explicitly considers headings alongside HTML and Open Graph titles, so this is a plausible source, not proof of the selection mechanism. The previously confirmed JavaScript overwrite is still present in the deployed revision. Publish the reviewed metadata fix first. If a later recrawl still chooses the question heading, consider making the visible main heading include Deep20Bench and the benchmark topic. Keep the descriptive title already approved. Updates require recrawling and may take days to weeks; exact wording cannot be forced. [Google title-link guidance](https://developers.google.com/search/docs/appearance/title-link).

Google's observed snippet uses the older prototype description, which still appears in `config/publication.yml`. The current initial HTML description is more specific. A later copy review should check where that legacy description remains visible. Google may select page text instead of the meta description, depending on the query. [Google snippet guidance](https://developers.google.com/search/docs/appearance/snippet).

**Favicon**

The only declared icon is SVG. Google's favicon page, dated 2026-08-28, lists supported formats that include PNG and ICO but omit SVG. Supply a stable square PNG or ICO, preferably 96 by 96 pixels or larger, and declare it on the chosen hostname's homepage. Google uses one favicon per hostname and does not guarantee display. [Google favicon guidance](https://developers.google.com/search/docs/appearance/favicon-in-search).

**Implementation scope for a dedicated hostname**

The publication already has `base_path` and `canonical_url` configuration. A migration should update these, generate the full site at the new root, retain the CNAME file through rebuilds, and use consistent site identity metadata. Test assets, direct routes, canonicals, sitemap URLs, and the existing metadata regression coverage against that build.

Preserve the external compatibility endpoint `https://mindalyze-com.github.io/deep-20-bench/data/deep20bench-v9.json` and its schema. Verify that old page URLs reach their corresponding new pages and that data consumers still receive current valid JSON. Do not assume redirect behavior without testing the actual deployment. Google recommends permanent redirects, updated canonicals and internal links, and a new sitemap. [Google migration guidance](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes).

Do not submit a host-wide Search Console Change of Address for this project move: the old host also serves MTL Explorer. The tool does not accept a path-level source property. Use the applicable URL redirects, canonicals, sitemap, and property verification instead. [Search Console Change of Address requirements](https://support.google.com/webmasters/answer/9370220).

The research used public searches, HTTP checks, and read-only GitHub API inspection. Following the user's request, the local publication now adds `og:site_name` and homepage WebSite JSON-LD alongside Dataset metadata. The observed live state above predates deployment of these changes. No hosting settings, DNS, or external content changed, and no Search Console recrawl was requested. Commit `8fa6f718e` remains local; publication requires the separate authorization specified in AGENTS.md.
