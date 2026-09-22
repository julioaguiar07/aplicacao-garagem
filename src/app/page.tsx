import { connection } from "next/server";
import { Cabecalho, FaixaInfo, Rodape } from "@/components/vitrine/cabecalho";
import { Catalogo } from "@/components/vitrine/catalogo";
import { vitrine } from "@/lib/vitrine";

const SITE = "https://www.carmelomultimarcas.com.br";

export const metadata = { alternates: { canonical: "/" } };

export default async function Vitrine() {
  await connection(); // sempre o estoque atual do banco
  const { veiculos, loja } = await vitrine();
  // Dados estruturados: nome do site e ficha da loja no Google
  const dadosGoogle = [
    { "@context": "https://schema.org", "@type": "WebSite", name: "Carmelo Multimarcas", url: `${SITE}/` },
    {
      "@context": "https://schema.org",
      "@type": "AutoDealer",
      name: "Carmelo Multimarcas",
      url: `${SITE}/`,
      logo: `${SITE}/marca/logo-circulo.png`,
      image: `${SITE}/marca/compartilhar.png`,
      telephone: `+${loja.whatsapp}`,
      address: {
        "@type": "PostalAddress",
        streetAddress: loja.endereco,
        addressLocality: loja.cidade.split("/")[0],
        addressRegion: loja.cidade.split("/")[1] ?? "RN",
        postalCode: loja.cep,
        addressCountry: "BR",
      },
    },
  ];
  return (
    <div className="min-h-dvh bg-[#0d0e10]">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(dadosGoogle).replace(/</g, "\\u003c") }} />
      <Cabecalho loja={loja} />
      <FaixaInfo disponiveis={veiculos.filter((v) => !v.reservado).length} loja={loja} />
      <main>
        <Catalogo veiculos={veiculos} simulacao={loja.simulacao} />
      </main>
      <Rodape loja={loja} />
    </div>
  );
}
