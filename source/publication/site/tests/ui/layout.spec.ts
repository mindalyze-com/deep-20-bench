import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "./support/fixture";

import { siteResourceLinks } from "../../src/lib/site-resources";
import {
  contractExampleEpisodePath,
  contractExampleHref,
  contractExampleRunPath,
  contractExampleSubjectPath,
  docsRoot,
  episodePath,
  expectMinimumSize,
  expectNoViewportOverflow,
  expectVerticalGap,
  firstTraversalTrialId,
  lastTraversalTrialId,
  nextTraversalSubjectId,
  previousTraversalSubjectId,
  runDocument,
  runPath,
  staticPaths,
  subjectPath,
  targetId,
  traversalSubjectId,
  trialId,
  unknownExampleEpisodePath,
  waitForPublication,
} from "./support/publication";

test("every page template uses the shared type system", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  const paths = [
    ...staticPaths,
    runPath,
    subjectPath,
    episodePath,
    "missing-page/",
  ];

  for (const routePath of paths) {
    await page.goto(routePath);
    await waitForPublication(page);
    const exceptions = await page.locator("#app *").evaluateAll((elements) => {
      const families = [
        "inter tight",
        "newsreader",
        "sfmono-regular",
        "math",
      ];
      const weights = new Set(["400", "500", "600", "700", "800"]);

      return elements.flatMap((element) => {
        const hasOwnText = [...element.childNodes].some(
          (node) =>
            node.nodeType === Node.TEXT_NODE &&
            node.textContent?.trim() !== "",
        );
        if (!hasOwnText) return [];
        const style = window.getComputedStyle(element);
        const family = style.fontFamily.toLowerCase();
        if (
          families.some((allowed) => family.includes(allowed)) &&
          weights.has(style.fontWeight)
        ) {
          return [];
        }
        return [
          {
            family: style.fontFamily,
            selector: `${element.tagName.toLowerCase()}.${element.className}`,
            text: element.textContent?.trim().slice(0, 60),
            weight: style.fontWeight,
          },
        ];
      });
    });
    expect(exceptions, routePath).toEqual([]);
  }
});

test("public routes stay within the viewport", { tag: ["@layout", "@both", "@smoke"] }, async ({ page }) => {
  for (const routePath of staticPaths) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator("h1").first()).toBeVisible();
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      `https://mindalyze-com.github.io/deep-20-bench/${routePath}`,
    );
    await expectNoViewportOverflow(page);
  }
});

test("data page keeps download, exploration, and reuse in one ordered flow", { tag: ["@layout", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto("data/");
  await waitForPublication(page);

  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Download the public benchmark record.",
  );
  await expect(page.locator(".data-lede")).toContainText(
    "Deep20Bench publishes the data behind its leaderboard",
  );
  await expect(
    page
      .getByRole("list", { name: "What the public data supports" })
      .getByRole("listitem"),
  ).toHaveText([
    "Trace each published result.",
    "Reproduce the official summaries.",
    "Build your own evaluations.",
  ]);
  await expect(page.locator(".flow-step")).toHaveText([
    "01 Choose a format",
    "02 Explore the file",
    "03 Verify and reuse",
  ]);
  const stageTops = await page.locator(".flow-stage").evaluateAll((elements) =>
    elements.map((element) => element.getBoundingClientRect().top + window.scrollY),
  );
  expect(stageTops).toEqual([...stageTops].sort((left, right) => left - right));

  const downloadCards = page.locator(".download-grid article");
  await expect(downloadCards).toHaveCount(3);
  await expect(downloadCards.first().getByRole("link")).toHaveAttribute(
    "href",
    "/deep-20-bench/data/deep20bench-v9.json",
  );
  if (testInfo.project.name.startsWith("desktop")) {
    const cardBoxes = await downloadCards.evaluateAll((elements) =>
      elements.map((element) => {
        const box = element.getBoundingClientRect();
        return { top: box.top, width: box.width };
      }),
    );
    expect(cardBoxes[0]!.width).toBeGreaterThan(cardBoxes[1]!.width);
    expect(cardBoxes[1]!.top).toBeCloseTo(cardBoxes[0]!.top, 0);
    expect(cardBoxes[2]!.top).toBeCloseTo(cardBoxes[0]!.top, 0);
  }
  await expectNoViewportOverflow(page);
});

const shellViewports = [
  { width: 320, height: 568 },
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1280, height: 720 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
] as const;
const shellRoutePaths = [
  ...staticPaths,
  "story/",
  runPath,
  subjectPath,
  episodePath,
  "missing-page/",
] as const;

for (const viewport of shellViewports) {
  test(
    `major route shells stay contained at ${viewport.width} × ${viewport.height}`,
    { tag: ["@layout", "@desktop"] },
    async ({ page }) => {
      const browserErrors: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error") browserErrors.push(message.text());
      });
      page.on("pageerror", (error) => browserErrors.push(error.message));

    await page.setViewportSize(viewport);
      for (const routePath of shellRoutePaths) {
        await page.goto(routePath);
        await waitForPublication(page);
        await expectNoViewportOverflow(page);
        const shellBoxes = await page
          .locator(".site-header, .drilldown-bar, .app-viewport, .site-footer")
          .evaluateAll((elements) =>
            elements
              .filter((element) => {
                const rectangle = element.getBoundingClientRect();
                return rectangle.width > 0 && rectangle.height > 0;
              })
              .map((element) => {
                const rectangle = element.getBoundingClientRect();
                return { left: rectangle.left, right: rectangle.right };
              }),
          );
        for (const box of shellBoxes) {
          expect(box.left).toBeGreaterThanOrEqual(-1);
          expect(box.right).toBeLessThanOrEqual(viewport.width + 1);
        }
      }

      expect(browserErrors).toEqual([]);
    },
  );
}

