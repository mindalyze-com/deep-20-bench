import path from "node:path";

import { expect, test } from "@playwright/test";

import {
  derivePublicationPaths,
  docsRoot,
  waitForPublication,
} from "./support/publication";

const { episodePath, runPath, subjectPath } = derivePublicationPaths(
  path.join(docsRoot, "data"),
);

test(
  "the generated publication loads each dynamic page template",
  { tag: ["@current-data", "@desktop", "@smoke"] },
  async ({ page }) => {
    const browserErrors: string[] = [];
    const failedResponses: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("pageerror", (error) => browserErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) {
        failedResponses.push(`${response.status()} ${response.url()}`);
      }
    });

    for (const routePath of ["", "results/", runPath, subjectPath, episodePath]) {
      await page.goto(routePath);
      await waitForPublication(page);
      await expect(page.locator("h1").first()).toBeVisible();
    }

    expect(browserErrors).toEqual([]);
    expect(failedResponses).toEqual([]);
  },
);
