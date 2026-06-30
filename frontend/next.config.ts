import type { NextConfig } from "next";

const allowDevInlineScripts = process.env.NARRATWIN_ALLOW_DEV_INLINE_CSP === "1";
const scriptSrc = allowDevInlineScripts ? "script-src 'self' 'unsafe-inline'" : "script-src 'self'";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*",
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
              `default-src 'self'; ${scriptSrc}; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'`,
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
