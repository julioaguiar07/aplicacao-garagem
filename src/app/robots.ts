import type { MetadataRoute } from "next";
import { MARCA } from "@/lib/marca";

export default function robots(): MetadataRoute.Robots {
  // Demonstração: nada indexado
  if (!MARCA.site) return { rules: { userAgent: "*", disallow: "/" } };
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/painel", "/entrar", "/api", "/arquivos/privado"] },
    sitemap: `${MARCA.site}/sitemap.xml`,
  };
}
