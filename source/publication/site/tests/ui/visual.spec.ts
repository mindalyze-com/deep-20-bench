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

test("question score CI width treatment matches the visual baseline", { tag: ["@visual", "@both", "@visual"] }, async ({
  page,
}, testInfo) => {
  await page.setViewportSize({
    width: testInfo.project.name.startsWith("mobile") ? 390 : 1280,
    height: testInfo.project.name.startsWith("mobile") ? 2200 : 1600,
  });
  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".comparison-panel .score-dot-plot")).toHaveScreenshot(
    "results-question-score-ci-widths.webp",
  );
});

test("focused publication surfaces match visual baselines", { tag: ["@visual", "@both", "@visual"] }, async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");

  await page.goto("results/");
  await waitForPublication(page);
  if (mobile) {
    await expect(page.locator(".site-header")).toHaveScreenshot("site-header.webp");
  }
  await expect(page.locator(".results-workspace-header")).toHaveScreenshot(
    "results-workspace-header.webp",
  );
  await expect(page.locator(".results-view .metric-grid").first()).toHaveScreenshot(
    "results-summary-metrics.webp",
  );

  await page.goto("results/reliability/");
  await waitForPublication(page);
  await expect(
    page.locator(".reliability-scatter-panel > .panel-heading"),
  ).toHaveScreenshot("results-reliability-heading-help.webp");
  await page.addStyleTag({ content: ".skip-link { display: none !important; }" });
  await expect(page.locator(".reliability-scatter-panel .reliability-scatter")).toHaveScreenshot(
    "results-reliability-scatter.webp",
  );

  await page.goto("results/efficiency/");
  await waitForPublication(page);
  await expect(page.locator(".metric-definition-card")).toHaveScreenshot(
    "results-metric-definition.webp",
  );

  await page.goto(runPath);
  await waitForPublication(page);
  await expect(page.locator(".run-workspace-hero")).toHaveScreenshot(
    "run-workspace-hero.webp",
  );
  await expect(page.locator(".workspace-metrics")).toHaveScreenshot(
    "run-summary-metrics.webp",
  );
  await expect(
    page.locator(mobile ? ".mobile-subjects" : ".model-rail"),
  ).toHaveScreenshot("run-subject-list.webp");

  await page.goto(subjectPath);
  await waitForPublication(page);
  await expect(page.locator(".episode-rail")).toHaveScreenshot(
    "subject-episode-list.webp",
  );
  if (!mobile) {
    await expect(page.locator(".subject-overview-inner")).toHaveScreenshot(
      "subject-overview.webp",
    );
  }

  await page.goto(episodePath);
  await waitForPublication(page);
  await expect(page.locator(".episode-hero")).toHaveScreenshot("episode-header.webp");
  await expect(page.locator(".episode-tabs")).toHaveScreenshot("episode-tabs.webp");
  if (!mobile) {
    await expect(page.locator(".turn-map")).toHaveScreenshot("episode-turn-map.webp");
  }
});
