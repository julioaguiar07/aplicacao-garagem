// Vocabulário do negócio, compartilhado entre servidor e interface.

export const STATUS_VEICULO = {
  rascunho: "Rascunho",
  em_preparacao: "Em preparação",
  disponivel: "Disponível",
  reservado: "Reservado",
  vendido: "Vendido",
  consignado: "Consignado",
} as const;
export type StatusVeiculo = keyof typeof STATUS_VEICULO;

export const ORIGEM_VEICULO = {
  compra: "Compra",
  troca: "Troca em venda",
  consignacao: "Consignação",
  leilao: "Leilão",
} as const;
export type OrigemVeiculo = keyof typeof ORIGEM_VEICULO;

export const CATEGORIAS = ["Hatch", "Sedan", "SUV", "Picape", "Coupé", "Utilitário", "Minivan", "Moto"] as const;
export const CAMBIOS = ["Manual", "Automático", "CVT", "Automatizado"] as const;
export const COMBUSTIVEIS = ["Flex", "Gasolina", "Etanol", "Diesel", "Híbrido", "Elétrico", "GNV"] as const;
export const CORES = ["Branco", "Preto", "Prata", "Cinza", "Vermelho", "Azul", "Verde", "Marrom", "Bege", "Amarelo", "Laranja", "Dourado", "Vinho"] as const;

export const OPCIONAIS = [
  "Ar-condicionado",
  "Ar digital",
  "Direção hidráulica",
  "Direção elétrica",
  "Vidros elétricos",
  "Travas elétricas",
  "Alarme",
  "Central multimídia",
  "Android Auto e CarPlay",
  "Câmera de ré",
  "Sensor de estacionamento",
  "Bancos em couro",
  "Teto solar",
  "Rodas de liga leve",
  "Piloto automático",
  "Chave presencial",
  "Airbags laterais",
  "Controle de tração",
  "4x4",
  "Engate",
];

export const DESTAQUES = ["Oferta da semana", "Baixa km", "Único dono", "Revisado", "Laudo aprovado", "Recém-chegado", "Na garantia"];

/** Documentos esperados para todo veículo em estoque (checklist) */
export const TIPOS_DOCUMENTO = ["CRLV", "Recibo de compra (ATPV-e)", "Laudo cautelar", "Consulta de débitos", "Contrato de entrada"];

export const CATEGORIAS_GASTO = ["Preparação", "Mecânica", "Funilaria e pintura", "Estética", "Pneus", "Documentação", "Outros"] as const;

export const ETAPAS_VENDA = {
  negociacao: "Negociação",
  reservado: "Reservado",
  ficha: "Ficha em análise",
  aprovado: "Crédito aprovado",
  contrato: "Contrato assinado",
  transferencia: "Transferência",
  entregue: "Entregue",
  cancelada: "Cancelada",
} as const;
export type EtapaVenda = keyof typeof ETAPAS_VENDA;
export const FLUXO_ETAPAS: EtapaVenda[] = ["negociacao", "reservado", "ficha", "aprovado", "contrato", "transferencia", "entregue"];
/** A partir do contrato o carro passa a "Vendido"; antes disso fica "Reservado" */
export const ETAPAS_VENDIDO: EtapaVenda[] = ["contrato", "transferencia", "entregue"];

export const FORMAS_PAGAMENTO = {
  sinal: "Sinal / reserva",
  pix_dinheiro: "PIX, dinheiro ou TED",
  cartao: "Cartão",
  financiamento_bancario: "Financiamento bancário (CDC)",
  leasing: "Leasing",
  financiamento_proprio: "Financiamento próprio (carnê)",
  cheque: "Cheque",
  consorcio: "Consórcio (carta de crédito)",
  troca: "Veículo na troca",
} as const;
export type FormaPagamento = keyof typeof FORMAS_PAGAMENTO;

export const TIPOS_CUSTO_VENDA = {
  comissao: "Comissão",
  despachante: "Despachante / transferência",
  garantia: "Garantia",
  brinde: "Brinde (tanque, acessórios)",
  outros: "Outros",
} as const;

