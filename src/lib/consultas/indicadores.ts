import "server-only";
import { DESPESAS_OPERACIONAIS, ETAPAS_VENDIDO, hojeISO, somarMeses, type EtapaVenda } from "@/lib/dominio";
import { listarVeiculos } from "./veiculos";
import { listarVendas, taxaCartao, type ItemVenda } from "./vendas";
import { listarContas, projecaoSaldo, todosLancamentos } from "./caixa";

const FORMAS_FINANCIADAS = ["financiamento_bancario", "leasing", "financiamento_proprio", "consorcio"];

export const fechada = (v: ItemVenda) => ETAPAS_VENDIDO.includes(v.venda.etapa as EtapaVenda);

function mesesAtras(n: number, hoje = hojeISO()) {
  return somarMeses(hoje.slice(0, 7) + "-01", -n).slice(0, 7);
}

function resumoDoMes(vendas: ItemVenda[], mes: string) {
  const doMes = vendas.filter((v) => fechada(v) && v.venda.dataVenda.startsWith(mes));
  const faturamento = doMes.reduce((s, v) => s + v.venda.precoFinal, 0);
  const lucro = doMes.reduce((s, v) => s + v.lucro, 0);
  return { mes, vendas: doMes.length, faturamento, lucro, ticket: doMes.length ? faturamento / doMes.length : 0, retorno: doMes.reduce((s, v) => s + v.retorno, 0) };
}

export function variacaoPct(atual: number, anterior: number) {
  if (!anterior) return null;
  return ((atual - anterior) / Math.abs(anterior)) * 100;
}

/** Tudo o que o Dashboard e os Relatórios precisam, calculado de uma vez */
export async function indicadores() {
  const hoje = hojeISO();
  const [estoqueLista, vendas, lancs, contas] = await Promise.all([listarVeiculos(), listarVendas(), todosLancamentos(), listarContas()]);

  const estoque = estoqueLista.filter((v) => v.status !== "rascunho");
  const mesAtual = hoje.slice(0, 7);
  const atual = resumoDoMes(vendas, mesAtual);
  const anterior = resumoDoMes(vendas, mesesAtras(1, hoje));
  const serie = Array.from({ length: 6 }, (_, i) => resumoDoMes(vendas, mesesAtras(5 - i, hoje)));

  // Estoque
  const valorEstoque = estoque.reduce((s, v) => s + v.preco, 0);
  const capitalInvestido = estoque.reduce((s, v) => s + v.custo + v.totalGastos, 0);
  const diasMedioPatio = estoque.length ? estoque.reduce((s, v) => s + v.dias, 0) / estoque.length : 0;

  // Vendas fechadas dos últimos 6 meses (base para médias)
  const inicioJanela = mesesAtras(5, hoje);
  const recentes = vendas.filter((v) => fechada(v) && v.venda.dataVenda.slice(0, 7) >= inicioJanela);
  const giroDias = recentes.length ? recentes.reduce((s, v) => s + v.diasAteVender, 0) / recentes.length : null;
  const somaDias = recentes.reduce((s, v) => s + Math.max(1, v.diasAteVender), 0);
  const lucroPorDia = somaDias ? recentes.reduce((s, v) => s + v.lucro, 0) / somaDias : null;
  const lucroMedio = recentes.length ? recentes.reduce((s, v) => s + v.lucro, 0) / recentes.length : null;
  const margemMedia = recentes.length ? (recentes.reduce((s, v) => s + v.lucro, 0) / recentes.reduce((s, v) => s + v.venda.precoFinal, 0)) * 100 : null;
  const descontoMedioPct = recentes.length
    ? (recentes.reduce((s, v) => s + v.desconto, 0) / recentes.reduce((s, v) => s + v.veiculo.preco, 0)) * 100
    : null;
  const pctFinanciadas = recentes.length
    ? (recentes.filter((v) => v.pagamentos.some((p) => FORMAS_FINANCIADAS.includes(p.forma))).length / recentes.length) * 100
    : null;
  const gastoMedioPreparacao = recentes.length ? recentes.reduce((s, v) => s + (v.custoTotal - v.veiculo.custo), 0) / recentes.length : null;

  // Ritmo: vendas por mês nos últimos 3 meses fechados + atual
  const ultimos3 = [1, 2, 3].map((n) => resumoDoMes(vendas, mesesAtras(n, hoje)));
  const vendasMes = ultimos3.reduce((s, m) => s + m.vendas, 0) / 3;
  const coberturaMeses = vendasMes > 0 ? estoque.length / vendasMes : null;

  // Despesas fixas (média 3 meses) e ponto de equilíbrio
  const despesasFixasMes =
    [1, 2, 3]
      .map((n) => mesesAtras(n, hoje))
      .map((mes) => lancs.filter((l) => l.tipo === "saida" && DESPESAS_OPERACIONAIS.includes(l.categoria) && l.vencimento.startsWith(mes)).reduce((s, l) => s + l.valor, 0))
      .reduce((s, x) => s + x, 0) / 3;
  const pontoEquilibrio = lucroMedio && lucroMedio > 0 ? despesasFixasMes / lucroMedio : null;

  // Carteira a receber de clientes (financiamento próprio, cheques) e inadimplência
  const carteira = lancs.filter((l) => l.tipo === "entrada" && !l.pagoEm && l.categoria === "Financiamento próprio");
  const carteiraTotal = carteira.reduce((s, l) => s + l.valor, 0);
  const carteiraAtrasada = carteira.filter((l) => l.status === "atrasado").reduce((s, l) => s + l.valor, 0);

  // Caixa
  const saldoContas = contas.reduce((s, c) => s + c.saldo, 0);
  const projecao = projecaoSaldo(saldoContas, lancs, 90, hoje);
  const aReceber = lancs.filter((l) => l.tipo === "entrada" && !l.pagoEm).reduce((s, l) => s + l.valor, 0);
  const aPagar = lancs.filter((l) => l.tipo === "saida" && !l.pagoEm).reduce((s, l) => s + l.valor, 0);

  // Formas de pagamento (vendas fechadas, 6 meses): quantidade por forma principal
  const formas = new Map<string, number>();
  for (const v of recentes) if (v.formaPrincipal) formas.set(v.formaPrincipal, (formas.get(v.formaPrincipal) ?? 0) + 1);

  return {
    hoje,
    mesAtual,
    atual,
    anterior,
    serie,
    estoque,
    valorEstoque,
    capitalInvestido,
    lucroPotencial: valorEstoque - capitalInvestido,
    diasMedioPatio,
    giroDias,
    lucroPorDia,
    lucroMedio,
    margemMedia,
    descontoMedioPct,
    pctFinanciadas,
    gastoMedioPreparacao,
    vendasMes,
    coberturaMeses,
    despesasFixasMes,
    pontoEquilibrio,
    carteiraTotal,
    carteiraAtrasada,
    inadimplenciaPct: carteiraTotal ? (carteiraAtrasada / carteiraTotal) * 100 : null,
    saldoContas,
    projecao,
    aReceber,
    aPagar,
    formas: [...formas.entries()].map(([forma, qtd]) => ({ forma, qtd })).sort((a, b) => b.qtd - a.qtd),
    vendas,
    lancamentos: lancs,
    emNegociacao: vendas.filter((v) => !fechada(v)),
  };
}

