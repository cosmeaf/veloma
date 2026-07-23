import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle for the Docker runtime stage.
  output: 'standalone',
  poweredByHeader: false,
};

export default nextConfig;
