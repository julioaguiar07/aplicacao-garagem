import { boolean, date, doublePrecision, index, integer, jsonb, pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

// Convenções: dinheiro em centavos (integer), datas de negócio em `date` (texto AAAA-MM-DD),
// momentos em `timestamp with time zone`.

const criadoEm = () => timestamp("criado_em", { withTimezone: true }).notNull().defaultNow();

export const configuracoes = pgTable("configuracoes", {
  chave: text("chave").primaryKey(),
  valor: jsonb("valor").notNull(),
});

export const clientes = pgTable(
  "clientes",
  {
    id: serial("id").primaryKey(),
    nome: text("nome").notNull(),
    telefone: text("telefone"),
    email: text("email"),
    cpf: text("cpf"),
    endereco: text("endereco"),
    cidade: text("cidade"),
    origem: text("origem"), // loja, whatsapp, instagram, indicacao, site, outro
    interesse: text("interesse"),
    observacoes: text("observacoes"),
    criadoEm: criadoEm(),
  },
  (t) => [index("clientes_nome_idx").on(t.nome)],
);

export const veiculos = pgTable(
  "veiculos",
  {
    id: serial("id").primaryKey(),
    slug: text("slug").notNull().unique(),
    marca: text("marca").notNull(),
    modelo: text("modelo").notNull(),
    versao: text("versao"),
    anoModelo: integer("ano_modelo").notNull(),
    anoFabricacao: integer("ano_fabricacao"),
    cor: text("cor"),
    km: integer("km"),
    categoria: text("categoria").notNull().default("Hatch"),
    cambio: text("cambio").notNull().default("Manual"),
    combustivel: text("combustivel").notNull().default("Flex"),
    portas: integer("portas"),
    placa: text("placa"),
    chassi: text("chassi"),
    renavam: text("renavam"),
    opcionais: jsonb("opcionais").$type<string[]>().notNull().default([]),
    destaques: jsonb("destaques").$type<string[]>().notNull().default([]),
    descricao: text("descricao"),
    status: text("status").notNull().default("disponivel"), // rascunho, em_preparacao, disponivel, reservado, vendido, consignado
    publicado: boolean("publicado").notNull().default(false),
    origem: text("origem").notNull().default("compra"), // compra, troca, consignacao, leilao
    fornecedor: text("fornecedor"),
    clienteOrigemId: integer("cliente_origem_id").references(() => clientes.id, { onDelete: "set null" }),
    dataEntrada: date("data_entrada").notNull(),
    custo: integer("custo").notNull(),
    preco: integer("preco").notNull(),
    descontoMaximoPct: doublePrecision("desconto_maximo_pct").notNull().default(5),
    precoFipe: integer("preco_fipe"),
    codigoFipe: text("codigo_fipe"),
    criadoEm: criadoEm(),
    atualizadoEm: timestamp("atualizado_em", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("veiculos_status_idx").on(t.status)],
);

export const fotos = pgTable("fotos", {
  id: serial("id").primaryKey(),
  veiculoId: integer("veiculo_id")
    .notNull()
    .references(() => veiculos.id, { onDelete: "cascade" }),
  chaveOriginal: text("chave_original").notNull(),
  chaveCard: text("chave_card").notNull(),
  focoY: doublePrecision("foco_y").notNull().default(0.57),
  ordem: integer("ordem").notNull().default(0),
  criadoEm: criadoEm(),
});

export const vendas = pgTable("vendas", {
  id: serial("id").primaryKey(),
  veiculoId: integer("veiculo_id")
    .notNull()
    .references(() => veiculos.id),
  clienteId: integer("cliente_id")
    .notNull()
    .references(() => clientes.id),
  etapa: text("etapa").notNull().default("negociacao"),
  precoFinal: integer("preco_final").notNull(),
  dataVenda: date("data_venda").notNull(),
  observacoes: text("observacoes"),
  criadoEm: criadoEm(),
});

export const pagamentos = pgTable("pagamentos", {
  id: serial("id").primaryKey(),
  vendaId: integer("venda_id")
    .notNull()
    .references(() => vendas.id, { onDelete: "cascade" }),
  forma: text("forma").notNull(),
  valor: integer("valor").notNull(),
  detalhes: jsonb("detalhes").$type<Record<string, string | number | boolean | null>>().notNull().default({}),
  criadoEm: criadoEm(),
});

export const custosVenda = pgTable("custos_venda", {
  id: serial("id").primaryKey(),
  vendaId: integer("venda_id")
    .notNull()
    .references(() => vendas.id, { onDelete: "cascade" }),
  tipo: text("tipo").notNull(), // comissao, despachante, garantia, brinde, repasse, outros
  descricao: text("descricao"),
  valor: integer("valor").notNull(),
});

export const contas = pgTable("contas", {
  id: serial("id").primaryKey(),
  nome: text("nome").notNull(),
  tipo: text("tipo").notNull().default("banco"), // caixa, banco
  saldoInicial: integer("saldo_inicial").notNull().default(0),
  ativa: boolean("ativa").notNull().default(true),
});

export const lancamentos = pgTable(
  "lancamentos",
  {
    id: serial("id").primaryKey(),
    tipo: text("tipo").notNull(), // entrada, saida
    descricao: text("descricao").notNull(),
    categoria: text("categoria").notNull(),
    valor: integer("valor").notNull(),
    vencimento: date("vencimento").notNull(),
    pagoEm: date("pago_em"),
    contaId: integer("conta_id").references(() => contas.id, { onDelete: "set null" }),
    veiculoId: integer("veiculo_id").references(() => veiculos.id, { onDelete: "set null" }),
    vendaId: integer("venda_id").references(() => vendas.id, { onDelete: "cascade" }),
    pagamentoId: integer("pagamento_id").references(() => pagamentos.id, { onDelete: "cascade" }),
    clienteId: integer("cliente_id").references(() => clientes.id, { onDelete: "set null" }),
    parcela: integer("parcela"),
    totalParcelas: integer("total_parcelas"),
    grupoRecorrencia: text("grupo_recorrencia"),
    comprovanteChave: text("comprovante_chave"),
    observacoes: text("observacoes"),
    criadoEm: criadoEm(),
  },
  (t) => [index("lancamentos_vencimento_idx").on(t.vencimento)],
);

export const gastos = pgTable("gastos", {
  id: serial("id").primaryKey(),
  veiculoId: integer("veiculo_id")
    .notNull()
    .references(() => veiculos.id, { onDelete: "cascade" }),
  data: date("data").notNull(),
  categoria: text("categoria").notNull(),
  descricao: text("descricao").notNull(),
  valor: integer("valor").notNull(),
  notaChave: text("nota_chave"),
  lancamentoId: integer("lancamento_id").references(() => lancamentos.id, { onDelete: "set null" }),
  criadoEm: criadoEm(),
});

export const documentos = pgTable("documentos", {
  id: serial("id").primaryKey(),
  veiculoId: integer("veiculo_id").references(() => veiculos.id, { onDelete: "cascade" }),
  vendaId: integer("venda_id").references(() => vendas.id, { onDelete: "cascade" }),
  tipo: text("tipo").notNull(),
  nomeArquivo: text("nome_arquivo").notNull(),
  chave: text("chave").notNull(),
  mime: text("mime").notNull(),
  tamanho: integer("tamanho").notNull(),
  validade: date("validade"),
  criadoEm: criadoEm(),
});

export const eventos = pgTable(
  "eventos",
  {
    id: serial("id").primaryKey(),
    veiculoId: integer("veiculo_id").references(() => veiculos.id, { onDelete: "cascade" }),
    vendaId: integer("venda_id").references(() => vendas.id, { onDelete: "cascade" }),
    clienteId: integer("cliente_id").references(() => clientes.id, { onDelete: "cascade" }),
    titulo: text("titulo").notNull(),
    detalhe: text("detalhe"),
    criadoEm: criadoEm(),
  },
  (t) => [index("eventos_criado_idx").on(t.criadoEm)],
);
