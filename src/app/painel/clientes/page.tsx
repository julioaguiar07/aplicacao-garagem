import { Repeat, UserPlus, Users, Wallet } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { GraficoBarras, GraficoRosca } from "@/components/painel/graficos";
import { NovoCliente, TabelaClientes } from "@/components/painel/clientes";
import { Legenda } from "@/components/legenda";
import { Cartao, Indicador } from "@/components/ui";
import { listarClientes } from "@/lib/consultas/clientes";
import { COR } from "@/lib/cores";
import { ORIGENS_CLIENTE, hojeISO, mesCurto, reaisInteiros, somarMeses } from "@/lib/dominio";

export const metadata = { title: "Clientes" };

export default async function Clientes() {
  const clientes = await listarClientes();
  const hoje = hojeISO();
  const mes = hoje.slice(0, 7);
  const meses = Array.from({ length: 6 }, (_, i) => somarMeses(mes + "-01", i - 5).slice(0, 7));
  const iso = (c: (typeof clientes)[number]) => c.criadoEm.toISOString().slice(0, 7);
  const porMes = meses.map((m) => ({
    mes: mesCurto(m),
    novos: clientes.filter((c) => iso(c) === m).length,
    compraram: clientes.filter((c) => c.ultimaCompra?.startsWith(m)).length,
  }));
  const origens = Object.entries(ORIGENS_CLIENTE)
    .map(([k, nome]) => ({ nome, valor: clientes.filter((c) => (c.origem ?? "outro") === k).length }))
    .filter((o) => o.valor > 0)
    .sort((a, b) => b.valor - a.valor);
  const compradores = clientes.filter((c) => c.compras > 0);
  const recorrentes = clientes.filter((c) => c.compras > 1).length;
  const aReceber = clientes.reduce((s, c) => s + c.aReceber, 0);
  const atrasado = clientes.reduce((s, c) => s + c.atrasado, 0);
  const conversao = clientes.length ? Math.round((compradores.length / clientes.length) * 100) : 0;

  return (
    <>
      <BarraSuperior titulo="Clientes" trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Clientes" }]} acoes={<NovoCliente />} />
      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
          <Indicador destaque rotulo="Clientes cadastrados" icone={Users} valor={clientes.length} rodape={`${compradores.length} já compraram · ${conversao}% de conversão`} />
          <Indicador rotulo="Novos neste mês" icone={UserPlus} valor={porMes.at(-1)!.novos} rodape={`${clientes.filter((c) => !c.compras).length} interessados sem compra`} />
          <Indicador rotulo="Voltaram a comprar" icone={Repeat} valor={recorrentes} rodape="Clientes com mais de uma compra" />
          <Indicador rotulo="Clientes devem à loja" icone={Wallet} valor={reaisInteiros(aReceber)} rodape={atrasado ? <span className="text-perigo">{reaisInteiros(atrasado)} atrasado</span> : "Nada atrasado"} />
        </div>
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
          <Cartao titulo="Novos clientes e compradores por mês">
            <GraficoBarras
              eixoX="mes"
              moeda={false}
              dados={porMes}
              series={[
                { chave: "novos", nome: "Novos cadastros", cor: COR.laranja },
                { chave: "compraram", nome: "Compraram", cor: COR.ambar },
              ]}
              altura={260}
            />
          </Cartao>
          <Cartao titulo="Como os clientes chegam">
            {origens.length ? (
              <>
                <GraficoRosca dados={origens} centro={String(clientes.length)} legendaCentro="clientes" />
                <Legenda itens={origens.map((o) => ({ nome: o.nome, valor: String(o.valor) }))} />
              </>
            ) : (
              <p className="text-sm text-nevoa">Sem clientes ainda.</p>
            )}
          </Cartao>
        </div>
        <TabelaClientes
          clientes={clientes.map((c) => ({
            id: c.id,
            nome: c.nome,
            telefone: c.telefone,
            origem: c.origem,
            interesse: c.interesse,
            compras: c.compras,
            totalComprado: c.totalComprado,
            ultimaCompra: c.ultimaCompra,
            aReceber: c.aReceber,
            atrasado: c.atrasado,
          }))}
        />
      </div>
    </>
  );
}
