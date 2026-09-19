// Teste local da migração: cria um banco "antigo" falso (mesmo schema do sistema Streamlit)
// e importa para um banco novo vazio em pastas temporárias.
// Uso: BANCO_LOCAL_DIR=<pasta nova> ARQUIVOS_DIR=<pasta arquivos> node --conditions=react-server --import tsx scripts/testar-migracao.ts <pasta-antigo> <foto.jpg>
import fs from "node:fs";
import { PGlite } from "@electric-sql/pglite";
import { sql } from "drizzle-orm";
import { banco, schema } from "@/db";
import { migrarSistemaAntigo } from "@/lib/migracao/antigo";

const [pastaAntigo, arquivoFoto] = process.argv.slice(2);

async function main() {
  fs.rmSync(pastaAntigo, { recursive: true, force: true });
  const antigo = new PGlite(pastaAntigo);
  await antigo.exec(`
    CREATE TABLE veiculos (id SERIAL PRIMARY KEY, modelo TEXT NOT NULL, ano INTEGER NOT NULL, marca TEXT NOT NULL, cor TEXT NOT NULL, preco_entrada REAL NOT NULL, preco_venda REAL NOT NULL, fornecedor TEXT NOT NULL, km INTEGER, placa TEXT, chassi TEXT, combustivel TEXT, cambio TEXT, portas INTEGER, observacoes TEXT, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'Em estoque', margem_negociacao REAL DEFAULT 30, foto BYTEA, renavam TEXT);
    CREATE TABLE gastos (id SERIAL PRIMARY KEY, veiculo_id INTEGER NOT NULL, tipo_gasto TEXT NOT NULL, valor REAL NOT NULL, data DATE NOT NULL, descricao TEXT, categoria TEXT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE vendas (id SERIAL PRIMARY KEY, veiculo_id INTEGER NOT NULL, comprador_nome TEXT NOT NULL, comprador_cpf TEXT, comprador_endereco TEXT, valor_venda REAL NOT NULL, data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP, contrato_path TEXT, status TEXT DEFAULT 'Concluída');
    CREATE TABLE documentos (id SERIAL PRIMARY KEY, veiculo_id INTEGER NOT NULL, nome_documento TEXT NOT NULL, tipo_documento TEXT NOT NULL, arquivo BYTEA, data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP, observacoes TEXT);
    CREATE TABLE fluxo_caixa (id SERIAL PRIMARY KEY, data DATE NOT NULL, descricao TEXT NOT NULL, tipo TEXT NOT NULL, categoria TEXT, valor REAL NOT NULL, veiculo_id INTEGER, status TEXT DEFAULT 'Pendente', data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE contatos (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, telefone TEXT, email TEXT, tipo TEXT, veiculo_interesse TEXT, data_contato DATE, status TEXT DEFAULT 'Novo', observacoes TEXT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE usuarios (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, nome TEXT NOT NULL, email TEXT, nivel_acesso TEXT DEFAULT 'usuario', data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE financiamentos (id SERIAL PRIMARY KEY, veiculo_id INTEGER NOT NULL, tipo_financiamento TEXT NOT NULL, valor_total REAL NOT NULL, valor_entrada REAL, num_parcelas INTEGER, data_contrato DATE, status TEXT DEFAULT 'Ativo', observacoes TEXT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE parcelas (id SERIAL PRIMARY KEY, financiamento_id INTEGER NOT NULL, numero_parcela INTEGER NOT NULL, valor_parcela REAL NOT NULL, data_vencimento DATE NOT NULL, data_pagamento DATE, status TEXT DEFAULT 'Pendente', forma_pagamento TEXT, observacoes TEXT, arquivo_comprovante BYTEA);
    CREATE TABLE documentos_financeiros (id SERIAL PRIMARY KEY, veiculo_id INTEGER, financiamento_id INTEGER, tipo_documento TEXT NOT NULL, nome_arquivo TEXT NOT NULL, arquivo BYTEA NOT NULL, data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP, observacoes TEXT);
    INSERT INTO usuarios (username, password_hash, nome, nivel_acesso) VALUES ('admin', 'admin123', 'Administrador', 'admin');
    INSERT INTO veiculos (modelo, ano, marca, cor, preco_entrada, preco_venda, fornecedor, km, placa, combustivel, cambio, portas, data_cadastro, status) VALUES
      ('HB20 ', 2022, 'HYUNDAI ', 'Prata', 70000, 78000, 'Particular', 52000, 'abc1d23', 'Gasolina', 'Automático', 4, '2026-09-17 17:16', 'Em estoque'),
      ('SRX TOYOTA', 2021, 'HILLUX', 'Branco', 200000, 219000, 'Loja X', 64000, NULL, 'Diesel', 'Automático', 4, '2026-04-01', 'Vendido'),
      ('T CROSS HL TSI', 2025, 'VOLKSWGAGEN ', 'Cinza', 136000, 149900, 'Particular', 9000, NULL, 'Flex', 'Automático', 4, '2026-08-01', 'Vendido'),
      ('Strada Endurance', 2024, 'Fiat', 'Prata', 88700, 98500, 'Particular', 21000, NULL, 'Flex', 'Manual', 4, '2026-05-10', 'Vendido'),
      ('Compass longitude ', 2017, 'Jeep ', 'Preto', 77000, 85000, 'Particular', 14000, NULL, 'Gasolina', 'Automático', 4, '2026-09-16', 'Reservado');
    INSERT INTO gastos (veiculo_id, tipo_gasto, valor, data, descricao) VALUES (1, 'Lavagem', 280, '2026-09-18', 'Higienização'), (4, 'Pneus', 1180, '2026-05-12', NULL);
    INSERT INTO vendas (veiculo_id, comprador_nome, comprador_cpf, comprador_endereco, valor_venda, data_venda) VALUES (4, 'Carlos Henrique Nunes', '123.456.789-00', 'Rua A, 10', 98500, '2026-06-10');
    INSERT INTO financiamentos (veiculo_id, tipo_financiamento, valor_total, valor_entrada, num_parcelas, data_contrato) VALUES (4, 'Financiamento Próprio', 98500, 40000, 3, '2026-06-10');
    INSERT INTO parcelas (financiamento_id, numero_parcela, valor_parcela, data_vencimento, data_pagamento, status) VALUES (1, 1, 19500, '2026-07-10', '2026-07-09', 'Pago'), (1, 2, 19500, '2026-08-10', NULL, 'Pendente'), (1, 3, 19500, '2026-09-10', NULL, 'Pendente');
    INSERT INTO fluxo_caixa (data, descricao, tipo, categoria, valor, veiculo_id, status) VALUES ('2026-06-10', 'Venda - Fiat Strada', 'Entrada', 'Vendas', 40000, 4, 'Concluído'), ('2026-09-10', 'Aluguel', 'Saída', 'Aluguel', 6500, NULL, 'Pago'), ('2026-09-25', 'Internet', 'Saída', 'Contas', 150, NULL, 'Pendente');
    INSERT INTO contatos (nome, telefone, tipo, veiculo_interesse, observacoes) VALUES ('Carlos Henrique Nunes', '(84) 98102-6655', 'Cliente', 'Fiat Strada', 'Comprou'), ('Gabriela Nogueira', '(84) 99870-1144', 'Interessado', 'SUV automático', NULL);
  `);
  const foto = fs.readFileSync(arquivoFoto);
  await antigo.query("UPDATE veiculos SET foto = $1 WHERE id IN (1, 5)", [foto]);
  await antigo.query("INSERT INTO documentos (veiculo_id, nome_documento, tipo_documento, arquivo) VALUES (1, 'crlv hb20', 'CRLV', $1)", [Buffer.from("%PDF-1.4 teste")]);

  const resumo = await migrarSistemaAntigo(async (q) => (await antigo.query<Record<string, unknown>>(q)).rows);
  const db = await banco();
  const veics = await db.select({ marca: schema.veiculos.marca, modelo: schema.veiculos.modelo, categoria: schema.veiculos.categoria, status: schema.veiculos.status, publicado: schema.veiculos.publicado, placa: schema.veiculos.placa }).from(schema.veiculos);
  console.table(veics);
  console.log(await db.select({ c: schema.configuracoes.chave }).from(schema.configuracoes));
  const [l] = await db.select({ n: sql<number>`count(*)::int`, abertos: sql<number>`count(*) filter (where pago_em is null)::int` }).from(schema.lancamentos);
  console.log("lançamentos", l, "resumo", resumo);
  // Segunda execução não pode duplicar
  const de_novo = await migrarSistemaAntigo(async (q) => (await antigo.query<Record<string, unknown>>(q)).rows);
  console.log("segunda execução:", de_novo);
  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
