**Deep20Bench Google SEO audit - 4 September 2026**

The site has a sound static crawl setup, useful visibility for its specific topic, and incomplete recognition of the shorter Deep20 name. A confirmed client-side metadata defect weakens the new SEO titles after the application renders. This is the first technical change to address. Public search results do not establish traffic growth or full indexing coverage.

The audit used direct Google searches in a signed-out browser, English language, personalization disabled through pws=0, with US and Switzerland country parameters as recorded below. These are point-in-time observations, not tracked average rankings. Country parameters do not reproduce every user's location or search context.

| Query | Country parameter | Homepage observation |
| --- | --- | --- |
| Deep20Bench | US | First main organic result; AI Overview present |
| Deep20Bench | Switzerland | Third main organic result, below a GitHub CONTRIBUTING.md result and Patrick Heusser's Medium article; AI Overview present |
| twenty questions llm benchmark | US | Fifth main organic result; related Deep20Bench Reddit post first and Patrick Heusser's Medium article fourth |
| deep20 | US | Absent from the first displayed results page |
| deep20 benchmark | US | Absent from the first displayed results page |
| llm benchmark | US | Absent from the first displayed results page |

Google recognizes the full brand and the benchmark's narrow topic. The abbreviated name is ambiguous. This supports focusing on the consistent name Deep20Bench and its Twenty Questions use case, rather than treating generic LLM benchmark visibility as already established. The US niche search shows that the existing explanatory posts are discoverable. Their visibility does not establish referral traffic or the ranking value of their links.

A site-prefix search displayed seven URLs: the homepage, methodology, results, data, about, the Ox Alpha run, and the Claude Fable 5 run. This is positive evidence that multiple page types are indexed and serving. It does not show that only seven URLs are indexed. Google explicitly warns that [site: results are not exhaustive](https://developers.google.com/search/docs/monitor-debug/search-operators/all-search-site). Search Console is needed to assess coverage of the full 137-URL sitemap and the recently published runs and subject pages.

**Confirmed metadata defect**

The raw HTML contains improved titles and descriptions. When Vue runs, App.vue replaces them using shorter route-context copy:

| Page | Initial HTML title | Title after JavaScript |
| --- | --- | --- |
| Homepage | Deep20Bench: A Twenty Questions LLM Benchmark | Deep20Bench |
| Results | LLM Benchmark Results and Leaderboard \| Deep20Bench | Results · Deep20Bench |
| Claude Fable 5 / Albert Einstein | Claude Fable 5 (high) on Albert Einstein - Twenty Questions Results \| Deep20Bench | Albert Einstein · Deep20Bench |
| Claude Fable 5.1 / Albert Einstein | Claude Fable 5.1 (high) on Albert Einstein - Twenty Questions Results \| Deep20Bench | Albert Einstein · Deep20Bench |

The descriptions are overwritten too. Both sampled subject pages end with the same title despite being results for different models. The source applies the same subject-name pattern across the subject routes. App.vue:158-166 is the shared writer; HomeView.vue and SubjectWorkspaceView.vue supply the short values. Canonical URLs stayed correct in the browser samples.

Recommended change: use one canonical metadata definition for static generation and client navigation. Keep full page titles and descriptions consistent before and after JavaScript, preserving both model and subject identities. Verify the homepage, results, two models for one subject, and navigation between page types. Current static-output checks alone do not detect this problem. Google [uses rendered HTML for indexing and supports JavaScript changes to titles and descriptions](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics). The defect is confirmed; its exact effect on ranking or Google's current choice of title is not measurable from this audit.

**Live technical checks**

- All 137 sitemap pages returned HTTP 200: 9 homepage/editorial/result pages, 16 run pages, and 112 subject pages.
- Every sitemap page matched the repository's generated HTML byte for byte.
- Each had a unique nonempty title and description in initial HTML, one H1, and the expected self-canonical URL. No sitemap page had an initial noindex directive or X-Robots-Tag restriction.
- All 137 pages were reachable from the homepage through ordinary links in static HTML. Internal link and directly declared asset targets from those pages existed in the generated tree. This does not claim that every external link or every asset was tested over HTTP.
- All 560 generated episode pages had noindex, follow and were absent from the sitemap. Two live episode samples confirmed this behavior. Transcript exclusion is intentional.
- The slashless homepage redirected with HTTP 301 to the slash URL. HTTP redirected to HTTPS. The index.html duplicate canonicalized to the homepage; the story alias canonicalized to about. An invented missing path returned a real HTTP 404.
- The sitemap, favicon, social image, and Google verification file were live. The host-root homepage and robots.txt returned HTTP 404.
- Missing host-root robots.txt does not block crawling: Google treats a robots.txt 404 as having no crawl restrictions. A robots.txt placed under /deep-20-bench/ would not control this host. See [Google's robots.txt rules](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec). Confirm sitemap submission in Search Console; the public verification file is not proof of successful submission or current account access.
- Homepage Dataset JSON-LD parsed successfully and described the current 16-model publication, with CSV and v9 JSON distributions. A smaller improvement is to add the actual result-data license URL and other applicable dataset identity metadata. Google [documents these dataset properties](https://developers.google.com/search/docs/appearance/structured-data/dataset). This was a local syntax/content inspection, not a Google rich-result eligibility certification.

**Search presentation and timing**

Google displayed the site name as “GitHub Pages documentation”, not Deep20Bench. The project is hosted in a subdirectory, and [Google does not support independent site names at subdirectory level](https://developers.google.com/search/docs/appearance/site-names). A custom domain or dedicated subdomain could provide clearer site identity. This is a branding and architecture decision, with no promised ranking improvement. Any future move must preserve the long-lived v9 data compatibility URL.

The repository records publication SEO improvements and subject prerendering on August 30, 2026, and the latest publication on September 2. All audited live sitemap pages match that output. Google still displays shorter titles and some older descriptive copy. The JavaScript overwrite and normal recrawl/reprocessing delays are both relevant; their individual contributions cannot be determined here. Google says [title updates may take days to weeks to be reprocessed](https://developers.google.com/search/docs/appearance/title-link).

**Performance and measurement limits**

The [PageSpeed test](https://pagespeed.web.dev/analysis/https-mindalyze-com-github-io-deep-20-bench/avgc2wvnke?form_factor=mobile) displayed no real-user data and failed to produce lab scores because Google's renderer was overloaded. The anonymous PageSpeed API also returned a quota error. No Lighthouse score or Core Web Vitals pass is claimed. Quick HTTP responses from this machine are not a substitute for mobile experience measurements.

No authenticated Search Console data was obtained. Clicks, impressions, CTR, average position, complete index counts, exclusion reasons, Google-selected canonicals, sitemap processing, security/manual-action status, and traffic trends remain unverified. A Performance export split by query/page/country/device, plus Page Indexing and Sitemaps reports, would close the largest measurement gap. Compare the periods before and after August 30 while accounting for the short elapsed time.

**Recommended order**

1. Correct the static/client metadata mismatch and regenerate the full publication locally.
2. Inspect the existing Search Console property, sitemap processing, and representative homepage, run, and subject URLs. Request recrawling after the corrected version is deployed through the authorized publication workflow.
3. Use Deep20Bench consistently and build on useful Twenty Questions/model-result explanations. The existing Reddit and Medium results already demonstrate topic discovery.
4. Consider clearer domain-level branding and enrich Dataset metadata as secondary improvements.
5. Obtain a successful mobile PageSpeed report and real Search Console performance data before making speed or traffic claims.

This audit changed no publication source or generated site output. Machine-readable observations are in evidence.json beside this report.
