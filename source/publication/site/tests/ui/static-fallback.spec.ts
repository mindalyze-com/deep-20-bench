import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

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

test("homepage remains useful without JavaScript", { tag: ["@static-fallback", "@both"] }, async ({ browser }, testInfo) => {
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
    "How well can AI models play Twenty Questions?",
  );
  await expect(staticHome).toContainText(
    "Deep20Bench tests how well AI models play the guessing game",
  );
  await expect(staticHome).toContainText(
    "Each question, wrong guess, or reply that does not follow the required format adds one point.",
  );
  await expect(staticHome).toContainText(
    "50 questions - more than the traditional twenty, giving models more room to finish a round.",
  );
  await expect(staticHome).toContainText(
    "The concept works and the first step is complete. Expanding the pilot is straightforward; cost is the main constraint.",
  );
  await expect(staticHome).not.toContainText("small first step");
  await expect(staticHome).not.toContainText("not a definitive ranking");
  await expect(staticHome).toContainText(
    "The Guesser asks. Three roles determine the answer.",
  );
  await expect(staticHome).toContainText(
    "An Oracle searches the live web and cites evidence.",
  );
  await expect(page.getByText("What this pilot tests", { exact: true })).toBeVisible();
  await expect(page.getByText("What it does not claim", { exact: true })).toBeVisible();
  const staticDiscussionLink = page.getByRole("link", {
    name: "Join discussion (opens in a new tab)",
  });
  await expect(staticDiscussionLink).toHaveAttribute(
    "href",
    "https://github.com/mindalyze-com/deep-20-bench/discussions",
  );
  await expect(staticDiscussionLink).toHaveAttribute("target", "_blank");
  const staticSupportLink = page.getByRole("link", {
    name: "Support future benchmark runs (opens in a new tab)",
  });
  await expect(staticSupportLink).toHaveAttribute("href", "https://ko-fi.com/mindalyze");
  await expect(staticSupportLink).toHaveAttribute("target", "_blank");
  await expect(page.getByText("Deep20Bench needs JavaScript")).toHaveCount(0);
  const staticFooter = page.locator(".static-footer");
  await expect(staticFooter).toBeVisible();
  for (const link of siteResourceLinks) {
    await expect(staticFooter.getByRole("link", { name: link.label })).toHaveAttribute(
      "href",
      link.href,
    );
  }
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

test("sitemap pages remain useful without JavaScript", { tag: ["@static-fallback", "@desktop"] }, async ({ browser }) => {
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

test("JavaScript users do not see the static page while the app loads", { tag: ["@static-fallback", "@desktop", "@smoke"] }, async ({
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
