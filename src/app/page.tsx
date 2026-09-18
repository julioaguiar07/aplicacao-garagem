import { Cabecalho, FaixaInfo, Rodape } from "@/components/vitrine/cabecalho";
import { Catalogo } from "@/components/vitrine/catalogo";
import { veiculosPublicados } from "@/lib/vitrine";

export default function Vitrine() {
  const veiculos = veiculosPublicados();
  return (
    <div className="min-h-dvh bg-[#0d0e10]">
      <Cabecalho />
      <FaixaInfo disponiveis={veiculos.length} />
      <main>
        <Catalogo veiculos={veiculos} />
      </main>
      <Rodape />
    </div>
  );
}
