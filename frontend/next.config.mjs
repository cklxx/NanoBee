import path from "path";
import { fileURLToPath } from "url";
import env from "@next/env";

const { loadEnvConfig } = env;

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(frontendDir, "..");

// Load environment variables from the frontend folder (default Next.js behavior)
// and additionally from the repository root so values like NEXT_PUBLIC_API_BASE
// in the top-level .env are available when running frontend commands directly.
loadEnvConfig(frontendDir);
loadEnvConfig(rootDir);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
