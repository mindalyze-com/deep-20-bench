import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Locator, type Page } from "@playwright/test";

interface ManifestRun {
  execution_id: string;
}

interface PublicationManifest {
  official_runs: ManifestRun[];
}

interface RunSubject {
  target_id: string;
}

interface RunDocumentFixture {
  subjects: RunSubject[];
}

interface TrialFixture {
  trial_id: string;
  status: string;
}

interface SubjectDocumentFixture {
  trials: TrialFixture[];
}

const dataRoot = path.resolve(process.cwd(), "../../../docs/data");
const manifest = JSON.parse(
  readFileSync(path.join(dataRoot, "manifest.json"), "utf8"),
) as PublicationManifest;
const executionId = manifest.official_runs[0]?.execution_id;

if (executionId === undefined) {
  throw new Error("The publication fixture has no official run.");
}

const runDocument = JSON.parse(
  readFileSync(path.join(dataRoot, "runs", `${executionId}.json`), "utf8"),
) as RunDocumentFixture;
const targetId = runDocument.subjects[0]?.target_id;

if (targetId === undefined) {
  throw new Error(`Run ${executionId} has no subjects.`);
}

const subjectDocument = JSON.parse(
  readFileSync(
    path.join(dataRoot, "runs", executionId, "subjects", `${targetId}.json`),
    "utf8",
  ),
) as SubjectDocumentFixture;
const trialId = subjectDocument.trials.find(
  (trial) => trial.status !== "infrastructure_failure",
)?.trial_id;

if (trialId === undefined) {
  throw new Error(`Subject ${targetId} has no public episode.`);
}

const runPath = `runs/${executionId}/`;
const subjectPath = `${runPath}subjects/${targetId}/`;
const episodePath = `${subjectPath}episodes/${trialId}/`;

const staticPaths = [
  "",
  "results/",
  "results/reliability/",
  "results/cost/",
  "results/time/",
  "results/efficiency/",
  "methodology/",
  "story/",
  "data/",
] as const;

const waitForPublication = async (page: Page): Promise<void> => {
  await page.locator("#main").waitFor();
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
};

const expectNoViewportOverflow = async (page: Page): Promise<void> => {
  const overflow = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(overflow.scroll).toBeLessThanOrEqual(overflow.client + 1);
};

const expectMinimumSize = async (
  locator: Locator,
  minimum: number,
): Promise<void> => {
  await expect(locator.first()).toBeVisible();
  const boxes = await locator.evaluateAll((elements) =>
    elements.map((element) => {
      const rectangle = element.getBoundingClientRect();
      return { width: rectangle.width, height: rectangle.height };
    }),
  );
  expect(boxes.length).toBeGreaterThan(0);
  for (const box of boxes) {
    expect(box.width).toBeGreaterThanOrEqual(minimum);
    expect(box.height).toBeGreaterThanOrEqual(minimum);
  }
};

const expectVerticalGap = async (
  upper: Locator,
  lower: Locator,
  minimum: number,
): Promise<void> => {
  const upperBox = await upper.boundingBox();
  const lowerBox = await lower.boundingBox();
  expect(upperBox).not.toBeNull();
  expect(lowerBox).not.toBeNull();
  expect(lowerBox!.y - (upperBox!.y + upperBox!.height)).toBeGreaterThanOrEqual(
    minimum,
  );
};

test("public routes stay within the viewport", async ({ page }) => {
  for (const routePath of staticPaths) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator("h1").first()).toBeVisible();
    await expectNoViewportOverflow(page);
  }
});

test("source link includes the GitHub mark", async ({ page }) => {
  await page.goto("");
  await waitForPublication(page);
  const sourceLink = page.getByRole("link", {
    name: "Source code (opens in a new tab)",
  });
  await expect(sourceLink.locator(".repository-icon")).toBeVisible();
});

test("question scores show repeated-trial confidence intervals", async ({ page }) => {
  await page.goto("");
  await waitForPublication(page);
  await expect(page.locator(".score-dot-plot-canvas svg")).toBeVisible();
  await expect(page.locator(".score-dot-plot figcaption")).toContainText(
    "Question score",
  );
  await expect(page.locator(".score-dot-plot figcaption")).toContainText(
    "lower is better",
  );
  await expect(page.locator(".score-dot-plot figcaption")).toContainText(
    "95% CI of average",
  );
  await expect(page.locator(".winner-card .score-confidence")).toContainText("95% CI");

  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".score-dot-plot-canvas svg")).toBeVisible();
  await expect
    .poll(() => page.locator('.score-dot-plot-canvas path[fill="#4f5dff"]').count())
    .toBeGreaterThan(0);
  await expect
    .poll(() => page.locator('.score-dot-plot-canvas path[stroke="#4f5dff"]').count())
    .toBeGreaterThan(0);
  await expect(page.locator(".score-dot-plot-legend-interval")).toHaveCSS(
    "background-color",
    "rgb(79, 93, 255)",
  );
  await expect(
    page.getByText("The range uses repeated seeded runs on the seven fixed subjects"),
  ).toBeVisible();
});

