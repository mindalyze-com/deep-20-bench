import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

import { staticHomepagePlugin } from "./static-home";

const configuredBase = process.env.DEEP20_BASE_PATH ?? "/deep-20-bench/";
const base = configuredBase.endsWith("/") ? configuredBase : `${configuredBase}/`;

export default defineConfig(({ command }) => {
  const publicDir =
    process.env.DEEP20_PUBLIC_DIR ??
    (command === "serve"
      ? fileURLToPath(new URL("../../../docs", import.meta.url))
      : "./public");

  return {
    base,
    publicDir,
    plugins: [vue(), staticHomepagePlugin(publicDir, base)],
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