test("a 320 pixel shell with a classic scrollbar keeps the header separate", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  await page.setViewportSize({ width: 305, height: 568 });
  await page.goto("");
  await waitForPublication(page);
  await expectNoViewportOverflow(page);

  const boxes = await page.evaluate(() => {
    const rectangle = (selector: string): { left: number; right: number } => {
      const element = document.querySelector<HTMLElement>(selector);
      if (element === null) throw new Error(`Missing header element: ${selector}`);
      const box = element.getBoundingClientRect();
      return { left: box.left, right: box.right };
    };
    return {
      wordmark: rectangle(".wordmark"),
      repository: rectangle(".repository-link"),
      menu: rectangle(".mobile-navigation summary"),
    };
  });
  expect(boxes.wordmark.right).toBeLessThanOrEqual(boxes.repository.left);
  expect(boxes.repository.right).toBeLessThanOrEqual(boxes.menu.left + 1);
});

test("iPad portrait and landscape touch contexts keep major routes usable", { tag: ["@layout", "@desktop"] }, async ({
  browser,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  test.setTimeout(60_000);
  const routes = ["", "results/efficiency/", runPath, subjectPath, episodePath];

  for (const viewport of [
    { width: 768, height: 1024 },
    { width: 1024, height: 768 },
  ]) {
    const context = await browser.newContext({
      baseURL: "http://127.0.0.1:4173/deep-20-bench/",
      hasTouch: true,
      isMobile: true,
      viewport,
    });
    const touchPage = await context.newPage();
    for (const routePath of routes) {
      await touchPage.goto(routePath);
      await waitForPublication(touchPage);
      await expectNoViewportOverflow(touchPage);
      await expect(touchPage.locator("h1").first()).toBeVisible();
    }
    await context.close();
  }
});

test("tablet popovers and footer content stay inside the viewport", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("results/cost/");
  await waitForPublication(page);

  await page.getByRole("button", { name: "Guesser and support cost" }).click();
  const popoverBox = await page
    .getByRole("dialog", { name: "Guesser and support cost" })
    .boundingBox();
  expect(popoverBox).not.toBeNull();
  expect(popoverBox!.x).toBeGreaterThanOrEqual(0);
  expect(popoverBox!.x + popoverBox!.width).toBeLessThanOrEqual(768);
  await page.getByRole("button", { name: "Close explanation" }).click();

  const footer = page.locator(".site-footer");
  await footer.scrollIntoViewIfNeeded();
  const linkBoxes = await footer.locator("nav a").evaluateAll((elements) =>
    elements.map((element) => {
      const rectangle = element.getBoundingClientRect();
      return { left: rectangle.left, right: rectangle.right };
    }),
  );
  for (const box of linkBoxes) {
    expect(box.left).toBeGreaterThanOrEqual(0);
    expect(box.right).toBeLessThanOrEqual(768);
  }
});

test("narrow result cards keep complete metric labels and values", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("results/efficiency/");
  await waitForPublication(page);

  const clippedMetrics = await page
    .locator(".mobile-result-metrics dt, .mobile-result-metrics dd")
    .evaluateAll((elements) =>
      elements.filter(
        (element) =>
          element.scrollWidth > element.clientWidth + 1 ||
          element.scrollHeight > element.clientHeight + 1,
      ).length,
    );
  expect(clippedMetrics).toBe(0);
});

test("iPad portrait workspace rails preserve episode metadata and model cards", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto(subjectPath);
  await waitForPublication(page);

  const clippedEpisodeMetadata = await page.locator(".episode-copy small").evaluateAll(
    (elements) =>
      elements.filter(
        (element) =>
          element.scrollWidth > element.clientWidth + 1 ||
          element.scrollHeight > element.clientHeight + 1,
      ).length,
  );
  expect(clippedEpisodeMetadata).toBe(0);

  await page.goto(runPath);
  await waitForPublication(page);
  const supportGrid = page.locator(".support-model-grid");
  const supportGridBox = await supportGrid.boundingBox();
  const firstSupportCardBox = await supportGrid.locator(".run-model-card").first().boundingBox();
  expect(supportGridBox).not.toBeNull();
  expect(firstSupportCardBox).not.toBeNull();
  expect(Math.abs(firstSupportCardBox!.width - supportGridBox!.width)).toBeLessThanOrEqual(1);

  const firstProviderDetails = supportGrid.locator(".provider-routing-details").first();
  await firstProviderDetails.locator("summary").click();
  const firstSupportCard = supportGrid.locator(".run-model-card").first();
  const providerOverflow = await firstSupportCard.evaluate(
    (element) => element.scrollWidth - element.clientWidth,
  );
  expect(providerOverflow).toBeLessThanOrEqual(1);
});

test("illustrative round typography is identical on Overview and Method", { tag: ["@layout", "@desktop"] }, async ({ page }) => {
  const typographySnapshot = async (): Promise<Record<string, Record<string, string>>> =>
    page.locator(".round-example").evaluate((round) => {
      const selectors = [
        ".round-head",
        ".round-card li p",
        ".round-card li > strong",
        ".round-guess-name",
        ".round-score-label",
        ".round-score-number",
        ".round-score-summary",
        ".round-score-direction > span",
      ];

      return Object.fromEntries(
        selectors.map((selector) => {
          const element = round.querySelector<HTMLElement>(selector);
          if (element === null) {
            throw new Error(`The illustrative round is missing ${selector}.`);
          }
          const style = getComputedStyle(element);
          return [
            selector,
            {
              color: style.color,
              fontFamily: style.fontFamily,
              fontSize: style.fontSize,
              fontWeight: style.fontWeight,
              letterSpacing: style.letterSpacing,
              lineHeight: style.lineHeight,
            },
          ];
        }),
      );
    });

  await page.goto("");
  await waitForPublication(page);
  const overviewTypography = await typographySnapshot();

  await page.goto("methodology/");
  await waitForPublication(page);
  const methodTypography = await typographySnapshot();

  expect(methodTypography).toEqual(overviewTypography);
});

