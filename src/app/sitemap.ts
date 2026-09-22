import type { MetadataRoute } from "next";
import { connection } from "next/server";
import { vitrine } from "@/lib/vitrine";

const SITE = "https://www.carmelomultimarcas.com.br";

// Vitrine e página de cada carro à venda, para o Google indexar
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  await connection();
  const { veiculos } = await vitrine();
  return [
    { url: `${SITE}/`, changeFrequency: "daily", priority: 1 },
    ...veiculos.map((v) => ({ url: `${SITE}/carros/${v.slug}`, changeFrequency: "weekly" as const, priority: 0.8 })),
  ];
}
