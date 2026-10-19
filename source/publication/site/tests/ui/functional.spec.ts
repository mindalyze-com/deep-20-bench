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

test(
  "functional pages replace embedded publication state with fixture data",
  { tag: ["@functional", "@desktop"] },
  async ({ page }) => {
    await page.goto("results/");
    await waitForPublication(page);

    await expect(page.locator("#deep20-page-state")).toHaveCount(0);
    await expect(page.locator(".results-table-wrap tbody tr").first()).toContainText(
      "Synthetic Model 12",
    );
    await expect(page.locator(".results-table-wrap tbody tr").first()).toBeInViewport();
    await expect(page.getByText("Claude Fable 5", { exact: false })).toHaveCount(0);
  },
);

test("unknown runs and models show the not-found page", { tag: ["@functional", "@desktop", "@smoke"] }, async ({ page }) => {
  for (const path of ["runs/not-a-run/", "editions/1.0/models/not-a-model/"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Page not found.");
    await expect(page.getByRole("link", { name: "All models" })).toBeVisible();
    await expect(page.getByRole("alert")).toHaveCount(0);
    await expectNoViewportOverflow(page);
  }
});

test("source link includes the GitHub mark", { tag: ["@functional", "@desktop"] }, async ({ page }) => {
  await page.goto("");
  await waitForPublication(page);
  const sourceLink = page.getByRole("link", {
    name: "Source code (opens in a new tab)",
  });
  await expect(sourceLink.locator(".repository-icon")).toBeVisible();
});

test("illustrative round connects the correct guess to its round score", { tag: ["@functional", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto("");
  await waitForPublication(page);

  const hero = page.locator(".hero-copy");
  await expect(hero).toContainText(
    "Deep20Bench is a public AI benchmark for large language models (LLMs)",
  );
  const details = page.locator(".hero-details");
  await expect(details).toContainText(
    "Each question, wrong guess, or reply in the wrong format adds one to the score.",
  );
  await expect(details).toContainText(
    "50 questions, more than the traditional twenty, so more rounds can finish.",
  );
  await expect(details).toContainText(
    "Each edition has its own comparison settings and results.",
  );
  await expect(details).not.toContainText("small first step");
  const pilotNote = details.locator(".hero-pilot-note");
  await expect(pilotNote).not.toContainText("not a definitive ranking");
  await expect(pilotNote.locator(".hero-detail-label span")).toHaveCount(0);
  await expect(pilotNote.locator(":scope > p strong")).toHaveCount(0);
  await expect(pilotNote).toHaveCSS("box-shadow", "none");
  const discussionLink = details.getByRole("link", {
    name: "Join discussion (opens in a new tab)",
  });
  await expect(discussionLink).toHaveAttribute(
    "href",
    "https://github.com/mindalyze-com/deep-20-bench/discussions",
  );
  await expect(discussionLink).toHaveAttribute("target", "_blank");
  await expect(discussionLink).toHaveText(/Join discussion/);
  const supportLink = details.getByRole("link", {
    name: "Support future benchmark runs (opens in a new tab)",
  });
  await expect(supportLink).toHaveAttribute("href", "https://ko-fi.com/mindalyze");
  await expect(supportLink).toHaveAttribute("target", "_blank");

  const round = page.locator(".round-example");
  const transcript = round.locator(".round-card");
  const score = round.locator(".round-score-card");
  await expect(round).toHaveAttribute(
    "aria-label",
    "Illustrative round: Garfield identified with a round score of 3",
  );
  await expect(round.locator(".round-head")).toContainText("Illustrative round");
  await expect(transcript.locator(".round-columns")).toContainText("Question");
  await expect(transcript.locator(".round-columns")).toContainText("Answer");
  await expect(transcript.locator(".round-guess")).toContainText("Guess");
  await expect(transcript.locator(".round-guess")).toContainText("Garfield");
  await expect(transcript.locator(".round-not-counted")).toHaveText("Not counted");
  await expect(transcript.locator(".round-guess > strong")).toHaveText(
    "Identified",
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
  if (testInfo.project.name.startsWith("desktop")) {
    const heroBox = await page.locator(".home-hero-inner").boundingBox();
    const roundBox = await round.boundingBox();
    const transcriptBox = await transcript.boundingBox();
    const detailsBox = await details.boundingBox();
    expect(heroBox).not.toBeNull();
    expect(roundBox).not.toBeNull();
    expect(transcriptBox).not.toBeNull();
    expect(detailsBox).not.toBeNull();
    expect(Math.abs(roundBox!.y - heroBox!.y)).toBeLessThanOrEqual(1);
    expect(transcriptBox!.height).toBeLessThanOrEqual(330);
    expect(detailsBox!.y - (roundBox!.y + roundBox!.height)).toBeLessThanOrEqual(40);
    expect(detailsBox!.y - heroBox!.y).toBeLessThanOrEqual(560);
  }
  await expectNoViewportOverflow(page);
});

test("illustrative round stops at its configured maximum", { tag: ["@functional", "@desktop"] }, async ({
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
      const cardStyle = getComputedStyle(card);
      return {
        maximum,
        exampleWidth: example.getBoundingClientRect().width,
        cardContentWidth: card.clientWidth
          - Number.parseFloat(cardStyle.paddingLeft)
          - Number.parseFloat(cardStyle.paddingRight),
        rowWidth: row.getBoundingClientRect().width,
      };
    });

    expect(layout.exampleWidth).toBeLessThanOrEqual(layout.maximum + 1);
    expect(Math.abs(layout.cardContentWidth - layout.rowWidth)).toBeLessThanOrEqual(2);
  }
});

test("homepage explains the game and keeps repeated-trial design on Method", { tag: ["@functional", "@desktop"] }, async ({
  page,
}) => {
  await page.goto("");
  await waitForPublication(page);

  const explanation = page.locator("#how-it-works");
  await expect(explanation.getByRole("heading", { level: 2 })).toHaveText(
    "The game combines several abilities.",
  );
  await expect(explanation).toContainText("What the game tests");
  await expect(explanation).toContainText(
    "Use all earlier questions and answers to plan the next question.",
  );
  await expect(explanation).toContainText("The Guesser is the model being tested");
  await expect(explanation).toContainText(
    "the Oracle searches the web and cites evidence instead of relying on memory",
  );
  await expect(explanation).toContainText(
    "The Guesser receives only the final YES, NO, or UNKNOWN.",
  );
  await expect(page.getByText("A score built from repeated trials.", { exact: true })).toHaveCount(
    0,
  );

  const trust = page.locator(".trust-section");
  await expect(trust.getByRole("heading", { level: 2 })).toHaveText(
    "Same test setup, limited conclusions.",
  );
  await expect(trust).toContainText("Consistent setup");
  await expect(trust).toContainText("Public records");
});

test("Why page explains the benchmark and links to the method", { tag: ["@functional", "@both"] }, async ({ page }) => {
  await page.goto("why/");
  await waitForPublication(page);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Easy to play, hard to play well.");
  await expect(page.locator('.primary-navigation a[aria-current="page"]')).toContainText("Why");
  await expect(page.locator("#reasons .numbered-points li")).toHaveCount(5);
  await expect(page.locator("#limits")).toContainText("not a measure of general intelligence");
  await expect(page.getByRole("link", { name: "How it works →" })).toHaveAttribute("href", /methodology\/$/);
  await expectNoViewportOverflow(page);
});

test("Method explains the game before offering technical details", { tag: ["@functional", "@both"] }, async ({ page }) => {
  await page.goto("methodology/");
  await waitForPublication(page);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("How Deep20Bench works");
  expect(await page.locator(".methodology-page > .content-section")
    .evaluateAll((sections) => sections.map((section) => section.id))).toEqual([
    "game", "answer-checks", "scoring", "repetition", "publication", "edition-history",
  ]);
  await expect(page.locator(".method-nav a")).toHaveCount(5);
  await expect(page.locator(".method-nav-shell + #game")).toBeVisible();
  await expect(page.locator("#publication + #edition-history")).toHaveCount(1);
  await expect(page.locator(".method-details[open], .edition-comparison-details[open]")).toHaveCount(0);
  await expect(page.locator("#game .answer-meanings dt")).toHaveText(["Yes", "No", "Unknown"]);
  await expect(page.locator(".round-example")).toHaveAttribute(
    "aria-label", "Illustrative round: Garfield identified with a round score of 3",
  );
  await expect(page.locator("#game")).toContainText("up to 50 counted questions, then one final guess");
  await expect(page.locator(".answer-roles li")).toHaveCount(3);
  await expect(page.locator(".isolation-callout")).toContainText("stay private");
  await expect(page.locator("#answer-checks > .editorial-copy")).toContainText("The transcript marks every reused answer");
  await expect(page.locator(".score-rules")).toContainText("The round scores 51");
  await expect(page.locator("#repetition .lead")).toContainText("7 subjects 5 times each: 35 rounds in total");
  await expect(page.locator(".scope-note")).toContainText("do not rank general intelligence");
  await expect(page.locator(".scope-note")).toContainText("training data");
  await expect(page.locator("#publication")).toContainText("not independently verified");
  await expect(page.locator("#publication").getByRole("link", { name: "Explore the results →" }))
    .toHaveAttribute("href", /results\/$/);
  await expect(page.getByRole("link", { name: "read the story on Medium" })).toHaveAttribute(
    "href", "https://medium.com/@patrick.heusser/i-built-an-llm-benchmark-around-twenty-questions-the-hard-part-wasnt-the-game-e743c0683da8",
  );

  const formulas = page.locator(".method-details").filter({ has: page.locator("#score-details") });
  await expect(formulas.locator("math").first()).toBeHidden();
  await formulas.locator("summary").focus();
  await formulas.locator("summary").press("Enter");
  await expect(formulas.locator("math")).toHaveCount(3);
  await expect(formulas.locator(".standard-error-formula math")).toBeVisible();
  await expect(formulas.locator(".standard-error-formula math")).toHaveAttribute(
    "aria-label", /sample variance of round scores divided by its round count/,
  );
  await expect(formulas).toContainText("is not a significance test");
  await expectNoViewportOverflow(page);
});

test("About keeps the origin, adds dated news, and removes repeated explanations", { tag: ["@functional", "@desktop"] }, async ({
  page,
}) => {
  await page.goto("about/");
  await waitForPublication(page);

  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "A shared idea, built into a benchmark.",
  );
  await expect(page.locator(".story-hero")).toContainText(
    "Patrick Heusser and Markus Tuor came up with Deep20Bench while playing Twenty Questions with the kids.",
  );

  const news = page.locator("#news");
  await expect(news.getByRole("heading", { name: "What’s new." })).toBeVisible();
  const entries = news.locator(".news-entry");
  await expect(entries).toHaveCount(16);
  await expect(news.locator(".news-entry:visible")).toHaveCount(4);
  await news.getByRole("button", { name: "Show 4 older updates" }).click();
  await news.getByRole("button", { name: "Show 4 older updates" }).click();
  await news.getByRole("button", { name: "Show 4 older updates" }).click();
  await expect(entries.nth(8).locator("time")).toHaveAttribute("datetime", "2026-09-05");
  await expect(entries.nth(8).locator("time")).toHaveText("5 September 2026");
  await expect(entries.nth(8)).toContainText("GPT-6 Astra (high) joins the leaderboard.");
  await expect(entries.nth(8)).toContainText("15.09 questions per round in edition 1.0, with 2 failed rounds out of 35.");
  // News links model pages. The fixture only has model pages for its three synthetic runs,
  // so other models fall back to the edition results.
  await expect(entries.nth(8).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/results/",
  );
  await expect(entries.nth(9).locator("time")).toHaveAttribute("datetime", "2026-09-04");
  await expect(entries.nth(9).locator("time")).toHaveText("4 September 2026");
  await expect(entries.nth(9)).toContainText("Gemini 3.8 Flash (high) joins the leaderboard.");
  await expect(entries.nth(9)).toContainText("13.14 questions per round in edition 1.0, with no failed rounds.");
  await expect(entries.nth(9).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/results/",
  );
  await expect(entries.nth(10).locator("time")).toHaveAttribute("datetime", "2026-09-02");
  await expect(entries.nth(10).locator("time")).toHaveText("2 September 2026");
  await expect(entries.nth(10)).toContainText("Claude Fable 5.1 (high) joins the leaderboard.");
  await expect(entries.nth(10)).toContainText("12.11 questions per round in edition 1.0, with 1 failed round out of 35.");
  await expect(entries.nth(10).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/results/",
  );
  await expect(entries.nth(11).locator("time")).toHaveAttribute("datetime", "2026-08-30");
  await expect(entries.nth(11).locator("time")).toHaveText("30 August 2026");
  await expect(entries.nth(11)).toContainText("Behind Deep20Bench: the hard part wasn’t the game.");
  await expect(entries.nth(11)).toContainText(
    "Patrick writes about what it took to build Deep20Bench: wrong answers from the answering model, the blind second check, format errors, and the design choices along the way.",
  );
  await expect(entries.nth(11).getByRole("link", { name: /Read article/ })).toHaveAttribute(
    "href",
    "https://medium.com/@patrick.heusser/i-built-an-llm-benchmark-around-twenty-questions-the-hard-part-wasnt-the-game-e743c0683da8",
  );
  await expect(entries.nth(12).locator("time")).toHaveAttribute("datetime", "2026-08-23");
  await expect(entries.nth(12).locator("time")).toHaveText("23 August 2026");
  await expect(entries.nth(12)).toContainText("We tried Ox Alpha (high) from OpenRouter.");
  await expect(entries.nth(12)).toContainText(
    "An anonymous stealth model on OpenRouter. It averaged 17.60 questions per round in edition 1.0, 12th of 15 models at the time.",
  );
  await expect(entries.nth(12).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/results/",
  );
  await expect(entries.nth(13).locator("time")).toHaveAttribute("datetime", "2026-08-17");
  await expect(entries.nth(13).locator("time")).toHaveText("17 August 2026");
  await expect(entries.nth(13)).toContainText("Gemini 3.7 Flash (high) joins the leaderboard.");
  await expect(entries.nth(13)).toContainText("14.03 questions per round in edition 1.0, with 1 failed round out of 35.");
  await expect(entries.nth(13).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/results/",
  );
  await expect(entries.nth(14).locator("time")).toHaveAttribute("datetime", "2026-08-15");
  await expect(entries.nth(14).locator("time")).toHaveText("15 August 2026");
  await expect(entries.nth(14)).toContainText("Grok 4.6 (high) joins the leaderboard.");
  await expect(entries.nth(14)).toContainText("14.29 questions per round in edition 1.0, with no failed rounds.");
  await expect(entries.nth(14).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/results/",
  );
  await expect(entries.nth(15).locator("time")).toHaveAttribute("datetime", "2026-08-05");
  await expect(entries.nth(15).locator("time")).toHaveText("5 August 2026");
  await expect(entries.nth(15)).toContainText("Claude Fable 5 (high) joins the leaderboard.");
  await expect(entries.nth(15).getByRole("link", { name: "View model results" })).toHaveAttribute(
    "href",
    "/deep-20-bench/editions/1.0/models/synthetic-model-12-high/",
  );

  await expect(page.locator(".round-section, .scope-section, .apple-spotlight")).toHaveCount(0);
  await expect(page.getByText("The Entity-Deduction Arena", { exact: true })).toHaveCount(1);
  await expectNoViewportOverflow(page);
});

