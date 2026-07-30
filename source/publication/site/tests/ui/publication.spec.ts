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

test("public routes stay within the viewport", async ({ page }) => {
  for (const routePath of staticPaths) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator("h1").first()).toBeVisible();
    await expectNoViewportOverflow(page);
  }
});

test("workspace routes stay within the viewport", async ({ page }) => {
  for (const routePath of [runPath, subjectPath, episodePath]) {
    await page.goto(routePath);
    await waitForPublication(page);
    await expect(page.locator(".loading-state")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  }
});

test("result navigation, tables, and charts use the shared workspace", async ({
  page,
}, testInfo) => {
  for (const routePath of [
    "results/",
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
  await expect(page.locator(".table-wrap").first()).toHaveCSS(
    "overflow-x",
    testInfo.project.name.startsWith("mobile") ? "auto" : /auto|visible/,
  );

  await page.goto("results/time/");
  await expect(page.locator(".metric-chart-canvas svg").first()).toBeVisible();

  await page.goto("results/efficiency/");
  await expect(page.locator(".efficiency-scatter-canvas svg")).toBeVisible();
});

test("route focus is quiet and interactive focus remains visible", async ({
  page,
}) => {
  await page.goto("");
  await waitForPublication(page);
  await page.getByRole("link", { name: "Results", exact: true }).click();
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
  await expectMinimumSize(page.locator(".site-header nav a"), 44);
  await expectMinimumSize(page.locator(".episode-tabs button"), 44);
});

test("focused publication surfaces match visual baselines", async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");

  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".results-workspace-header")).toHaveScreenshot(
    "results-workspace-header.png",
  );
  await expect(page.locator(".results-view .metric-grid").first()).toHaveScreenshot(
    "results-summary-metrics.png",
  );

  await page.goto(runPath);
  await waitForPublication(page);
  await expect(page.locator(".run-workspace-hero")).toHaveScreenshot(
    "run-workspace-hero.png",
  );
  await expect(page.locator(".workspace-metrics")).toHaveScreenshot(
    "run-summary-metrics.png",
  );

  await page.goto(subjectPath);
  await waitForPublication(page);
  if (mobile) {
    await expect(page.locator(".episode-rail")).toHaveScreenshot(
      "subject-episode-list.png",
    );
  } else {
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
