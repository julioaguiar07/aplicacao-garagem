import Link from "next/link";
import { AlertTriangle, ArrowDownLeft, ArrowUpRight, ChevronLeft, ChevronRight, Landmark, Wallet } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { GraficoArea, GraficoBarras, GraficoRosca } from "@/components/painel/graficos";
import { EditarConta, type FiltroCaixa, NovoLancamento, TabelaLancamentos } from "@/components/painel/caixa";
import { Legenda } from "@/components/legenda";
import { Cartao, Indicador } from "@/components/ui";
import { listarContas, listarLancamentos, projecaoSaldo, seriePorMes, todosLancamentos, totaisPorCategoria } from "@/lib/consultas/caixa";
import { urlArquivo } from "@/lib/armazenamento";
import { COR } from "@/lib/cores";
import { dataBR, hojeISO, mesCurto, mesLongo, reais, reaisInteiros, somarDias, somarMeses } from "@/lib/dominio";

export const metadata = { title: "Fluxo de caixa" };

const FILTROS_GLOBAIS: FiltroCaixa[] = ["receber", "pagar", "atrasados"];

export default async function Caixa({ searchParams }: PageProps<"/painel/caixa">) {
  const sp = await searchParams;
  const hoje = hojeISO();
  const mes = typeof sp.mes === "string" && /^\d{4}-\d{2}$/.test(sp.mes) ? sp.mes : hoje.slice(0, 7);
  const filtro = (typeof sp.filtro === "string" && ["todos", "receber", "pagar", "atrasados", "realizados"].includes(sp.filtro) ? sp.filtro : "todos") as FiltroCaixa;
  const global = FILTROS_GLOBAIS.includes(filtro);

  const inicio = `${mes}-01`;
  const fim = somarDias(somarMeses(inicio, 1), -1);
  const [contas, todos] = await Promise.all([listarContas(), todosLancamentos()]);
  const doPeriodo = global ? await listarLancamentos({ de: "2000-01-01", ate: "2100-01-01" }) : await listarLancamentos({ de: inicio, ate: fim });
  const nomeConta = new Map(contas.map((c) => [c.id, c.nome]));

  const saldo = contas.reduce((s, c) => s + c.saldo, 0);
  const ate30 = somarDias(hoje, 30);
  const receber30 = todos.filter((l) => l.tipo === "entrada" && !l.pagoEm && l.vencimento <= ate30).reduce((s, l) => s + l.valor, 0);
  const pagar30 = todos.filter((l) => l.tipo === "saida" && !l.pagoEm && l.vencimento <= ate30).reduce((s, l) => s + l.valor, 0);
  const atrasados = todos.filter((l) => l.status === "atrasado");
  const serie = seriePorMes(todos, 6, hoje);
  const projecao = projecaoSaldo(saldo, todos, 90, hoje);
  const saidasMes = global ? [] : totaisPorCategoria(doPeriodo, "saida");

  return (
    <>
      <BarraSuperior titulo="Fluxo de caixa" trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Fluxo de caixa" }]} acoes={<NovoLancamento contas={contas} />} />
      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
          <Indicador destaque rotulo="Saldo nas contas" icone={Wallet} valor={reaisInteiros(saldo)} rodape={`${contas.length} conta(s)`} />
          <Indicador rotulo="A receber em 30 dias" icone={ArrowDownLeft} valor={<span className="text-sucesso">{reaisInteiros(receber30)}</span>} />
          <Indicador rotulo="A pagar em 30 dias" icone={ArrowUpRight} valor={reaisInteiros(pagar30)} rodape={`Saldo previsto em 30 dias: ${reaisInteiros(saldo + receber30 - pagar30)}`} />
          <Indicador
            rotulo="Atrasados"
            icone={AlertTriangle}
            valor={<span className={atrasados.length ? "text-perigo" : ""}>{atrasados.length}</span>}
            rodape={
              atrasados.length ? (
                <Link href="/painel/caixa?filtro=atrasados" className="text-perigo hover:underline">
                  {reaisInteiros(atrasados.reduce((s, l) => s + l.valor, 0))} em aberto
                </Link>
              ) : (
                "Nada atrasado"
              )
            }
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {contas.map((c) => (
            <div key={c.id} className="rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-4">
              <div className="flex items-center gap-2 text-sm text-nevoa">
                {c.tipo === "caixa" ? <Wallet size={15} /> : <Landmark size={15} />}
                <span className="flex-1 truncate">{c.nome}</span>
                <EditarConta conta={c} />
              </div>
              <p className={`display num mt-3 text-2xl font-bold ${c.saldo < 0 ? "text-perigo" : ""}`}>{reais(c.saldo)}</p>
            </div>
          ))}
          <EditarConta />
        </div>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <Cartao titulo="Entradas e saídas realizadas">
            <GraficoBarras
              eixoX="mes"
              dados={serie.map((m) => ({ mes: mesCurto(m.mes), entradas: m.entradas / 100, saidas: m.saidas / 100 }))}
              series={[
                { chave: "entradas", nome: "Entradas", cor: COR.verde },
                { chave: "saidas", nome: "Saídas", cor: COR.laranja },
              ]}
              altura={270}
            />
          </Cartao>
          <Cartao titulo="Saldo projetado (90 dias)">
            <GraficoArea eixoX="dia" dados={projecao.map((p) => ({ dia: dataBR(p.dia).slice(0, 5), saldo: p.saldo / 100 }))} series={[{ chave: "saldo", nome: "Saldo previsto", cor: COR.laranja }]} altura={270} />
          </Cartao>
        </div>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
          <Cartao className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5"
            titulo={global ? "Lançamentos em aberto (todas as datas)" : `Lançamentos de ${mesLongo(mes)}`}
            acao={
              !global && (
                <div className="flex items-center gap-1">
                  <Link href={`/painel/caixa?mes=${somarMeses(inicio, -1).slice(0, 7)}`} className="rounded-lg p-1.5 text-nevoa hover:bg-chumbo hover:text-giz" aria-label="Mês anterior">
                    <ChevronLeft size={16} />
                  </Link>
                  <span className="num w-16 text-center text-sm">{mesCurto(mes)}</span>
                  <Link href={`/painel/caixa?mes=${somarMeses(inicio, 1).slice(0, 7)}`} className="rounded-lg p-1.5 text-nevoa hover:bg-chumbo hover:text-giz" aria-label="Próximo mês">
                    <ChevronRight size={16} />
                  </Link>
                </div>
              )
            }
          >
            {global && (
              <p className="px-5 pb-3 text-xs text-nevoa">
                Mostrando tudo o que está em aberto. <Link href="/painel/caixa" className="text-laranja hover:underline">Voltar para o mês atual</Link>
              </p>
            )}
            <TabelaLancamentos
              key={`${mes}-${filtro}`}
              filtroInicial={filtro}
              contas={contas}
              linhas={doPeriodo.map((l) => ({
                id: l.id,
                tipo: l.tipo,
                descricao: l.descricao,
                categoria: l.categoria,
                valor: l.valor,
                vencimento: l.vencimento,
                pagoEm: l.pagoEm,
                status: l.status,
                contaNome: l.contaId ? (nomeConta.get(l.contaId) ?? null) : null,
                vendaId: l.vendaId,
                veiculo: l.veiculo?.id ? { id: l.veiculo.id, nome: `${l.veiculo.modelo} ${l.veiculo.ano}` } : null,
                cliente: l.cliente?.id ? { id: l.cliente.id, nome: l.cliente.nome } : null,
                recorrente: Boolean(l.grupoRecorrencia),
                comprovante: l.comprovanteChave ? urlArquivo(l.comprovanteChave) : null,
              }))}
            />
          </Cartao>
          {!global && (
            <Cartao titulo={`Saídas por categoria · ${mesCurto(mes)}`}>
              {saidasMes.length ? (
                <>
                  <GraficoRosca dados={saidasMes.map((c) => ({ nome: c.categoria, valor: c.total / 100 }))} moeda centro={`R$ ${new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 }).format(saidasMes.reduce((s, c) => s + c.total, 0) / 100)}`} legendaCentro="de saídas" />
                  <Legenda itens={saidasMes.map((c) => ({ nome: c.categoria, valor: reaisInteiros(c.total) }))} />
                </>
              ) : (
                <p className="text-sm text-nevoa">Sem saídas neste mês.</p>
              )}
            </Cartao>
          )}
        </div>
      </div>
    </>
  );
}
