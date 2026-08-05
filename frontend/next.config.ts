import type { NextConfig } from "next";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const apiProxyTarget = process.env.NARRATWIN_API_PROXY_TARGET ?? "http://127.0.0.1:8000";
const NARRATWIN_BUILD_ID_INPUTS = [
  "package.json",
  "package-lock.json",
  "next.config.ts",
  "tsconfig.json",
  "src",
];

function addBuildInput(hash: ReturnType<typeof createHash>, path: string): void {
  const stat = statSync(path);
  hash.update(path).update("\0");
  if (stat.isDirectory()) {
    for (const name of readdirSync(path).sort()) addBuildInput(hash, join(path, name));
    return;
  }
  hash.update(readFileSync(path)).update("\0");
}

const nextConfig: NextConfig = {
  output: "standalone",
  generateBuildId: async () => {
    const hash = createHash("sha256");
    for (const path of NARRATWIN_BUILD_ID_INPUTS) addBuildInput(hash, path);
    return `narratwin-${hash.digest("hex").slice(0, 32)}`;
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiProxyTarget}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
          },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
