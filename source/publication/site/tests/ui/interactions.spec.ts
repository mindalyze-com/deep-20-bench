import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "./support/fixture";

import { splitModelName } from "../../src/lib/model-name";
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

test("tables and horizontal breakdowns expose accessible names and focus", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  const resultTables = [
    { path: "results/", caption: "Result comparison" },
    { path: "results/reliability/", caption: "Stability ranking" },
    { path: "results/cost/", caption: "Cost comparison" },
    { path: "results/time/", caption: "Time comparison" },
    { path: "results/efficiency/", caption: "Efficiency ranking" },
  ];
  for (const result of resultTables) {
    await page.goto(result.path);
    await waitForPublication(page);
    await expect(page.locator("table caption", { hasText: result.caption })).toHaveCount(1);
  }

  await page.goto("results/cost/");
  await waitForPublication(page);
  await page.getByText("Exact adjudication breakdown", { exact: true }).click();
  const breakdown = page.locator(".stacked-chart-breakdown-table-wrap");
  await expect(breakdown).toHaveAttribute("tabindex", "0");
  await expect(breakdown).toHaveAttribute(
    "aria-label",
    "Scrollable exact adjudication cost breakdown",
  );

  await page.goto(episodePath);
  await waitForPublication(page);
  await page.getByRole("tab", { name: /Usage/ }).click();
  await expect(page.locator(".telemetry-table caption")).toHaveText("Component telemetry");

  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".score-dot-plot-canvas[tabindex]")).toHaveCount(0);
});

test("official cost and time rows open the selected run", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}) => {
  for (const routePath of ["results/cost/", "results/time/"]) {
    await page.goto(routePath);
    await waitForPublication(page);
    const row = page.locator(".ranking-table tbody tr").first();
    const link = row.getByRole("link");
    const href = await link.getAttribute("href");
    expect(href).not.toBeNull();
    await row.locator("td[data-numeric]").first().click();
    await expect(page).toHaveURL(new RegExp(`${href?.replaceAll("/", "\\/")}$`));
  }
});

test("mobile score plots preserve vertical pan and open model runs", { tag: ["@interactions", "@both", "@smoke"] }, async ({
  page,
}, testInfo) => {
  for (const routePath of ["", "results/"]) {
    await page.goto(routePath);
    await waitForPublication(page);

    const scoreCanvases = page.locator(".score-dot-plot-canvas");
    await expect(scoreCanvases).toHaveCount(2);

    if (testInfo.project.name.startsWith("mobile")) {
      await expect(scoreCanvases.first()).toHaveCSS("pointer-events", "auto");
      await expect(scoreCanvases.first()).toHaveCSS("touch-action", "pan-y");
      await expect(scoreCanvases.last()).toHaveCSS("pointer-events", "auto");
      await expect(scoreCanvases.last()).toHaveCSS("touch-action", "pan-y");

      await scoreCanvases.first().scrollIntoViewIfNeeded();
      await expect(scoreCanvases.first().locator("svg")).toBeVisible();
      const chartBounds = await scoreCanvases.first().boundingBox();
      const viewport = page.viewportSize();
      expect(chartBounds).not.toBeNull();
      expect(viewport).not.toBeNull();
      const touchX = (chartBounds?.x ?? 0) + (chartBounds?.width ?? 0) - 24;
      const touchStartY = Math.min(
        (chartBounds?.y ?? 0) + (chartBounds?.height ?? 0) - 32,
        (viewport?.height ?? 0) - 32,
      );
      const touchEndY = Math.max((chartBounds?.y ?? 0) + 32, touchStartY - 240);
      expect(touchStartY - touchEndY).toBeGreaterThan(80);
      const urlBeforePan = page.url();
      const scrollBeforePan = await page.evaluate(() => window.scrollY);
      const browserSession = await page.context().newCDPSession(page);
      await browserSession.send("Input.dispatchTouchEvent", {
        type: "touchStart",
        touchPoints: [{ x: touchX, y: touchStartY }],
      });
      for (let step = 1; step <= 4; step += 1) {
        await browserSession.send("Input.dispatchTouchEvent", {
          type: "touchMove",
          touchPoints: [
            {
              x: touchX,
              y: touchStartY + ((touchEndY - touchStartY) * step) / 4,
            },
          ],
        });
      }
      await browserSession.send("Input.dispatchTouchEvent", {
        type: "touchEnd",
        touchPoints: [],
      });
      await browserSession.detach();
      await expect
        .poll(async () =>
          Math.abs((await page.evaluate(() => window.scrollY)) - scrollBeforePan),
        )
        .toBeGreaterThan(20);
      await expect(page).toHaveURL(urlBeforePan);

      const runLink = page
        .locator('ol[aria-label$="question scores"] a')
        .first();
      const href = await runLink.getAttribute("href");
      const linkLabel = await runLink.textContent();
      expect(href).not.toBeNull();
      expect(linkLabel).not.toBeNull();
      const modelName = splitModelName(
        linkLabel?.replace("View full run for ", "") ?? "",
      ).displayName;

      await scoreCanvases
        .first()
        .getByText(modelName, { exact: true })
        .tap();
      await expect(page).toHaveURL(new RegExp(`${href?.replaceAll("/", "\\/")}$`));
    } else {
      await expect(scoreCanvases.first()).toHaveCSS("pointer-events", "auto");
      await expect(scoreCanvases.last()).toHaveCSS("pointer-events", "auto");
    }
  }
});

