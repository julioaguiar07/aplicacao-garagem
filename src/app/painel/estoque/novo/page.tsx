import { BarraSuperior } from "@/components/painel/barra-superior";
import { FormVeiculo } from "@/components/painel/form-veiculo";
import { cadastrarVeiculo } from "@/lib/acoes/veiculos";
import { listarContas } from "@/lib/consultas/caixa";

export const metadata = { title: "Cadastrar veículo" };

export default async function NovoVeiculo() {
  const contas = await listarContas();
  return (
    <>
      <BarraSuperior
        titulo="Cadastrar veículo"
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Estoque", href: "/painel/estoque" }, { rotulo: "Novo" }]}
        acoes={<span />}
      />
      <FormVeiculo acao={cadastrarVeiculo} contas={contas.map((c) => ({ id: c.id, nome: c.nome }))} />
    </>
  );
}
