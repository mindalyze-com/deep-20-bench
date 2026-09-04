**Deep20Bench SEO audit - custom domain - 4 September 2026**

The live site at https://deep20bench.com/ has no confirmed crawl-blocking defect in the checks below. The new domain, permanent redirects, prerendered pages, and shared static/browser metadata are working. The priorities are to confirm Google indexing after the move, reduce initial JavaScript work, and complete the Dataset metadata.

This report checks the custom-domain deployment and supersedes the earlier audit's deployment-specific findings about the old GitHub Pages address. It does not establish search traffic, rankings, or full indexing coverage.

| Priority | Finding | Recommended action |
| --- | --- | --- |
| High | Google discovery of the new domain is unconfirmed. A signed-out Google `site:deep20bench.com` query returned no documents. | Verify the new property in Search Console, submit the sitemap if needed, and inspect the homepage plus representative result, run, and subject pages. |
| Medium | Homepage lab performance shows substantial main-thread work, especially on desktop. | Profile initial chart rendering, reduce unnecessary JavaScript, and consider loading charts when they approach the viewport. Retain the existing static results and links. |
| Low | Dataset JSON-LD omits the result-data license. | Add `license: "https://creativecommons.org/licenses/by/4.0/"` to the Dataset node. |

**Crawling and migration**

- All 145 sitemap URLs returned HTTP 200: 9 homepage/editorial/result pages, 17 run pages, and 119 subject pages. Every response matched its generated `docs/` HTML byte for byte.
- All 145 had a unique, nonempty title and description, one H1, `lang="en"`, the expected self-canonical, and no `noindex` restriction in the initial HTML or response headers.
- All sitemap pages were reachable from the homepage through ordinary static HTML links. Linked internal files and fragment targets existed in the matching generated tree. This is not a claim that every internal target or external link was requested over HTTP.
- All 13 unique assets directly declared by those pages returned HTTP 200. The social image and CSV download also returned HTTP 200. This asset check did not recursively crawl JavaScript imports or CSS font URLs.
- Root `robots.txt` allows crawling and advertises the correct [sitemap](https://deep20bench.com/sitemap.xml).
- HTTP apex, HTTPS www, and HTTP www each redirected to the HTTPS apex in one HTTP 301 hop. Slashless `/results` redirected to `/results/`.
- The old GitHub Pages homepage, results page, and sampled run, subject, and episode URLs each redirected in one HTTP 301 hop to the corresponding new URL, which returned HTTP 200.
- The old v9 JSON and schema URLs redirected to valid, current JSON matching the local generated files. Keep these long-lived compatibility endpoints available.
- An invented missing path returned an actual HTTP 404 and `noindex, follow`.
- `/index.html` canonicalized to `/`; `/story/` canonicalized to `/about/`. Both returned HTTP 200. These aliases are not a current priority because canonical signals are present and neither is in the sitemap.
- All 595 generated episode pages contained `noindex, follow` and were outside the sitemap. Two live episode samples confirmed the directive. This follows the intended publication policy.

Keep the working redirects and update controlled links to the new domain. Google's migration guidance recommends retaining redirects for at least a year, with longer retention useful for users. The project's compatibility endpoint requires ongoing preservation. See [Google's site-move guidance](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes).

**Metadata and content**

The earlier client-side title and description overwrite is fixed in the browser samples. The homepage retains `Deep20Bench: A Twenty Questions LLM Benchmark`; the results page retains `LLM Benchmark Results and Leaderboard | Deep20Bench`. Both Albert Einstein pages retain distinct titles and descriptions containing their respective Claude Fable 5 and Claude Fable 5.1 model names. Canonicals stay on the correct new-domain routes. Navigating from a `noindex` episode back to results removes the robots restriction.

The homepage clearly describes the benchmark, its scoring, its current 17-model pilot, and its limits. The results are available as text and ordinary links before JavaScript. Methodology, authorship, citation, and licensing pages are linked. These are useful foundations; there is no evidence here that a broad rewrite or more repeated keywords would help.

Homepage WebSite and Dataset JSON-LD both parse. WebSite identifies Deep20Bench at the domain root, satisfying the location and required-property aspects of Google's [site-name guidance](https://developers.google.com/search/docs/appearance/site-names). Google still chooses the displayed name automatically.

The Dataset has a name, description, creator, modification date, current cohort description, measured variables, and CSV/JSON distributions. Its missing `license` is a recommended-property improvement, not a required-field failure. The footer already identifies the results as CC BY 4.0. Add that specific license URL to the Dataset, following [Google's dataset guidance](https://developers.google.com/search/docs/appearance/structured-data/dataset). JSON syntax and field presence were inspected; no Google structured-data validation certificate is claimed.

**Performance**

The public PageSpeed UI completed the test at approximately 15:42 UTC. The anonymous API returned a quota error, so the figures below come from the completed UI report.

| Homepage lab metric | Mobile | Desktop |
| --- | ---: | ---: |
| Lighthouse SEO | 100 | 100 |
| Performance | 83 | 47 |
| Accessibility | 100 | 100 |
| Best Practices | 100 | 100 |
| First Contentful Paint | 1.8 s | 1.1 s |
| Largest Contentful Paint | 3.0 s | 2.3 s |
| Total Blocking Time | 400 ms | 2,000 ms |
| Cumulative Layout Shift | 0.017 | 0.004 |

These are single lab runs, not an overall SEO rating or a real-user Core Web Vitals assessment. No real-user data was available. [Mobile report](https://pagespeed.web.dev/analysis/https-deep20bench-com/3j0o9jxebf?form_factor=mobile), [desktop report](https://pagespeed.web.dev/analysis/https-deep20bench-com/3j0o9jxebf?form_factor=desktop).

Mobile diagnostics flag about 70 KiB of unused JavaScript in the ECharts-related chunk and a render-blocking stylesheet. Desktop diagnostics report 6.2 seconds of main-thread work and 2.8 seconds of JavaScript execution. Both flag short asset cache lifetimes.

Source inspection provides a concrete profiling target: `use-responsive-echart.ts` initializes charts on mount, with no viewport visibility gate, and enables animation above the mobile breakpoint. This is a plausible contributor to the desktop/mobile difference, not a proven attribution of all blocking time. Profile chart initialization and animation, then compare repeated before/after runs. Loading below-the-fold charts later could preserve the current static result content while reducing initial work.

The measured cache header is `max-age=600`. Longer caching of content-hashed assets could help repeat visits if a hosting layer supports it. Keep HTML and stable-name data freshness separate from that decision; this finding alone does not justify a hosting migration.

**Search visibility and next steps**

A direct signed-out Google search on 4 September, using `hl=en` and `pws=0`, returned no documents for `site:deep20bench.com`. The web search tool also returned no results. This is a discovery observation, not proof that the new domain has zero indexed pages: [Google states that site searches are not exhaustive](https://developers.google.com/search/docs/monitor-debug/search-operators/all-search-site).

The next useful check is authenticated Search Console: property verification, sitemap processing, URL Inspection, Google-selected canonicals, Page Indexing exclusions, and query/page performance. None of those account reports was obtained in this audit. Inspect the new domain independently of the old property and request a homepage recrawl if appropriate.

Do not use a host-wide Change of Address for `mindalyze-com.github.io`. The old site was one project path and the host contains another project; the tool does not support path-level source properties. See [Search Console's scope rules](https://support.google.com/webmasters/answer/9370220).

Audit evidence is saved in `evidence.json` beside this report. Only audit files were added; publication source, generated output, hosting settings, and Search Console settings were not changed.
