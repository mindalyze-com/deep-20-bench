import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Locator, type Page } from "@playwright/test";

import {
  classifyConfidenceWidths,
  confidenceIntervalWidth,
  confidenceWidthScale,
} from "../../src/lib/confidence-width";

interface ManifestRun {
  execution_id: string;
}

interface PublicationManifest {
  official_runs: ManifestRun[];
}

interface LeaderboardFixture {
  leaderboard: Array<{
    model: { model_id: string };
    question_score_confidence_interval: {
      lower: string;
      upper: string;
    } | null;
  }>;
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

const docsRoot = path.resolve(process.cwd(), "../../../docs");
const dataRoot = path.join(docsRoot, "data");
const manifest = JSON.parse(
  readFileSync(path.join(dataRoot, "manifest.json"), "utf8"),
) as PublicationManifest;
const leaderboardFixture = JSON.parse(
  readFileSync(path.join(dataRoot, "leaderboard.json"), "utf8"),
) as LeaderboardFixture;
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

test("every page template uses the shared type system", async ({
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

test("confidence width bands divide the displayed scale and keep ties together", () => {
  const observations = leaderboardFixture.leaderboard.flatMap((row) => {
    const interval = row.question_score_confidence_interval;
    if (interval === null) return [];
    const width = confidenceIntervalWidth(
      Number(interval.lower),
      Number(interval.upper),
    );
    return width === null ? [] : [{ key: row.model.model_id, width }];
  });
  const scale = confidenceWidthScale(observations);
  const bands = scale.bands;

  expect(scale.maximum).toBe(12);
  expect(scale.lowerThreshold).toBe(4);
  expect(scale.upperThreshold).toBe(8);
  expect([...bands.entries()].filter(([, band]) => band === "tight").map(([key]) => key))
    .toEqual(expect.arrayContaining(["M-0003", "M-0005", "M-0006", "M-0010", "M-0014"]));
  expect([...bands.entries()].filter(([, band]) => band === "middle").map(([key]) => key))
    .toEqual(expect.arrayContaining(["M-0001", "M-0002", "M-0004", "M-0007", "M-0008", "M-0012"]));
  expect([...bands.entries()].filter(([, band]) => band === "wide").map(([key]) => key))
    .toEqual(["M-0009"]);

  const tied = classifyConfidenceWidths([
    { key: "a", width: 1 },
    { key: "b", width: 2 },
    { key: "c", width: 2 },
    { key: "d", width: 2 },
    { key: "e", width: 3 },
    { key: "f", width: 4 },
    { key: "g", width: 5 },
    { key: "h", width: 6 },
  ]);
  expect(tied.get("b")).toBe("middle");
  expect(tied.get("c")).toBe(tied.get("b"));
  expect(tied.get("d")).toBe(tied.get("b"));

  expect(classifyConfidenceWidths([{ key: "only", width: 2 }]).get("only")).toBeNull();
  expect(
    [...classifyConfidenceWidths([
      { key: "one", width: 2 },
      { key: "two", width: 2 },
    ]).values()],
  ).toEqual([null, null]);
  expect(confidenceIntervalWidth(Number.NaN, 2)).toBeNull();
  expect(confidenceIntervalWidth(3, 2)).toBeNull();
});

test("homepage remains useful without JavaScript", async ({ browser }, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: mobile ? { width: 390, height: 844 } : { width: 1280, height: 720 },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/deep-20-bench/");

  const staticHome = page.locator("main.static-home");
  await expect(staticHome).toBeVisible();
  await expect(staticHome).toHaveCSS("background-color", "rgb(243, 240, 232)");
  await expect(page.locator(".static-header")).toHaveCSS(
    "background-color",
    "rgb(12, 17, 27)",
  );
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Deep20Bench: can an LLM ask its way to the answer?",
  );
  await expect(staticHome).toContainText(
    "Deep20Bench repeats this game across multiple subjects and rounds.",
  );
  await expect(staticHome).toContainText(
    "The average number of questions becomes the Deep20Bench score - lower is better.",
  );
  await expect(staticHome).toContainText(
    "The Guesser asks. Three roles determine the answer.",
  );
  await expect(staticHome).toContainText(
    "An Oracle searches the live web and cites evidence.",
  );
  await expect(page.getByText("Executive summary", { exact: true })).toBeVisible();
  await expect(page.getByText("What it does not claim", { exact: true })).toBeVisible();
  await expect(page.getByText("Deep20Bench needs JavaScript")).toHaveCount(0);
  await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(1);
  const structuredData = await page
    .locator('script[type="application/ld+json"]')
    .textContent();
  expect(structuredData).not.toBeNull();
  const dataset = JSON.parse(structuredData!) as {
    alternateName?: string[];
    keywords?: string[];
  };
  expect(dataset.alternateName).toEqual(["Deep20 Bench", "D20B"]);
  expect(dataset.keywords).toEqual(
    expect.arrayContaining(["Deep20Bench", "Deep20 Bench", "LLM benchmark"]),
  );
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "https://mindalyze-com.github.io/deep-20-bench/",
  );
  const viewport = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(viewport.scroll).toBeLessThanOrEqual(viewport.client + 1);

  await context.close();
});

test("sitemap pages remain useful without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();

  for (const routePath of staticPaths.slice(1)) {
    await page.setContent(
      readFileSync(path.join(docsRoot, routePath, "index.html"), "utf8"),
    );
    const fallback = page.locator("main.static-route-fallback--editorial");
    await expect(fallback).toBeVisible();
    await expect(fallback.getByRole("heading", { level: 1 })).not.toHaveText(
      "This detailed view uses JavaScript.",
    );
  }

  await page.setContent(
    readFileSync(path.join(docsRoot, "results", "index.html"), "utf8"),
  );
  await expect(page.getByText("The current leader has a question score of")).toBeVisible();
  await expect(page.getByRole("list", { name: "Top three official model results" })).toBeVisible();

  await context.close();
});

test("JavaScript users do not see the static page while the app loads", async ({
  page,
}) => {
  let releaseEntry = (): void => undefined;
  const entryGate = new Promise<void>((resolve) => {
    releaseEntry = resolve;
  });
  await page.route("**/src/main.ts", async (route) => {
    await entryGate;
    await route.continue();
  });

  const navigation = page.goto("");
  const staticHome = page.locator("main.static-home");
  await staticHome.waitFor({ state: "attached" });
  await expect(staticHome).toBeHidden();
  await expect(page.locator("html")).toHaveClass(/app-loading/);

  releaseEntry();
  await navigation;
  await waitForPublication(page);
  await expect(staticHome).toHaveCount(0);
  await expect(page.locator("html")).not.toHaveClass(/app-loading/);
});

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
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      `https://mindalyze-com.github.io/deep-20-bench/${routePath}`,
    );
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

