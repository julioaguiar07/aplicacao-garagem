import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/painel", "/entrar", "/api", "/arquivos/privado"] },
    sitemap: "https://www.carmelomultimarcas.com.br/sitemap.xml",
  };
}
