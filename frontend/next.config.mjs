/** @type {import('next').NextConfig} */
const nextConfig = {
  // Strict mode for highlighting potential problems
  reactStrictMode: true,

  // Local dev proxy: forward /api/v1/* to the backend.
  // On Vercel, vercel.json rewrites take over instead.
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },

  // Performance optimizations
  poweredByHeader: false,
  compress: true,

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
  },

  // Experimental features for better performance
  experimental: {
    optimizePackageImports: ['@/components/ui'],
  },
};

export default nextConfig;