test("illustrative round connects the correct guess to its trial score", async ({
  page,
}) => {
  await page.goto("");
  await waitForPublication(page);

  const hero = page.locator(".hero-copy");
  await expect(hero).toContainText(
    "Deep20Bench repeats this game across multiple subjects and rounds.",
  );
  await expect(hero).toContainText(
    "The average number of questions becomes the Deep20Bench score - lower is better.",
  );

  const round = page.locator(".round-example");
  const transcript = round.locator(".round-card");
  const score = round.locator(".round-score-card");
  await expect(round).toHaveAttribute(
    "aria-label",
    "Illustrative round: Garfield identified with a trial score of 3",
  );
  await expect(round.locator(".round-head")).toContainText("Illustrative round");
  await expect(transcript.locator(".round-columns")).toContainText("Question");
  await expect(transcript.locator(".round-columns")).toContainText("Answer");
  await expect(transcript.locator(".round-guess")).toContainText("Guess");
  await expect(transcript.locator(".round-guess")).toContainText("Garfield");
  await expect(transcript.locator(".round-not-counted")).toHaveText("Not counted");
  await expect(transcript.locator(".round-guess > strong")).toHaveText(
    /Garfield - identified/i,
  );
  await expect(round.locator(".round-score-connector")).toBeVisible();
  await expect(score.locator(".round-score-label")).toHaveText(
    "Question score (single round)",
  );
  await expect(score.locator(".round-score-number")).toHaveText("3");
  await expect(score).toContainText("3 questions counted.");
  await expect(score).toContainText("The correct guess is excluded.");
  await expect(score).toContainText("Lower is better");
  await expect(score).toContainText("Fewer questions → better score");
  const scoreBox = await score.boundingBox();
  const scoreLabelBox = await score.locator(".round-score-label").boundingBox();
  const scoreContentBox = await score.locator(".round-score-content").boundingBox();
  const scoreNumberBox = await score.locator(".round-score-number").boundingBox();
  const scoreCopyBox = await score.locator(".round-score-copy").boundingBox();
  expect(scoreBox).not.toBeNull();
  expect(scoreLabelBox).not.toBeNull();
  expect(scoreContentBox).not.toBeNull();
  expect(scoreNumberBox).not.toBeNull();
  expect(scoreCopyBox).not.toBeNull();
  expect(scoreNumberBox!.y - (scoreLabelBox!.y + scoreLabelBox!.height)).toBeGreaterThanOrEqual(
    15,
  );
  expect(scoreNumberBox!.y - scoreCopyBox!.y).toBeGreaterThanOrEqual(3);
  expect(scoreNumberBox!.y - scoreCopyBox!.y).toBeLessThanOrEqual(4);
  const scoreColumnCenter = scoreContentBox!.x + (6.75 * 16) / 2;
  const scoreNumberCenter = scoreNumberBox!.x + scoreNumberBox!.width / 2;
  expect(Math.abs(scoreNumberCenter - scoreColumnCenter)).toBeLessThanOrEqual(1);
  expect(scoreNumberBox!.y).toBeGreaterThanOrEqual(scoreBox!.y);
  expect(scoreNumberBox!.y + scoreNumberBox!.height).toBeLessThanOrEqual(
    scoreBox!.y + scoreBox!.height,
  );
  const connectorGeometry = await round.locator(".round-score-connector").evaluate(
    (element) => {
      const elbow = getComputedStyle(element, "::before");
      const stem = getComputedStyle(element.querySelector("span")!);
      const arrowheadLeft = getComputedStyle(element.querySelector("span")!, "::before");
      const arrowhead = getComputedStyle(element.querySelector("span")!, "::after");
      return {
        elbowBottom: elbow.borderBottomStyle,
        elbowRight: elbow.borderRightStyle,
        stemHeight: Number.parseFloat(stem.height),
        stemWidth: Number.parseFloat(stem.width),
        arrowheadLeftWidth: Number.parseFloat(arrowheadLeft.width),
        arrowheadRightWidth: Number.parseFloat(arrowhead.width),
      };
    },
  );
  expect(connectorGeometry).toEqual({
    elbowBottom: "solid",
    elbowRight: "solid",
    stemHeight: expect.any(Number),
    stemWidth: 1,
    arrowheadLeftWidth: expect.any(Number),
    arrowheadRightWidth: expect.any(Number),
  });
  expect(connectorGeometry.stemHeight).toBeGreaterThan(0);
  expect(connectorGeometry.arrowheadLeftWidth).toBeGreaterThan(0);
  expect(connectorGeometry.arrowheadRightWidth).toBeGreaterThan(0);
  await expectNoViewportOverflow(page);
});