test("About watermark stays inside its hero", { tag: ["@layout", "@desktop"] }, async ({ page }) => {
  await page.goto("about/");
  await waitForPublication(page);

  const bounds = await page.evaluate(() => {
    const hero = document.querySelector<HTMLElement>(".story-hero");
    const watermark = document.querySelector<HTMLElement>(".hero-number");
    if (hero === null || watermark === null) {
      throw new Error("The About hero watermark is missing.");
    }
    return {
      heroRight: hero.getBoundingClientRect().right,
      watermarkRight: watermark.getBoundingClientRect().right,
    };
  });

  expect(bounds.watermarkRight).toBeLessThanOrEqual(bounds.heroRight + 1);
});

test("primary navigation pages share one wide-screen content boundary", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.setViewportSize({ width: 1920, height: 900 });

  const routes = [
    { path: "", selectors: [".home-hero-inner", ".origin-strip-inner"] },
    { path: "results/", selectors: [".results-workspace-header-inner"] },
    { path: "methodology/", selectors: [".page-hero-inner", ".method-nav"] },
    { path: "about/", selectors: [".story-hero-inner", ".story-closing-inner"] },
    { path: "data/", selectors: [".page-hero-inner", ".site-footer-inner"] },
  ] as const;

  for (const route of routes) {
    await page.goto(route.path);
    await waitForPublication(page);
    for (const selector of route.selectors) {
      const boundary = page.locator(selector);
      await expect(boundary).toHaveClass(/site-boundary/);
      const dimensions = await boundary.evaluate((element) => ({
        maximum: Number.parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue("--max"),
        ),
        width: element.getBoundingClientRect().width,
      }));
      expect(dimensions.width).toBeCloseTo(dimensions.maximum, 0);
    }
  }
});

test("Data contract keeps the publisher note close to the contract panel", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));

  for (const width of [1920, 480]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("data/");
    await waitForPublication(page);

    const gap = await page.evaluate(() => {
      const columns = document.querySelector<HTMLElement>(".contract-columns");
      const note = document.querySelector<HTMLElement>(".publisher-note");
      if (columns === null || note === null) {
        throw new Error("The data contract panel is incomplete.");
      }
      return note.getBoundingClientRect().top - columns.getBoundingClientRect().bottom;
    });

    expect(gap).toBeGreaterThanOrEqual(20);
    expect(gap).toBeLessThanOrEqual(27);
    await expectNoViewportOverflow(page);
  }
});

test("Method editorial content uses the shared wide-screen boundary", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.setViewportSize({ width: 1920, height: 900 });
  await page.goto("methodology/");
  await waitForPublication(page);

  const layout = await page.evaluate(() => {
    const hero = document.querySelector<HTMLElement>(".page-hero-inner");
    const editorial = document.querySelector<HTMLElement>("#game .editorial-copy");
    const rail = editorial?.firstElementChild as HTMLElement | null;
    const main = editorial?.lastElementChild as HTMLElement | null;
    const lead = editorial?.querySelector<HTMLElement>(".lead") ?? null;
    const round = editorial?.querySelector<HTMLElement>(".method-round") ?? null;
    const roundExample = editorial?.querySelector<HTMLElement>(".round-example") ?? null;
    const methodNote = editorial?.querySelector<HTMLElement>(".method-note") ?? null;
    const methodNoteParagraph = methodNote?.querySelector<HTMLElement>("p") ?? null;
    const rationaleNote = document.querySelector<HTMLElement>(".rationale-note");
    const rationaleNoteParagraph = rationaleNote?.querySelector<HTMLElement>("p") ?? null;
    if (
      hero === null ||
      editorial === null ||
      rail === null ||
      main === null ||
      lead === null ||
      round === null ||
      roundExample === null ||
      methodNote === null ||
      methodNoteParagraph === null ||
      rationaleNote === null ||
      rationaleNoteParagraph === null
    ) {
      throw new Error("The Method editorial layout surfaces are missing.");
    }

    const probe = document.createElement("div");
    probe.style.cssText = [
      "position: fixed",
      "visibility: hidden",
      "display: grid",
      "width: var(--editorial-rail)",
      "max-width: var(--editorial-measure)",
      "column-gap: var(--editorial-column-gap)",
    ].join(";");
    document.body.append(probe);
    const probeStyle = getComputedStyle(probe);
    const tokens = {
      rail: Number.parseFloat(probeStyle.width),
      measure: Number.parseFloat(probeStyle.maxWidth),
      gap: Number.parseFloat(probeStyle.columnGap),
    };
    probe.remove();

    const box = (element: HTMLElement) => {
      const bounds = element.getBoundingClientRect();
      return {
        left: bounds.left,
        right: bounds.right,
        width: bounds.width,
      };
    };
    return {
      tokens,
      hero: box(hero),
      editorial: box(editorial),
      rail: box(rail),
      main: box(main),
      lead: box(lead),
      round: box(round),
      roundExample: box(roundExample),
      methodNote: box(methodNote),
      methodNoteParagraph: box(methodNoteParagraph),
      methodNoteContentRight:
        methodNote.getBoundingClientRect().right -
        Number.parseFloat(getComputedStyle(methodNote).paddingRight),
      rationaleNote: box(rationaleNote),
      rationaleNoteParagraph: box(rationaleNoteParagraph),
      gap: main.getBoundingClientRect().left - rail.getBoundingClientRect().right,
    };
  });

  expect(layout.editorial.left).toBeCloseTo(layout.hero.left, 0);
  expect(layout.editorial.right).toBeCloseTo(layout.hero.right, 0);
  expect(layout.rail.width).toBeCloseTo(layout.tokens.rail, 0);
  expect(layout.gap).toBeCloseTo(layout.tokens.gap, 0);
  expect(layout.main.right).toBeCloseTo(layout.editorial.right, 0);
  expect(layout.round.left).toBeCloseTo(layout.main.left, 0);
  expect(layout.roundExample.width).toBeLessThanOrEqual(layout.tokens.measure + 1);
  expect(layout.round.right).toBeLessThan(layout.main.right);
  expect(layout.lead.width).toBeLessThanOrEqual(layout.tokens.measure + 1);
  expect(layout.methodNote.right).toBeCloseTo(layout.main.right, 0);
  expect(layout.methodNoteParagraph.right).toBeCloseTo(layout.methodNoteContentRight, 0);
  expect(layout.rationaleNote.right).toBeCloseTo(layout.main.right, 0);
  expect(layout.rationaleNoteParagraph.right).toBeCloseTo(layout.rationaleNote.right, 0);
  expect(layout.main.width).toBeGreaterThan(layout.lead.width);
});

