import { defineConfig } from "astro/config";

const configuredBase = process.env.DEEP20_BASE_PATH ?? "/deep-20-bench/";
const base = configuredBase === "/" ? "/" : configuredBase.replace(/\/$/, "");
const outDir = process.env.DEEP20_OUTPUT_DIR ?? "./dist";

export default defineConfig({
  base,
  outDir,
  output: "static",
  trailingSlash: "always",
  build: {
    assets: "_assets",
  },
  vite: {
    build: {
      sourcemap: false,
    },
  },
});
