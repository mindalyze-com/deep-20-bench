import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

import { parseRouteMetadata } from "./src/lib/route-metadata";

const configuredBase = process.env.DEEP20_BASE_PATH ?? "/";
const base = configuredBase.endsWith("/") ? configuredBase : `${configuredBase}/`;
const configuredCanonicalUrl =
  process.env.DEEP20_CANONICAL_URL ??
  "https://deep20bench.com/";
const canonicalUrl = configuredCanonicalUrl.endsWith("/")
  ? configuredCanonicalUrl
  : `${configuredCanonicalUrl}/`;

export default defineConfig(({ command, isSsrBuild }) => {
  const publicDir =
    process.env.DEEP20_PUBLIC_DIR ??
    (command === "serve"
      ? fileURLToPath(new URL("../../../docs", import.meta.url))
      : "./public");
  const routeManifestPath = process.env.DEEP20_ROUTE_MANIFEST ??
    join(publicDir, "data", "routes.json");
  const routeMetadata = parseRouteMetadata(
    JSON.parse(readFileSync(routeManifestPath, "utf8")) as unknown,
  );

  return {
    base,
    publicDir,
    plugins: [vue()],
    define: {
      __DEEP20_CANONICAL_URL__: JSON.stringify(canonicalUrl),
      __DEEP20_ROUTE_METADATA__: JSON.stringify(routeMetadata),
    },
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    ssr: {
      noExternal: true,
    },
    build: {
      assetsDir: "_assets",
      chunkSizeWarningLimit: 550,
      copyPublicDir: !isSsrBuild,
      emptyOutDir: true,
      outDir: isSsrBuild
        ? (process.env.DEEP20_SSR_OUTPUT_DIR ?? "./.ssr")
        : (process.env.DEEP20_OUTPUT_DIR ?? "./dist"),
      sourcemap: false,
    },
  };
});
