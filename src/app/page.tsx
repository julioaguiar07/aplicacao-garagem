import { connection } from "next/server";
import { Cabecalho, FaixaInfo, Rodape } from "@/components/vitrine/cabecalho";
import { Catalogo } from "@/components/vitrine/catalogo";
import { vitrine } from "@/lib/vitrine";

export default async function Vitrine() {
  await connection(); // sempre o estoque atual do banco
  const { veiculos, loja } = await vitrine();
  return (
    <div className="min-h-dvh bg-[#0d0e10]">
      <Cabecalho loja={loja} />
      <FaixaInfo disponiveis={veiculos.filter((v) => !v.reservado).length} loja={loja} />
      <main>
        <Catalogo veiculos={veiculos} simulacao={loja.simulacao} />
      </main>
      <Rodape loja={loja} />
    </div>
  );
}
