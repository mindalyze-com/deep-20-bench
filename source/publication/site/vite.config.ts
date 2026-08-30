import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

const configuredBase = process.env.DEEP20_BASE_PATH ?? "/deep-20-bench/";
const base = configuredBase.endsWith("/") ? configuredBase : `${configuredBase}/`;
const configuredCanonicalUrl =
  process.env.DEEP20_CANONICAL_URL ??
  "https://mindalyze-com.github.io/deep-20-bench/";
const canonicalUrl = configuredCanonicalUrl.endsWith("/")
  ? configuredCanonicalUrl
  : `${configuredCanonicalUrl}/`;

export default defineConfig(({ command, isSsrBuild }) => {
  const publicDir =
    process.env.DEEP20_PUBLIC_DIR ??
    (command === "serve"
      ? fileURLToPath(new URL("../../../docs", import.meta.url))
      : "./public");

  return {
    base,
    publicDir,
    plugins: [vue()],
    define: {
      __DEEP20_CANONICAL_URL__: JSON.stringify(canonicalUrl),
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
