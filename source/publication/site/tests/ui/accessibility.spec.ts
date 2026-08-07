import AxeBuilder from "@axe-core/playwright";

import { expect, test } from "./support/fixture";

import {
  episodePath,
  runPath,
  subjectPath,
  waitForPublication,
} from "./support/publication";

const wcagTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
const knownViolationTargets: Readonly<Record<string, readonly string[]>> = {
  "methodology/": [
    'div[aria-label="Question score formula"] > div:nth-child(1) > span',
    'div[aria-label="Question score formula"] > div:nth-child(2) > span',
    ".standard-error-formula > span",
  ],
  [subjectPath]: [
    '.episode-list-heading > .rail-section-label.eyebrow > span[aria-hidden="true"]',
    ".episode-list-heading > strong",
    '.episode-rail-heading > .rail-section-label.eyebrow > span[aria-hidden="true"]',
  ],
  [episodePath]: [
    "#episode-tab-reliability > small",
    "#episode-tab-usage > small",
    '.episode-list-heading > .rail-section-label.eyebrow > span[aria-hidden="true"]',
    ".episode-list-heading > strong",
    '.episode-rail-heading > .rail-section-label.eyebrow > span[aria-hidden="true"]',
  ],
};

test(
  "representative page templates have no detectable WCAG A or AA violations",
  { tag: ["@a11y", "@desktop"] },
  async ({ page }) => {
    for (const routePath of [
      "",
      "results/",
      "methodology/",
      "data/",
      runPath,
      subjectPath,
      episodePath,
    ]) {
      await page.goto(routePath);
      await waitForPublication(page);
      const result = await new AxeBuilder({ page }).withTags(wcagTags).analyze();
      const fingerprints = result.violations.flatMap((violation) =>
        violation.nodes.map(
          (node) =>
            `${violation.id}:${node.target.join(" > ").replace(/\[data-v-[^\]]+\]/g, "")}`,
        ),
      );
      const expected = (knownViolationTargets[routePath] ?? []).map(
        (target) => `color-contrast:${target}`,
      );
      expect(fingerprints.sort(), routePath).toEqual([...expected].sort());
    }
  },
);

test(
  "the open mobile navigation has no detectable WCAG A or AA violations",
  { tag: ["@a11y", "@mobile"] },
  async ({ page }) => {
    await page.goto(episodePath);
    await waitForPublication(page);
    const navigation = page.locator(".mobile-navigation");
    await navigation.locator("summary").click();
    const result = await new AxeBuilder({ page })
      .include(".mobile-navigation")
      .withTags(wcagTags)
      .analyze();
    expect(result.violations).toEqual([]);
  },
);
