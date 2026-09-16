import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // On Vercel, NEXT_PUBLIC_API_URL=/api (.env.production).
  // vercel.json rewrites /api/:path* to the Python serverless function, and
  // Mangum strips the /api prefix before FastAPI sees the route.
  // Locally, NEXT_PUBLIC_API_URL=http://localhost:8000 (.env.local) so the
  // browser calls the FastAPI dev server directly.
};

export default nextConfig;
