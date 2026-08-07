import { readFile } from "node:fs/promises";
import path from "node:path";

import { expect, test as base } from "@playwright/test";

const dataRoot = path.resolve(
  process.cwd(),
  "tests/fixtures/publication/data",
);

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route("**/deep-20-bench/data/**", async (route) => {
      const marker = "/deep-20-bench/data/";
      const pathname = new URL(route.request().url()).pathname;
      const encodedPath = pathname.split(marker)[1];
      if (encodedPath === undefined) {
        await route.abort("failed");
        return;
      }
      if (encodedPath === "") {
        await route.continue();
        return;
      }
      const relativePath = decodeURIComponent(encodedPath);
      const fixturePath = path.resolve(dataRoot, relativePath);
      if (!fixturePath.startsWith(`${dataRoot}${path.sep}`)) {
        await route.fulfill({ status: 400, body: "Invalid fixture path." });
        return;
      }
      try {
        const body = await readFile(fixturePath);
        await route.fulfill({
          status: 200,
          contentType: "application/json; charset=utf-8",
          body,
        });
      } catch (error: unknown) {
        if (
          typeof error === "object" &&
          error !== null &&
          "code" in error &&
          error.code === "ENOENT"
        ) {
          await route.fulfill({ status: 404, body: "Fixture document not found." });
          return;
        }
        throw error;
      }
    });
    await use(page);
  },
});

export { expect };
