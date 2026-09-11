import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { docsRoot, staticPaths } from "./support/publication";

interface OfficialRunReference {
  execution_id: string;
}

interface ManifestFixture {
  official_runs: OfficialRunReference[];
}

interface RunFixture {
  run: {
    contract: { status: "clean" | "breached" | "not_evaluable" };
    model_name: string;
  };
  subjects: Array<{ target_id: string }>;
}

const staticBase = "http://127.0.0.1:4174/";
const manifest = JSON.parse(
  readFileSync(path.join(docsRoot, "data", "manifest.json"), "utf8"),
) as ManifestFixture;
const representative = manifest.official_runs
  .map((reference) => ({
    executionId: reference.execution_id,
    run: JSON.parse(
      readFileSync(
        path.join(docsRoot, "data", "runs", `${reference.execution_id}.json`),
        "utf8",
      ),
    ) as RunFixture,
  }))
  .find(({ run }) => run.run.contract.status === "clean");
if (representative === undefined) {
  throw new Error("The publication needs an official run for static rendering tests.");
}
const representativeExecutionId = representative.executionId;
const representativeRun = representative.run;
const representativeTargetId = representativeRun.subjects[0]?.target_id;
if (representativeTargetId === undefined) {
  throw new Error("The publication needs a subject for static rendering tests.");
}

test(
  "homepage remains complete without JavaScript",
  { tag: ["@static-fallback", "@both"] },
  async ({ browser }, testInfo) => {
    const mobile = testInfo.project.name.startsWith("mobile");
    const context = await browser.newContext({
      javaScriptEnabled: false,
      viewport: mobile ? { width: 390, height: 844 } : { width: 1280, height: 720 },
    });
    const page = await context.newPage();
    await page.goto(staticBase);

    const content = page.locator("#route-content.home-page");
    await expect(content).toBeVisible();
    await expect(page.locator(".home-hero-inner")).toHaveCSS("display", "grid");
    await expect(page.locator(".hero-details")).toHaveCSS("display", "grid");
    await expect(page.locator(".round-example")).toHaveCSS("position", "relative");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "How well can AI models play Twenty Questions?",
    );
    await expect(content).toContainText("What this pilot tests");
    await expect(content).toContainText("How to read the pilot");
    await expect(content).toContainText("Comparable runs, limited conclusions.");
    await expect(page.locator(".site-footer")).toBeVisible();
    await expect(page.locator(".static-home, .static-route-fallback")).toHaveCount(0);
    await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(2);
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      "https://deep20bench.com/editions/1.1/",
    );

    await context.close();
  },
);

test(
  "homepage keeps its styled content while JavaScript is delayed and during hydration",
  { tag: ["@static-fallback", "@both", "@smoke", "@editions"] },
  async ({ page }) => {
    const hydrationMessages: string[] = [];
    page.on("console", (message) => {
      if (/hydration|mismatch/i.test(message.text())) hydrationMessages.push(message.text());
    });
    await page.route("https://**/*", (route) => route.abort());
    let releaseScripts = (): void => {};
    const scriptsReady = new Promise<void>((resolve) => { releaseScripts = resolve; });
    await page.route("**/_assets/*.js", async (route) => {
      await scriptsReady;
      await route.continue();
    });

    try {
      await page.goto(new URL("editions/1.1/", staticBase).href, { waitUntil: "commit" });
      const hero = page.locator(".home-hero");
      await expect(hero).toBeVisible();
      await expect(page.locator(".home-hero-inner")).toHaveCSS("display", "grid");
      await expect(page.locator(".round-card")).toHaveCSS("border-radius", "10px");
      await page.waitForFunction(() =>
        [...document.querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"]')]
          .every((link) => link.sheet !== null),
      );
      // WebKit's fonts.ready also waits for document load, which is deliberately held here.
      await page.evaluate(async () => {
        await Promise.all(
          [...document.querySelectorAll(".hero-copy h1, .hero-lead, .round-example")]
            .map((element) => {
              const style = getComputedStyle(element);
              return document.fonts.load(`${style.fontWeight} ${style.fontSize} ${style.fontFamily}`);
            }),
        );
      });
      const heading = await page.getByRole("heading", { level: 1 }).elementHandle();
      if (heading === null) throw new Error("The initial heading is missing.");
      const beforeHero = await hero.boundingBox();
      const beforeHeading = await heading.boundingBox();
      const beforeRound = await page.locator(".round-example").boundingBox();

      releaseScripts();
      await page.waitForFunction(() => {
        const app = document.getElementById("app");
        return app !== null && "__vue_app__" in app;
      });

      // Hydration reuses the visible content and preserves its geometry.
      expect(await heading.evaluate((element) => element.isConnected)).toBe(true);
      expect(await hero.boundingBox()).toEqual(beforeHero);
      expect(await heading.boundingBox()).toEqual(beforeHeading);
      expect(await page.locator(".round-example").boundingBox()).toEqual(beforeRound);
      expect(hydrationMessages).toEqual([]);
      await expect(page.locator("#route-content")).toHaveCount(1);
      await page.getByRole("link", { name: "Explore pilot results" }).click();
      await expect(page).toHaveURL(/\/editions\/1\.1\/results\/$/);
    } finally {
      releaseScripts();
    }
  },
);

test(
  "every editorial page has readable initial HTML and ordinary links",
  { tag: ["@static-fallback", "@desktop"] },
  async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();

    for (const routePath of staticPaths.slice(1)) {
      await page.goto(new URL(routePath, staticBase).href);
      await expect(page.locator("#route-content")).toBeVisible();
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expect(page.locator('meta[name="robots"]')).toHaveCount(0);
    }

    await page.goto(new URL("editions/1.0/results/", staticBase).href);
    for (const reference of manifest.official_runs) {
      await expect(
        page.locator(`a[href="/runs/${reference.execution_id}/"]`).first(),
      ).toBeAttached();
    }
    for (const routePath of staticPaths.filter((value) => value.startsWith("results/"))) {
      await expect(
        page.locator(`a[href="/editions/1.0/${routePath}"]`).first(),
      ).toBeAttached();
    }

    await context.close();
  },
);

