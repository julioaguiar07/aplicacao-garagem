import "server-only";
import { and, asc, desc, eq, inArray, ne, sql } from "drizzle-orm";
import { banco, schema } from "@/db";
import { capas, checklistDocumentos, nomeVeiculo } from "./veiculos";
import { diasEntre, statusLancamento } from "@/lib/dominio";

const { vendas, veiculos, clientes, pagamentos, custosVenda, lancamentos, gastos, documentos, eventos } = schema;

type Pagamento = typeof pagamentos.$inferSelect;

/** Taxa de cartão retida pela maquininha, em centavos */
export function taxaCartao(p: Pagamento) {
  if (p.forma !== "cartao") return 0;
  return Math.round((p.valor * Number(p.detalhes.taxaPct ?? 0)) / 100);
}

/** Comissão (retorno) paga pelo banco à loja */
export function retornoBancario(p: Pagamento) {
  return p.forma === "financiamento_bancario" ? Number(p.detalhes.retorno ?? 0) : 0;
}

/**
 * Lucro da venda: preço final − custo do carro − gastos de preparação − custos da venda
 * − taxas de cartão + retorno bancário. Juros do financiamento próprio ficam fora (receita financeira).
 */
export function calcularLucro(a: { precoFinal: number; custo: number; gastos: number; custos: number; pagamentos: Pagamento[] }) {
  const taxas = a.pagamentos.reduce((s, p) => s + taxaCartao(p), 0);
  const retorno = a.pagamentos.reduce((s, p) => s + retornoBancario(p), 0);
  return { lucro: a.precoFinal - a.custo - a.gastos - a.custos - taxas + retorno, taxas, retorno };
}

/** Todas as vendas (sem as canceladas, a não ser que pedido), com lucro e forma principal */
export async function listarVendas(opcoes: { incluirCanceladas?: boolean } = {}) {
  const db = await banco();
  const linhas = await db
    .select({ venda: vendas, veiculo: veiculos, cliente: clientes })
    .from(vendas)
    .innerJoin(veiculos, eq(veiculos.id, vendas.veiculoId))
    .innerJoin(clientes, eq(clientes.id, vendas.clienteId))
    .where(opcoes.incluirCanceladas ? undefined : ne(vendas.etapa, "cancelada"))
    .orderBy(desc(vendas.dataVenda), desc(vendas.id));
  const ids = linhas.map((l) => l.venda.id);
  const veicIds = linhas.map((l) => l.veiculo.id);
  const [pags, custos, somaGastos, mapaCapas] = await Promise.all([
    ids.length ? db.select().from(pagamentos).where(inArray(pagamentos.vendaId, ids)) : [],
    ids.length ? db.select().from(custosVenda).where(inArray(custosVenda.vendaId, ids)) : [],
    veicIds.length
      ? db.select({ veiculoId: gastos.veiculoId, total: sql<number>`sum(${gastos.valor})::int` }).from(gastos).where(inArray(gastos.veiculoId, veicIds)).groupBy(gastos.veiculoId)
      : [],
    capas(veicIds),
  ]);
  const gastoPor = new Map(somaGastos.map((g) => [g.veiculoId, g.total]));
  return linhas.map(({ venda, veiculo, cliente }) => {
    const pagsVenda = pags.filter((p) => p.vendaId === venda.id);
    const custosTotal = custos.filter((c) => c.vendaId === venda.id).reduce((s, c) => s + c.valor, 0);
    const gastosTotal = gastoPor.get(veiculo.id) ?? 0;
    const { lucro, retorno } = calcularLucro({ precoFinal: venda.precoFinal, custo: veiculo.custo, gastos: gastosTotal, custos: custosTotal, pagamentos: pagsVenda });
    const principal = [...pagsVenda].sort((a, b) => b.valor - a.valor)[0];
    return {
      venda,
      veiculo,
      cliente,
      nomeVeiculo: `${nomeVeiculo(veiculo)} ${veiculo.anoModelo}`,
      capa: mapaCapas.get(veiculo.id),
      pagamentos: pagsVenda,
      formaPrincipal: principal?.forma ?? null,
      lucro,
      retorno,
      custoTotal: veiculo.custo + gastosTotal + custosTotal,
      desconto: Math.max(0, veiculo.preco - venda.precoFinal),
      diasAteVender: diasEntre(veiculo.dataEntrada, venda.dataVenda),
    };
  });
}
export type ItemVenda = Awaited<ReturnType<typeof listarVendas>>[number];

export async function vendaCompleta(id: number) {
  if (!Number.isInteger(id) || id <= 0) return null;
  const db = await banco();
  const [linha] = await db
    .select({ venda: vendas, veiculo: veiculos, cliente: clientes })
    .from(vendas)
    .innerJoin(veiculos, eq(veiculos.id, vendas.veiculoId))
    .innerJoin(clientes, eq(clientes.id, vendas.clienteId))
    .where(eq(vendas.id, id));
  if (!linha) return null;
  const [pags, custos, lancs, gastosVeic, docsVenda, docsVeic, hist, mapaCapas] = await Promise.all([
    db.select().from(pagamentos).where(eq(pagamentos.vendaId, id)).orderBy(asc(pagamentos.id)),
    db.select().from(custosVenda).where(eq(custosVenda.vendaId, id)),
    db.select().from(lancamentos).where(eq(lancamentos.vendaId, id)).orderBy(asc(lancamentos.vencimento), asc(lancamentos.id)),
    db.select().from(gastos).where(eq(gastos.veiculoId, linha.veiculo.id)),
    db.select().from(documentos).where(eq(documentos.vendaId, id)),
    db.select().from(documentos).where(eq(documentos.veiculoId, linha.veiculo.id)),
    db.select().from(eventos).where(eq(eventos.vendaId, id)).orderBy(desc(eventos.criadoEm)),
    capas([linha.veiculo.id]),
  ]);
  // Veículos que entraram como troca nesta venda
  const idsTroca = pags.map((p) => Number(p.detalhes.veiculoTrocaId)).filter(Boolean);
  const trocas = idsTroca.length ? await db.select().from(veiculos).where(inArray(veiculos.id, idsTroca)) : [];
  const totalGastos = gastosVeic.reduce((s, g) => s + g.valor, 0);
  const totalCustos = custos.reduce((s, c) => s + c.valor, 0);
  const calc = calcularLucro({ precoFinal: linha.venda.precoFinal, custo: linha.veiculo.custo, gastos: totalGastos, custos: totalCustos, pagamentos: pags });
  return {
    ...linha,
    capa: mapaCapas.get(linha.veiculo.id),
    pagamentos: pags,
    custos: custos,
    lancamentos: lancs.map((l) => ({ ...l, status: statusLancamento(l) })),
    trocas,
    documentos: docsVenda,
    checklistVeiculo: checklistDocumentos(docsVeic),
    eventos: hist,
    totalGastos,
    totalCustos,
    totalPago: pags.reduce((s, p) => s + p.valor, 0),
    ...calc,
  };
}
export type VendaCompleta = NonNullable<Awaited<ReturnType<typeof vendaCompleta>>>;

export async function vendasDoCliente(clienteId: number) {
  return (await listarVendas({ incluirCanceladas: true })).filter((v) => v.cliente.id === clienteId);
}

export async function temVendaAtiva(veiculoId: number) {
  const db = await banco();
  const r = await db.select({ id: vendas.id }).from(vendas).where(and(eq(vendas.veiculoId, veiculoId), ne(vendas.etapa, "cancelada")));
  return r.length > 0;
}
