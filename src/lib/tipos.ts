// Modelo de domínio da v2. Espelha o schema que será criado no Prisma na Fase 1.

export type StatusVeiculo =
  | "rascunho"
  | "em_preparacao"
  | "disponivel"
  | "reservado"
  | "vendido"
  | "consignado";

export type Categoria = "Hatch" | "Sedan" | "SUV" | "Picape" | "Coupé" | "Utilitário";
export type Cambio = "Automático" | "Manual" | "CVT";
export type Combustivel = "Flex" | "Gasolina" | "Etanol" | "Diesel" | "Híbrido" | "Elétrico";
export type OrigemVeiculo = "compra" | "troca" | "consignacao" | "leilao";

export interface FotoVeiculo {
  /** Foto original tratada (sem EXIF/GPS), para a galeria */
  original: string;
  /** Foto completa no formato do card (4:3) */
  card: string;
  capa?: boolean;
}

export type StatusDocumento = "ok" | "pendente" | "vencido";

export interface DocumentoVeiculo {
  tipo: string;
  status: StatusDocumento;
  arquivo?: string;
  validade?: string;
  enviadoEm?: string;
}

export interface GastoVeiculo {
  id: string;
  data: string;
  categoria: "Preparação" | "Mecânica" | "Funilaria e pintura" | "Estética" | "Pneus" | "Documentação" | "Outros";
  descricao: string;
  valor: number;
  comNota: boolean;
}

export interface EventoVeiculo {
  data: string;
  titulo: string;
  detalhe?: string;
}

export interface Veiculo {
  id: number;
  slug: string;
  marca: string;
  modelo: string;
  versao?: string;
  anoModelo: number;
  anoFabricacao?: number;
  cor: string;
  km: number;
  categoria: Categoria;
  cambio: Cambio;
  combustivel: Combustivel;
  portas: number;
  // Dados opcionais: pedidos só quando o contrato precisar deles
  placa?: string;
  chassi?: string;
  renavam?: string;

  opcionais: string[];
  descricao?: string;
  destaques: string[];

  status: StatusVeiculo;
  publicado: boolean;
  cadastradoEm: string;

  origem: OrigemVeiculo;
  fornecedor?: string;
  custo: number;
  preco: number;
  descontoMaximoPct: number;
  precoFipe?: number;

  fotos: FotoVeiculo[];
  documentos: DocumentoVeiculo[];
  gastos: GastoVeiculo[];
  historico: EventoVeiculo[];
}

export type FormaPagamento =
  | "sinal"
  | "pix_dinheiro"
  | "cartao"
  | "financiamento_bancario"
  | "leasing"
  | "financiamento_proprio"
  | "cheque"
  | "consorcio"
  | "troca";

export interface Venda {
  id: number;
  veiculo: string;
  cliente: string;
  data: string;
  valor: number;
  lucro: number;
  formaPrincipal: FormaPagamento;
  etapa: "negociacao" | "reservado" | "ficha" | "aprovado" | "contrato" | "transferencia" | "entregue";
}

export interface Lancamento {
  id: number;
  descricao: string;
  tipo: "entrada" | "saida";
  valor: number;
  vencimento: string;
  status: "previsto" | "realizado" | "atrasado";
  categoria: string;
}