test(
  "official run summary is complete without JavaScript",
  { tag: ["@static-fallback", "@desktop"] },
  async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(new URL(`runs/${representativeExecutionId}/`, staticBase).href);

    const overview = page.locator(".run-overview-pane");
    await expect(overview).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toContainText(
      representativeRun.run.model_name.replace(/ \([^)]+\)$/, ""),
    );
    await expect(overview).toContainText("Question score");
    await expect(overview).toContainText("95% CI");
    await expect(overview).toContainText("Success");
    await expect(overview).toContainText("Contract compliance");
    await expect(overview).toContainText("Guesser cost");
    await expect(overview).toContainText("Wall-clock runtime");
    await expect(overview).toContainText(
      representativeRun.run.contract.status === "clean"
        ? "Output contract clean."
        : "Output contract breached.",
    );
    for (const subject of representativeRun.subjects) {
      await expect(
        page.locator(
          `a[href="/runs/${representativeExecutionId}/subjects/${subject.target_id}/"]`,
        ).first(),
      ).toBeAttached();
    }

    await context.close();
  },
);

test(
  "prerendered run hydrates once without an initial data refetch",
  { tag: ["@static-fallback", "@desktop", "@smoke"] },
  async ({ page }) => {
    const hydrationMessages: string[] = [];
    const dataRequests: string[] = [];
    page.on("console", (message) => {
      if (/hydration|mismatch/i.test(message.text())) hydrationMessages.push(message.text());
    });
    page.on("request", (request) => {
      if (request.url().includes("/data/")) {
        dataRequests.push(request.url());
      }
    });

    await page.goto(new URL(`runs/${representativeExecutionId}/`, staticBase).href);
    await page.locator("#route-content").waitFor();
    await page.locator(".run-overview-pane").waitFor();

    await expect(page.locator("#route-content")).toHaveCount(1);
    await expect(page.locator(".static-home, .static-route-fallback")).toHaveCount(0);
    await expect(page.locator("html")).toHaveAttribute("data-prerendered", "true");
    expect(hydrationMessages).toEqual([]);
    expect(dataRequests).toEqual([]);
  },
);

test(
  "subject summary is complete without JavaScript",
  { tag: ["@static-fallback", "@desktop", "@smoke"] },
  async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    const subjectPath =
      `runs/${representativeExecutionId}/subjects/${representativeTargetId}/`;
    await page.goto(new URL(subjectPath, staticBase).href);

    const overview = page.locator(".subject-overview-pane");
    await expect(overview).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(overview).toContainText("Average questions");
    await expect(overview).toContainText("Episodes");
    await expect(overview).toContainText("Successful");
    await expect(page.locator(".episode-list a")).toHaveCount(5);
    await expect(page.locator('meta[name="robots"]')).toHaveCount(0);
    await expect(page.locator("html")).toHaveAttribute("data-prerendered", "true");

    await context.close();
  },
);
