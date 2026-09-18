import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  CarFront,
  CircleDollarSign,
  FileWarning,
  Handshake,
  MoreHorizontal,
  TrendingUp,
  AlertTriangle,
  Clock,
  ArrowRight,
} from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { GraficoFormas, GraficoSaldo, GraficoVendas } from "@/components/painel/graficos";
import { FotoCarro } from "@/components/foto-carro";
import { VEICULOS, nomeCompleto, totalGastos } from "@/lib/demo/veiculos";
import { ATIVIDADES, LANCAMENTOS, NOME_FORMA, SALDO_PROJETADO, VENDAS, serieMensal, vendasPorForma } from "@/lib/demo/financeiro";
import { TONS_GRAFICO } from "@/lib/cores";
import { data, diasDesde, pct, reais, reaisInteiros } from "@/lib/formato";
import { cn } from "@/lib/cn";

export const metadata = { title: "Visão geral" };

function variacao(atual: number, anterior: number) {
  return anterior ? ((atual - anterior) / anterior) * 100 : 0;
}

function Selo({ valor, sufixo = "vs agosto" }: { valor: number; sufixo?: string }) {
  const sobe = valor >= 0;
  return (
    <span className="flex items-center gap-1.5 whitespace-nowrap text-xs text-nevoa">
      <span
        className={cn(
          "num inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 font-medium",
          sobe ? "bg-sucesso/12 text-sucesso" : "bg-perigo/12 text-perigo",
        )}
      >
        {sobe ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
        {pct(Math.abs(valor))}
      </span>
      {sufixo}
    </span>
  );
}

function Cartao({ className, children }: { className?: string; children: React.ReactNode }) {
  return <section className={cn("rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5", className)}>{children}</section>;
}

function TituloCartao({ titulo, acao }: { titulo: string; acao?: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="display text-[17px] font-semibold">{titulo}</h2>
      {acao ?? (
        <button className="rounded-lg p-1 text-nevoa hover:bg-chumbo hover:text-giz" aria-label={`Opções de ${titulo}`}>
          <MoreHorizontal size={18} />
        </button>
      )}
    </div>
  );
}

export default function VisaoGeral() {
  const serie = serieMensal();
  const [ago, set] = [serie[4], serie[5]];
  const emEstoque = VEICULOS.filter((v) => v.status !== "vendido");
  const capital = emEstoque.reduce((s, v) => s + v.custo + totalGastos(v), 0);
  const potencial = emEstoque.reduce((s, v) => s + v.preco, 0);
  const diasMedio = emEstoque.reduce((s, v) => s + diasDesde(v.cadastradoEm), 0) / emEstoque.length;
  const formas = vendasPorForma();
  const parados = [...emEstoque]
    .map((v) => ({ v, dias: diasDesde(v.cadastradoEm) }))
    .sort((a, b) => b.dias - a.dias)
    .slice(0, 4);
  const docsPendentes = emEstoque.reduce((s, v) => s + v.documentos.filter((d) => d.status !== "ok").length, 0);
  const docsVencidos = emEstoque.flatMap((v) => v.documentos.filter((d) => d.status === "vencido").map((d) => ({ v, d })));
  const atrasados = LANCAMENTOS.filter((l) => l.status === "atrasado");
  const ticket = set.vendas ? set.faturamento / set.vendas : 0;
  const ticketAgo = ago.vendas ? ago.faturamento / ago.vendas : 0;

  return (
    <>
      <BarraSuperior titulo="Visão geral" trilha={[{ rotulo: "Painel" }, { rotulo: "Setembro de 2026" }]} />

      <div className="grid gap-5 min-[1400px]:grid-cols-[1fr_300px]">
        <div className="min-w-0 space-y-5">
          {/* Indicadores */}
          <div className="grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
            <Cartao className="brilho-laranja relative overflow-hidden">
              <div className="flex items-start justify-between">
                <span className="grid size-9 place-items-center rounded-xl bg-laranja/15 text-laranja">
                  <CircleDollarSign size={18} />
                </span>
              </div>
              <p className="mt-4 text-xs text-nevoa sm:mt-5 sm:text-sm">Faturamento do mês</p>
              <p className="display num mt-1 text-[20px] font-bold leading-none sm:text-[26px]">{reaisInteiros(set.faturamento)}</p>
              <div className="mt-3">
                <Selo valor={variacao(set.faturamento, ago.faturamento)} sufixo="vs agosto" />
              </div>
            </Cartao>

            <Cartao>
              <span className="grid size-9 place-items-center rounded-xl bg-chumbo text-giz">
                <TrendingUp size={18} />
              </span>
              <p className="mt-4 text-xs text-nevoa sm:mt-5 sm:text-sm">Lucro bruto do mês</p>
              <p className="display num mt-1 text-[20px] font-bold leading-none sm:text-[26px]">{reaisInteiros(set.lucro)}</p>
              <div className="mt-3">
                <Selo valor={variacao(set.lucro, ago.lucro)} />
              </div>
            </Cartao>

            <Cartao>
              <span className="grid size-9 place-items-center rounded-xl bg-chumbo text-giz">
                <Handshake size={18} />
              </span>
              <p className="mt-4 text-xs text-nevoa sm:mt-5 sm:text-sm">Vendas no mês</p>
              <p className="display num mt-1 text-[20px] font-bold leading-none sm:text-[26px]">
                {set.vendas}
                <span className="ml-2 text-sm font-normal text-nevoa">ticket {reaisInteiros(ticket)}</span>
              </p>
              <div className="mt-3">
                <Selo valor={variacao(ticket, ticketAgo)} sufixo="ticket vs agosto" />
              </div>
            </Cartao>

            <Cartao>
              <span className="grid size-9 place-items-center rounded-xl bg-chumbo text-giz">
                <CarFront size={18} />
              </span>
              <p className="mt-4 text-xs text-nevoa sm:mt-5 sm:text-sm">Em estoque</p>
              <p className="display num mt-1 text-[20px] font-bold leading-none sm:text-[26px]">
                {emEstoque.length}
                <span className="ml-2 text-sm font-normal text-nevoa">carros</span>
              </p>
              <p className="num mt-3 text-xs text-nevoa">
                {reaisInteiros(capital)} investidos<br />{diasMedio.toFixed(0)} dias no pátio, em média
              </p>
            </Cartao>
          </div>

          {/* Gráfico principal + formas de pagamento */}
          <div className="grid gap-5 xl:grid-cols-[1fr_300px]">
            <Cartao>
              <TituloCartao
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
              />
              <GraficoVendas dados={serie} />
            </Cartao>

            <Cartao>
              <TituloCartao titulo="Como os clientes pagam" />
              <GraficoFormas dados={formas} total={VENDAS.length} />
              <ul className="mt-5 space-y-2">
                {formas.map((f, i) => (
                  <li key={f.forma} className="flex items-center gap-2 text-sm">
                    <span className="size-2 shrink-0 rounded-full" style={{ background: TONS_GRAFICO[i % TONS_GRAFICO.length] }} />
                    <span className="flex-1 text-nevoa">{f.nome}</span>
                    <span className="num font-medium">{f.qtd}</span>
                  </li>
                ))}
              </ul>
            </Cartao>
          </div>

          {/* Estoque parado + saldo projetado */}
          <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
            <Cartao>
              <TituloCartao
                titulo="Há mais tempo no pátio"
                acao={
                  <Link href="/painel/estoque" className="flex items-center gap-1 text-xs text-nevoa hover:text-laranja">
                    Ver estoque <ArrowRight size={14} />
                  </Link>
                }
              />
              <ul className="space-y-3">
                {parados.map(({ v, dias }) => {
                  const nivel = dias >= 90 ? "perigo" : dias >= 45 ? "alerta" : "ok";
                  return (
                    <li key={v.id}>
                      <Link href={`/painel/estoque/${v.id}`} className="group flex items-center gap-3">
                        <FotoCarro foto={v.fotos[0]} alt="" className="h-12 w-16 shrink-0 rounded-xl" sizes="64px" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium group-hover:text-laranja">
                            {nomeCompleto(v)} {v.anoModelo}
                          </p>
                          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-chumbo">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                nivel === "perigo" ? "bg-perigo" : nivel === "alerta" ? "bg-laranja" : "bg-nevoa-2",
                              )}
                              style={{ width: `${Math.min(100, (dias / 90) * 100)}%` }}
                            />
                          </div>
                        </div>
                        <span className={cn("num w-16 text-right text-sm", nivel !== "ok" ? "text-laranja" : "text-nevoa")}>
                          {dias} {dias === 1 ? "dia" : "dias"}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
              <p className="mt-4 text-xs text-nevoa">Alerta em 45 dias, crítico em 90.</p>
            </Cartao>

            <Cartao className="brilho-laranja">
              <TituloCartao titulo="Saldo projetado" />
              <p className="text-sm text-nevoa">Próximos 90 dias, com o que já está previsto no caixa</p>
              <p className="display num mt-2 text-[28px] font-bold">{reaisInteiros(SALDO_PROJETADO.at(-1)!.saldo)}</p>
              <GraficoSaldo dados={SALDO_PROJETADO} />
              <div className="mt-2 grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-xl bg-asfalto/50 p-3">
                  <p className="text-nevoa">Potencial do estoque</p>
                  <p className="num mt-1 text-sm font-semibold">{reaisInteiros(potencial)}</p>
                </div>
                <div className="rounded-xl bg-asfalto/50 p-3">
                  <p className="text-nevoa">Lucro previsto no estoque</p>
                  <p className="num mt-1 text-sm font-semibold text-ambar">{reaisInteiros(potencial - capital)}</p>
                </div>
              </div>
            </Cartao>
          </div>

          {/* Últimas vendas */}
          <Cartao className="p-0">
            <div className="p-5 pb-0">
              <TituloCartao
                titulo="Últimas vendas"
                acao={
                  <Link href="/painel/vendas" className="flex items-center gap-1 text-xs text-nevoa hover:text-laranja">
                    Ver todas <ArrowRight size={14} />
                  </Link>
                }
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead>
                  <tr className="border-y border-linha/60 text-left text-xs text-nevoa">
                    <th className="px-5 py-2.5 font-medium">Veículo</th>
                    <th className="px-3 py-2.5 font-medium">Cliente</th>
                    <th className="px-3 py-2.5 font-medium">Pagamento</th>
                    <th className="px-3 py-2.5 font-medium">Data</th>
                    <th className="px-3 py-2.5 text-right font-medium">Valor</th>
                    <th className="px-5 py-2.5 text-right font-medium">Lucro</th>
                  </tr>
                </thead>
                <tbody>
                  {VENDAS.slice(0, 5).map((v) => (
                    <tr key={v.id} className="border-b border-linha/40 last:border-0 hover:bg-chumbo/40">
                      <td className="px-5 py-3 font-medium">{v.veiculo}</td>
                      <td className="px-3 py-3 text-nevoa">{v.cliente}</td>
                      <td className="px-3 py-3">
                        <span className="rounded-full border border-linha px-2 py-0.5 text-xs text-nevoa">{NOME_FORMA[v.formaPrincipal]}</span>
                      </td>
                      <td className="num px-3 py-3 text-nevoa">{data(v.data + "T12:00:00-03:00")}</td>
                      <td className="num px-3 py-3 text-right">{reais(v.valor)}</td>
                      <td className="num px-5 py-3 text-right text-sucesso">{reais(v.lucro)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Cartao>
        </div>

        {/* Coluna direita: o que precisa de atenção */}
        <aside className="space-y-6 min-[1400px]:border-l min-[1400px]:border-linha/60 min-[1400px]:pl-5">
          <div>
            <h2 className="display mb-3 text-[17px] font-semibold">Precisa de atenção</h2>
            <ul className="space-y-2.5">
              {atrasados.map((l) => (
                <li key={l.id} className="flex gap-3 rounded-2xl border border-perigo/30 bg-perigo/8 p-3">
                  <AlertTriangle size={17} className="mt-0.5 shrink-0 text-perigo" />
                  <div className="text-sm leading-snug">
                    <p className="font-medium">Parcela atrasada</p>
                    <p className="text-nevoa">
                      {l.descricao} · <span className="num">{reais(l.valor)}</span>
                    </p>
                  </div>
                </li>
              ))}
              {docsVencidos.map(({ v, d }) => (
                <li key={v.id + d.tipo}>
                  <Link href={`/painel/estoque/${v.id}?aba=documentos`} className="flex gap-3 rounded-2xl border border-laranja/30 bg-laranja/8 p-3 hover:border-laranja/60">
                    <FileWarning size={17} className="mt-0.5 shrink-0 text-laranja" />
                    <div className="text-sm leading-snug">
                      <p className="font-medium">{d.tipo} vencida</p>
                      <p className="text-nevoa">
                        {nomeCompleto(v)} {v.anoModelo}
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
              {parados
                .filter((p) => p.dias >= 45)
                .map(({ v, dias }) => (
                  <li key={"p" + v.id}>
                    <Link href={`/painel/estoque/${v.id}`} className="flex gap-3 rounded-2xl border border-linha bg-grafite p-3 hover:border-laranja/50">
                      <Clock size={17} className="mt-0.5 shrink-0 text-ambar" />
                      <div className="text-sm leading-snug">
                        <p className="font-medium">{dias} dias no pátio</p>
                        <p className="text-nevoa">
                          {nomeCompleto(v)} · {reaisInteiros(v.custo + totalGastos(v))} parados
                        </p>
                      </div>
                    </Link>
                  </li>
                ))}
              <li className="flex gap-3 rounded-2xl border border-linha bg-grafite p-3">
                <FileWarning size={17} className="mt-0.5 shrink-0 text-nevoa" />
                <p className="text-sm leading-snug">
                  <span className="font-medium">{docsPendentes} documentos pendentes</span>
                  <span className="block text-nevoa">em {emEstoque.filter((v) => v.documentos.some((d) => d.status !== "ok")).length} carros do estoque</span>
                </p>
              </li>
            </ul>
          </div>

          <div>
            <h2 className="display mb-3 text-[17px] font-semibold">Próximos vencimentos</h2>
            <ul className="divide-y divide-linha/50">
              {LANCAMENTOS.filter((l) => l.status === "previsto").map((l) => (
                <li key={l.id} className="flex items-center gap-3 py-2.5 text-sm">
                  <span className="num w-11 shrink-0 text-xs text-nevoa">{data(l.vencimento + "T12:00:00-03:00").slice(0, 5)}</span>
                  <span className="min-w-0 flex-1 truncate">{l.descricao}</span>
                  <span className={cn("num shrink-0", l.tipo === "entrada" ? "text-sucesso" : "text-giz")}>
                    {l.tipo === "entrada" ? "+" : "−"}
                    {reaisInteiros(l.valor)}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="display mb-3 text-[17px] font-semibold">Atividades</h2>
            <ol className="relative space-y-4 border-l border-linha pl-5">
              {ATIVIDADES.map((a) => (
                <li key={a.quando} className="relative text-sm">
                  <span className="absolute -left-[25px] top-1 size-2.5 rounded-full border-2 border-asfalto bg-laranja" />
                  <p className="leading-snug">{a.texto}</p>
                  {a.detalhe && <p className="text-xs text-nevoa">{a.detalhe}</p>}
                  <p className="num mt-0.5 text-[11px] text-nevoa-2">
                    {new Date(a.quando).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "America/Fortaleza" })}
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
