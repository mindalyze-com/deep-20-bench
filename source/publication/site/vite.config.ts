import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

import { staticHomepagePlugin } from "./static-home";

const configuredBase = process.env.DEEP20_BASE_PATH ?? "/deep-20-bench/";
const base = configuredBase.endsWith("/") ? configuredBase : `${configuredBase}/`;
const configuredCanonicalUrl =
  process.env.DEEP20_CANONICAL_URL ??
  "https://mindalyze-com.github.io/deep-20-bench/";
const canonicalUrl = configuredCanonicalUrl.endsWith("/")
  ? configuredCanonicalUrl
  : `${configuredCanonicalUrl}/`;

export default defineConfig(({ command }) => {
  const publicDir =
    process.env.DEEP20_PUBLIC_DIR ??
    (command === "serve"
      ? fileURLToPath(new URL("../../../docs", import.meta.url))
      : "./public");

  return {
    base,
    publicDir,
    plugins: [vue(), staticHomepagePlugin(publicDir, base, canonicalUrl)],
    define: {
      __DEEP20_CANONICAL_URL__: JSON.stringify(canonicalUrl),
    },
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    build: {
      assetsDir: "_assets",
      chunkSizeWarningLimit: 550,
      emptyOutDir: true,
      outDir: process.env.DEEP20_OUTPUT_DIR ?? "./dist",
      sourcemap: false,
    },
  };
});