test("primary and result navigation use distinct section names", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  await page.goto("results/");
  await waitForPublication(page);

  const aboutLink = page.locator(".primary-navigation a").filter({ hasText: "About" });
  await expect(aboutLink).toHaveAttribute("href", "/deep-20-bench/about/");
  await expect(page.locator(".primary-navigation a").filter({ hasText: "Story" })).toHaveCount(0);

  const resultLinks = page.locator(".results-nav a");
  await expect(resultLinks).toHaveText(["Score", "Stability", "Cost", "Time", "Efficiency"]);
  await expect(page.locator(".results-nav a.active")).toHaveText("Score");
  await expect(
    page.locator(".results-nav").getByRole("link", { name: "Overview", exact: true }),
  ).toHaveCount(0);

  await page.goto("about/");
  await waitForPublication(page);
  await expect(page).toHaveTitle("Deep20Bench Origin and Related LLM Research");
  await expect(aboutLink).toHaveAttribute("aria-current", "page");
});

test("canonical URL resolves aliases and follows client navigation", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  const canonical = page.locator('link[rel="canonical"]');

  await page.goto("story/");
  await waitForPublication(page);
  await expect(canonical).toHaveAttribute(
    "href",
    "https://mindalyze-com.github.io/deep-20-bench/about/",
  );

  await page.locator(".primary-navigation a").filter({ hasText: "Results" }).click();
  await expect(page).toHaveURL(/\/deep-20-bench\/results\/$/);
  await expect(canonical).toHaveAttribute(
    "href",
    "https://mindalyze-com.github.io/deep-20-bench/results/",
  );

  await page.locator(".primary-navigation a").filter({ hasText: "About" }).click();
  await expect(page).toHaveURL(/\/deep-20-bench\/about\/$/);
  await expect(canonical).toHaveAttribute(
    "href",
    "https://mindalyze-com.github.io/deep-20-bench/about/",
  );
});