test("Method role and isolation headings stay close to their related text", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));

  for (const width of [1800, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("methodology/");
    await waitForPublication(page);

    const gaps = await page.evaluate(() => {
      const roleGaps = Array.from(document.querySelectorAll(".answer-roles article")).map(
        (card) => {
          const label = card.querySelector<HTMLElement>("span");
          const heading = card.querySelector<HTMLElement>("h3");
          if (label === null || heading === null) {
            throw new Error("A methodology role card is incomplete.");
          }
          return heading.getBoundingClientRect().top - label.getBoundingClientRect().bottom;
        },
      );
      const calloutHeading = document.querySelector<HTMLElement>(".isolation-callout h3");
      const calloutBody = document.querySelector<HTMLElement>(".isolation-callout p");
      if (calloutHeading === null || calloutBody === null) {
        throw new Error("The methodology isolation callout is incomplete.");
      }
      return {
        callout:
          calloutBody.getBoundingClientRect().top - calloutHeading.getBoundingClientRect().bottom,
        roles: roleGaps,
      };
    });

    expect(gaps.roles).toHaveLength(4);
    for (const gap of gaps.roles) {
      expect(gap).toBeGreaterThanOrEqual(12);
      expect(gap).toBeLessThanOrEqual(18);
    }
    expect(gaps.callout).toBeGreaterThanOrEqual(15);
    expect(gaps.callout).toBeLessThanOrEqual(17);
    await expectNoViewportOverflow(page);
  }
});

test("question score and CI width plots align on desktop and stack on mobile", { tag: ["@layout", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto("results/");
  await waitForPublication(page);
  const scoreCanvas = page.locator(".score-dot-plot-canvas--score");
  const widthCanvas = page.locator(".score-dot-plot-canvas--width");
  const scoreBox = await scoreCanvas.boundingBox();
  const widthBox = await widthCanvas.boundingBox();
  expect(scoreBox).not.toBeNull();
  expect(widthBox).not.toBeNull();
  expect(widthBox!.height).toBe(scoreBox!.height);
  const scoreSvgText = await scoreCanvas.locator("svg").textContent();
  const widthSvgText = await widthCanvas.locator("svg").textContent();
  const scoreValueRightEdges = await scoreCanvas.locator("svg text").evaluateAll(
    (elements) =>
      elements
        .filter((element) => /^\d+\.\d{2}$/.test(element.textContent ?? ""))
        .map((element) => element.getBoundingClientRect().right),
  );
  expect(scoreValueRightEdges).toHaveLength(11);
  expect(
    Math.max(...scoreValueRightEdges) - Math.min(...scoreValueRightEdges),
  ).toBeLessThanOrEqual(1);
  expect(scoreSvgText).toContain("32.23");
  expect(scoreSvgText).toContain("Synthetic Model 09");

  if (testInfo.project.name.startsWith("mobile")) {
    expect(widthBox!.y).toBeGreaterThan(scoreBox!.y + scoreBox!.height);
    expect(scoreSvgText).toContain("Synthetic Model 12high");
    expect(scoreSvgText).toContain("Synthetic Model 03medium");
    expect(scoreSvgText).toContain("Synthetic Model 09none");
    expect(scoreSvgText).not.toContain("Synthetic Model 12 (high)");
    expect(widthSvgText).toContain("Synthetic Model 12high");
    expect(widthSvgText).not.toContain("Synthetic Model 12 (high)");
  } else {
    expect(widthBox!.x).toBeGreaterThan(scoreBox!.x + scoreBox!.width);
    expect(Math.abs(widthBox!.y - scoreBox!.y)).toBeLessThanOrEqual(1);
    expect(scoreSvgText).toContain("Synthetic Model 12 (high)");
  }
});

test("home score heading uses the section-heading scale and alignment", { tag: ["@layout", "@desktop"] }, async ({ page }) => {
  await page.goto("");
  await waitForPublication(page);
  const heading = page.getByRole("heading", {
    name: "Question score",
    level: 3,
  });
  const description = page.locator(".score-chart .chart-description");
  await expect(heading).toBeVisible();
  const headingStyle = await heading.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      fontFamily: style.fontFamily,
      fontSize: Number.parseFloat(style.fontSize),
    };
  });
  expect(headingStyle.fontFamily).toContain("Newsreader");
  expect(headingStyle.fontSize).toBeGreaterThanOrEqual(32);
  const headingBox = await heading.boundingBox();
  const descriptionBox = await description.boundingBox();
  expect(headingBox).not.toBeNull();
  expect(descriptionBox).not.toBeNull();
  expect(Math.abs(headingBox!.x - descriptionBox!.x)).toBeLessThan(1);
});