/** Resultado do mês (DRE simplificada), por competência */
export async function dre(mes: string) {
  const [vendas, lancs] = await Promise.all([listarVendas(), todosLancamentos()]);
  const doMes = vendas.filter((v) => fechada(v) && v.venda.dataVenda.startsWith(mes));
  const receita = doMes.reduce((s, v) => s + v.venda.precoFinal, 0);
  const custoVeiculos = doMes.reduce((s, v) => s + v.veiculo.custo, 0);
  const preparacao = doMes.reduce((s, v) => s + (v.custoTotal - v.veiculo.custo), 0); // gastos + custos de venda
  const taxas = doMes.reduce((s, v) => s + v.pagamentos.reduce((t, p) => t + taxaCartao(p), 0), 0);
  const retorno = doMes.reduce((s, v) => s + v.retorno, 0);
  const lucroBruto = receita - custoVeiculos - preparacao - taxas + retorno;
  const doMesL = lancs.filter((l) => l.vencimento.startsWith(mes));
  const despesas = DESPESAS_OPERACIONAIS.map((categoria) => ({
    categoria,
    valor: doMesL.filter((l) => l.tipo === "saida" && l.categoria === categoria).reduce((s, l) => s + l.valor, 0),
  })).filter((d) => d.valor > 0);
  const totalDespesas = despesas.reduce((s, d) => s + d.valor, 0);
  const outrasReceitas = doMesL.filter((l) => l.tipo === "entrada" && l.categoria === "Outras receitas").reduce((s, l) => s + l.valor, 0);
  return {
    mes,
    vendas: doMes,
    receita,
    custoVeiculos,
    preparacao,
    taxas,
    retorno,
    lucroBruto,
    despesas,
    totalDespesas,
    outrasReceitas,
    resultado: lucroBruto - totalDespesas + outrasReceitas,
  };
}
