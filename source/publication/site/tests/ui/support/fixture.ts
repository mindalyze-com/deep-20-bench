import { readFile } from "node:fs/promises";
import path from "node:path";

import { expect, test as base } from "@playwright/test";

const dataRoot = path.resolve(
  process.cwd(),
  "tests/fixtures/publication/data",
);
const publicationBasePath = "/deep-20-bench/";
const embeddedPageState =
  /<script\b(?=[^>]*\bid=["']deep20-page-state["'])[^>]*>[\s\S]*?<\/script>\s*/;

export const test = base.extend({
  page: async ({ page, browserName, baseURL }, use) => {
    if (browserName === "chromium" && baseURL !== undefined) {
      // Fulfilled fixture pages still connect to the local Vite development server.
      await page.context().grantPermissions(["local-network-access"], {
        origin: new URL(baseURL).origin,
      });
    }
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
    await page.route(
      (url) => url.pathname.startsWith(publicationBasePath),
      async (route) => {
        if (route.request().resourceType() !== "document") {
          await route.fallback();
          return;
        }
        let response = await route.fetch();
        if (response.status() === 404) {
          response = await route.fetch({
            url: new URL(publicationBasePath, route.request().url()).href,
          });
        }
        const contentType = response.headers()["content-type"] ?? "";
        if (!contentType.includes("text/html")) {
          await route.fulfill({ response });
          return;
        }
        const body = (await response.text()).replace(embeddedPageState, "");
        await route.fulfill({ response, body });
      },
    );
    await use(page);
  },
});

export { expect };