test("news reveals older updates in batches and returns to the latest", { tag: ["@functional", "@both", "@smoke"] }, async ({ page }) => {
  await page.goto("about/");
  await waitForPublication(page);

  const news = page.locator("#news");
  const entries = news.locator(".news-entry");
  const visibleEntries = news.locator(".news-entry:visible");
  const status = news.getByRole("status");
  const latestOnly = news.getByRole("button", { name: "Show latest only" });
  await expect(entries).toHaveCount(16);
  await expect(visibleEntries).toHaveCount(4);
  await expect(status).toHaveText("Showing 4 of 16 updates");
  await expect(latestOnly).toHaveCount(0);
  await expect(entries.first()).toContainText("Gemini 4 Argon (high) matches the lowest average score.");
  await expect(entries.nth(1)).toContainText("Muse Wonder (high) joins the leaderboard.");

  for (const [previousCount, batchSize, expectedCount] of [[4, 4, 8], [8, 4, 12], [12, 4, 16]]) {
    const showOlder = news.getByRole("button", { name: `Show ${batchSize} older updates` });
    await expectMinimumSize(showOlder, 44);
    await showOlder.scrollIntoViewIfNeeded();
    await showOlder.focus();
    const previousScroll = await page.evaluate(() => window.scrollY);
    await showOlder.press("Enter");
    await expect(visibleEntries).toHaveCount(expectedCount);
    await expect(status).toHaveText(`Showing ${expectedCount} of 16 updates`);
    await expect(entries.nth(previousCount)).toBeFocused();
    expect(Math.abs(await page.evaluate(() => window.scrollY) - previousScroll)).toBeLessThanOrEqual(1);
    await expectNoViewportOverflow(page);
  }

  await expect(news.getByRole("button", { name: /older updates/ })).toHaveCount(0);
  await expectMinimumSize(latestOnly, 44);
  await latestOnly.click();
  await expect(visibleEntries).toHaveCount(4);
  await expect(status).toHaveText("Showing 4 of 16 updates");
  await expect(news.getByRole("button", { name: "Show 4 older updates" })).toBeFocused();
  await expect(latestOnly).toHaveCount(0);
});