export const CATEGORIAS_ENTRADA = ["Venda de veículo", "Sinal", "Financiamento próprio", "Retorno de financiamento", "Outras receitas"];
export const CATEGORIAS_SAIDA = [
  "Compra de veículo",
  "Repasse de consignação",
  "Preparação de veículo",
  "Custo de venda",
  "Comissão",
  "Aluguel",
  "Salários",
  "Impostos e taxas",
  "Contas (água, luz, internet)",
  "Marketing",
  "Outras despesas",
];
/** Categorias que entram como despesa operacional no resultado do mês (DRE) */
export const DESPESAS_OPERACIONAIS = ["Aluguel", "Salários", "Impostos e taxas", "Contas (água, luz, internet)", "Marketing", "Outras despesas"];

export const ORIGENS_CLIENTE = {
  loja: "Visitou a loja",
  whatsapp: "WhatsApp",
  instagram: "Instagram",
  indicacao: "Indicação",
  site: "Site",
  outro: "Outro",
} as const;

// ---------- dinheiro (centavos) ----------

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const brlInteiro = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

export const reais = (centavos: number) => brl.format(centavos / 100);
export const reaisInteiros = (centavos: number) => brlInteiro.format(Math.round(centavos / 100));

/** "50.000,00", "50000", "R$ 1.234,5" → centavos; null se inválido */
export function paraCentavos(texto: string | null | undefined): number | null {
  if (!texto) return null;
  let t = String(texto).replace(/R\$|\s/g, "").trim();
  if (!t) return null;
  if (t.includes(",")) t = t.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, "");
  const n = Number(t);
  return Number.isFinite(n) && n >= 0 ? Math.round(n * 100) : null;
}

/** Parcela pela Tabela Price, em centavos */
export function parcelaPrice(centavos: number, taxaMensalPct: number, meses: number) {
  if (meses <= 0) return centavos;
  const i = taxaMensalPct / 100;
  if (i === 0) return Math.round(centavos / meses);
  return Math.round((centavos * i) / (1 - Math.pow(1 + i, -meses)));
}

// ---------- datas (AAAA-MM-DD, fuso de Mossoró) ----------

export function hojeISO() {
  return new Date().toLocaleDateString("en-CA", { timeZone: "America/Fortaleza" });
}

export function somarDias(iso: string, dias: number) {
  const d = new Date(iso + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + dias);
  return d.toISOString().slice(0, 10);
}

export function somarMeses(iso: string, meses: number) {
  const d = new Date(iso + "T12:00:00Z");
  const dia = d.getUTCDate();
  d.setUTCDate(1);
  d.setUTCMonth(d.getUTCMonth() + meses);
  const ultimo = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate();
  d.setUTCDate(Math.min(dia, ultimo));
  return d.toISOString().slice(0, 10);
}

export function diasEntre(deISO: string, ateISO: string) {
  return Math.round((new Date(ateISO + "T12:00:00Z").getTime() - new Date(deISO + "T12:00:00Z").getTime()) / 86_400_000);
}

export function dataBR(iso: string | null | undefined) {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
}

const MESES_CURTOS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const MESES_LONGOS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
/** "2026-09" → "Set/26" */
export const mesCurto = (am: string) => `${MESES_CURTOS[Number(am.slice(5, 7)) - 1]}/${am.slice(2, 4)}`;
/** "2026-09" → "setembro de 2026" */
export const mesLongo = (am: string) => `${MESES_LONGOS[Number(am.slice(5, 7)) - 1]} de ${am.slice(0, 4)}`;

export function slugify(texto: string) {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

/** Status de um lançamento a partir das datas */
export function statusLancamento(l: { pagoEm: string | null; vencimento: string }, hoje = hojeISO()) {
  if (l.pagoEm) return "realizado" as const;
  return l.vencimento < hoje ? ("atrasado" as const) : ("previsto" as const);
}
