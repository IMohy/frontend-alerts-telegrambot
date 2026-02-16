import { defineConfig } from "tsup";

export default defineConfig([
  {
    entry: ["index.ts"],
    format: ["esm", "cjs"],
    dts: true,
    splitting: false,
    clean: true,
    outDir: "dist",
    external: ["react"],
  },
  {
    entry: ["react/index.ts"],
    format: ["esm", "cjs"],
    dts: true,
    splitting: false,
    outDir: "dist/react",
    external: ["react"],
  },
]);