test("Data provides schema guidance, reuse terms, and next steps", { tag: ["@functional", "@desktop"] }, async ({ page }) => {
  await page.goto("data/");
  await waitForPublication(page);

  const downloads = page.locator(".download-grid a[download]");
  await expect(downloads).toHaveCount(3);
  await expect(page.getByRole("link", { name: "Download JSON" })).toHaveAttribute(
    "href",
    /data\/editions\/1.0\/deep20bench-v10\.json$/,
  );
  await expect(page.getByRole("link", { name: "Download CSV" })).toHaveAttribute(
    "href",
    /data\/editions\/1.0\/leaderboard\.csv$/,
  );
  await expect(page.getByRole("link", { name: "Download schema" })).toHaveAttribute(
    "href",
    /data\/editions\/1.0\/deep20bench-v10\.schema\.json$/,
  );
  await expect(page.locator(".field-guide")).toContainText("leaderboard[]");
  await expect(page.locator(".field-guide")).toContainText("official_runs[]");
  await expect(page.locator(".query-example code")).toContainText(
    ".model.display_name",
  );
  await expect(page.locator(".reuse-panel")).toContainText("CC BY 4.0");
  await expect(page.locator(".reuse-panel").getByRole("link", { name: /Citation/ }))
    .toHaveAttribute("href", /CITATION\.cff$/);
  await expect(page.getByRole("link", { name: "View official results" })).toHaveAttribute(
    "href",
    /results\/$/,
  );
  await expect(page.getByRole("link", { name: "How it works" }))
    .toHaveAttribute("href", /methodology\/$/);
  await expectNoViewportOverflow(page);
});