test("repeat-average controls remain unavailable", async ({ page }) => {
  for (const routePath of ["", "results/"]) {
    let repeatAverageRequests = 0;
    const countRepeatRequest = (request: { url: () => string }): void => {
      if (request.url().endsWith("/data/repeat-averages.json")) {
        repeatAverageRequests += 1;
      }
    };
    page.on("request", countRepeatRequest);
    await page.goto(routePath);
    await waitForPublication(page);

    await expect(
      page.getByRole("switch", { name: /Show repeat averages/ }),
    ).toHaveCount(0);
    expect(repeatAverageRequests).toBe(0);
    await expect(page.locator(".score-dot-plot-caption")).not.toContainText(
      "repeat average",
    );
    await expectNoViewportOverflow(page);
    page.off("request", countRepeatRequest);
  }
});

test("home score heading uses the section-heading scale and alignment", async ({ page }) => {
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

test("question score stays visually primary in both leaderboards", async ({
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
      page.getByText("Shorter lines suggest more consistent performance", { exact: false }),
    ).toBeVisible();

    if (mobile) {
      const primaryMetric = page.locator(
        '.mobile-result-metrics [data-tone="primary"]',
      ).first();
      await expect(primaryMetric).toBeVisible();
      await expect(primaryMetric.locator("dt")).toHaveText("Score");
      await expect(primaryMetric.locator("dd")).toHaveCSS(
        "color",
        "rgb(48, 68, 210)",
      );
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
          ".comparison-ranking-table thead th:not(.rank-column):not(.model-column):not(.run-column)",
        )
        .evaluateAll((cells) => cells.map((cell) => cell.getBoundingClientRect().width));
      expect(Math.max(...metricWidths) - Math.min(...metricWidths)).toBeLessThan(1);
      const metricAlignments = await page
        .locator(
          ".comparison-ranking-table thead th:not(.rank-column):not(.model-column):not(.run-column)",
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

test("result metric explanations work by keyboard and tap", async ({ page }) => {
  await page.goto("results/");
  await waitForPublication(page);
  const scoreHelp = page.getByRole("button", { name: "Question score" });
  await scoreHelp.click();
  await expect(page.getByRole("dialog", { name: "Question score" })).toContainText(
    "Failed trials receive the benchmark penalty",
  );
  await page.keyboard.press("Escape");
  await expect(scoreHelp).toBeFocused();

  await page.goto("results/reliability/");
  await waitForPublication(page);
  await page.getByRole("button", { name: "Repeatability width" }).click();
  await expect(
    page.getByRole("dialog", { name: "Repeatability width" }),
  ).toContainText("upper 95% confidence bound minus the lower bound");
});

test("result hints stay inside their chart headings", async ({
  page,
}, testInfo) => {
  const routes = [
    { path: "results/", helpCount: 1 },
    { path: "results/reliability/", helpCount: 1 },
    { path: "results/cost/", helpCount: 1 },
    { path: "results/time/", helpCount: 1 },
    { path: "results/efficiency/", helpCount: 2 },
  ] as const;

  for (const route of routes) {
    await page.goto(route.path);
    await waitForPublication(page);
    await expect(page.locator(".content-inner > .result-help")).toHaveCount(0);
    await expect(
      page.locator(".panel-heading--with-help > .result-help"),
    ).toHaveCount(route.helpCount);
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

test("detailed metric definitions stay contained", async ({ page }) => {
  await page.goto("results/efficiency/");
  await waitForPublication(page);
  const definition = page.locator(".metric-definition-card");
  await expect(definition).toBeVisible();
  await expect(definition).toContainText("Cost-adjusted score.");
  await expect(page.locator(".definition-section")).toHaveCount(0);
  await definition.locator("summary").click();
  await expect(definition.locator("details")).toHaveAttribute("open", "");
  await expect(definition.locator(".metric-definition-toggle-open")).toBeVisible();
  await expect(definition).toContainText("12.3 questions × $0.0500 per episode");
  await expectNoViewportOverflow(page);
});

test("workspace routes stay within the viewport", async ({ page }) => {
  for (const routePath of [runPath, subjectPath, episodePath]) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator(".loading-state")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  }
});

test("workspace rows show persistent drill-down affordances", async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");
  await page.goto(runPath);
  await waitForPublication(page);

  const subjectLinks = page.locator(
    mobile ? ".mobile-subjects a" : ".subject-rail-list a",
  );
  const subjectArrows = subjectLinks.locator(
    mobile ? ":scope > span:last-child" : ".rail-link-arrow",
  );
  await expect(subjectArrows).toHaveCount(await subjectLinks.count());
  await expect(subjectArrows.first()).toBeVisible();
  if (!mobile) {
    await expect(page.locator(".subject-list-heading")).toContainText("Subjects");
    await expect(page.locator(".subject-list-heading")).toContainText("choose one");
  }

  await subjectLinks.first().focus();
  await expect(subjectLinks.first()).toHaveCSS("outline-style", "solid");
  await expect(subjectLinks.first()).toHaveCSS("outline-offset", "-3px");

  await subjectLinks.first().click();
  await expect(page).toHaveURL(new RegExp(`/subjects/${targetId}/$`));
  await waitForPublication(page);
  const episodeLinks = page.locator(".episode-list > a");
  await expect(page.locator(".episode-list-heading")).toContainText("Episodes");
  await expect(page.locator(".episode-list-heading")).toContainText("choose one");
  await expect(page.locator(".episode-link-arrow")).toHaveCount(
    await episodeLinks.count(),
  );
  await expect(page.locator(".episode-link-arrow").first()).toBeVisible();
  await expect(
    page.locator(".episode-list > span.disabled .episode-link-arrow"),
  ).toHaveCount(0);

  await episodeLinks.first().focus();
  await expect(episodeLinks.first()).toHaveCSS("outline-style", "solid");
  await expect(episodeLinks.first()).toHaveCSS("outline-offset", "-3px");
  await episodeLinks.first().click();
  await expect(page).toHaveURL(new RegExp(`/episodes/${trialId}/$`));
});

test("result navigation, tables, and charts use the shared workspace", async ({
  page,
}, testInfo) => {
  for (const routePath of [
    "results/",
    "results/reliability/",
    "results/cost/",
    "results/time/",
    "results/efficiency/",
  ]) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator(".results-workspace-header")).toBeVisible();
    await expect(page.locator(".results-nav a.active")).toHaveCount(1);
    await expect(page.locator(".results-workspace-header .results-nav")).toHaveCount(1);
    await expect(page.locator(".results-view > .page-hero")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  }

  await page.goto("results/cost/");
  await expect(page.locator(".stacked-chart-canvas svg")).toBeVisible();
  await expect(page.locator(".cost-panel + .component-ledger")).toHaveCount(1);
  await expect(page.locator(".cost-panel .component-ledger")).toHaveCount(0);
  await expect(page.locator(".result-chart-stack")).toHaveCSS(
    "background-color",
    "rgba(0, 0, 0, 0)",
  );
  await expect(page.locator(".results-view")).toHaveCSS(
    "background-color",
    "rgb(243, 240, 232)",
  );
  await expectVerticalGap(
    page.locator(".cost-panel > .metric-chart"),
    page.locator(".component-ledger"),
    23,
  );
  await expect(page.locator(".table-wrap").first()).toHaveCSS(
    "overflow-x",
    testInfo.project.name.startsWith("mobile") ? "auto" : /auto|visible/,
  );

  await page.goto("results/time/");
  await expect(page.locator(".metric-chart-canvas svg").first()).toBeVisible();
  await expect(page.locator(".time-panel + .runtime-ledger")).toHaveCount(1);
  await expect(page.locator(".time-panel .runtime-ledger")).toHaveCount(0);
  await expectVerticalGap(
    page.locator(".time-panel > .metric-chart"),
    page.locator(".runtime-ledger"),
    23,
  );

  await page.goto("results/efficiency/");
  await expect(page.locator(".efficiency-scatter-canvas svg")).toBeVisible();

  await page.goto("results/reliability/");
  await expect(page.locator(".reliability-scatter-canvas svg")).toBeVisible();
  await expect(page.locator(".reliability-comparison")).toHaveCount(0);
  await expect(page.locator(".ranking-table tbody tr").first()).toContainText(
    "Claude Opus 5",
  );
  await expect(page.locator(".ranking-table tbody tr").first()).toContainText("1.86");
});

test("route focus is quiet and interactive focus remains visible", async ({
  page,
}, testInfo) => {
  await page.goto("");
  await waitForPublication(page);
  if (testInfo.project.name.startsWith("mobile")) {
    const mobileMenu = page.locator(".mobile-navigation");
    await mobileMenu.locator("summary").click();
    await mobileMenu.getByRole("link", { name: "Results", exact: true }).click();
  } else {
    await page.locator(".primary-navigation").getByRole("link", {
      name: "Results",
      exact: true,
    }).click();
  }
  const routeContent = page.locator("#route-content");
  await expect(page.locator(".results-nav")).toBeVisible();
  await page.evaluate(
    () =>
      new Promise<void>((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
      }),
  );
  await routeContent.focus();
  await expect(routeContent).toBeFocused();
  await expect(routeContent).toHaveCSS("outline-style", "none");

  await page.keyboard.press("Tab");
  const resultLink = page.locator(".results-nav a").first();
  await expect(resultLink).toBeFocused();
  await expect(resultLink).toHaveCSS("outline-width", "3px");
  await expect(resultLink).toHaveCSS("outline-style", "solid");
});

test("episode tabs support arrow, Home, and End keys", async ({ page }) => {
  await page.goto(episodePath);
  await waitForPublication(page);
  const transcript = page.getByRole("tab", { name: /Transcript/ });
  const reliability = page.getByRole("tab", { name: /Reliability/ });
  const usage = page.getByRole("tab", { name: /Models & usage/ });

  await transcript.focus();
  await transcript.press("ArrowRight");
  await expect(reliability).toBeFocused();
  await expect(reliability).toHaveAttribute("aria-selected", "true");

  await reliability.press("End");
  await expect(usage).toBeFocused();
  await expect(usage).toHaveAttribute("aria-selected", "true");

  await usage.press("Home");
  await expect(transcript).toBeFocused();
  await expect(transcript).toHaveAttribute("aria-selected", "true");

  await transcript.press("ArrowLeft");
  await expect(usage).toBeFocused();
});

test("score explanation restores focus on Escape", async ({ page }) => {
  await page.goto(runPath);
  await waitForPublication(page);
  const trigger = page.locator(".run-primary-score .info-popover-trigger");
  await trigger.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("episode summary follows the five, three, and two column rules", async ({
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
    expect(Math.abs(boxes[0]!.top - boxes[2]!.top)).toBeLessThan(2);
    expect(Math.abs(boxes[3]!.top - boxes[4]!.top)).toBeLessThan(2);
    expect(boxes[4]!.width).toBeGreaterThan(boxes[3]!.width * 1.9);
  }

  const smallTextSizes = await page
    .locator(".episode-summary-metrics dt, .episode-summary-metrics small")
    .evaluateAll((elements) =>
      elements.map((element) => Number.parseFloat(getComputedStyle(element).fontSize)),
    );
  expect(Math.min(...smallTextSizes)).toBeGreaterThanOrEqual(11);
});

test("mobile navigation and episode tabs meet the touch target minimum", async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("mobile"));
  await page.goto(episodePath);
  await waitForPublication(page);
  const mobileMenu = page.locator(".mobile-navigation");
  const mobileMenuTrigger = mobileMenu.locator("summary");
  await expectMinimumSize(mobileMenuTrigger, 44);
  const triggerFontSize = await mobileMenuTrigger.evaluate((element) =>
    Number.parseFloat(getComputedStyle(element).fontSize),
  );
  expect(triggerFontSize).toBeGreaterThanOrEqual(13);
  await expectMinimumSize(mobileMenu.locator(".mobile-navigation-glyph"), 20);
  await expect(mobileMenu.locator(".mobile-navigation-glyph")).toHaveCSS(
    "color",
    "rgb(214, 255, 38)",
  );
  await mobileMenu.locator("summary").click();
  await expect(mobileMenu).toHaveAttribute("open", "");
  await expectMinimumSize(mobileMenu.locator("nav a"), 44);
  const navigationFontSizes = await mobileMenu.locator("nav a").evaluateAll(
    (elements) =>
      elements.map((element) =>
        Number.parseFloat(getComputedStyle(element).fontSize),
      ),
  );
  expect(Math.min(...navigationFontSizes)).toBeGreaterThanOrEqual(14);
  await expectMinimumSize(page.locator(".episode-tabs button"), 44);

  await page.goto(runPath);
  await waitForPublication(page);
  await expectMinimumSize(page.locator(".mobile-subjects a"), 44);

  await page.goto(subjectPath);
  await waitForPublication(page);
  await expectMinimumSize(page.locator(".episode-list > a"), 44);
});

test("mobile pages use one document scroll and no fixed site navigation", async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("mobile"));
  await page.goto(episodePath);
  await waitForPublication(page);
  await expect(page.locator(".loading-state")).toHaveCount(0);

  const initial = await page.evaluate(() => {
    const main = document.querySelector<HTMLElement>(".app-viewport");
    const panel = document.querySelector<HTMLElement>(".episode-panel");
    const header = document.querySelector<HTMLElement>(".site-header");
    if (main === null || panel === null || header === null) {
      throw new Error("The mobile scroll surfaces are missing.");
    }
    return {
      documentHeight: document.documentElement.scrollHeight,
      viewportHeight: window.innerHeight,
      mainOverflowY: getComputedStyle(main).overflowY,
      panelOverflowY: getComputedStyle(panel).overflowY,
      panelScrollTop: panel.scrollTop,
      headerTop: header.getBoundingClientRect().top,
    };
  });

  expect(initial.documentHeight).toBeGreaterThan(initial.viewportHeight * 2);
  expect(initial.mainOverflowY).toBe("visible");
  expect(initial.panelOverflowY).toBe("visible");
  expect(initial.panelScrollTop).toBe(0);
  await expect(page.locator(".primary-navigation")).toBeHidden();
  await expect(page.locator(".mobile-navigation")).toHaveCSS("position", "relative");

  await page.evaluate(() => window.scrollTo({ top: 600 }));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(500);
  const afterScroll = await page.evaluate(() => {
    const panel = document.querySelector<HTMLElement>(".episode-panel");
    const header = document.querySelector<HTMLElement>(".site-header");
    if (panel === null || header === null) {
      throw new Error("The mobile scroll surfaces are missing.");
    }
    return {
      panelScrollTop: panel.scrollTop,
      headerTop: header.getBoundingClientRect().top,
    };
  });
  expect(afterScroll.panelScrollTop).toBe(0);
  expect(afterScroll.headerTop).toBeLessThan(initial.headerTop - 500);
});

test("mobile header menu provides global navigation and closes after selection", async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("mobile"));
  await page.goto(episodePath);
  await waitForPublication(page);

  const mobileMenu = page.locator(".mobile-navigation");
  await mobileMenu.locator("summary").click();
  await expect(mobileMenu).toHaveAttribute("open", "");
  await mobileMenu.getByRole("link", { name: "Method", exact: true }).click();
  await expect(page).toHaveURL(/\/methodology\/$/);
  await expect(mobileMenu).not.toHaveAttribute("open", "");
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
});

test("focused publication surfaces match visual baselines", async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");

  await page.goto("results/");
  await waitForPublication(page);
  if (mobile) {
    await expect(page.locator(".site-header")).toHaveScreenshot("site-header.png");
  }
  await expect(page.locator(".results-workspace-header")).toHaveScreenshot(
    "results-workspace-header.png",
  );
  await expect(page.locator(".results-view .metric-grid").first()).toHaveScreenshot(
    "results-summary-metrics.png",
  );

  await page.goto("results/reliability/");
  await waitForPublication(page);
  await expect(
    page.locator(".reliability-scatter-panel > .panel-heading"),
  ).toHaveScreenshot("results-reliability-heading-help.png");
  await expect(page.locator(".reliability-scatter-panel .reliability-scatter")).toHaveScreenshot(
    "results-reliability-scatter.png",
  );

  await page.goto("results/efficiency/");
  await waitForPublication(page);
  await expect(page.locator(".metric-definition-card")).toHaveScreenshot(
    "results-metric-definition.png",
  );

  await page.goto(runPath);
  await waitForPublication(page);
  await expect(page.locator(".run-workspace-hero")).toHaveScreenshot(
    "run-workspace-hero.png",
  );
  await expect(page.locator(".workspace-metrics")).toHaveScreenshot(
    "run-summary-metrics.png",
  );
  await expect(
    page.locator(mobile ? ".mobile-subjects" : ".model-rail"),
  ).toHaveScreenshot("run-subject-list.png");

  await page.goto(subjectPath);
  await waitForPublication(page);
  await expect(page.locator(".episode-rail")).toHaveScreenshot(
    "subject-episode-list.png",
  );
  if (!mobile) {
    await expect(page.locator(".subject-overview-inner")).toHaveScreenshot(
      "subject-overview.png",
    );
  }

  await page.goto(episodePath);
  await waitForPublication(page);
  await expect(page.locator(".episode-hero")).toHaveScreenshot("episode-header.png");
  await expect(page.locator(".episode-tabs")).toHaveScreenshot("episode-tabs.png");
  if (!mobile) {
    await expect(page.locator(".turn-map")).toHaveScreenshot("episode-turn-map.png");
  }
});