test("illustrative round typography is identical on Overview and Method", async ({ page }) => {
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

test("illustrative round stops at its configured maximum", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.goto("methodology/");
  await waitForPublication(page);

  for (const width of [900, 1024, 1280, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    const layout = await page.locator("#game .method-round").evaluate((frame) => {
      const example = frame.querySelector<HTMLElement>(".round-example");
      const card = frame.querySelector<HTMLElement>(".round-card");
      const row = frame.querySelector<HTMLElement>(".round-card li");
      if (example === null || card === null || row === null) {
        throw new Error("The illustrative round layout is incomplete.");
      }
      const probe = document.createElement("div");
      probe.style.cssText = "position: fixed; visibility: hidden; max-width: var(--round-example-max)";
      document.body.append(probe);
      const maximum = Number.parseFloat(getComputedStyle(probe).maxWidth);
      probe.remove();
      return {
        maximum,
        exampleWidth: example.getBoundingClientRect().width,
        cardWidth: card.getBoundingClientRect().width,
        rowWidth: row.getBoundingClientRect().width,
      };
    });

    expect(layout.exampleWidth).toBeLessThanOrEqual(layout.maximum + 1);
    expect(Math.abs(layout.cardWidth - layout.rowWidth)).toBeLessThanOrEqual(2);
  }
});

test("homepage explains the game and keeps repeated-trial design on Method", async ({
  page,
}) => {
  await page.goto("");
  await waitForPublication(page);

  const explanation = page.locator("#how-it-works");
  await expect(explanation.getByRole("heading", { level: 2 })).toHaveText(
    "The task requires several core competencies.",
  );
  await expect(explanation).toContainText("Why this game works as an LLM benchmark");
  await expect(explanation).toContainText(
    "Use all prior questions and answers to plan the next question.",
  );
  await expect(explanation).toContainText("The Guesser is the LLM under test");
  await expect(explanation).toContainText(
    "the Oracle must search the live web and cite evidence instead of relying on memory",
  );
  await expect(explanation).toContainText(
    "The Guesser is isolated from this process and receives only the final YES, NO, or UNKNOWN.",
  );
  await expect(page.getByText("A score built from repeated trials.", { exact: true })).toHaveCount(
    0,
  );

  const trust = page.locator(".trust-section");
  await expect(trust.getByRole("heading", { level: 2 })).toHaveText(
    "Comparable runs. Inspectable results.",
  );
  await expect(trust).toContainText("The same test");
  await expect(trust).toContainText("Results can be audited");
});

test("Method builds from one round to repetition, scoring, and publication", async ({
  page,
}, testInfo) => {
  await page.goto("methodology/");
  await waitForPublication(page);

  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "From one round to a comparable score.",
  );
  await expect(page.locator(".methodology-page > .content-section")).toHaveCount(7);
  if (!testInfo.project.name.startsWith("mobile")) {
    const alignment = await page.evaluate(() => {
      const methodNav = document.querySelector<HTMLElement>(".method-nav");
      const hero = document.querySelector<HTMLElement>(".page-hero-inner");
      if (methodNav === null || hero === null) {
        throw new Error("The Method layout surfaces are missing.");
      }
      const methodNavBox = methodNav.getBoundingClientRect();
      const heroBox = hero.getBoundingClientRect();
      return {
        methodNavLeft: methodNavBox.left,
        methodNavRight: methodNavBox.right,
        heroLeft: heroBox.left,
        heroRight: heroBox.right,
      };
    });
    expect(alignment.methodNavLeft).toBeCloseTo(alignment.heroLeft, 0);
    expect(alignment.methodNavRight).toBeCloseTo(alignment.heroRight, 0);
  }
  expect(
    await page
      .locator(".methodology-page > .content-section")
      .evaluateAll((sections) => sections.map((section) => section.id)),
  ).toEqual([
    "game",
    "answer-checks",
    "repetition",
    "scoring",
    "reliability",
    "eligibility",
    "publication",
  ]);

  const game = page.locator("#game");
  await expect(game.getByRole("heading", { name: "One hidden subject. One adaptive conversation." })).toBeVisible();
  await expect(game.locator(".round-example")).toHaveAttribute(
    "aria-label",
    "Illustrative round: Garfield identified with a trial score of 3",
  );
  await expect(game).toContainText("Question score (single round)");
  await expect(game).toContainText("Twenty Questions names the game, not the scoring limit.");
  await expect(game).toContainText(
    "Every additional question increases the trial value and remains visible in the final average.",
  );

  const checks = page.locator("#answer-checks");
  await expect(checks).toContainText("Oracle");
  await expect(checks).toContainText("Reviewer");
  await expect(checks).toContainText("Judge");
  await expect(checks).toContainText("Guess Validator");
  await expect(checks).toContainText("The Guesser is fully isolated from adjudication.");
  await expect(checks).toContainText(
    "contains only the broad category, its own prior actions, final YES, NO, or UNKNOWN tokens",
  );

  const repetition = page.locator("#repetition");
  await expect(repetition.getByRole("heading", { name: "One round becomes 35 isolated trials." })).toBeVisible();
  await expect(repetition).toContainText(
    "Every model plays the same 7 subjects in 5 fresh trials per subject.",
  );
  await expect(repetition).toContainText("Subject design and contamination");
  await expect(repetition).toContainText("Seven subjects is too small for broad conclusions.");
  await expect(repetition).toContainText(
    "does not claim that this public cohort is resistant to benchmark contamination",
  );
  await expect(repetition).toContainText("Future cohorts will aim to include more subjects");
  await expect(repetition).toContainText("not a general ranking of model intelligence");

  const scoring = page.locator("#scoring");
  await expect(scoring.getByRole("heading", { name: "Question score is the average counted questions." })).toBeVisible();
  await expect(scoring).toContainText("A model failure counts as 51");
  const standardErrorFormula = scoring.locator(".standard-error-formula");
  await expect(standardErrorFormula.locator("math")).toHaveAttribute("display", "block");
  await expect(standardErrorFormula.locator("math")).toHaveAttribute(
    "aria-label",
    /sample trial variance divided by its trial count/,
  );
  await expect(standardErrorFormula).toContainText("sample trial variance for subject");

  const official = page.locator("#eligibility");
  await expect(official).toContainText(
    "The subjects, game policy, Oracle, Reviewer, Judge, Guess Validator, trial count, and scoring policy stay fixed.",
  );

  const publication = page.locator("#publication");
  await expect(publication).toContainText("Publication happens after play is finished.");
  await expect(publication).toContainText("Published data never returns to the Guesser.");
  await expectNoViewportOverflow(page);
});

test("Story keeps the origin, adds dated news, and removes repeated explanations", async ({
  page,
}) => {
  await page.goto("story/");
  await waitForPublication(page);

  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "A shared idea, built into a benchmark.",
  );
  await expect(page.locator(".story-hero")).toContainText(
    "Patrick Heusser and Markus Tuor came up with Deep20Bench while playing Twenty Questions with the kids.",
  );

  const news = page.locator("#news");
  await expect(news.getByRole("heading", { name: "Project news." })).toBeVisible();
  await expect(news.locator("time")).toHaveAttribute("datetime", "2026-08-05");
  await expect(news.locator("time")).toHaveText("5 August 2026");
  await expect(news).toContainText("Claude Fable 5 (high) added.");
  await expect(news.getByRole("link", { name: "View run" })).toHaveAttribute(
    "href",
    "/deep-20-bench/runs/BX-20260805-official-M0014-011/",
  );

  await expect(page.locator(".round-section, .scope-section, .apple-spotlight")).toHaveCount(0);
  await expect(page.getByText("The Entity-Deduction Arena", { exact: true })).toHaveCount(1);
  await expectNoViewportOverflow(page);
});