test("question score stays primary in charts and desktop leaderboards", { tag: ["@layout", "@both"] }, async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");

  for (const routePath of ["", "results/"]) {
    await page.goto(routePath);
    await waitForPublication(page);

    const legend = page.locator(".score-dot-plot-legend-item--primary");
    await expect(legend).toBeVisible();
    await expect(legend).toContainText("Question score");
    await expect(legend.locator("strong")).toHaveCSS("color", "rgb(12, 17, 27)");
    await expect(
      page.getByText("The companion plot shows each exact CI width", {
        exact: false,
      }).first(),
    ).toBeVisible();

    if (mobile) {
      await expect(page.locator(".mobile-result-metrics [data-tone]")).toHaveCount(0);
      const firstMetric = page.locator(".mobile-result-metrics > div").first();
      await expect(firstMetric).toBeVisible();
      await expect(firstMetric.locator("dt")).toHaveText("Question score");
      await expect(firstMetric).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
      const cardAction = page.locator(".mobile-result-action").first();
      await expect(cardAction).toHaveCSS("background-color", "rgb(250, 249, 245)");
      await expect(cardAction).toHaveCSS("color", "rgb(48, 68, 210)");
    } else {
      const primaryColumn = page.locator(".ranking-table .primary-metric-column");
      await expect(primaryColumn.first()).toBeVisible();
      expect(await primaryColumn.count()).toBeGreaterThan(1);
      const tableScore = page.locator(".question-score--table").first();
      await expect(tableScore).toBeVisible();
      await expect(tableScore).toHaveAttribute(
        "aria-label",
        /95% confidence interval/,
      );
      await expect(tableScore.locator("strong")).toHaveCSS(
        "color",
        "rgb(48, 68, 210)",
      );
      await expect(tableScore.locator("strong")).toHaveCSS("font-size", "16px");
      await expect(tableScore.locator(".score-confidence")).not.toContainText("95% CI");
      await expect(
        page.locator("th.primary-metric-column .table-header-stack span").last(),
      ).toHaveCSS("color", "rgb(96, 99, 106)");

      const metricWidths = await page
        .locator(
          ".comparison-ranking-table thead th:not(.rank-column):not(.model-column)",
        )
        .evaluateAll((cells) => cells.map((cell) => cell.getBoundingClientRect().width));
      expect(Math.max(...metricWidths) - Math.min(...metricWidths)).toBeLessThan(1);
      const metricAlignments = await page
        .locator(
          ".comparison-ranking-table thead th:not(.rank-column):not(.model-column)",
        )
        .evaluateAll((cells) => cells.map((cell) => getComputedStyle(cell).textAlign));
      expect(metricAlignments.every((alignment) => alignment === "right")).toBe(true);
      const reasoningCell = page.locator(".comparison-ranking-table td.reasoning-column").first();
      if ((await reasoningCell.count()) > 0) {
        await expect(reasoningCell).toHaveCSS("text-align", "right");
      }
    }
  }
});

test("result tables use the available width before collapsing to cards", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.setViewportSize({ width: 1130, height: 900 });

  for (const routePath of [
    "results/",
    "results/reliability/",
    "results/cost/",
    "results/time/",
    "results/efficiency/",
  ]) {
    await page.goto(routePath);
    await waitForPublication(page);
    const tableWrap = page.locator(".results-table-wrap");
    await expect(tableWrap).toBeVisible();
    await expect(page.locator(".mobile-result-list")).toBeHidden();
    const spacing = await page.locator(".content-inner").evaluate((element) => {
      const box = element.getBoundingClientRect();
      return {
        left: box.left,
        right: document.documentElement.clientWidth - box.right,
      };
    });
    expect(spacing.left).toBeGreaterThanOrEqual(40);
    expect(spacing.right).toBeGreaterThanOrEqual(40);
    await expectNoViewportOverflow(page);
  }

  await page.setViewportSize({ width: 1129, height: 900 });
  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".results-table-wrap")).toBeHidden();
  await expect(page.locator(".mobile-result-list")).toBeVisible();
});

