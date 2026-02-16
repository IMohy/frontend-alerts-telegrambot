import { defineConfig } from "tsup";
import { readFileSync } from "fs";
import { resolve } from "path";

function loadEnv(): Record<string, string> {
  try {
    const raw = readFileSync(resolve(__dirname, "../.env"), "utf-8");
    const vars: Record<string, string> = {};
    for (const line of raw.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eqIdx = trimmed.indexOf("=");
      if (eqIdx === -1) continue;
      vars[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
    }
    return vars;
  } catch {
    return {};
  }
}

const envVars = loadEnv();

const clientEnv = {
  CLIENT_WEBHOOK_URL: envVars.CLIENT_WEBHOOK_URL || "",
  CLIENT_WEBHOOK_SECRET: envVars.CLIENT_WEBHOOK_SECRET || "",
};

export default defineConfig([
  {
    entry: ["index.ts"],
    format: ["esm", "cjs"],
    dts: true,
    splitting: false,
    clean: true,
    outDir: "dist",
    external: ["react"],
    env: clientEnv,
  },
  {
    entry: ["react/index.ts"],
    format: ["esm", "cjs"],
    dts: true,
    splitting: false,
    outDir: "dist/react",
    external: ["react"],
    env: clientEnv,
  },
]);
