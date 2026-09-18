import type { FormaPagamento, Lancamento, Venda } from "@/lib/tipos";

/*
 * FICTÍCIO: vendas e lançamentos de demonstração para o Dashboard do protótipo.
 * Os modelos vendidos são os 15 que aparecem como "Vendido" no painel atual;
 * clientes, datas e valores são inventados.
 */

export const VENDAS: Venda[] = [
  { id: 1, veiculo: "Volkswagen Polo Track 2024", cliente: "Ana Beatriz S.", data: "2026-09-12", valor: 84900, lucro: 7200, formaPrincipal: "financiamento_bancario", etapa: "transferencia" },
  { id: 2, veiculo: "Chevrolet Onix Joy 2018", cliente: "Marcos V. Lima", data: "2026-09-08", valor: 52000, lucro: 5100, formaPrincipal: "pix_dinheiro", etapa: "entregue" },
  { id: 3, veiculo: "Volkswagen T-Cross Highline 2025", cliente: "Rafaela Costa", data: "2026-09-03", valor: 149900, lucro: 11800, formaPrincipal: "financiamento_bancario", etapa: "entregue" },
  { id: 4, veiculo: "Honda Civic EX 2020", cliente: "João Pedro A.", data: "2026-08-27", valor: 112000, lucro: 9400, formaPrincipal: "troca", etapa: "entregue" },
  { id: 5, veiculo: "Toyota Hilux SR 2021", cliente: "Agropecuária Serra Verde", data: "2026-08-19", valor: 198000, lucro: 14500, formaPrincipal: "financiamento_bancario", etapa: "entregue" },
  { id: 6, veiculo: "Fiat Strada Endurance 2024", cliente: "Carlos H. Nunes", data: "2026-08-10", valor: 98500, lucro: 8200, formaPrincipal: "financiamento_proprio", etapa: "entregue" },
  { id: 7, veiculo: "Volkswagen Saveiro 2024", cliente: "Francisca M.", data: "2026-07-29", valor: 91000, lucro: 7600, formaPrincipal: "consorcio", etapa: "entregue" },
  { id: 8, veiculo: "Volkswagen Saveiro 2024", cliente: "Pedro Henrique R.", data: "2026-07-18", valor: 89900, lucro: 6900, formaPrincipal: "pix_dinheiro", etapa: "entregue" },
  { id: 9, veiculo: "Volkswagen Nivus 2024", cliente: "Luana Freitas", data: "2026-07-04", valor: 118000, lucro: 9900, formaPrincipal: "financiamento_bancario", etapa: "entregue" },
  { id: 10, veiculo: "Hyundai HB20S Comfort 2025", cliente: "Tiago B.", data: "2026-06-21", valor: 96500, lucro: 7300, formaPrincipal: "cartao", etapa: "entregue" },
  { id: 11, veiculo: "Jeep Renegade S 2022", cliente: "Mariana Alves", data: "2026-06-09", valor: 118500, lucro: 10200, formaPrincipal: "financiamento_bancario", etapa: "entregue" },
  { id: 12, veiculo: "Toyota Corolla XEi 2023", cliente: "Dr. Rodrigo P.", data: "2026-05-24", valor: 142000, lucro: 12100, formaPrincipal: "troca", etapa: "entregue" },
  { id: 13, veiculo: "Honda HR-V EXL 2020", cliente: "Juliana T.", data: "2026-05-11", valor: 109000, lucro: 8800, formaPrincipal: "financiamento_bancario", etapa: "entregue" },
  { id: 14, veiculo: "Toyota Hilux SRX 2021", cliente: "Transportes Oeste", data: "2026-04-26", valor: 219000, lucro: 16300, formaPrincipal: "leasing", etapa: "entregue" },
  { id: 15, veiculo: "Jeep Compass Longitude 2017", cliente: "Fábio Moura", data: "2026-04-08", valor: 86000, lucro: 6400, formaPrincipal: "pix_dinheiro", etapa: "entregue" },
];

