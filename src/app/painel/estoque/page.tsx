import { BarraSuperior } from "@/components/painel/barra-superior";
import { GradeEstoque, type CartaoEstoque } from "@/components/painel/grade-estoque";
import { listarVeiculos } from "@/lib/consultas/veiculos";

export const metadata = { title: "Estoque" };

export default async function Estoque({ searchParams }: PageProps<"/painel/estoque">) {
  const sp = await searchParams;
  const lista = await listarVeiculos({ incluirVendidos: true });
  const cartoes: CartaoEstoque[] = lista.map((v) => ({
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
    publicado: v.publicado,
    dias: v.dias,
    pendencias: v.status === "vendido" ? 0 : v.pendencias,
    foto: v.capa?.urlCard ?? null,
  }));

  return (
    <>
      <BarraSuperior titulo="Estoque" trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Estoque" }]} />
      <GradeEstoque veiculos={cartoes} soPendencias={sp.pendencias === "1"} />
    </>
  );
}
