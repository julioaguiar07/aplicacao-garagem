import { BarraSuperior } from "@/components/painel/barra-superior";
import { GradeEstoque, type CartaoEstoque } from "@/components/painel/grade-estoque";
import { VEICULOS, pendencias } from "@/lib/demo/veiculos";
import { diasDesde } from "@/lib/formato";

export const metadata = { title: "Estoque" };

export default function Estoque() {
  const cartoes: CartaoEstoque[] = VEICULOS.map((v) => ({
    id: v.id,
    marca: v.marca,
    modelo: v.modelo,
    versao: v.versao,
    ano: v.anoModelo,
    km: v.km,
    cambio: v.cambio,
    combustivel: v.combustivel,
    categoria: v.categoria,
    preco: v.preco,
    status: v.status,
    dias: diasDesde(v.cadastradoEm),
    pendencias: pendencias(v).total,
    foto: v.fotos.find((f) => f.capa) ?? v.fotos[0],
  }));

  return (
    <>
      <BarraSuperior titulo="Estoque" trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Estoque" }]} />
      <GradeEstoque veiculos={cartoes} />
    </>
  );
}
