import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone', // Required for Docker deployment
  reactCompiler: true,
};

export default nextConfig;
