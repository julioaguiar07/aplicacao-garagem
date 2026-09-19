import Link from "next/link";
import { desc } from "drizzle-orm";
import { AlertTriangle, ArrowRight, CarFront, CircleDollarSign, Clock, FileWarning, Handshake, TrendingUp } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { GraficoArea, GraficoRosca, GraficoSaldo } from "@/components/painel/graficos";
import { FotoCarro } from "@/components/foto-carro";
import { Legenda } from "@/components/legenda";
import { Cartao, Indicador, MiniIndicador, Tabela, td, th, Vazio } from "@/components/ui";
import { banco, schema } from "@/db";
import { indicadores, variacaoPct } from "@/lib/consultas/indicadores";
import { nomeVeiculo } from "@/lib/consultas/veiculos";
import { COR } from "@/lib/cores";
import { ETAPAS_VENDA, FORMAS_PAGAMENTO, type FormaPagamento, dataBR, mesCurto, mesLongo, reais, reaisInteiros } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export const metadata = { title: "Visão geral" };

const pct = (v: number | null, casas = 1) => (v === null ? "—" : `${v.toLocaleString("pt-BR", { maximumFractionDigits: casas })}%`);

export default async function VisaoGeral() {
  const k = await indicadores();
  const db = await banco();
  const atividades = await db.select().from(schema.eventos).orderBy(desc(schema.eventos.criadoEm)).limit(6);

  const parados = [...k.estoque].sort((a, b) => b.dias - a.dias).slice(0, 5);
  const atrasados = k.lancamentos.filter((l) => l.status === "atrasado").sort((a, b) => a.vencimento.localeCompare(b.vencimento));
  const proximos = k.lancamentos.filter((l) => l.status === "previsto").sort((a, b) => a.vencimento.localeCompare(b.vencimento)).slice(0, 6);
  const semDocs = k.estoque.filter((v) => v.pendencias > 0);
  const formas = k.formas.map((f) => ({ nome: FORMAS_PAGAMENTO[f.forma as FormaPagamento] ?? f.forma, valor: f.qtd }));
  const totalFormas = formas.reduce((s, f) => s + f.valor, 0);

  return (
    <>
      <BarraSuperior titulo="Visão geral" trilha={[{ rotulo: "Painel" }, { rotulo: mesLongo(k.mesAtual) }]} />

      <div className="grid grid-cols-1 gap-5 min-[1400px]:grid-cols-[1fr_300px]">
        <div className="min-w-0 space-y-5">
          <div className="grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
            <Indicador destaque rotulo="Faturamento do mês" icone={CircleDollarSign} valor={reaisInteiros(k.atual.faturamento)} variacao={variacaoPct(k.atual.faturamento, k.anterior.faturamento)} />
            <Indicador rotulo="Lucro bruto do mês" icone={TrendingUp} valor={reaisInteiros(k.atual.lucro)} variacao={variacaoPct(k.atual.lucro, k.anterior.lucro)} />
            <Indicador
              rotulo="Vendas no mês"
              icone={Handshake}
              valor={
                <>
                  {k.atual.vendas}
                  <span className="block text-xs font-normal text-nevoa sm:ml-2 sm:inline sm:text-sm">ticket {reaisInteiros(k.atual.ticket)}</span>
                </>
              }
              rodape={k.emNegociacao.length ? `${k.emNegociacao.length} em andamento` : undefined}
            />
            <Indicador
              rotulo="Valor em estoque"
              icone={CarFront}
              valor={reaisInteiros(k.valorEstoque)}
              rodape={
                <>
                  {k.estoque.length} carros · {reaisInteiros(k.capitalInvestido)} investidos
                  <br />
                  <span className="text-ambar">{reaisInteiros(k.lucroPotencial)} de lucro potencial</span>
                </>
              }
            />
          </div>

          <section>
            <h2 className="display mb-3 text-[17px] font-semibold">Indicadores do negócio</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
              <MiniIndicador rotulo="Giro médio" valor={k.giroDias === null ? "—" : `${Math.round(k.giroDias)} dias`} dica="Da entrada do carro até a venda (6 meses)" />
              <MiniIndicador rotulo="Lucro por dia de pátio" valor={k.lucroPorDia === null ? "—" : reaisInteiros(k.lucroPorDia)} dica="Quanto cada dia parado rendeu nas vendas" />
              <MiniIndicador rotulo="Margem média" valor={pct(k.margemMedia)} dica="Lucro sobre o preço de venda" tom={k.margemMedia !== null && k.margemMedia < 5 ? "alerta" : undefined} />
              <MiniIndicador rotulo="Desconto médio" valor={pct(k.descontoMedioPct)} dica="Entre o anunciado e o fechado" />
              <MiniIndicador rotulo="Vendas financiadas" valor={pct(k.pctFinanciadas, 0)} dica="Banco, leasing, carnê ou consórcio" />
              <MiniIndicador
                rotulo="Ponto de equilíbrio"
                valor={k.pontoEquilibrio === null ? "—" : `${k.pontoEquilibrio.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} carros/mês`}
                dica={`Para cobrir ${reaisInteiros(k.despesasFixasMes)} de despesas fixas`}
              />
              <MiniIndicador
                rotulo="Cobertura do estoque"
                valor={k.coberturaMeses === null ? "—" : `${k.coberturaMeses.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} meses`}
                dica={`Vendendo ${k.vendasMes.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} carros por mês`}
                tom={k.coberturaMeses !== null && k.coberturaMeses > 3 ? "alerta" : undefined}
              />
              <MiniIndicador
                rotulo="A receber de clientes"
                valor={reaisInteiros(k.carteiraTotal)}
                dica={k.carteiraAtrasada ? `${reaisInteiros(k.carteiraAtrasada)} atrasado (${pct(k.inadimplenciaPct, 0)})` : "Carnês em dia"}
                tom={k.carteiraAtrasada ? "ruim" : undefined}
              />
              <MiniIndicador rotulo="Preparação média" valor={k.gastoMedioPreparacao === null ? "—" : reaisInteiros(k.gastoMedioPreparacao)} dica="Gastos e custos de venda por carro vendido" />
              <MiniIndicador rotulo="Saldo nas contas" valor={reaisInteiros(k.saldoContas)} dica={`${reaisInteiros(k.aReceber)} a receber · ${reaisInteiros(k.aPagar)} a pagar`} />
            </div>
          </section>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <Cartao
              titulo="Faturamento e lucro"
              acao={
                <div className="flex items-center gap-4 text-xs text-nevoa">
                  <span className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-laranja" /> Faturamento
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-ambar" /> Lucro
                  </span>
                </div>
              }
            >
              <GraficoArea
                eixoX="mes"
                dados={k.serie.map((m) => ({ mes: mesCurto(m.mes), faturamento: m.faturamento / 100, lucro: m.lucro / 100 }))}
                series={[
                  { chave: "faturamento", nome: "Faturamento", cor: COR.laranja },
                  { chave: "lucro", nome: "Lucro", cor: COR.ambar },
                ]}
                altura={320}
              />
            </Cartao>

            <Cartao titulo="Como os clientes pagam">
              {formas.length ? (
                <>
                  <GraficoRosca dados={formas} centro={String(totalFormas)} legendaCentro="vendas em 6 meses" />
                  <Legenda itens={formas.map((f) => ({ nome: f.nome, valor: String(f.valor) }))} />
                </>
              ) : (
                <p className="text-sm text-nevoa">Nenhuma venda fechada ainda.</p>
              )}
            </Cartao>
          </div>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            <Cartao
              titulo="Há mais tempo no pátio"
              acao={
                <Link href="/painel/estoque" className="flex items-center gap-1 text-xs text-nevoa hover:text-laranja">
                  Ver estoque <ArrowRight size={14} />
                </Link>
              }
            >
              {parados.length === 0 ? (
                <p className="text-sm text-nevoa">Estoque vazio.</p>
              ) : (
                <ul className="space-y-3">
                  {parados.map((v) => {
                    const nivel = v.dias >= 90 ? "perigo" : v.dias >= 45 ? "alerta" : "ok";
                    return (
                      <li key={v.id}>
                        <Link href={`/painel/estoque/${v.id}`} className="group flex items-center gap-3">
                          <FotoCarro src={v.capa?.urlCard} alt="" className="h-12 w-16 shrink-0 rounded-xl" sizes="64px" />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium group-hover:text-laranja">
                              {nomeVeiculo(v)} {v.anoModelo}
                            </p>
                            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-chumbo">
                              <div
                                className={cn("h-full rounded-full", nivel === "perigo" ? "bg-perigo" : nivel === "alerta" ? "bg-laranja" : "bg-nevoa-2")}
                                style={{ width: `${Math.max(3, Math.min(100, (v.dias / 90) * 100))}%` }}
                              />
                            </div>
                          </div>
                          <span className={cn("num w-20 text-right text-sm", nivel !== "ok" ? "text-laranja" : "text-nevoa")}>
                            {v.dias === 0 ? "hoje" : `${v.dias} ${v.dias === 1 ? "dia" : "dias"}`}
                          </span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
              <p className="mt-4 text-xs text-nevoa">Alerta em 45 dias, crítico em 90. Média atual: {Math.round(k.diasMedioPatio)} dias.</p>
            </Cartao>

            <Cartao className="brilho-laranja" titulo="Saldo projetado">
              <p className="text-sm text-nevoa">Saldo das contas somado ao que está previsto para os próximos 90 dias</p>
              <p className="display num mt-2 text-[28px] font-bold">{reaisInteiros(k.projecao.at(-1)?.saldo ?? 0)}</p>
              <GraficoSaldo dados={k.projecao.map((p) => ({ dia: dataBR(p.dia).slice(0, 5), saldo: p.saldo / 100 }))} />
              <div className="mt-2 grid grid-cols-2 gap-3 text-xs">
                <Link href="/painel/caixa?filtro=receber" className="rounded-xl bg-asfalto/50 p-3 hover:bg-asfalto/80">
                  <p className="text-nevoa">A receber</p>
                  <p className="num mt-1 text-sm font-semibold text-sucesso">{reaisInteiros(k.aReceber)}</p>
                </Link>
                <Link href="/painel/caixa?filtro=pagar" className="rounded-xl bg-asfalto/50 p-3 hover:bg-asfalto/80">
                  <p className="text-nevoa">A pagar</p>
                  <p className="num mt-1 text-sm font-semibold">{reaisInteiros(k.aPagar)}</p>
                </Link>
              </div>
            </Cartao>
          </div>

          <Cartao
            className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5"
            titulo="Últimas vendas"
            acao={
              <Link href="/painel/vendas" className="flex items-center gap-1 text-xs text-nevoa hover:text-laranja">
                Ver todas <ArrowRight size={14} />
              </Link>
            }
          >
            {k.vendas.length === 0 ? (
              <div className="px-5 pb-5">
                <Vazio>Nenhuma venda registrada.</Vazio>
              </div>
            ) : (
              <Tabela>
                <thead>
                  <tr className="border-y border-linha/60">
                    <th className={th}>Veículo</th>
                    <th className={th}>Cliente</th>
                    <th className={th}>Etapa</th>
                    <th className={th}>Data</th>
                    <th className={cn(th, "text-right")}>Valor</th>
                    <th className={cn(th, "text-right")}>Lucro</th>
                  </tr>
                </thead>
                <tbody>
                  {k.vendas.slice(0, 6).map((v) => (
                    <tr key={v.venda.id} className="border-b border-linha/40 last:border-0 hover:bg-chumbo/40">
                      <td className={cn(td, "font-medium")}>
                        <Link href={`/painel/vendas/${v.venda.id}`} className="hover:text-laranja">
                          {v.nomeVeiculo}
                        </Link>
                      </td>
                      <td className={cn(td, "text-nevoa")}>{v.cliente.nome}</td>
                      <td className={td}>
                        <span className="rounded-full border border-linha px-2 py-0.5 text-xs text-nevoa">{ETAPAS_VENDA[v.venda.etapa as keyof typeof ETAPAS_VENDA]}</span>
                      </td>
                      <td className={cn(td, "num text-nevoa")}>{dataBR(v.venda.dataVenda)}</td>
                      <td className={cn(td, "num text-right")}>{reais(v.venda.precoFinal)}</td>
                      <td className={cn(td, "num text-right", v.lucro >= 0 ? "text-sucesso" : "text-perigo")}>{reais(v.lucro)}</td>
                    </tr>
                  ))}
                </tbody>
              </Tabela>
            )}
          </Cartao>
        </div>

        <aside className="space-y-6 min-[1400px]:border-l min-[1400px]:border-linha/60 min-[1400px]:pl-5">
          <div>
            <h2 className="display mb-3 text-[17px] font-semibold">Precisa de atenção</h2>
            <ul className="space-y-2.5">
              {atrasados.slice(0, 4).map((l) => (
                <li key={l.id}>
                  <Link href="/painel/caixa?filtro=atrasados" className="flex gap-3 rounded-2xl border border-perigo/30 bg-perigo/8 p-3 hover:border-perigo/60">
                    <AlertTriangle size={17} className="mt-0.5 shrink-0 text-perigo" />
                    <div className="text-sm leading-snug">
                      <p className="font-medium">{l.tipo === "entrada" ? "Recebimento atrasado" : "Pagamento atrasado"}</p>
                      <p className="text-nevoa">
                        {l.descricao} · <span className="num">{reais(l.valor)}</span>
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
              {k.estoque
                .filter((v) => v.dias >= 45)
                .map((v) => (
                  <li key={"p" + v.id}>
                    <Link href={`/painel/estoque/${v.id}`} className="flex gap-3 rounded-2xl border border-linha bg-grafite p-3 hover:border-laranja/50">
                      <Clock size={17} className="mt-0.5 shrink-0 text-ambar" />
                      <div className="text-sm leading-snug">
                        <p className="font-medium">{v.dias} dias no pátio</p>
                        <p className="text-nevoa">
                          {nomeVeiculo(v)} · {reaisInteiros(v.custo + v.totalGastos)} parados
                        </p>
                      </div>
                    </Link>
                  </li>
                ))}
              {k.emNegociacao.map((v) => (
                <li key={"n" + v.venda.id}>
                  <Link href={`/painel/vendas/${v.venda.id}`} className="flex gap-3 rounded-2xl border border-laranja/30 bg-laranja/8 p-3 hover:border-laranja/60">
                    <Handshake size={17} className="mt-0.5 shrink-0 text-laranja" />
                    <div className="text-sm leading-snug">
                      <p className="font-medium">{ETAPAS_VENDA[v.venda.etapa as keyof typeof ETAPAS_VENDA]}</p>
                      <p className="text-nevoa">
                        {v.nomeVeiculo} · {v.cliente.nome}
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
              {semDocs.length > 0 && (
                <li>
                  <Link href="/painel/estoque?pendencias=1" className="flex gap-3 rounded-2xl border border-linha bg-grafite p-3 hover:border-laranja/50">
                    <FileWarning size={17} className="mt-0.5 shrink-0 text-nevoa" />
                    <p className="text-sm leading-snug">
                      <span className="font-medium">{semDocs.reduce((s, v) => s + v.pendencias, 0)} documentos pendentes</span>
                      <span className="block text-nevoa">em {semDocs.length} carros do estoque</span>
                    </p>
                  </Link>
                </li>
              )}
              {!atrasados.length && !k.emNegociacao.length && !semDocs.length && !k.estoque.some((v) => v.dias >= 45) && (
                <li className="text-sm text-nevoa">Tudo em dia.</li>
              )}
            </ul>
          </div>

          <div>
            <h2 className="display mb-3 text-[17px] font-semibold">Próximos vencimentos</h2>
            {proximos.length === 0 ? (
              <p className="text-sm text-nevoa">Nada previsto.</p>
            ) : (
              <ul className="divide-y divide-linha/50">
                {proximos.map((l) => (
                  <li key={l.id} className="flex items-center gap-3 py-2.5 text-sm">
                    <span className="num w-11 shrink-0 text-xs text-nevoa">{dataBR(l.vencimento).slice(0, 5)}</span>
                    <span className="min-w-0 flex-1 truncate" title={l.descricao}>
                      {l.descricao}
                    </span>
                    <span className={cn("num shrink-0", l.tipo === "entrada" ? "text-sucesso" : "text-giz")}>
                      {l.tipo === "entrada" ? "+" : "−"}
                      {reaisInteiros(l.valor)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <h2 className="display mb-3 text-[17px] font-semibold">Atividades</h2>
            <ol className="relative space-y-4 border-l border-linha pl-5">
              {atividades.map((a) => (
                <li key={a.id} className="relative text-sm">
                  <span className="absolute -left-[25px] top-1 size-2.5 rounded-full border-2 border-asfalto bg-laranja" />
                  <p className="leading-snug">{a.titulo}</p>
                  {a.detalhe && <p className="text-xs text-nevoa">{a.detalhe}</p>}
                  <p className="num mt-0.5 text-[11px] text-nevoa-2">
                    {a.criadoEm.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "America/Fortaleza" })}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>
    </>
  );
}