test("result hints stay inside their chart headings", { tag: ["@layout", "@both"] }, async ({
  page,
}, testInfo) => {
  const routes = [
    { path: "results/", helpCount: 1 },
    { path: "results/reliability/", helpCount: 1 },
    { path: "results/cost/", helpCount: 1 },
    { path: "results/time/", helpCount: 1 },
    { path: "results/efficiency/", helpCount: 1 },
  ] as const;

  for (const route of routes) {
    await page.goto(route.path);
    await waitForPublication(page);
    await expect(page.locator(".content-inner > .result-help")).toHaveCount(0);
    await expect(
      page.locator(".panel-heading--with-help > .result-help"),
    ).toHaveCount(route.helpCount);
    await expect(page.locator(".result-help-heading")).toHaveCount(0);
    await expectMinimumSize(page.locator(".result-help .info-popover-trigger"), 44);

    const titleGroups = page.locator(
      ".result-chart-panel > .panel-heading > div:first-child",
    );
    const titleGroupCount = await titleGroups.count();
    for (let index = 0; index < titleGroupCount; index += 1) {
      const titleGroup = titleGroups.nth(index);
      const eyebrowBox = await titleGroup.locator(".eyebrow").boundingBox();
      const headingBox = await titleGroup.locator("h2, h3").boundingBox();
      expect(eyebrowBox).not.toBeNull();
      expect(headingBox).not.toBeNull();
      expect(Math.abs(eyebrowBox!.x - headingBox!.x)).toBeLessThan(1);
      await expect(titleGroup).toHaveCSS("text-align", "left");
    }
  }

  if (testInfo.project.name.startsWith("mobile")) {
    await page.goto("results/reliability/");
    await waitForPublication(page);
    const heading = page.locator(".reliability-scatter-panel > .panel-heading");
    const copyBox = await heading.locator(":scope > p").boundingBox();
    const helpBox = await heading.locator(":scope > .result-help").boundingBox();
    expect(copyBox).not.toBeNull();
    expect(helpBox).not.toBeNull();
    expect(helpBox!.y).toBeGreaterThanOrEqual(copyBox!.y + copyBox!.height - 1);
  } else {
    await page.setViewportSize({ width: 1200, height: 900 });
    await page.goto("results/");
    await waitForPublication(page);
    const compactHeading = page.locator(".panel-heading--with-help");
    const compactTitleBox = await compactHeading
      .locator(":scope > div:first-child")
      .boundingBox();
    const compactCopyBox = await compactHeading.locator(":scope > p").boundingBox();
    const compactHelpBox = await compactHeading
      .locator(":scope > .result-help")
      .boundingBox();
    expect(compactTitleBox).not.toBeNull();
    expect(compactCopyBox).not.toBeNull();
    expect(compactHelpBox).not.toBeNull();
    expect(compactCopyBox!.width).toBeGreaterThan(compactTitleBox!.width);
    expect(Math.abs(compactHelpBox!.x - compactCopyBox!.x)).toBeLessThan(1);
    expect(Math.abs(compactHelpBox!.width - compactCopyBox!.width)).toBeLessThan(1);

    await page.setViewportSize({ width: 1920, height: 1080 });
    for (const route of routes) {
      await page.goto(route.path);
      await waitForPublication(page);
      const headings = page.locator(".panel-heading--with-help");
      await expect(headings).toHaveCount(route.helpCount);

      for (let index = 0; index < route.helpCount; index += 1) {
        const heading = headings.nth(index);
        const copyBox = await heading.locator(":scope > p").boundingBox();
        const helpBox = await heading.locator(":scope > .result-help").boundingBox();
        expect(copyBox).not.toBeNull();
        expect(helpBox).not.toBeNull();
        expect(copyBox!.width).toBeGreaterThanOrEqual(560);
        expect(copyBox!.width).toBeLessThanOrEqual(576);
        expect(helpBox!.x).toBeGreaterThanOrEqual(copyBox!.x + copyBox!.width);
      }
      await expectNoViewportOverflow(page);
    }
  }
  await expectNoViewportOverflow(page);
});

test("detailed metric definitions stay contained", { tag: ["@layout", "@desktop"] }, async ({ page }) => {
  await page.goto("results/efficiency/");
  await waitForPublication(page);
  const definition = page.locator(".metric-definition-card");
  await expect(definition).toBeVisible();
  await expect(definition).toContainText("Normalized ideal distance.");
  await expect(page.locator(".definition-section")).toHaveCount(0);
  await definition.locator("summary").click();
  await expect(definition.locator("details")).toHaveAttribute("open", "");
  await expect(definition.locator(".metric-definition-toggle-open")).toBeVisible();
  await expect(definition).toContainText("normalized question score 0.06");
  await expectNoViewportOverflow(page);
});

test("workspace routes stay within the viewport", { tag: ["@layout", "@desktop", "@smoke"] }, async ({ page }) => {
  for (const routePath of [runPath, subjectPath, episodePath]) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator(".loading-state")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  }
});