test("question scores show repeated-trial confidence intervals", { tag: ["@functional", "@desktop", "@smoke"] }, async ({ page }) => {
  await page.goto("", { waitUntil: "networkidle" });
  await waitForPublication(page);
  await page.locator(".score-dot-plot-canvas").first().scrollIntoViewIfNeeded();
  await expect(page.locator(".score-dot-plot-canvas svg")).toHaveCount(2);
  await expect(page.locator(".score-dot-plot-caption")).toContainText(
    "Question score",
  );
  await expect(page.locator(".score-dot-plot-caption")).toContainText(
    "lower is better",
  );
  await expect(page.locator(".score-dot-plot-caption")).toContainText(
    "95% CI · color = CI width",
  );
  await expect(page.locator(".score-dot-plot-caption")).toContainText("Narrow");
  await expect(page.locator(".score-dot-plot-caption")).toContainText("Medium");
  await expect(page.locator(".score-dot-plot-caption")).toContainText("Wide");
  await expect(page.locator(".confidence-width-caption")).toContainText("CI width");
  await expect(page.locator(".confidence-width-caption")).toContainText("stability");
  await expect(page.locator(".confidence-width-caption")).toContainText(
    "lower is better",
  );
  await expect(page.locator(".confidence-width-caption")).toContainText(
    "Rows follow question-score order",
  );
  await expect(page.locator(".confidence-width-caption")).toContainText(
    "Colors describe CI width. Compare question scores separately.",
  );
  await expect(page.locator(".winner-card .score-confidence")).toContainText("95% CI");
  await expect(page.locator('ol[aria-label="Official question scores"]')).toHaveCount(1);

  await page.goto("results/", { waitUntil: "networkidle" });
  await waitForPublication(page);
  await page.locator(".score-dot-plot-canvas").first().scrollIntoViewIfNeeded();
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
      '.score-dot-plot-confidence-band i[data-confidence-band="middle"]',
    ),
  ).toHaveCSS(
    "background-color",
    "rgb(208, 138, 0)",
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
  ).toContainText("CI width: 1.86 questions; narrow band");
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
    page.getByText("The 95% CI comes from repeated rounds on this edition's subjects"),
  ).toBeVisible();
});

