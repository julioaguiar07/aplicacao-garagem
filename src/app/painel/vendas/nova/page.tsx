import { BarraSuperior } from "@/components/painel/barra-superior";
import { FormVenda } from "@/components/painel/form-venda";
import { Vazio, LinkBotao } from "@/components/ui";
import { listarContas } from "@/lib/consultas/caixa";
import { opcoesClientes } from "@/lib/consultas/clientes";
import { listarVeiculos, nomeVeiculo, precoMinimo } from "@/lib/consultas/veiculos";

export const metadata = { title: "Nova venda" };

export default async function NovaVenda({ searchParams }: PageProps<"/painel/vendas/nova">) {
  const sp = await searchParams;
  const [estoque, clientes, contas] = await Promise.all([listarVeiculos(), opcoesClientes(), listarContas()]);
  const vendaveis = estoque.filter((v) => ["disponivel", "em_preparacao", "consignado"].includes(v.status));
  return (
    <>
      <BarraSuperior titulo="Nova venda" trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Vendas", href: "/painel/vendas" }, { rotulo: "Nova" }]} acoes={<span />} />
      {vendaveis.length === 0 ? (
        <Vazio acao={<LinkBotao href="/painel/estoque/novo" variante="primario">Cadastrar veículo</LinkBotao>}>Nenhum carro disponível para venda.</Vazio>
      ) : (
        <FormVenda
          veiculos={vendaveis.map((v) => ({
            id: v.id,
            nome: `${nomeVeiculo(v)} ${v.anoModelo}`,
            preco: v.preco,
            minimo: precoMinimo(v),
            custo: v.custo,
            gastos: v.totalGastos,
            consignado: v.origem === "consignacao",
          }))}
          clientes={clientes}
          contas={contas.map((c) => ({ id: c.id, nome: c.nome }))}
          veiculoInicial={sp.veiculo ? Number(sp.veiculo) : undefined}
          clienteInicial={sp.cliente ? Number(sp.cliente) : undefined}
        />
      )}
    </>
  );
}