test("leaderboard links and headers remain clear while scrolling", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  await page.goto("");
  await waitForPublication(page);

  const firstRow = page.locator(".comparison-ranking-table tbody tr").first();
  await expect(firstRow.locator("a")).toHaveCount(1);
  await expect(firstRow.locator(".model-run-link-chevron")).toBeVisible();
  await expect(page.locator(".comparison-ranking-table .run-column")).toHaveCount(0);

  const singleViolationRow = page
    .locator(".comparison-ranking-table tbody tr")
    .filter({ hasText: "Synthetic Model 04" });
  await expect(singleViolationRow).toContainText(">99%");
  await expect(singleViolationRow).toContainText("1 violation");
  await expect(singleViolationRow).not.toContainText("1 violations");

  await page.goto("results/");
  await waitForPublication(page);
  const episodeCosts = await page
    .locator(".comparison-ranking-table td.cost-column")
    .allTextContents();
  expect(episodeCosts.length).toBeGreaterThan(0);
  expect(
    episodeCosts.every((cost) => /^\$\d+\.\d{4}$/.test(cost.trim())),
  ).toBe(true);

  const table = page.locator(".comparison-ranking-table");
  const firstHeader = table.locator("thead th").first();
  // App.vue reapplies restored scroll at 70 ms and 220 ms after navigation.
  await page.waitForTimeout(250);
  await table.scrollIntoViewIfNeeded();
  await page.evaluate(() => window.scrollBy(0, 140));
  await expect.poll(async () => {
    const box = await firstHeader.boundingBox();
    return box?.y ?? null;
  }).toBe(0);
});

test("collapsed result cards highlight the complete entry", { tag: ["@interactions", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.setViewportSize({
    width: testInfo.project.name.startsWith("mobile") ? 390 : 1100,
    height: 900,
  });
  await page.goto("results/");
  await waitForPublication(page);

  const card = page.locator(".mobile-result-card").first();
  const action = card.locator(".mobile-result-action");
  await expect(card).toBeVisible();
  await expect(action).toHaveCSS("background-color", "rgb(250, 249, 245)");
  await expect(action).toHaveCSS("color", "rgb(48, 68, 210)");
  await expect(action).toHaveCSS("border-top-style", "solid");
  await card.hover();
  await expect(card).toHaveCSS("background-color", "rgb(238, 240, 255)");
  await expect(action).toHaveCSS("background-color", "rgb(238, 240, 255)");
});

test("result metric explanations work by keyboard and tap", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
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
  await page.getByRole("button", { name: "CI width" }).click();
  await expect(
    page.getByRole("dialog", { name: "CI width" }),
  ).toContainText("upper 95% CI bound minus the lower bound");
});

test("workspaces preload the next drilldown view before it is clicked", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}) => {
  const requested = new Set<string>();
  page.on("request", (request) => {
    const url = request.url();
    if (/SubjectWorkspaceView/.test(url)) requested.add("subject");
    if (/EpisodeView/.test(url)) requested.add("episode");
  });

  await page.goto(runPath);
  await waitForPublication(page);
  await expect
    .poll(() => requested.has("subject"))
    .toBe(true);

  await page.goto(subjectPath);
  await waitForPublication(page);
  await expect
    .poll(() => requested.has("episode"))
    .toBe(true);
});

test("cached workspace transitions keep route identities scoped to their workspace", { tag: ["@interactions", "@both", "@smoke"] }, async ({
  page,
}, testInfo) => {
  const invalidDataRequests: string[] = [];
  const browserErrors: string[] = [];
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (/(?:runs|subjects|episodes)\/\.json$/.test(path)) {
      invalidDataRequests.push(path);
    }
  });
  page.on("pageerror", (error) => browserErrors.push(error.message));

  await page.goto("results/");
  await waitForPublication(page);
  await page.locator(`a[href$="/${runPath}"]:visible`).last().click();
  await expect(page).toHaveURL(new RegExp(`${runPath}$`));
  await page.locator(`a[href$="/${subjectPath}"]:visible`).first().click();
  await expect(page).toHaveURL(new RegExp(`${subjectPath}$`));
  await page.locator(`a[href$="/${episodePath}"]:visible`).first().click();
  await expect(page).toHaveURL(new RegExp(`${episodePath}$`));
  await page.locator(`a[href$="/${subjectPath}"]:visible`).last().click();
  await expect(page).toHaveURL(new RegExp(`${subjectPath}$`));
  await page.locator(`a[href$="/${runPath}"]:visible`).first().click();
  await expect(page).toHaveURL(new RegExp(`${runPath}$`));

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
  await expect(page).toHaveURL(/\/results\/$/);
  await page.waitForTimeout(100);

  expect(invalidDataRequests).toEqual([]);
  expect(browserErrors).toEqual([]);
});

