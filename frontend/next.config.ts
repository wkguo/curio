import type { NextConfig } from "next";

// All /api/* calls are proxied to the FastAPI backend. If it is not running, the
// client falls back to the bundled offline fixtures (see lib/api.ts).
const API = process.env.CURIO_API_URL ?? "http://127.0.0.1:8000";

const config: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default config;
