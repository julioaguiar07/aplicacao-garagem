import "server-only";
import { and, asc, eq, gte, lte } from "drizzle-orm";
import { banco, schema } from "@/db";
import { hojeISO, somarDias, somarMeses, statusLancamento } from "@/lib/dominio";

const { lancamentos, contas, veiculos, clientes } = schema;

export type Lancamento = typeof lancamentos.$inferSelect;
export type StatusLancamento = "previsto" | "realizado" | "atrasado";

export async function listarContas() {
  const db = await banco();
  const [lista, realizados] = await Promise.all([
    db.select().from(contas).orderBy(asc(contas.id)),
    db.select({ contaId: lancamentos.contaId, tipo: lancamentos.tipo, valor: lancamentos.valor, pagoEm: lancamentos.pagoEm }).from(lancamentos),
  ]);
  return lista.map((c) => {
    const saldo = realizados
      .filter((l) => l.contaId === c.id && l.pagoEm)
      .reduce((s, l) => s + (l.tipo === "entrada" ? l.valor : -l.valor), c.saldoInicial);
    return { ...c, saldo };
  });
}

/** Lançamentos com vencimento no período, com nomes de veículo e cliente */
export async function listarLancamentos(filtro: { de: string; ate: string }) {
  const db = await banco();
  const linhas = await db
    .select({ l: lancamentos, veiculo: { id: veiculos.id, marca: veiculos.marca, modelo: veiculos.modelo, ano: veiculos.anoModelo }, cliente: { id: clientes.id, nome: clientes.nome } })
    .from(lancamentos)
    .leftJoin(veiculos, eq(veiculos.id, lancamentos.veiculoId))
    .leftJoin(clientes, eq(clientes.id, lancamentos.clienteId))
    .where(and(gte(lancamentos.vencimento, filtro.de), lte(lancamentos.vencimento, filtro.ate)))
    .orderBy(asc(lancamentos.vencimento), asc(lancamentos.id));
  const hoje = hojeISO();
  return linhas.map(({ l, veiculo, cliente }) => ({ ...l, status: statusLancamento(l, hoje), veiculo, cliente }));
}
export type ItemLancamento = Awaited<ReturnType<typeof listarLancamentos>>[number];

/** Todos os lançamentos (para séries e indicadores) */
export async function todosLancamentos() {
  const db = await banco();
  const hoje = hojeISO();
  return (await db.select().from(lancamentos)).map((l) => ({ ...l, status: statusLancamento(l, hoje) }));
}

/** Entradas e saídas realizadas por mês ("AAAA-MM"), dos últimos n meses até o atual */
export function seriePorMes(lista: Lancamento[], meses = 6, hoje = hojeISO()) {
  const chaves = Array.from({ length: meses }, (_, i) => somarMeses(hoje.slice(0, 7) + "-01", i - meses + 1).slice(0, 7));
  return chaves.map((mes) => {
    const doMes = lista.filter((l) => l.pagoEm?.startsWith(mes));
    const entradas = doMes.filter((l) => l.tipo === "entrada").reduce((s, l) => s + l.valor, 0);
    const saidas = doMes.filter((l) => l.tipo === "saida").reduce((s, l) => s + l.valor, 0);
    return { mes, entradas, saidas, resultado: entradas - saidas };
  });
}

/** Saldo projetado: saldo atual das contas + lançamentos em aberto até cada data (semanal) */
export function projecaoSaldo(saldoAtual: number, lista: Lancamento[], dias = 90, hoje = hojeISO()) {
  const abertos = lista.filter((l) => !l.pagoEm);
  // Atrasados entram como se fossem acontecer hoje
  const pontos: { dia: string; saldo: number }[] = [];
  for (let d = 0; d <= dias; d += 7) {
    const ate = somarDias(hoje, d);
    const saldo = abertos.filter((l) => l.vencimento <= ate).reduce((s, l) => s + (l.tipo === "entrada" ? l.valor : -l.valor), saldoAtual);
    pontos.push({ dia: ate, saldo });
  }
  return pontos;
}

export function totaisPorCategoria(lista: Lancamento[], tipo: "entrada" | "saida") {
  const mapa = new Map<string, number>();
  for (const l of lista) if (l.tipo === tipo) mapa.set(l.categoria, (mapa.get(l.categoria) ?? 0) + l.valor);
  return [...mapa.entries()].map(([categoria, total]) => ({ categoria, total })).sort((a, b) => b.total - a.total);
}
