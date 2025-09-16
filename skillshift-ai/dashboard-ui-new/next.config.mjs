/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      // MANUS-AI FIX: Remove conflicting /api/* rewrite that bypasses frontend API routes
      // Only proxy specific endpoints that don't have frontend handlers
      {
        source: '/health',
        destination: 'http://localhost:8000/health',
      },
      {
        source: '/api/backend/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
}

export default nextConfig