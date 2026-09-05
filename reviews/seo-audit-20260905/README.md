**Deep20Bench SEO audit - 5 September 2026**

Deep20Bench has a sound technical SEO foundation. No crawl-blocking defect was found in the public site. The earlier metadata overwrite is fixed, the chart-loading improvement is live, and Google is beginning to show the new domain. The main remaining work is to verify the domain migration in Search Console, correct stale repository information, and improve a few presentation details.

This audit covers [deep20bench.com](https://deep20bench.com/), its old GitHub Pages redirects, the complete live sitemap, all internal URLs linked from sitemap pages, recursively referenced static assets, browser metadata, current Google results, and fresh PageSpeed tests. The local generated publication was checked separately. This is an audit; no site source, generated publication, repository settings, or Search Console settings were changed.

| Priority | Finding | Action and acceptance check |
| --- | --- | --- |
| First | Google is showing a mixture of new-domain pages and the old homepage URL. Full migration status is unknown. | Inspect the new homepage in Search Console, including Google-selected canonical and latest crawl. Confirm sitemap processing and inspect representative results, run, and subject URLs. This is a measurement priority, not a confirmed indexing defect. |
| Medium | GitHub's public homepage setting still points to the old domain. README copy says 12 models; the live publication has 17. | Set the repository homepage to `https://deep20bench.com/`. Remove the hardcoded README count or derive it from the publication's source of truth. Check the public repository after the authorized update. |
| Medium | Mobile lab LCP is 3.0 seconds. Chart initialization is deferred, but its large JavaScript chunk still downloads initially. | Profile loading the chart module closer to visibility and the stylesheet/font path. Compare repeated mobile tests while retaining complete static tables, links, and reserved chart dimensions. |
| Low | The homepage Dataset JSON-LD omits its data license. | Add `license: "https://creativecommons.org/licenses/by/4.0/"` to the Dataset node and validate the regenerated HTML. This is a recommended-property improvement. |
| Low | Many subject-page titles are long, and their H1s identify only the subject. | Consider shorter titles that keep both model and subject, plus clearer model context in the principal heading. Verify actual title presentation and CTR before a broad copy change. |

**The live crawl passed across the full published page set.**

| Check | Live result | Local generated result |
| --- | --- | --- |
| Sitemap pages | 145 | 153 |
| Homepage, editorial and result pages | 9 | 9 |
| Official run summaries | 17 | 18 |
| Subject summaries | 119 | 126 |
| Unique nonempty titles and descriptions | 145/145 | 153/153 |
| One H1, English language, expected self-canonical | 145/145 | 153/153 |
| Unintended noindex on sitemap pages | 0 | 0 |
| Sitemap pages unreachable through static links | 0 | 0 |
| Maximum static link distance from homepage | 2 | 2 |

Every live sitemap URL returned HTTP 200 without a redirect. None had an HTTP `X-Robots-Tag` restriction. There were no duplicate HTML IDs or broken fragment targets among the sitemap pages. Each page contains its actual text, results, and ordinary links in initial HTML. Indexable content does not require JavaScript to become available. This follows [Google's crawlable-link guidance](https://developers.google.com/search/docs/crawling-indexing/links-crawlable).

All 776 distinct internal URLs linked from sitemap pages were requested and returned HTTP 200. These include 145 indexable pages, 595 episode pages, 33 episode query variants, and three download links. All 595 episodes and all 33 `?violation=first` variants emit `noindex, follow`; none is in the sitemap. Query variants canonicalize to their underlying episode. This is the intended transcript policy, not lost indexing that needs to be fixed. The local build has 630 episode pages, all with noindex, and no missing internal link targets.

All 90 discovered static assets returned HTTP 200: 50 JavaScript files, 25 stylesheets, 13 fonts, one favicon, and one social image. This inventory follows references across route bundles; it is not a claim that a visitor downloads all 90 assets on the homepage. JavaScript references were extracted statically rather than by executing every possible interaction. The live social image matches the local 1200 × 630 WebP. Thirteen external links from editorial pages were also checked: eleven returned 200; Medium and Ko-fi returned 403 to the audit client. Those two are unverified, not confirmed dead links. Model-reported evidence links inside transcripts were outside this SEO link-check scope.

All 145 live sitemap documents match the current Git HEAD byte for byte. None matches the working tree's newly generated HTML, which includes an eighteenth model. The live publication timestamp is 4 September 2026 at 16:05 UTC. The live site is coherent; unpublished local data is not a deployment defect.

**The migration's HTTP configuration is working.**

Root [robots.txt](https://deep20bench.com/robots.txt) permits crawling and advertises the correct [sitemap](https://deep20bench.com/sitemap.xml). All sitemap locations use the HTTPS apex domain. Their modification timestamps match the declared publication timestamp.

HTTP apex, HTTPS www, and HTTP www each reach the HTTPS apex through one HTTP 301 hop. Slashless `/results` redirects to `/results/`. The original GitHub Pages homepage, results page, and sampled run, subject, and episode paths each reach their corresponding new URL through one 301 hop and then return 200. The old v9 dataset and schema endpoints still redirect to valid, current live JSON. Keep those compatibility endpoints available indefinitely under the project's existing contract.

An invented missing URL returns a real HTTP 404 with `noindex, follow`. `/index.html` remains a 200 alias with the homepage canonical; `/story/` remains a 200 alias canonicalizing to `/about/`. Neither is in the sitemap. These aliases are not urgent issues because the consolidation signals agree.

The public [repository metadata](https://api.github.com/repos/mindalyze-com/deep-20-bench) confirms its `homepage` value is still the old GitHub Pages address. The README's main links already use the new domain, so the remaining repository URL correction is its About/homepage setting. Google's [migration guidance](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes) recommends updating controlled links and retaining redirects for at least a year; existing data compatibility requirements call for longer retention here.

**Google discovery has progressed since yesterday, but the homepage still needs inspection.**

These observations came from signed-out Google searches with English language, personalization disabled through `pws=0`, and `gl=us`. They are individual results-page observations, not tracked rankings or a reproduction of every user's location.

| Query | Observation |
| --- | --- |
| `site:deep20bench.com` | Four new-domain pages displayed: methodology, data, results, and about. The homepage did not appear in this sample. |
| `Deep20Bench` | New-domain Data page was the first main organic result. The old homepage was fifth; the new About page was seventh. An AI Overview was present. |
| `twenty questions llm benchmark` | New-domain Methodology page was fourth among main organic results; the old homepage was sixth. An AI Overview mentioned Deep20Bench. |

This is evidence of new-domain search visibility, unlike yesterday's empty site-query sample. It does not establish that only four pages are indexed or that the homepage is excluded. Google explicitly says [site queries are not exhaustive](https://developers.google.com/search/docs/monitor-debug/search-operators/all-search-site). The old homepage still displayed the site name “GitHub Pages documentation”; new-domain results displayed the domain name. The homepage already supplies the correct root-level WebSite JSON-LD and `og:site_name`. Google's [site-name selection](https://developers.google.com/search/docs/appearance/site-names) is automatic, so another speculative metadata rewrite is not the first action.

The useful next account checks are: property verification, sitemap status, homepage URL Inspection, Google-selected canonicals, and Page Indexing exclusions split by page type. Inspect at least one recent model run and one subject summary as well. Compare query/page/country/device performance across the old and new properties when enough post-move data exists. Request indexing of the homepage if URL Inspection indicates that it is appropriate. No authenticated Search Console reports were obtained, so clicks, impressions, CTR, average position, complete coverage, manual actions, and backlink totals remain unknown. A public verification file does not establish those account states.

**The metadata repair is live and holds during navigation.**

Browser checks preserved the intended homepage and results titles and descriptions. Two Albert Einstein pages retained distinct metadata for Claude Fable 5 and Claude Fable 5.1, including their different model names and results. Their canonicals stayed correct. Entering an episode applied `noindex, follow`; navigating back to Results removed it and restored Results metadata. No errors or warnings appeared in the initial homepage/results/subject console sample. The source of truth remains the shared route manifest, which is the right design for [JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics).

The live titles range from 43 to 93 characters; 115 of 145 exceed a 65-character review threshold. This is not a Google limit or a failed check. The longer titles usually preserve the useful model and subject first and repeat “Twenty Questions Results” near the end. A possible shorter form is `Claude Fable 5 on Albert Einstein | Deep20Bench`, retaining a reasoning-setting identifier where needed to distinguish pages. All titles and descriptions are already unique. Google [truncates titles according to available width](https://developers.google.com/search/docs/appearance/title-link); a shorter template is a presentation option, not a promised ranking gain.

The 119 subject pages use seven repeated subject-only H1s. Model identity is visible nearby and present in the title and description, so this is not a duplicate-page defect. Adding concise model context to the main heading could make these standalone landing pages clearer. The static result data is useful original content; short subject summaries should not be labeled “thin” solely by a word count.

Homepage WebSite and Dataset JSON-LD parse successfully. Dataset has its required name and description, plus creator, current cohort size, modification date, measured variables, and working CSV/JSON distributions. Its missing license is a small confirmed improvement in `source/publication/site/scripts/prerender.mjs:188`. Google's [Dataset documentation](https://developers.google.com/search/docs/appearance/structured-data/dataset) lists license as recommended. The software license and result-data license must remain distinct. No Google rich-result validation certificate is claimed.

**Fresh live performance measurements show that yesterday's large blocking-time problem has improved.**

| Homepage lab metric | Mobile | Desktop |
| --- | ---: | ---: |
| Performance | 93 | 99 |
| Lighthouse SEO | 100 | 100 |
| Accessibility | 100 | 100 |
| Best Practices | 100 | 100 |
| First Contentful Paint | 1.8 s | 0.3 s |
| Largest Contentful Paint | 3.0 s | 0.7 s |
| Total Blocking Time | 10 ms | 10 ms |
| Cumulative Layout Shift | 0.017 | 0.071 |
| Speed Index | 1.8 s | 0.6 s |

The [mobile report](https://pagespeed.web.dev/analysis/https-deep20bench-com/j2tpdmn5fx?form_factor=mobile) and [desktop report](https://pagespeed.web.dev/analysis/https-deep20bench-com/j2tpdmn5fx?form_factor=desktop) were captured on 5 September at approximately 11:09 UTC, with Lighthouse 13.4.1 and Chromium 151. The deployed homepage references `index-C0LBYoZR.js`, and diagnostics identify `use-responsive-echart-BvyuJzlJ.js`, the bundles from the earlier chart-loading fix. Yesterday's custom-domain audit reported performance 83 mobile / 47 desktop and TBT 400 / 2,000 ms. Today's samples are much better, although independent lab runs cannot attribute every difference to the code change.

The mobile report still estimates 130.7 KiB of unused JavaScript in the 160.3 KiB chart chunk. The current renderer imports ECharts eagerly and defers initialization; deferring the module download is the next concrete profiling candidate. The 8.7 KiB blocking stylesheet is associated with an estimated 600 ms saving. That estimate is not a guaranteed result or something to add to the JavaScript estimate. Inspect the actual font and CSS dependency path before adding preloads or inlining CSS.

Assets use `max-age=600`. Longer caching for content-hashed assets could help repeat visits if a hosting layer supports it, but the measured performance does not justify a hosting migration on that fact alone. Keep HTML and stable-name JSON freshness separate.

PageSpeed reports no CrUX real-user data. Mobile LCP of 3.0 seconds is above Google's 2.5-second good threshold, but this single lab sample does not establish a field Core Web Vitals failure. TBT is not INP. See [Google's Core Web Vitals guidance](https://developers.google.com/search/docs/appearance/core-web-vitals). The browser's attempted narrow viewport override did not take effect, so no manual mobile-layout pass is claimed beyond the mobile lab check. Lighthouse SEO 100 measures basic checks, not total SEO health.

**Content and source consistency offer more value than adding generic SEO pages.**

The existing homepage, methodology, results, authorship, citation, and data pages already explain the benchmark's distinct Twenty Questions scope and limitations. Preserve that focus. The primary branded query should remain Deep20Bench; the shorter DeepBench name also refers to unrelated projects, including [Baidu's hardware benchmark](https://github.com/baidu-research/DeepBench).

The clearest content correction is [README.md:34](/Users/pheusser/IdeaProjects/Deep20Bench/README.md:34): its 12-model statement disagrees with the live 17-model publication and upcoming local 18-model publication. Avoid another manually maintained count. The branded Google AI Overview also described the software as open-source, which conflicts with the site's explicit source-available licensing statement. Keep the distinction between reusable data and software licensing prominent and consistent in controlled project descriptions. The current footer already states it correctly; changing the footer alone is not an evidenced solution to Google's summary.

For future editorial work, prioritize one useful, dated explanation of a measured model comparison or failure pattern, linked to the existing runs, uncertainty estimates, and transcripts. This serves the topic already appearing in search. Avoid creating many model-pair pages with near-identical copy or implying this small pilot measures general model intelligence. The current results, cost, time, and stability routes already cover distinct questions. No search-volume or keyword-difficulty data was obtained to justify a larger content program.

A separate future URL-lifetime consideration follows from the publisher's documented latest-qualified-run selection. It generates only selected official runs. When a rerun replaces an existing selected run, its old evidence URL can disappear from the generated tree. Before promoting frequently rerun model pages, define how superseded public evidence remains accessible and whether a stable model overview should link to the current run. This is an architectural risk to future incoming links, not a current broken URL found in this crawl.

Evidence is retained in [evidence.json](/Users/pheusser/IdeaProjects/Deep20Bench/reviews/seo-audit-20260905/evidence.json), [extended-evidence.json](/Users/pheusser/IdeaProjects/Deep20Bench/reviews/seo-audit-20260905/extended-evidence.json), and [browser-evidence.json](/Users/pheusser/IdeaProjects/Deep20Bench/reviews/seo-audit-20260905/browser-evidence.json). The [live page inventory](/Users/pheusser/IdeaProjects/Deep20Bench/reviews/seo-audit-20260905/live-pages.csv) and [local page inventory](/Users/pheusser/IdeaProjects/Deep20Bench/reviews/seo-audit-20260905/local-pages.csv) include every sitemap URL and its metadata. The accompanying read-only audit scripts reproduce the HTTP and static checks; public response bodies were cached in temporary directories rather than added to the repository.