test("repeat-average controls remain unavailable", { tag: ["@functional", "@desktop"] }, async ({ page }) => {
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
      page.getByRole("switch", { name: /Show averages by round/ }),
    ).toHaveCount(0);
    expect(repeatAverageRequests).toBe(0);
    await expect(page.locator(".score-dot-plot-caption")).not.toContainText(
      "average for one round number",
    );
    await expectNoViewportOverflow(page);
    page.off("request", countRepeatRequest);
  }
});

test("result pages use shared metric names", { tag: ["@functional", "@desktop"] }, async ({ page }) => {
  await page.goto("results/");
  await waitForPublication(page);
  const overview = page.locator("#route-content");
  await expect(overview).toContainText("Total benchmark cost");
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
  await expect(stability).toContainText("Score stability");
  await expect(stability).not.toContainText("Repeated-run stability");
  const stabilityChart = stability.locator(".reliability-scatter-canvas");
  await expect(stabilityChart).toHaveAttribute(
    "aria-label",
    /Question score and stability across rounds on these subjects\./,
  );
  await expect(stabilityChart).not.toHaveAttribute("aria-label", /repeated-run stability/i);
  await expect(stability).toContainText("CI width");
  await expect(stability).not.toContainText("Repeatability");

  await page.goto("results/cost/");
  await waitForPublication(page);
  const cost = page.locator("#route-content");
  await expect(cost).toContainText("Total benchmark cost");
  await expect(cost).toContainText("Total Guesser cost");
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
  await expect(efficiency).toContainText("Guesser cost");
  await expect(efficiency).not.toContainText("tested-model cost");
});

