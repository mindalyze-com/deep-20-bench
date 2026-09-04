**Desktop blocking-time analysis and fix - 4 September 2026**

The main avoidable cost was initializing the two homepage ECharts SVGs during hydration, although they were about 2,593 pixels below the top of the viewport. Initial rendering measured and laid out chart labels, drew both charts, and immediately resized each chart again. Repeated number-format construction added avoidable work in the charts and tables.

The local fix defers chart creation until its container is within 300 pixels of the viewport, supplies explicit initial dimensions, resizes only when dimensions change, and reuses number formatters. Static HTML, result tables, accessible text, links, and reserved chart dimensions remain available immediately. Cached routes reconnect observers, pending offscreen data updates are retained, and existing SVGs still resize when the viewport narrows.

**Where the original two seconds went**

The original [Google desktop report](https://pagespeed.web.dev/analysis/https-deep20bench-com/3j0o9jxebf?form_factor=desktop) measured about 2,000 ms of Total Blocking Time. Its largest task belonged to `use-responsive-echart-CxumnWgn.js` and lasted 1,308 ms. That task alone contributes about 1,258 ms after the 50 ms long-task allowance, roughly 63% of the reported blocking time. Other chart tasks lasted 234 ms and 64 ms. Page layout and hydration contributed additional tasks.

The report attributed 2,933 ms of total CPU work to the chart bundle, including 2,360 ms of script evaluation. Across the entire page it recorded 2,601 ms of style/layout work and 2,541 ms of script evaluation. These are overlapping views of CPU attribution, not numbers to add to TBT. TBT counts only the blocking portions of relevant long tasks. See [Chrome's TBT definition](https://developer.chrome.com/docs/lighthouse/performance/lighthouse-total-blocking-time).

A local CPU profile identified ECharts text measurement as a major cost. Under a 6x slowdown, instrumenting the original shared renderer measured about 515 ms and 121 ms for the two chart option/layout calls, followed by unnecessary resize calls of 54 ms and 24 ms. Both charts were offscreen. A reduced-motion comparison did not materially improve the result, so animations were retained.

**User-supplied live Chrome profile**

The supplied screenshots show the original chart bundle, `use-responsive-echart-CxumnWgn.js`. A live HTML check still referenced `index-BDGg41Mz.js`, while the regenerated local output references `index-C0LBYoZR.js` and chart bundle `use-responsive-echart-BvyuJzlJ.js`. The screenshots therefore describe the deployed baseline, before the local fix.

The selected interval represents approximately 255 ms of activity. The call tree attributes 112.1 ms to `setOption` and another 11.5 ms to the immediate `resize`. Bottom-up attribution shows 68.9 ms in text measurement, including rich-text and plain-text callers. Text measurement is part of chart rendering; these inclusive call stacks must not be added together. The original compiled renderer confirms the sequence: read width, call `setOption`, then call `resize` unconditionally. ECharts uses a canvas context to measure text even when its output renderer is SVG.

This supports the chart-rendering diagnosis, but it does not establish the cause of the earlier elapsed-time gap. The recording begins on a browser new-tab page, and substantial activity for the destination appears around 3.1 seconds into the recording. The 2,675.1 ms frame interval is not a measurement of JavaScript execution or Total Blocking Time. An exported Performance trace with navigation and request timing is needed to distinguish time before navigation from connection, response, and resource-loading delays. The selected interval also cannot be directly equated to the separate, throttled Google measurement of about 2,000 ms TBT.

**Measured result**

Both builds were served locally and tested sequentially with Lighthouse 13.4.1, Chrome 151, the desktop preset, DevTools throttling, and a 6x CPU slowdown. The baseline is a preserved copy of the original generated publication. The after measurement uses the regenerated production output, including formatter reuse.

| Metric | Before | After |
| --- | ---: | ---: |
| Total Blocking Time | 1,147 ms | 387 ms |
| Longest task | 999 ms | 235 ms |
| Total main-thread work | 1,779 ms | 947 ms |
| Script evaluation and compilation | 1,031 ms | 283 ms |
| Largest Contentful Paint | 669 ms | 660 ms |
| Performance score | 71 | 83 |

Blocking time fell by about 66% in this matched test. The largest chart task no longer appears in initial-load diagnostics. Instrumentation confirms zero SVG chart initializations before scrolling and two correct SVGs after scrolling. Number-formatter construction fell from 291 instances to 5, remaining at 5 after the charts rendered.

This is an initial-load improvement, not elimination of all chart work. The final scroll probe still recorded a 633 ms chart-rendering task under the deliberately slow 6x setting. It performed no redundant initial resize calls. Native-speed runs of the unchanged live and local site measured about 20 ms TBT on this machine, so the original Google sample does not represent a universal two-second delay. There is no after-deployment Google score or real-user Core Web Vitals claim.

**Implementation and validation**

- `source/publication/site/src/lib/use-responsive-echart.ts` owns visibility gating, dirty-state handling, explicit chart dimensions, resize handling, and cached-route lifecycle cleanup.
- `source/publication/site/src/lib/format.ts` reuses decimal, integer, and percentage formatters while retaining their existing output conventions.
- Unit regression coverage checks offscreen initialization, repeated updates, viewport changes, cached navigation, unmounting, observer fallback, and independent numeric precision.
- Browser coverage exercises the generated production homepage, scrolling into charts, resize behavior, chart interactions, expanded graphs, mobile layouts, static content, and cached navigation. Chart assertions now scroll the relevant container into view before inspecting its SVG.
- A readiness race in one browser test was resolved by waiting for network idle before scrolling, allowing the application's existing initial scroll-restoration timers to settle.
- The complete `docs/` tree was regenerated. The v9 dataset and manifest differ from the baseline only in their declared build timestamps. The v9 schema and all benchmark result values remain unchanged.

Strict type checks and all 18 unit tests passed. The final complete functional run passed 108 of 109 cases; the one scroll-readiness test was corrected and passed in the subsequent targeted run. That run passed all 10 tests, repeating the affected scenarios twice.

The two chart golden-image tests report existing differences of 1,689 pixels on desktop and 5,938 on mobile. Repeating them with both modified source files restored to their original versions produced exactly the same differences. The actual before/after images are byte-for-byte identical. The stored goldens were not updated. The verified current renders are saved as `chart-desktop.webp` and `chart-mobile.webp`.

These changes are confined to public presentation. They make no model requests and do not change benchmark execution, scoring, Guesser-visible state, or provider caching. No commit, push, or external publication was performed.

The detailed observations are in `measurements.json`. Full Lighthouse results are in `before.lighthouse.json` and `after.lighthouse.json`; compressed Chrome traces are retained beside them. Decompress a trace and load it in Chrome DevTools Performance to inspect the tasks.

The matched Lighthouse command used the following options for each local build:

```text
lighthouse <local-build-url> --preset=desktop --only-categories=performance
  --throttling-method=devtools --throttling.cpuSlowdownMultiplier=6
  --output=json --save-assets --chrome-flags=--headless
```

Recheck the live homepage with PageSpeed after the reviewed generated output is deployed through the authorized publication workflow.
