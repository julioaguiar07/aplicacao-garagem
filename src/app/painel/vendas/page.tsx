import Link from "next/link";
import { CircleDollarSign, Handshake, Landmark, Plus, TrendingUp } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { GraficoArea, GraficoBarras, GraficoRosca } from "@/components/painel/graficos";
import { ListaVendas } from "@/components/painel/lista-vendas";
import { FotoCarro } from "@/components/foto-carro";
import { Legenda } from "@/components/legenda";
import { Cartao, Indicador, LinkBotao, MiniIndicador } from "@/components/ui";
import { fechada, indicadores, variacaoPct } from "@/lib/consultas/indicadores";
import { listarVendas } from "@/lib/consultas/vendas";
import { COR } from "@/lib/cores";
import { ETAPAS_VENDA, FLUXO_ETAPAS, FORMAS_PAGAMENTO, type FormaPagamento, mesCurto, reais, reaisInteiros } from "@/lib/dominio";

export const metadata = { title: "Vendas" };

const compacto = (reais: number) => `R$ ${new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 }).format(reais)}`;

export default async function Vendas() {
  const [k, todas] = await Promise.all([indicadores(), listarVendas({ incluirCanceladas: true })]);
  const andamento = todas.filter((v) => v.venda.etapa !== "cancelada" && !fechada(v));
  const colunas = FLUXO_ETAPAS.filter((e) => !["contrato", "transferencia", "entregue"].includes(e) || andamento.some((v) => v.venda.etapa === e));
  const fechadas6 = k.vendas.filter((v) => fechada(v) && v.venda.dataVenda.slice(0, 7) >= k.serie[0].mes);
  const retornoTotal = fechadas6.reduce((s, v) => s + v.retorno, 0);
  // Recebido x a receber por forma de pagamento (6 meses)
  const porForma = new Map<string, number>();
  for (const v of fechadas6) for (const p of v.pagamentos) porForma.set(p.forma, (porForma.get(p.forma) ?? 0) + p.valor);
  const formasValor = [...porForma.entries()].map(([f, valor]) => ({ nome: FORMAS_PAGAMENTO[f as FormaPagamento], valor: valor / 100 })).sort((a, b) => b.valor - a.valor);
  const top = [...fechadas6].sort((a, b) => b.lucro - a.lucro).slice(0, 5);

  return (
    <>
      <BarraSuperior
        titulo="Vendas"
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Vendas" }]}
        acoes={
          <LinkBotao href="/painel/vendas/nova" variante="primario">
            <Plus size={17} /> Nova venda
          </LinkBotao>
        }
      />

      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
          <Indicador destaque rotulo="Faturamento do mês" icone={CircleDollarSign} valor={reaisInteiros(k.atual.faturamento)} variacao={variacaoPct(k.atual.faturamento, k.anterior.faturamento)} />
          <Indicador rotulo="Lucro do mês" icone={TrendingUp} valor={reaisInteiros(k.atual.lucro)} variacao={variacaoPct(k.atual.lucro, k.anterior.lucro)} />
          <Indicador rotulo="Em andamento" icone={Handshake} valor={`${andamento.length}`} rodape={`${reaisInteiros(andamento.reduce((s, v) => s + v.venda.precoFinal, 0))} em negociação`} />
          <Indicador rotulo="Retorno de bancos (6 meses)" icone={Landmark} valor={reaisInteiros(retornoTotal)} rodape={`${k.atual.retorno ? reaisInteiros(k.atual.retorno) : "R$ 0"} neste mês`} />
        </div>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="display text-[17px] font-semibold">Negócios em andamento</h2>
            <span className="text-xs text-nevoa">Clique para abrir e mover de etapa</span>
          </div>
          {andamento.length === 0 ? (
            <p className="rounded-[var(--radius-card)] border border-dashed border-linha p-6 text-center text-sm text-nevoa">
              Nenhuma venda em andamento. <Link href="/painel/vendas/nova" className="text-laranja hover:underline">Registrar uma venda</Link>
            </p>
          ) : (
            <div className="grid auto-cols-[minmax(230px,1fr)] grid-flow-col gap-3 overflow-x-auto pb-2 scrollbar-fina">
              {colunas.map((e) => {
                const itens = andamento.filter((v) => v.venda.etapa === e);
                return (
                  <div key={e} className="rounded-2xl border border-linha/60 bg-grafite/60 p-3">
                    <p className="mb-3 flex items-center justify-between text-sm font-medium">
                      {ETAPAS_VENDA[e]} <span className="num rounded-full bg-chumbo px-2 text-xs text-nevoa">{itens.length}</span>
                    </p>
                    <ul className="space-y-2">
                      {itens.map((v) => (
                        <li key={v.venda.id}>
                          <Link href={`/painel/vendas/${v.venda.id}`} className="group block overflow-hidden rounded-xl border border-linha/70 bg-grafite hover:border-laranja/50">
                            <FotoCarro src={v.capa?.urlCard} alt="" className="aspect-[16/9]" sizes="240px" />
                            <div className="p-3">
                              <p className="truncate text-sm font-medium group-hover:text-laranja">{v.nomeVeiculo}</p>
                              <p className="truncate text-xs text-nevoa">{v.cliente.nome}</p>
                              <p className="num mt-1.5 text-sm font-semibold">{reais(v.venda.precoFinal)}</p>
                            </div>
                          </Link>
                        </li>
                      ))}
                      {itens.length === 0 && <li className="rounded-xl border border-dashed border-linha/60 py-6 text-center text-xs text-nevoa-2">vazio</li>}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <Cartao titulo="Carros vendidos por mês">
            <GraficoBarras
              eixoX="mes"
              moeda={false}
              dados={k.serie.map((m) => ({ mes: mesCurto(m.mes), vendas: m.vendas }))}
              series={[{ chave: "vendas", nome: "Vendas", cor: COR.laranja }]}
              altura={260}
            />
          </Cartao>
          <Cartao titulo="Ticket médio e lucro médio por venda">
            <GraficoArea
              eixoX="mes"
              dados={k.serie.map((m) => ({ mes: mesCurto(m.mes), ticket: m.ticket / 100, lucroMedio: m.vendas ? m.lucro / m.vendas / 100 : 0 }))}
              series={[
                { chave: "ticket", nome: "Ticket médio", cor: COR.laranja },
                { chave: "lucroMedio", nome: "Lucro médio", cor: COR.ambar },
              ]}
              altura={260}
            />
          </Cartao>
        </div>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[320px_1fr_1fr]">
          <Cartao titulo="Dinheiro por forma de pagamento">
            {formasValor.length ? (
              <>
                <GraficoRosca dados={formasValor} moeda centro={compacto(formasValor.reduce((s, f) => s + f.valor, 0))} legendaCentro="em 6 meses" />
                <Legenda itens={formasValor.map((f) => ({ nome: f.nome, valor: reaisInteiros(f.valor * 100) }))} />
              </>
            ) : (
              <p className="text-sm text-nevoa">Sem vendas fechadas.</p>
            )}
          </Cartao>
          <Cartao titulo="Vendas mais lucrativas (6 meses)">
            <ul className="space-y-3">
              {top.map((v, i) => (
                <li key={v.venda.id}>
                  <Link href={`/painel/vendas/${v.venda.id}`} className="flex items-center gap-3 hover:text-laranja">
                    <span className="num w-5 text-sm text-nevoa">{i + 1}</span>
                    <span className="min-w-0 flex-1 truncate text-sm">{v.nomeVeiculo}</span>
                    <span className="num text-sm text-sucesso">{reaisInteiros(v.lucro)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </Cartao>
          <div className="grid grid-cols-2 content-start gap-3">
            <MiniIndicador rotulo="Giro médio" valor={k.giroDias === null ? "—" : `${Math.round(k.giroDias)} dias`} dica="Entrada até a venda" />
            <MiniIndicador rotulo="Desconto médio" valor={k.descontoMedioPct === null ? "—" : `${k.descontoMedioPct.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`} dica="Sobre o anunciado" />
            <MiniIndicador rotulo="Vendas financiadas" valor={k.pctFinanciadas === null ? "—" : `${Math.round(k.pctFinanciadas)}%`} dica="Banco, leasing, carnê, consórcio" />
            <MiniIndicador rotulo="Margem média" valor={k.margemMedia === null ? "—" : `${k.margemMedia.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`} dica="Lucro sobre o preço" />
          </div>
        </div>

        <ListaVendas
          vendas={todas.map((v) => ({
            id: v.venda.id,
            veiculo: v.nomeVeiculo,
            cliente: v.cliente.nome,
            etapa: v.venda.etapa,
            data: v.venda.dataVenda,
            valor: v.venda.precoFinal,
            lucro: v.lucro,
            forma: v.formaPrincipal,
            dias: v.diasAteVender,
          }))}
        />
      </div>
    </>
  );
}
