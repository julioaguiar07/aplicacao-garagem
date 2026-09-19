import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Postgres embutido e driver pg rodam como módulos Node, fora do bundle
  serverExternalPackages: ["@electric-sql/pglite", "pg", "sharp"],
  experimental: {
    serverActions: {
      // fotos de celular chegam com 3 a 6 MB cada; várias por envio
      bodySizeLimit: "25mb",
    },
  },
};

export default nextConfig;