test("efficiency can be viewed by normalized distance from the ideal", { tag: ["@functional", "@both"] }, async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name.startsWith("mobile");
  if (!mobile) await page.setViewportSize({ width: 1280, height: 1089 });
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
      [2, 3, 4, 5, 6, 7].map((index) => tableHeaders.nth(index).boundingBox()),
    );
    expect(headerBoxes.every((box) => box !== null)).toBe(true);
    const metricWidths = headerBoxes.map((box) => box!.width);
    expect(Math.max(...metricWidths) / Math.min(...metricWidths)).toBeLessThan(1.9);
    const paretoHeader = tableHeaders.nth(3);
    await expect(paretoHeader).toContainText("Pareto");
    await expect(paretoHeader).toContainText("efficient");
  }

  const inlineChart = page.locator(".tradeoff-visual .efficiency-scatter-canvas");
  await inlineChart.scrollIntoViewIfNeeded();
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
  await expect(rows.nth(0)).toContainText("Synthetic Model 02");
  await expect(rows.nth(1)).toContainText("Synthetic Model 03");
  await expect(rows.nth(2)).toContainText("Synthetic Model 08");
  await expect(rows.nth(10)).toContainText("Synthetic Model 07");
});

test("workspace rows show persistent drill-down affordances", { tag: ["@functional", "@both"] }, async ({
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
    await expect(page.locator(".status-legend")).toContainText("No format errors");
    await expect(page.locator(".status-legend")).toContainText("Format errors");
    await expect(subjectLinks.first().locator(".visually-hidden")).toContainText(
      "Format:",
    );
  }

  await subjectLinks.first().focus();
  await expect(subjectLinks.first()).toHaveCSS("outline-style", "solid");
  await expect(subjectLinks.first()).toHaveCSS("outline-offset", "-3px");

  await subjectLinks.first().click();
  await expect(page).toHaveURL(new RegExp(`/subjects/${targetId}/$`));
  await waitForPublication(page);
  const episodeLinks = page.locator(".episode-list > a");
  await expect(page.locator(".episode-list-heading")).toContainText("Rounds");
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

test("run overview explains its totals and keeps every subject row available", { tag: ["@functional", "@desktop"] }, async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name.startsWith("mobile"));
  await page.goto(runPath);
  await waitForPublication(page);

  await expect(page.locator(".question-score")).toHaveCount(1);
  await expect(page.locator(".run-workspace-hero")).toContainText("Official run");
  await expect(page.locator(".run-workspace-hero")).not.toContainText("Certified");
  await expect(page.locator(".run-deck")).toContainText(
    `: ${runDocument.subjects.length} subjects,`,
  );
  await expect(page.locator(".run-deck")).toContainText(
    "In this Twenty Questions AI benchmark",
  );
  await expect(page.locator(".run-deck")).toContainText("scored rounds");

  const roleGuide = page.locator(".role-guide");
  await expect(roleGuide.locator("dt")).toHaveText([
    "Guesser",
    "Oracle",
    "Reviewer",
    "Judge",
    "Validator",
  ]);
  await expect(roleGuide.getByRole("link", { name: /roles and answer checks/ }))
    .toHaveAttribute("href", /methodology\/#answer-checks$/);

  const rail = page.locator(".model-rail");
  const subjectList = page.locator(".subject-rail-list");
  const subjectLinks = subjectList.locator("a");
  await expect(subjectLinks).toHaveCount(runDocument.subjects.length);
  await expect(rail).toHaveCSS("overflow-y", "auto");
  const bounds = await page.evaluate(() => {
    const railElement = document.querySelector<HTMLElement>(".model-rail");
    const links = [...document.querySelectorAll<HTMLElement>(".subject-rail-list a")];
    if (railElement === null || links.length === 0) {
      throw new Error("The run subject rail is incomplete.");
    }
    const railBox = railElement.getBoundingClientRect();
    const firstBox = links[0]!.getBoundingClientRect();
    const lastBox = links.at(-1)!.getBoundingClientRect();
    return {
      firstTop: firstBox.top,
      lastBottom: lastBox.bottom,
      railBottom: railBox.bottom,
      railTop: railBox.top,
    };
  });
  expect(bounds.firstTop).toBeGreaterThanOrEqual(bounds.railTop);
  expect(bounds.lastBottom).toBeLessThanOrEqual(bounds.railBottom + 1);

  const first = subjectLinks.first();
  await first.hover();
  await expect(first).toHaveCSS("background-color", "rgba(255, 255, 255, 0.15)");
  await expect(first.locator(".rail-link-arrow")).toHaveCSS(
    "transform",
    "matrix(1, 0, 0, 1, 3, 0)",
  );
  await expect(rail).toBeVisible();
});

// Round pages hide the run sidebar so the transcript gets the full width.
for (const [label, routePath] of [
  ["run", runPath],
  ["subject", subjectPath],
] as const) {
  test(`${label} sidebar scrolls from its heading and keeps all subjects reachable`, {
    tag: ["@functional", "@desktop", "@smoke"],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 480 });
    await page.goto(routePath);
    await waitForPublication(page);

    const rail = page.locator(".model-rail");
    const links = rail.locator(".subject-rail-list a");
    const last = links.last();
    await expect(links).toHaveCount(runDocument.subjects.length);
    await expect(rail).toHaveCSS("overflow-y", "auto");
    expect(await rail.evaluate((element) => element.scrollHeight))
      .toBeGreaterThan(await rail.evaluate((element) => element.clientHeight));
    await expect(last).not.toBeInViewport();

    await rail.locator(".model-rail-heading").hover();
    // Firefox can limit one wheel event to about one viewport of scrolling.
    await expect.poll(async () => {
      const remaining = await rail.evaluate((element) =>
        element.scrollHeight - element.clientHeight - element.scrollTop);
      if (remaining > 1) await page.mouse.wheel(0, 2000);
      return remaining;
    }).toBeLessThanOrEqual(1);
    expect(await rail.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
    // Allow fractional pixel rounding at the scroll limits.
    await expect(last).toBeInViewport({ ratio: 0.99 });
    expect(await page.evaluate(() => window.scrollY)).toBe(0);

    await links.first().focus();
    await expect(links.first()).toBeInViewport({ ratio: 0.99 });
    await last.focus();
    await expect(last).toBeInViewport({ ratio: 0.99 });
    const destination = await last.getAttribute("href");
    expect(destination).not.toBeNull();
    await last.click();
    await expect(page).toHaveURL(new URL(destination!, page.url()).href);
    await waitForPublication(page);
    await expect(last).toHaveAttribute("aria-current", "page");
  });
}