test("primary navigation pages share one wide-screen content boundary", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.setViewportSize({ width: 1920, height: 900 });

  const routes = [
    { path: "", selectors: [".home-hero-inner", ".origin-strip-inner"] },
    { path: "results/", selectors: [".results-workspace-header-inner"] },
    { path: "methodology/", selectors: [".page-hero-inner", ".method-nav"] },
    { path: "story/", selectors: [".story-hero-inner", ".story-closing-inner"] },
    { path: "data/", selectors: [".page-hero-inner", ".data-build-note-inner"] },
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

test("Method editorial content uses the shared wide-screen boundary", async ({
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

test("question scores show repeated-trial confidence intervals", async ({ page }) => {
  await page.goto("");
  await waitForPublication(page);
  await expect(page.locator(".score-dot-plot-canvas svg")).toHaveCount(2);
  await expect(page.locator(".score-dot-plot figcaption")).toContainText(
    "Question score",
  );
  await expect(page.locator(".score-dot-plot figcaption")).toContainText(
    "lower is better",
  );
  await expect(page.locator(".score-dot-plot figcaption")).toContainText(
    "95% CI · color = CI width",
  );
  await expect(page.locator(".score-dot-plot figcaption")).toContainText("Tighter");
  await expect(page.locator(".score-dot-plot figcaption")).toContainText("Wider");
  await expect(page.locator(".confidence-width-caption")).toContainText("CI width");
  await expect(page.locator(".confidence-width-caption")).toContainText("stability");
  await expect(page.locator(".confidence-width-caption")).toContainText(
    "lower is better",
  );
  await expect(page.locator(".winner-card .score-confidence")).toContainText("95% CI");

  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".score-dot-plot-canvas svg")).toHaveCount(2);
  await expect
    .poll(() => page.locator('.score-dot-plot-canvas path[fill="#4f5dff"]').count())
    .toBeGreaterThan(0);
  await expect(
    page.locator(
      '.score-dot-plot-confidence-band i[data-confidence-band="tight"]',
    ),
  ).toHaveCSS(
    "background-color",
    "rgb(39, 146, 60)",
  );
  await expect(
    page.locator(
      '.score-dot-plot-confidence-band i[data-confidence-band="wide"]',
    ),
  ).toHaveCSS(
    "background-color",
    "rgb(223, 61, 50)",
  );
  await expect(
    page.locator('[data-model-id="M-0006"]'),
  ).toContainText("CI width: 1.86 questions; tighter band");
  await expect(page.locator('[data-model-id="M-0014"]')).toContainText(
    "Best score",
  );
  await expect(page.locator('[data-model-id="M-0006"]')).toContainText(
    "Smallest CI width",
  );
  await expect(page.locator('[data-model-id="M-0007"]')).toHaveAttribute(
    "data-confidence-band",
    "middle",
  );
  await expect(
    page.getByText("The 95% CI uses repeated seeded trials on the seven fixed subjects"),
  ).toBeVisible();
});

test("question score and CI width plots align on desktop and stack on mobile", async ({
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

  if (testInfo.project.name.startsWith("mobile")) {
    expect(widthBox!.y).toBeGreaterThan(scoreBox!.y + scoreBox!.height);
    expect(scoreSvgText).toContain("Claude Fable 5high");
    expect(scoreSvgText).toContain("GPT-5 Nanomedium");
    expect(scoreSvgText).toContain("Llama 4 Mavericknon-thinking");
    expect(scoreSvgText).not.toContain("Claude Fable 5 (high)");
    expect(widthSvgText).toContain("Claude Fable 5high");
    expect(widthSvgText).not.toContain("Claude Fable 5 (high)");
  } else {
    expect(widthBox!.x).toBeGreaterThan(scoreBox!.x + scoreBox!.width);
    expect(Math.abs(widthBox!.y - scoreBox!.y)).toBeLessThanOrEqual(1);
    expect(scoreSvgText).toContain("Claude Fable 5 (high)");
  }
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
      page.getByText("The companion plot shows each exact CI width", {
        exact: false,
      }).first(),
    ).toBeVisible();

    if (mobile) {
      const primaryMetric = page.locator(
        '.mobile-result-metrics [data-tone="primary"]',
      ).first();
      await expect(primaryMetric).toBeVisible();
      await expect(primaryMetric.locator("dt")).toHaveText("Question score");
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
  await page.getByRole("button", { name: "CI width" }).click();
  await expect(
    page.getByRole("dialog", { name: "CI width" }),
  ).toContainText("upper 95% CI bound minus the lower bound");
});

test("result pages use shared metric names", async ({ page }) => {
  await page.goto("results/");
  await waitForPublication(page);
  const overview = page.locator("#route-content");
  await expect(overview).toContainText("Total model cost");
  await expect(overview).toContainText("Total model time");
  await expect(overview).toContainText("95% CI");
  await expect(overview).toContainText("CI width");
  await expect(overview).not.toContainText("Repeatability range");
  await expect(overview).not.toContainText("Recorded spend");
  await expect(overview).not.toContainText("Combined model time");

  await page.goto("results/reliability/");
  await waitForPublication(page);
  const stability = page.locator("#route-content");
  await expect(stability.getByRole("heading", { name: "Stability" }).last()).toBeVisible();
  await expect(stability).toContainText("Repeated-trial stability");
  await expect(stability).not.toContainText("Repeated-run stability");
  const stabilityChart = stability.locator(".reliability-scatter-canvas");
  await expect(stabilityChart).toHaveAttribute(
    "aria-label",
    /Question score and repeated-trial stability on the fixed subjects\./,
  );
  await expect(stabilityChart).not.toHaveAttribute("aria-label", /repeated-run stability/i);
  await expect(stability).toContainText("CI width");
  await expect(stability).not.toContainText("Repeatability");

  await page.goto("results/cost/");
  await waitForPublication(page);
  const cost = page.locator("#route-content");
  await expect(cost).toContainText("Total benchmark cost");
  await expect(cost).toContainText("Total model cost");
  await expect(cost).not.toContainText("Recorded spend");
  await expect(cost).not.toContainText("Full cost");

  await page.goto("results/time/");
  await waitForPublication(page);
  const time = page.locator("#route-content");
  await expect(time).toContainText("Total model time");
  await expect(time).toContainText("Total end-to-end time");
  await expect(time).not.toContainText("Combined model time");
  await expect(time).not.toContainText("Model response time");

  await page.goto("results/efficiency/");
  await waitForPublication(page);
  const efficiency = page.locator("#route-content");
  await expect(efficiency).toContainText("Question score");
  await expect(efficiency).toContainText("Model cost");
  await expect(efficiency).not.toContainText("tested-model cost");
});

test("result hints stay inside their chart headings", async ({
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
  await expect(definition).toContainText("Normalized ideal distance.");
  await expect(page.locator(".definition-section")).toHaveCount(0);
  await definition.locator("summary").click();
  await expect(definition.locator("details")).toHaveAttribute("open", "");
  await expect(definition.locator(".metric-definition-toggle-open")).toBeVisible();
  await expect(definition).toContainText("normalized question score 0.06");
  await expectNoViewportOverflow(page);
});

test("efficiency can be viewed by normalized distance from the ideal", async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");
  if (!mobile) await page.setViewportSize({ width: 1106, height: 1089 });
  await page.goto("results/efficiency/");
  await waitForPublication(page);

  const efficiency = page.locator("#route-content");
  await expect(efficiency).toContainText("Distance from the lower-left ideal.");
  await expect(efficiency).not.toContainText("Legacy product");
  await expect(efficiency).toContainText("Pareto");
  await expect(efficiency).toContainText("Diamond");
  await expect(efficiency).toContainText("Circle");
  await expect(page.locator(".tradeoff-copy > .result-help")).toHaveCount(1);

  if (!mobile) {
    const tableHeaders = page.locator(".efficiency-results-table thead th");
    const headerBoxes = await Promise.all(
      [3, 4, 5, 6, 7, 8].map((index) => tableHeaders.nth(index).boundingBox()),
    );
    expect(headerBoxes.every((box) => box !== null)).toBe(true);
    const metricWidths = headerBoxes.map((box) => box!.width);
    expect(Math.max(...metricWidths) / Math.min(...metricWidths)).toBeLessThan(1.6);
    const paretoHeader = tableHeaders.nth(4);
    await expect(paretoHeader).toContainText("Pareto");
    await expect(paretoHeader).toContainText("efficient");
  }

  const inlineChart = page.locator(".tradeoff-visual .efficiency-scatter-canvas");
  await expect(inlineChart.locator("svg")).toBeVisible();
  const inlineChartBox = await inlineChart.boundingBox();
  expect(inlineChartBox).not.toBeNull();
  expect(inlineChartBox!.height).toBeGreaterThanOrEqual(480);
  if (!mobile) {
    expect(inlineChartBox!.width).toBeGreaterThanOrEqual(580);
    expect(inlineChartBox!.height).toBeLessThanOrEqual(inlineChartBox!.width);
  }

  if (mobile) {
    const tradeoffCopyBox = await page.locator(".tradeoff-copy").boundingBox();
    const tradeoffVisualBox = await page.locator(".tradeoff-visual").boundingBox();
    const tradeoffPanelBox = await page.locator(".tradeoff-panel").boundingBox();
    const mobileRankingBox = await page.locator(".mobile-result-list").boundingBox();
    expect(tradeoffCopyBox).not.toBeNull();
    expect(tradeoffVisualBox).not.toBeNull();
    expect(tradeoffPanelBox).not.toBeNull();
    expect(mobileRankingBox).not.toBeNull();
    expect(
      Math.abs(
        tradeoffVisualBox!.y - (tradeoffCopyBox!.y + tradeoffCopyBox!.height),
      ),
    ).toBeLessThanOrEqual(1);
    expect(mobileRankingBox!.y - (tradeoffPanelBox!.y + tradeoffPanelBox!.height)).toBeGreaterThanOrEqual(30);
  }

  const expandButton = page.getByRole("button", { name: "Expand graph" });
  await expectMinimumSize(expandButton, 44);
  await expandButton.click();
  const expandedDialog = page.locator(".expanded-chart-dialog");
  await expect(expandedDialog).toBeVisible();
  await expect(expandedDialog).toHaveAttribute("open", "");
  const expandedChart = expandedDialog.locator(
    ".expanded-chart-visual .efficiency-scatter-canvas",
  );
  await expect(expandedChart.locator("svg")).toBeVisible();
  const expandedChartBox = await expandedChart.boundingBox();
  expect(expandedChartBox).not.toBeNull();
  if (!mobile) expect(expandedChartBox!.width).toBeGreaterThan(inlineChartBox!.width);
  if (mobile) {
    const dialogBox = await expandedDialog.boundingBox();
    const compactHeaderBox = await expandedDialog
      .locator(".expanded-chart-copy")
      .boundingBox();
    expect(dialogBox).not.toBeNull();
    expect(compactHeaderBox).not.toBeNull();
    expect(dialogBox!.width).toBeGreaterThanOrEqual(380);
    expect(compactHeaderBox!.height).toBeLessThan(150);
    await expect(expandedDialog.locator(".mobile-model-key")).toBeHidden();
  }
  await page.getByRole("button", { name: "Close expanded graph" }).click();
  await expect(expandedDialog).not.toBeVisible();
  await expandButton.click();
  await expect(expandedDialog).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(expandedDialog).not.toBeVisible();
  await expect(expandButton).toBeFocused();

  const rows = page.locator(".ranking-table tbody tr");
  await expect(rows.nth(0)).toContainText("gpt-oss-120B");
  await expect(rows.nth(1)).toContainText("Claude Opus 5");
  await expect(rows.nth(2)).toContainText("Grok 4.5");
  await expect(rows.nth(10)).toContainText("Llama 4 Maverick");
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

test("result charts remain contained across the mobile breakpoint", async ({
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
  const answerLabels = page.locator(".turn-list .answer > span");
  await expect(answerLabels.first()).toHaveText("2 · Adjudication returns");
  await expect(answerLabels.last()).toHaveText("2 · Validator returns");
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

test("turn-map markers scroll the selected turn into view", async ({
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

test("question score CI width treatment matches the visual baseline", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({
    width: testInfo.project.name.startsWith("mobile") ? 390 : 1280,
    height: testInfo.project.name.startsWith("mobile") ? 2200 : 1600,
  });
  await page.goto("results/");
  await waitForPublication(page);
  await expect(page.locator(".comparison-panel .score-dot-plot")).toHaveScreenshot(
    "results-question-score-ci-widths.png",
  );
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