test("a slow route module still acknowledges the click", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  await page.route(/EpisodeView/, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_500));
    await route.continue();
  });

  await page.goto(subjectPath);
  await waitForPublication(page);

  await page.locator(".episode-list > a").first().click({ noWaitAfter: true });
  await expect(page.locator(".route-progress")).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`/episodes/${trialId}/$`));
  await expect(page.locator(".route-progress")).toHaveCount(0);
});

test("the first episode stays clickable in a short desktop workspace", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop"));
  await page.setViewportSize({ width: 1280, height: 600 });
  await page.goto(subjectPath);
  await waitForPublication(page);

  const episodeList = page.locator(".episode-list");
  const firstEpisode = episodeList.locator(":scope > a").first();
  const boxes = await Promise.all([
    episodeList.boundingBox(),
    firstEpisode.boundingBox(),
  ]);
  const [listBox, firstBox] = boxes;
  expect(listBox).not.toBeNull();
  expect(firstBox).not.toBeNull();
  expect(firstBox!.y).toBeGreaterThanOrEqual(listBox!.y);
  expect(firstBox!.y + firstBox!.height).toBeLessThanOrEqual(
    listBox!.y + listBox!.height,
  );

  await firstEpisode.click();
  await expect(page).toHaveURL(new RegExp(`/episodes/${trialId}/$`));
  await expect(page.getByRole("heading", { name: "Episode 1", exact: true })).toBeVisible();
});

test("episode navigation continues across subject boundaries", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  const traversalSubjectPath = `${runPath}subjects/${traversalSubjectId}/`;

  await page.goto(
    `${traversalSubjectPath}episodes/${firstTraversalTrialId}/`,
  );
  await waitForPublication(page);
  await expect(page.locator(".loading-state")).toHaveCount(0);

  const firstEpisodeNavigation = page.locator(".sibling-controls");
  await expect(
    firstEpisodeNavigation.getByRole("link", {
      name: "Previous: Previous subject",
    }),
  ).toHaveAttribute(
    "href",
    new RegExp(`/subjects/${previousTraversalSubjectId}/$`),
  );
  await expect(firstEpisodeNavigation.locator('a[rel="next"]')).toContainText(
    "Episode",
  );

  await page.goto(
    `${traversalSubjectPath}episodes/${lastTraversalTrialId}/`,
  );
  await waitForPublication(page);
  await expect(page.locator(".loading-state")).toHaveCount(0);

  const lastEpisodeNavigation = page.locator(".sibling-controls");
  await expect(lastEpisodeNavigation.locator('a[rel="prev"]')).toContainText(
    "Episode",
  );
  const nextSubject = lastEpisodeNavigation.getByRole("link", {
    name: "Next: Next subject",
  });
  await expect(nextSubject).toHaveAttribute(
    "href",
    new RegExp(`/subjects/${nextTraversalSubjectId}/$`),
  );
  await nextSubject.click();
  await expect(page).toHaveURL(
    new RegExp(`/subjects/${nextTraversalSubjectId}/$`),
  );
  await expect(page.locator(".loading-state")).toHaveCount(0);
  await expect(page.locator(".subject-workspace")).not.toHaveClass(/has-episode/);
});