export const NOME_FORMA: Record<FormaPagamento, string> = {
  sinal: "Sinal / reserva",
  pix_dinheiro: "À vista (PIX/dinheiro)",
  cartao: "Cartão",
  financiamento_bancario: "Financiamento bancário",
  leasing: "Leasing",
  financiamento_proprio: "Financiamento próprio",
  cheque: "Cheque",
  consorcio: "Consórcio",
  troca: "Com troca",
};

const MESES = ["Abr", "Mai", "Jun", "Jul", "Ago", "Set"];

/** Faturamento e lucro por mês, calculados a partir das vendas acima */
export function serieMensal() {
  return MESES.map((mes, i) => {
    const m = i + 4; // abril = 4
    const doMes = VENDAS.filter((v) => new Date(v.data + "T12:00:00").getMonth() + 1 === m);
    return {
      mes,
      faturamento: doMes.reduce((s, v) => s + v.valor, 0),
      lucro: doMes.reduce((s, v) => s + v.lucro, 0),
      vendas: doMes.length,
    };
  });
}

export function vendasPorForma() {
  const mapa = new Map<FormaPagamento, number>();
  for (const v of VENDAS) mapa.set(v.formaPrincipal, (mapa.get(v.formaPrincipal) ?? 0) + 1);
  return [...mapa.entries()]
    .map(([forma, qtd]) => ({ forma, nome: NOME_FORMA[forma], qtd }))
    .sort((a, b) => b.qtd - a.qtd);
}

export const LANCAMENTOS: Lancamento[] = [
  { id: 1, descricao: "Banco Pan: liberação Polo Track", tipo: "entrada", valor: 64900, vencimento: "2026-09-19", status: "previsto", categoria: "Venda de veículo" },
  { id: 2, descricao: "Retorno bancário Polo Track (R2)", tipo: "entrada", valor: 2596, vencimento: "2026-09-25", status: "previsto", categoria: "Retorno de financiamento" },
  { id: 3, descricao: "Parcela 2/12, Strada (carnê)", tipo: "entrada", valor: 3240, vencimento: "2026-09-15", status: "atrasado", categoria: "Financiamento próprio" },
  { id: 4, descricao: "Aluguel do galpão", tipo: "saida", valor: 6500, vencimento: "2026-09-20", status: "previsto", categoria: "Despesa fixa" },
  { id: 5, descricao: "Despachante: transferência Polo Track", tipo: "saida", valor: 780, vencimento: "2026-09-22", status: "previsto", categoria: "Custo de venda" },
  { id: 6, descricao: "Parcela 3/12, Strada (carnê)", tipo: "entrada", valor: 3240, vencimento: "2026-10-15", status: "previsto", categoria: "Financiamento próprio" },
];

/** Saldo projetado para os próximos 90 dias (demonstração) */
export const SALDO_PROJETADO = [
  { dia: "18/09", saldo: 128400 },
  { dia: "25/09", saldo: 189200 },
  { dia: "02/10", saldo: 176900 },
  { dia: "09/10", saldo: 181300 },
  { dia: "16/10", saldo: 184500 },
  { dia: "23/10", saldo: 171800 },
  { dia: "30/10", saldo: 176200 },
  { dia: "06/11", saldo: 179400 },
  { dia: "13/11", saldo: 182600 },
  { dia: "20/11", saldo: 169900 },
  { dia: "27/11", saldo: 173100 },
  { dia: "04/12", saldo: 176300 },
  { dia: "11/12", saldo: 179500 },
];

export const ATIVIDADES = [
  { quando: "2026-09-18T09:30:00-03:00", texto: "Gasto lançado no HB20 2022", detalhe: "Higienização interna · R$ 280" },
  { quando: "2026-09-17T17:16:00-03:00", texto: "HB20 2022 cadastrado", detalhe: "Compra de particular" },
  { quando: "2026-09-17T15:40:00-03:00", texto: "Titano Volcano publicado na vitrine" },
  { quando: "2026-09-12T14:05:00-03:00", texto: "Venda do Polo Track fechada", detalhe: "Financiamento Banco Pan" },
  { quando: "2026-09-08T10:12:00-03:00", texto: "Onix Joy entregue", detalhe: "Checklist de entrega assinado" },
];