test("dates use one UTC format in every locale", { tag: ["@functional", "@desktop"] }, async ({ browser }) => {
  const context = await browser.newContext({
    locale: "de-CH",
    timezoneId: "Europe/Zurich",
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/deep-20-bench/results/");
  await waitForPublication(page);
  const publicationTime = page.locator(".site-footer time").first();
  const value = await publicationTime.getAttribute("datetime");
  expect(value).not.toBeNull();
  const timestamp = new Date(value!);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const expected =
    `${timestamp.getUTCDate()} ${months[timestamp.getUTCMonth()]} ${timestamp.getUTCFullYear()}, ` +
    `${String(timestamp.getUTCHours()).padStart(2, "0")}:` +
    `${String(timestamp.getUTCMinutes()).padStart(2, "0")} UTC`;
  await expect(publicationTime).toHaveText(expected);
  await context.close();
});

test("run model roles separate the Guesser from game support", { tag: ["@functional", "@both"] }, async ({
  page,
}, testInfo) => {
  await page.goto(runPath);
  await waitForPublication(page);

  const cards = page.locator(".run-model-card");
  await expect(cards).toHaveCount(5);
  await expect(cards.locator(".run-model-role")).toHaveText([
    "Guesser",
    "Oracle",
    "Reviewer",
    "Judge",
    "Guess Validator",
  ]);
  await expect(cards.first()).toHaveClass(/featured/);
  await expect(cards.first().locator(".model-test-sticker")).toHaveText(
    "Model under test",
  );
  await expect(cards.first().locator(".provider-routing-details")).toHaveCSS(
    "border-top-width",
    "0px",
  );
  await expect(page.locator(".model-test-sticker")).toHaveCount(1);
  await expect(page.locator(".support-section")).toHaveCount(1);
  await expect(page.locator(".support-model-grid > .run-model-card")).toHaveCount(4);

  const oracleLabels = cards.nth(1).locator("dt");
  await expect(oracleLabels).toContainText(["Calls", "Prompt version"]);

  const boxes = await cards.evaluateAll((elements) =>
    elements.map((element) => {
      const rectangle = element.getBoundingClientRect();
      return {
        left: rectangle.left,
        top: rectangle.top,
        width: rectangle.width,
        height: rectangle.height,
      };
    }),
  );

  const supportGridGap = await page
    .locator(".support-model-grid")
    .evaluate((element) => Number.parseFloat(getComputedStyle(element).rowGap));
  const supportHeadingBottom = await page
    .locator(".support-heading")
    .evaluate((element) => element.getBoundingClientRect().bottom);
  await expect(page.locator(".support-heading")).toHaveCSS(
    "border-bottom-width",
    "1px",
  );
  await expect(page.locator(".support-model-grid")).toHaveCSS(
    "border-top-width",
    "0px",
  );
  const centralSpacing = await page.evaluate(() => {
    const probe = document.createElement("div");
    probe.style.padding = "var(--workspace-panel-padding)";
    document.body.append(probe);
    const styles = getComputedStyle(probe);
    const dimensions = {
      panelPadding: Number.parseFloat(styles.paddingTop),
    };
    probe.remove();
    return dimensions;
  });
  const cardPadding = await cards.evaluateAll((elements) =>
    elements.map((element) => {
      const styles = getComputedStyle(element);
      return {
        top: Number.parseFloat(styles.paddingTop),
        right: Number.parseFloat(styles.paddingRight),
        bottom: Number.parseFloat(styles.paddingBottom),
        left: Number.parseFloat(styles.paddingLeft),
      };
    }),
  );
  const upperCardGap = boxes[1]!.top - supportHeadingBottom;
  expect(supportGridGap).toBe(0);
  expect(Math.abs(upperCardGap + 1)).toBeLessThanOrEqual(1);
  for (const padding of cardPadding) {
    expect(Math.abs(padding.top - centralSpacing.panelPadding)).toBeLessThan(2);
    expect(Math.abs(padding.right - centralSpacing.panelPadding)).toBeLessThan(2);
    expect(Math.abs(padding.bottom - centralSpacing.panelPadding)).toBeLessThan(2);
    expect(Math.abs(padding.left - centralSpacing.panelPadding)).toBeLessThan(2);
  }

  if (testInfo.project.name.startsWith("mobile")) {
    for (let index = 1; index < boxes.length; index += 1) {
      expect(boxes[index]!.top).toBeGreaterThan(boxes[index - 1]!.top);
      expect(Math.abs(boxes[index]!.left - boxes[0]!.left)).toBeLessThan(2);
      expect(Math.abs(boxes[index]!.width - boxes[0]!.width)).toBeLessThan(2);

      if (index > 1) {
        const previousBottom = boxes[index - 1]!.top + boxes[index - 1]!.height;
        expect(Math.abs(boxes[index]!.top - previousBottom + 1)).toBeLessThanOrEqual(1);
      }
    }
  } else {
    expect(boxes[1]!.top).toBeGreaterThan(boxes[0]!.top);
    expect(boxes[0]!.width).toBeGreaterThan(boxes[1]!.width * 1.9);
    expect(Math.abs(boxes[1]!.top - boxes[2]!.top)).toBeLessThan(2);
    expect(Math.abs(boxes[3]!.top - boxes[4]!.top)).toBeLessThan(2);
    expect(boxes[3]!.top).toBeGreaterThan(boxes[1]!.top);
    const columnGap = boxes[2]!.left - (boxes[1]!.left + boxes[1]!.width);
    const rowGap = boxes[3]!.top - (boxes[1]!.top + boxes[1]!.height);
    expect(Math.abs(columnGap + 1)).toBeLessThanOrEqual(1);
    expect(Math.abs(rowGap + 1)).toBeLessThanOrEqual(1);
  }

  await expectNoViewportOverflow(page);
});

test("mobile pages use one document scroll and no fixed site navigation", { tag: ["@functional", "@mobile"] }, async ({
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