test("contract summaries open one clearly labeled recorded example", { tag: ["@interactions", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto(contractExampleRunPath);
  await waitForPublication(page);

  const runMetricLink = page
    .locator(".workspace-metrics")
    .getByRole("link", { name: "View one example" });
  const runCardLink = page
    .locator(".contract-status-card")
    .getByRole("link", { name: "View one recorded example" });
  await expect(runMetricLink).toHaveAttribute("href", contractExampleHref);
  await expect(runCardLink).toHaveAttribute("href", contractExampleHref);

  if (!testInfo.project.name.startsWith("mobile")) {
    await page.goto(contractExampleSubjectPath);
    await waitForPublication(page);
    await expect(
      page.locator(".subject-facts").getByRole("link", {
        name: "View one example",
      }),
    ).toHaveAttribute("href", contractExampleHref);
    await expect(
      page.locator(".contract-status-card").getByRole("link", {
        name: "View one recorded example",
      }),
    ).toHaveAttribute("href", contractExampleHref);
  }

  await page.goto(contractExampleEpisodePath);
  await waitForPublication(page);
  const episodeLink = page
    .locator(".episode-summary-metrics")
    .getByRole("link", { name: "View one example" });
  await expect(episodeLink).toHaveAttribute("href", contractExampleHref);
  await episodeLink.click();
  await expect(page).toHaveURL(new RegExp("\\?violation=first$"));

  const openedViolation = page.locator(".turn:has(.violation-detail[open])");
  await expect(openedViolation).toHaveCount(1);
  await expect(openedViolation).toContainText("Model broke the output contract.");
  const disclosure = openedViolation.locator(".violation-detail");
  await expect(disclosure).toHaveAttribute("open", "");
  await expect(disclosure.locator("summary")).toBeFocused();
  await expect(disclosure).toBeInViewport();
});

test("result navigation, tables, and charts use the shared results layout", { tag: ["@interactions", "@both"] }, async ({
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
  await page.locator(".metric-chart-canvas").first().scrollIntoViewIfNeeded();
  await expect(page.locator(".metric-chart-canvas svg").first()).toBeVisible();
  await page.locator(".stacked-chart-canvas").scrollIntoViewIfNeeded();
  await expect(page.locator(".stacked-chart-canvas svg")).toBeVisible();
  const guesserCostAxisLabels = await page
    .locator(".metric-chart-canvas svg")
    .first()
    .locator("text")
    .allTextContents();
  const benchmarkCostAxisLabels = await page
    .locator(".stacked-chart-canvas svg text")
    .allTextContents();
  expect(guesserCostAxisLabels.filter((label) => label.startsWith("$"))[0]).toBe(
    "$0.00",
  );
  expect(benchmarkCostAxisLabels.filter((label) => label.startsWith("$"))[0]).toBe(
    "$0.00",
  );
  const stackedLegend = page.locator(".stacked-chart figcaption");
  await expect(stackedLegend).toContainText("Guesser");
  await expect(stackedLegend).toContainText("Primary Oracle");
  await expect(stackedLegend).toContainText("Adjudication");
  await expect(stackedLegend).not.toContainText("Reviewer");
  await expect(stackedLegend).not.toContainText("Judge");
  await expect(stackedLegend).not.toContainText("Validator");
  const adjudicationBreakdown = page.locator(".stacked-chart-breakdown");
  await expect(adjudicationBreakdown.locator("summary")).toHaveText(
    "Exact adjudication breakdown",
  );
  await expect(adjudicationBreakdown.locator("table")).toBeHidden();
  await adjudicationBreakdown.locator("summary").click();
  await expect(adjudicationBreakdown.locator("table")).toBeVisible();
  await expect(
    adjudicationBreakdown.getByRole("columnheader", { name: "Reviewer" }),
  ).toBeVisible();
  await expect(
    adjudicationBreakdown.getByRole("columnheader", { name: "Judge" }),
  ).toBeVisible();
  await expect(
    adjudicationBreakdown.getByRole("columnheader", { name: "Validator" }),
  ).toBeVisible();
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
  await page.locator(".metric-chart-canvas").first().scrollIntoViewIfNeeded();
  await expect(page.locator(".metric-chart-canvas svg").first()).toBeVisible();
  await expect(page.locator(".time-panel + .runtime-ledger")).toHaveCount(1);
  await expect(page.locator(".time-panel .runtime-ledger")).toHaveCount(0);
  await expectVerticalGap(
    page.locator(".time-panel > .metric-chart"),
    page.locator(".runtime-ledger"),
    23,
  );

  await page.goto("results/efficiency/");
  await page.locator(".efficiency-scatter-canvas").scrollIntoViewIfNeeded();
  await expect(page.locator(".efficiency-scatter-canvas svg")).toBeVisible();

  await page.goto("results/reliability/");
  await page.locator(".reliability-scatter-canvas").scrollIntoViewIfNeeded();
  await expect(page.locator(".reliability-scatter-canvas svg")).toBeVisible();
  await expect(page.locator(".reliability-comparison")).toHaveCount(0);
  await expect(page.locator(".ranking-table tbody tr").first()).toContainText(
    "Synthetic Model 06",
  );
  await expect(page.locator(".ranking-table tbody tr").first()).toContainText("1.86");
});

test("result navigation avoids exposed scrollbars and reveals the active view", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto("results/efficiency/");
  await waitForPublication(page);

  const navigation = page.locator(".results-nav");
  await expect(navigation).toHaveCSS("overflow-x", "auto");
  await expect(navigation).toHaveCSS("scrollbar-width", "none");

  const bounds = await navigation.evaluate((element) => {
    const active = element.querySelector("a.active");
    if (active === null) {
      throw new Error("The result navigation has no active link.");
    }
    const navigationBox = element.getBoundingClientRect();
    const activeBox = active.getBoundingClientRect();
    return {
      activeLeft: activeBox.left,
      activeRight: activeBox.right,
      navigationLeft: navigationBox.left,
      navigationRight: navigationBox.right,
    };
  });
  expect(bounds.activeLeft).toBeGreaterThanOrEqual(bounds.navigationLeft - 1);
  expect(bounds.activeRight).toBeLessThanOrEqual(bounds.navigationRight + 1);
});

test("public results use document scrolling and expose shared resources", { tag: ["@interactions", "@desktop"] }, async ({
  page,
}) => {
  await page.goto("results/cost/");
  await waitForPublication(page);

  const initial = await page.evaluate(() => {
    const main = document.querySelector<HTMLElement>(".app-viewport");
    const results = document.querySelector<HTMLElement>(".results-view");
    if (main === null || results === null) {
      throw new Error("The public result scroll surfaces are missing.");
    }
    return {
      documentHeight: document.documentElement.scrollHeight,
      mainOverflowY: getComputedStyle(main).overflowY,
      mainScrollTop: main.scrollTop,
      resultsOverflowY: getComputedStyle(results).overflowY,
      resultsScrollTop: results.scrollTop,
      viewportHeight: window.innerHeight,
    };
  });

  expect(initial.documentHeight).toBeGreaterThan(initial.viewportHeight * 2);
  expect(initial.mainOverflowY).toBe("visible");
  expect(initial.resultsOverflowY).toBe("visible");
  await expect
    .poll(() =>
      page.evaluate(() => {
        window.scrollTo({ top: 700 });
        return window.scrollY;
      }),
    )
    .toBeGreaterThan(600);
  expect(initial.mainScrollTop).toBe(0);
  expect(initial.resultsScrollTop).toBe(0);

  const footer = page.locator(".site-footer");
  await footer.scrollIntoViewIfNeeded();
  await expect(footer).toBeVisible();
  for (const link of siteResourceLinks) {
    await expect(footer.getByRole("link", { name: new RegExp(link.label) })).toHaveAttribute(
      "href",
      link.href,
    );
  }
  const times = footer.locator("time");
  await expect(times).toHaveCount(1);
  await expect(times.first()).toHaveAttribute("datetime", /^\d{4}-\d{2}-\d{2}T/);
  expect(await times.first().textContent()).not.toMatch(/\d{4}-\d{2}-\d{2}T/);
  await expect(footer).toContainText("Publication updated");

  await page.goto(runPath);
  await waitForPublication(page);
  await expect(page.locator(".site-footer")).toHaveCount(0);
});

test("route focus is quiet and interactive focus remains visible", { tag: ["@interactions", "@both"] }, async ({
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

test("episode tabs support arrow, Home, and End keys", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  await page.goto(episodePath);
  await waitForPublication(page);
  const answerLabels = page.locator(".turn-list .answer > span");
  await expect(answerLabels.first()).toHaveText("2 · Adjudication returns");
  await expect(answerLabels.last()).toHaveText("2 · Validator returns");
  const transcript = page.getByRole("tab", { name: /Transcript/ });
  const reliability = page.getByRole("tab", { name: /Reliability/ });
  const usage = page.getByRole("tab", { name: /Usage/ });

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

test("turn-map markers scroll the selected turn into view", { tag: ["@interactions", "@both"] }, async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto(episodePath);
  await waitForPublication(page);

  const transcript = page.locator(".episode-transcript");
  const target = page.locator(".turn-list > article").last();
  const targetIsVisible = async (): Promise<boolean> =>
    target.evaluate((element, isMobile) => {
      const targetBounds = element.getBoundingClientRect();
      if (isMobile) {
        return targetBounds.top >= 0 && targetBounds.top < window.innerHeight;
      }
      const panel = element.closest<HTMLElement>(".episode-panel");
      if (panel === null) return false;
      const panelBounds = panel.getBoundingClientRect();
      return targetBounds.top >= panelBounds.top && targetBounds.top < panelBounds.bottom;
    }, mobile);

  expect(await targetIsVisible()).toBe(false);
  await page.locator(".turn-map button").last().click();
  expect(await targetIsVisible()).toBe(true);
  await expect(target).toBeFocused();

  if (mobile) {
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  } else {
    await expect
      .poll(() => transcript.evaluate((element) => element.scrollTop))
      .toBeGreaterThan(0);
  }
});

test("turn-map markers expand for long answer tokens", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  for (const [path, answer] of [
    [unknownExampleEpisodePath, "UNKNOWN"],
    [contractExampleEpisodePath, "FORMAT"],
  ] as const) {
    await page.goto(path);
    await waitForPublication(page);

    const turnMap = page.locator(".turn-map");
    const shortMarker = turnMap.locator("button").filter({
      has: page.locator("strong", { hasText: /^NO$/ }),
    }).first();
    const longMarker = turnMap.locator("button").filter({
      has: page.locator("strong", { hasText: new RegExp(`^${answer}$`) }),
    }).first();

    await expect(shortMarker).toBeVisible();
    await expect(longMarker).toBeVisible();

    const shortWidth = await shortMarker.evaluate((element) => element.clientWidth);
    const longDimensions = await longMarker.evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));

    expect(longDimensions.clientWidth).toBeGreaterThan(shortWidth);
    expect(longDimensions.scrollWidth).toBeLessThanOrEqual(longDimensions.clientWidth);
  }
});

test("score explanation restores focus on Escape", { tag: ["@interactions", "@desktop"] }, async ({ page }) => {
  await page.goto(runPath);
  await waitForPublication(page);
  const trigger = page.locator(".run-primary-score .info-popover-trigger");
  await trigger.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("mobile navigation and episode tabs meet the touch target minimum", { tag: ["@interactions", "@mobile"] }, async ({
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
  await expectMinimumSize(page.locator(".subject-return"), 44);

  await page.goto(runPath);
  await waitForPublication(page);
  await expectMinimumSize(page.locator(".mobile-subjects a"), 44);

  await page.goto(subjectPath);
  await waitForPublication(page);
  await expectMinimumSize(page.locator(".mobile-run-back"), 44);
  await expectMinimumSize(page.locator(".episode-list > a"), 44);
});

test("mobile header menu provides global navigation and closes after selection", { tag: ["@interactions", "@mobile", "@smoke"] }, async ({
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

test("mobile header menu restores focus after Escape", { tag: ["@interactions", "@mobile"] }, async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("mobile"));
  await page.goto(episodePath);
  await waitForPublication(page);

  const mobileMenu = page.locator(".mobile-navigation");
  const summary = mobileMenu.locator("summary");
  await summary.click();
  const methodLink = mobileMenu.getByRole("link", { name: "Method", exact: true });
  await methodLink.focus();
  await page.keyboard.press("Escape");
  await expect(mobileMenu).not.toHaveAttribute("open", "");
  await expect(summary).toBeFocused();
});