test("workspace model names separate reasoning effort and panels stay aligned", { tag: ["@layout", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto(runPath);
  await waitForPublication(page);

  const title = page.locator(".run-workspace-hero h1");
  const titleLabel = title.locator(".model-name-label");
  const effort = title.locator(".model-name-effort");
  await expect(titleLabel).not.toContainText("(");
  await expect(effort).toBeVisible();
  await expect(effort).toHaveCSS("border-top-style", "solid");
  const typeSizes = await title.evaluate((element) => {
    const badge = element.querySelector<HTMLElement>(".model-name-effort");
    if (badge === null) throw new Error("The model effort badge is missing.");
    return {
      title: Number.parseFloat(getComputedStyle(element).fontSize),
      badge: Number.parseFloat(getComputedStyle(badge).fontSize),
    };
  });
  expect(typeSizes.badge).toBeLessThan(typeSizes.title / 2);

  const titleLabelBox = await titleLabel.boundingBox();
  const effortBox = await effort.boundingBox();
  const titleBox = await title.boundingBox();
  expect(titleLabelBox).not.toBeNull();
  expect(effortBox).not.toBeNull();
  expect(titleBox).not.toBeNull();
  expect(effortBox!.y).toBeGreaterThanOrEqual(titleLabelBox!.y - 1);
  expect(effortBox!.y + effortBox!.height).toBeLessThanOrEqual(
    titleBox!.y + titleBox!.height + 1,
  );

  const scoreCard = page.locator(".run-primary-score");
  const scoreLabelBox = await scoreCard.locator(".score-label").boundingBox();
  const scoreValueBox = await scoreCard.locator("strong").boundingBox();
  const scoreCardBox = await scoreCard.boundingBox();
  expect(scoreLabelBox).not.toBeNull();
  expect(scoreValueBox).not.toBeNull();
  expect(scoreCardBox).not.toBeNull();
  expect(scoreValueBox!.x).toBeGreaterThan(scoreLabelBox!.x + scoreLabelBox!.width);
  expect(scoreCardBox!.height).toBeLessThan(210);

  if (!testInfo.project.name.startsWith("mobile")) {
    const metricsBox = await page.locator(".workspace-metrics").boundingBox();
    const gridBox = await page.locator(".run-overview-grid").boundingBox();
    const totalsBox = await page.locator(".run-totals").boundingBox();
    const rolesBox = await page.locator(".role-ledger").boundingBox();
    const metricCells = await page
      .locator(".workspace-metrics > div")
      .evaluateAll((elements) =>
        elements.map((element) => {
          const rectangle = element.getBoundingClientRect();
          return { left: rectangle.left, right: rectangle.right };
        }),
      );
    expect(metricsBox).not.toBeNull();
    expect(gridBox).not.toBeNull();
    expect(totalsBox).not.toBeNull();
    expect(rolesBox).not.toBeNull();
    expect(Math.abs(metricsBox!.x - gridBox!.x)).toBeLessThanOrEqual(1);
    expect(
      Math.abs(
        metricsBox!.x + metricsBox!.width - (gridBox!.x + gridBox!.width),
      ),
    ).toBeLessThanOrEqual(1);
    expect(
      Math.abs(gridBox!.y - (metricsBox!.y + metricsBox!.height)),
    ).toBeLessThanOrEqual(1);
    expect(Math.abs(totalsBox!.y - rolesBox!.y)).toBeLessThanOrEqual(1);
    expect(
      Math.abs(rolesBox!.x - (totalsBox!.x + totalsBox!.width)),
    ).toBeLessThanOrEqual(1);
    expect(metricCells).toHaveLength(4);
    expect(
      Math.abs(metricCells[1]!.right - (totalsBox!.x + totalsBox!.width)),
    ).toBeLessThanOrEqual(1);
    expect(Math.abs(metricCells[2]!.left - rolesBox!.x)).toBeLessThanOrEqual(2);
  }
});

test("workspace detail boundaries stay left aligned on wide screens", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.setViewportSize({ width: 1920, height: 1080 });

  for (const route of [
    {
      path: runPath,
      pane: ".run-overview-pane",
      boundary: ".run-workspace-hero",
    },
    {
      path: subjectPath,
      pane: ".subject-overview-pane",
      boundary: ".subject-overview-inner",
    },
    {
      path: episodePath,
      pane: ".episode-panel",
      boundary: ".episode-panel > .content-inner",
    },
  ]) {
    await page.goto(route.path);
    await waitForPublication(page);
    await page.locator(route.boundary).first().waitFor();
    const spacing = await page.evaluate(({ paneSelector, boundarySelector }) => {
      const pane = document.querySelector<HTMLElement>(paneSelector);
      const boundary = document.querySelector<HTMLElement>(boundarySelector);
      if (pane === null || boundary === null) {
        throw new Error("The workspace detail boundary was not rendered");
      }
      const paneBox = pane.getBoundingClientRect();
      const boundaryBox = boundary.getBoundingClientRect();
      return {
        left: boundaryBox.left - paneBox.left,
        right: paneBox.right - boundaryBox.right,
      };
    }, { paneSelector: route.pane, boundarySelector: route.boundary });

    expect(spacing.left).toBeGreaterThanOrEqual(30);
    expect(spacing.left).toBeLessThanOrEqual(46);
    expect(spacing.right).toBeGreaterThanOrEqual(spacing.left);
    await expectNoViewportOverflow(page);
  }
});

test("subject overview score matches the subject title scale", { tag: ["@layout", "@desktop"] }, async ({ page }) => {
  await page.goto(subjectPath);
  await waitForPublication(page);

  const typeSizes = await page.evaluate(() => {
    const title = document.querySelector<HTMLElement>(".subject-overview-inner h2");
    const score = document.querySelector<HTMLElement>(".subject-score-card strong");
    if (title === null || score === null) {
      throw new Error("The subject overview title or score was not rendered");
    }
    return {
      title: Number.parseFloat(getComputedStyle(title).fontSize),
      score: Number.parseFloat(getComputedStyle(score).fontSize),
      titleLineHeight: Number.parseFloat(getComputedStyle(title).lineHeight),
      scoreLineHeight: Number.parseFloat(getComputedStyle(score).lineHeight),
    };
  });

  expect(typeSizes.score).toBe(typeSizes.title);
  expect(typeSizes.scoreLineHeight).toBe(typeSizes.titleLineHeight);
});

test("footer links keep their external arrow on the same line", { tag: ["@layout", "@desktop"] }, async ({ page }) => {
  for (const width of [1200, 320]) {
    await page.setViewportSize({ width, height: 700 });
    await page.goto("results/");
    await waitForPublication(page);
    const footer = page.locator(".site-footer");
    await footer.scrollIntoViewIfNeeded();
    const links = footer.locator("nav a");
    expect(await links.count()).toBeGreaterThan(0);
    for (let index = 0; index < (await links.count()); index += 1) {
      const link = links.nth(index);
      await expect(link).toHaveCSS("white-space", "nowrap");
      const box = await link.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.height).toBeLessThan(30);
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1);
    }
    await expectNoViewportOverflow(page);
  }
});

test("result charts remain contained across the mobile breakpoint", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));

  for (const routePath of [
    "results/",
    "results/reliability/",
    "results/cost/",
    "results/time/",
    "results/efficiency/",
  ]) {
    await page.setViewportSize({ width: 1000, height: 900 });
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator(".result-chart-panel svg").first()).toBeVisible();

    for (const width of [720, 840, 720]) {
      await page.setViewportSize({ width, height: 900 });
      await expect
        .poll(() =>
          page.evaluate(() => {
            const root = document.documentElement;
            const panels = [...document.querySelectorAll(".result-chart-panel")];
            const panelsContained = panels.every((panel) => {
              const panelBounds = panel.getBoundingClientRect();
              return [...panel.children].every((child) => {
                const childBounds = child.getBoundingClientRect();
                return (
                  childBounds.left >= panelBounds.left - 1 &&
                  childBounds.right <= panelBounds.right + 1
                );
              });
            });
            const canvases = [
              ...document.querySelectorAll(".result-chart-panel [class$='-canvas']"),
            ];
            const chartsResized = canvases.every((canvas) => {
              const renderer = canvas.firstElementChild;
              return (
                renderer === null ||
                Math.abs(
                  renderer.getBoundingClientRect().width -
                    canvas.getBoundingClientRect().width,
                ) <= 1
              );
            });
            return (
              root.scrollWidth <= root.clientWidth + 1 &&
              panelsContained &&
              chartsResized
            );
          }),
        )
        .toBe(true);
    }
  }
});

test("episode summary follows the five, three, and two column rules", { tag: ["@layout", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto(episodePath);
  await waitForPublication(page);
  const cells = page.locator(".episode-summary-metrics > div");
  await expect(cells).toHaveCount(5);
  const boxes = await cells.evaluateAll((elements) =>
    elements.map((element) => {
      const rectangle = element.getBoundingClientRect();
      return {
        left: rectangle.left,
        top: rectangle.top,
        width: rectangle.width,
      };
    }),
  );

  if (testInfo.project.name.startsWith("mobile")) {
    expect(Math.abs(boxes[0]!.top - boxes[1]!.top)).toBeLessThan(2);
    expect(Math.abs(boxes[2]!.top - boxes[3]!.top)).toBeLessThan(2);
    expect(boxes[4]!.width).toBeGreaterThan(boxes[3]!.width * 1.9);
  } else {
    expect(Math.abs(boxes[0]!.top - boxes[4]!.top)).toBeLessThan(2);
    expect(Math.abs(boxes[0]!.width - boxes[4]!.width)).toBeLessThan(2);

    await page.setViewportSize({ width: 1280, height: 900 });
    const tallBoxes = await cells.evaluateAll((elements) =>
      elements.map((element) => {
        const rectangle = element.getBoundingClientRect();
        return {
          top: rectangle.top,
          width: rectangle.width,
        };
      }),
    );
    expect(Math.abs(tallBoxes[0]!.top - tallBoxes[2]!.top)).toBeLessThan(2);
    expect(Math.abs(tallBoxes[3]!.top - tallBoxes[4]!.top)).toBeLessThan(2);
    expect(tallBoxes[4]!.width).toBeGreaterThan(tallBoxes[3]!.width * 1.9);
  }

  const smallTextSizes = await page
    .locator(".episode-summary-metrics dt, .episode-summary-metrics small")
    .evaluateAll((elements) =>
      elements.map((element) => Number.parseFloat(getComputedStyle(element).fontSize)),
    );
  expect(Math.min(...smallTextSizes)).toBeGreaterThanOrEqual(11);

  const displayType = await page.evaluate(() => {
    const title = document.querySelector<HTMLElement>(".episode-summary h1");
    const transcriptTitle = document.querySelector<HTMLElement>(
      ".episode-transcript .section-heading h2",
    );
    const metricValues = Array.from(
      document.querySelectorAll<HTMLElement>(".episode-summary-metrics dd"),
    );
    const panelTitles = Array.from(
      document.querySelectorAll<HTMLElement>(".episode-panel .section-heading h2"),
    );
    if (title === null || transcriptTitle === null || metricValues.length === 0) {
      throw new Error("Episode display type was not rendered");
    }
    return {
      titleSize: Number.parseFloat(getComputedStyle(title).fontSize),
      transcriptTitleSize: Number.parseFloat(
        getComputedStyle(transcriptTitle).fontSize,
      ),
      panelTitleSizes: panelTitles.map((panelTitle) =>
        Number.parseFloat(getComputedStyle(panelTitle).fontSize),
      ),
      metricSizes: metricValues.map((value) =>
        Number.parseFloat(getComputedStyle(value).fontSize),
      ),
    };
  });
  expect(displayType.titleSize).toBeLessThanOrEqual(43);
  expect(displayType.transcriptTitleSize).toBeLessThanOrEqual(43);
  expect(Math.max(...displayType.panelTitleSizes)).toBeLessThanOrEqual(43);
  expect(Math.max(...displayType.metricSizes)).toBeLessThanOrEqual(29);
});

test("short desktop episode leaves room for a complete turn", { tag: ["@layout", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.setViewportSize({ width: 1175, height: 724 });
  await page.goto(episodePath);
  await waitForPublication(page);

  const layout = await page.evaluate(() => {
    const content = document.querySelector<HTMLElement>(".episode-content");
    const hero = document.querySelector<HTMLElement>(".episode-hero");
    const firstTurn = document.querySelector<HTMLElement>(".turn");
    if (content === null || hero === null || firstTurn === null) {
      throw new Error("Episode layout was not rendered");
    }
    return {
      contentHeight: content.getBoundingClientRect().height,
      heroHeight: hero.getBoundingClientRect().height,
      turnHeight: firstTurn.getBoundingClientRect().height,
    };
  });

  expect(layout.heroHeight).toBeLessThanOrEqual(165);
  expect(layout.contentHeight).toBeGreaterThanOrEqual(380);
  expect(layout.contentHeight).toBeGreaterThanOrEqual(layout.turnHeight);
});
