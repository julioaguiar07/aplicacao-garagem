// Carga de DEMONSTRAÇÃO. Apaga tudo e recria.
// Uso local: npm run semear. Na instalação de demonstração roda sozinho no primeiro start (scripts/iniciar.ts).
//
// Carros em estoque: os 8 da vitrine atual (marca, modelo, ano, km, preço, fotos reais).
// Custos, gastos, documentos, vendas, clientes e despesas são fictícios.
// Os dados reais entram pela migração do sistema antigo (Fase 2), não por aqui.

import fs from "node:fs/promises";
import path from "node:path";
import { eq, sql } from "drizzle-orm";
import { PDFDocument, StandardFonts } from "pdf-lib";
import { banco, schema } from "@/db";
import { processarFoto } from "@/lib/fotos";
import { salvarArquivo } from "@/lib/armazenamento";
import { registrarVenda, type NovaVenda } from "@/lib/negocio/venda";
import { registrarEvento } from "@/lib/negocio/eventos";
import { hojeISO, somarDias, somarMeses, slugify, TIPOS_DOCUMENTO } from "@/lib/dominio";

const { veiculos, fotos, gastos, lancamentos, documentos, contas, clientes, vendas } = schema;
const R = (reais: number) => Math.round(reais * 100);

// Datas da demonstração foram pensadas para 18/09/2026; tudo é deslocado para "hoje"
const REFERENCIA = "2026-09-18";
const hoje = hojeISO();
const desloc = Math.round((new Date(hoje).getTime() - new Date(REFERENCIA).getTime()) / 86_400_000);
const D = (iso: string) => somarDias(iso, desloc);

async function pdfDemo(titulo: string) {
  const doc = await PDFDocument.create();
  const pagina = doc.addPage([595, 842]);
  const fonte = await doc.embedFont(StandardFonts.Helvetica);
  pagina.drawText(`${titulo} (documento de demonstração)`, { x: 50, y: 780, size: 14, font: fonte });
  return Buffer.from(await doc.save());
}

export async function semear() {
  const db = await banco();
  console.log("Limpando banco e arquivos locais…");
  await db.execute(
    sql`TRUNCATE eventos, documentos, gastos, lancamentos, custos_venda, pagamentos, vendas, fotos, veiculos, clientes, contas RESTART IDENTITY CASCADE`,
  );
  if (!process.env.ARQUIVOS_DIR) await fs.rm(path.join(process.cwd(), ".dados", "arquivos"), { recursive: true, force: true });

  const [caixa] = await db.insert(contas).values({ nome: "Caixa da loja", tipo: "caixa", saldoInicial: R(15000) }).returning();
  const [bb] = await db.insert(contas).values({ nome: "Banco do Brasil", tipo: "banco", saldoInicial: R(120000) }).returning();

  // ---------- estoque atual (os 8 carros reais) ----------
  type Estoque = {
    demoId: number; marca: string; modelo: string; versao?: string; ano: number; cor: string; km: number; categoria: string; cambio: string;
    portas: number; preco: number; custo: number; fipe: number; desconto: number; entrada: string; origem: "compra" | "troca" | "consignacao";
    opcionais: string[]; destaques: string[]; descricao?: string; docsOk: number; vencido?: string; gastos: [string, string, string, number][];
  };
  const estoque: Estoque[] = [
    { demoId: 111, marca: "Hyundai", modelo: "HB20", ano: 2022, cor: "Prata", km: 52000, categoria: "Hatch", cambio: "Automático", portas: 4, preco: 78000, custo: 70000, fipe: 76900, desconto: 5, entrada: "2026-09-17", origem: "compra", opcionais: ["Ar-condicionado", "Direção elétrica", "Vidros elétricos", "Central multimídia"], destaques: ["Recém-chegado"], docsOk: 2, gastos: [["2026-09-18", "Estética", "Higienização interna", 280]] },
    { demoId: 109, marca: "Fiat", modelo: "Titano", versao: "Volcano", ano: 2025, cor: "Branco", km: 47706, categoria: "Picape", cambio: "Automático", portas: 4, preco: 175000, custo: 162000, fipe: 181500, desconto: 4, entrada: "2026-09-16", origem: "compra", opcionais: ["4x4", "Bancos em couro", "Câmera de ré", "Controle de tração", "Central multimídia"], destaques: ["Laudo aprovado"], docsOk: 4, gastos: [["2026-09-16", "Estética", "Polimento e cristalização", 650], ["2026-09-17", "Documentação", "Vistoria e laudo cautelar", 350]] },
    { demoId: 108, marca: "Toyota", modelo: "Yaris", versao: "XL", ano: 2019, cor: "Prata", km: 133000, categoria: "Hatch", cambio: "Automático", portas: 4, preco: 70000, custo: 62000, fipe: 68200, desconto: 6, entrada: "2026-09-16", origem: "compra", opcionais: ["Ar-condicionado", "Direção elétrica", "Airbags laterais"], destaques: [], docsOk: 3, vencido: "Consulta de débitos", gastos: [["2026-09-16", "Pneus", "2 pneus dianteiros", 1180], ["2026-09-17", "Mecânica", "Troca de óleo e filtros", 420]] },
    { demoId: 106, marca: "Volkswagen", modelo: "Gol", ano: 2018, cor: "Branco", km: 155000, categoria: "Hatch", cambio: "Manual", portas: 4, preco: 46000, custo: 40000, fipe: 44800, desconto: 6, entrada: "2026-09-16", origem: "compra", opcionais: ["Ar-condicionado", "Direção hidráulica"], destaques: [], docsOk: 5, gastos: [["2026-09-17", "Funilaria e pintura", "Retoque no para-choque", 480]] },
    { demoId: 105, marca: "Jeep", modelo: "Compass", versao: "Longitude", ano: 2017, cor: "Preto", km: 14000, categoria: "SUV", cambio: "Automático", portas: 4, preco: 85000, custo: 77000, fipe: 88300, desconto: 5, entrada: "2026-09-16", origem: "consignacao", opcionais: ["Bancos em couro", "Teto solar", "Chave presencial", "Central multimídia", "Sensor de estacionamento"], destaques: ["Baixa km"], docsOk: 3, gastos: [] },
    { demoId: 104, marca: "Renault", modelo: "Duster", ano: 2020, cor: "Cinza", km: 115000, categoria: "SUV", cambio: "Automático", portas: 4, preco: 85000, custo: 76000, fipe: 82700, desconto: 5, entrada: "2026-09-15", origem: "compra", opcionais: ["Ar-condicionado", "Central multimídia", "Rodas de liga leve"], destaques: [], docsOk: 4, gastos: [["2026-09-15", "Mecânica", "Pastilhas de freio", 390]] },
    { demoId: 103, marca: "Volvo", modelo: "XC40", versao: "T5 Hybrid R-Design", ano: 2022, cor: "Vermelho", km: 500, categoria: "SUV", cambio: "Automático", portas: 4, preco: 190000, custo: 178000, fipe: 196400, desconto: 3, entrada: "2026-09-15", origem: "compra", opcionais: ["Teto solar", "Bancos em couro", "Piloto automático", "Câmera de ré"], destaques: ["Oferta da semana"], docsOk: 5, gastos: [["2026-09-15", "Estética", "Vitrificação de pintura", 1200]] },
    { demoId: 100, marca: "Hyundai", modelo: "HB20S", versao: "Premium 1.6", ano: 2019, cor: "Branco", km: 65000, categoria: "Sedan", cambio: "Automático", portas: 4, preco: 75000, custo: 70000, fipe: 73900, desconto: 4, entrada: "2026-08-01", origem: "compra", opcionais: ["Bancos em couro", "Ar digital", "Direção elétrica", "Android Auto e CarPlay", "Rodas de liga leve", "Sensor de estacionamento", "Câmera de ré"], destaques: ["Único dono"], descricao: "Sedã que une conforto, tecnologia e bom desempenho. Motor 1.6 flex e câmbio automático de 6 marchas, condução suave e econômica, ideal para cidade e estrada.", docsOk: 5, gastos: [["2026-08-02", "Estética", "Higienização completa", 320], ["2026-08-05", "Mecânica", "Revisão 60 mil km", 890]] },
  ];

  const consignante = (await db.insert(clientes).values({ nome: "Roberto Lima", telefone: "(84) 99812-4410", origem: "indicacao", observacoes: "Dono do Compass em consignação" }).returning())[0];
  let idDuster = 0;

  for (const e of estoque) {
    const entrada = D(e.entrada);
    const [v] = await db
      .insert(veiculos)
      .values({
        slug: "tmp-" + e.demoId,
        marca: e.marca, modelo: e.modelo, versao: e.versao ?? null, anoModelo: e.ano, anoFabricacao: e.ano, cor: e.cor, km: e.km, categoria: e.categoria,
        cambio: e.cambio, combustivel: "Flex", portas: e.portas, opcionais: e.opcionais, destaques: e.destaques, descricao: e.descricao ?? null,
        status: e.origem === "consignacao" ? "consignado" : "disponivel", publicado: true, origem: e.origem,
        fornecedor: e.origem === "compra" ? "Particular" : null, clienteOrigemId: e.origem === "consignacao" ? consignante.id : null,
        dataEntrada: entrada, custo: R(e.custo), preco: R(e.preco), descontoMaximoPct: e.desconto, precoFipe: R(e.fipe),
      })
      .returning();
    await db.update(veiculos).set({ slug: `${slugify(`${e.marca} ${e.modelo} ${e.versao ?? ""} ${e.ano}`)}-${v.id}` }).where(eq(veiculos.id, v.id));
    if (e.modelo === "Duster") idDuster = v.id;

    const original = await fs.readFile(path.join(process.cwd(), "public", "demo", "veiculos", String(e.demoId), "original.webp"));
    await db.insert(fotos).values({ veiculoId: v.id, ...(await processarFoto(v.id, original)), ordem: 0 });

    if (e.origem === "compra")
      await db.insert(lancamentos).values({ tipo: "saida", descricao: `Compra: ${e.marca} ${e.modelo} ${e.ano}`, categoria: "Compra de veículo", valor: R(e.custo), vencimento: entrada, pagoEm: entrada, contaId: bb.id, veiculoId: v.id });

    for (const [data, categoria, descricao, valor] of e.gastos) {
      const [l] = await db.insert(lancamentos).values({ tipo: "saida", descricao: `${descricao} (${e.modelo} ${e.ano})`, categoria: "Preparação de veículo", valor: R(valor), vencimento: D(data), pagoEm: D(data), contaId: caixa.id, veiculoId: v.id }).returning();
      await db.insert(gastos).values({ veiculoId: v.id, data: D(data), categoria, descricao, valor: R(valor), lancamentoId: l.id });
    }

    for (const [i, tipo] of TIPOS_DOCUMENTO.entries()) {
      if (i >= e.docsOk && tipo !== e.vencido) continue;
      const chave = await salvarArquivo(`privado/veiculos/${v.id}`, `${slugify(tipo)}.pdf`, await pdfDemo(tipo));
      await db.insert(documentos).values({ veiculoId: v.id, tipo, nomeArquivo: `${slugify(tipo)}.pdf`, chave, mime: "application/pdf", tamanho: 900, validade: tipo === e.vencido ? D("2026-09-05") : null });
    }
    await registrarEvento({ veiculoId: v.id, titulo: "Veículo cadastrado", detalhe: e.origem === "consignacao" ? "Consignação" : "Compra de particular" });
    await registrarEvento({ veiculoId: v.id, titulo: "Publicado na vitrine" });
    console.log(`  estoque: ${e.marca} ${e.modelo} ${e.ano}`);
  }

  // ---------- vendas dos últimos meses ----------
  type Forma = NovaVenda["pagamentos"][number];
  const bancoFin = (valor: number, banco: string, liberacao: string): Forma => ({ forma: "financiamento_bancario", valor: R(valor), detalhes: { banco, parcelas: 48, taxaMensal: 1.89, retorno: R(valor * 0.03), previsaoLiberacao: liberacao, ficha: "aprovada" } });
  const pix = (valor: number, data: string): Forma => ({ forma: "pix_dinheiro", valor: R(valor), detalhes: { data, recebido: true, contaId: bb.id } });

  const vendidos: { marca: string; modelo: string; versao?: string; ano: number; categoria: string; cambio: string; cor: string; km: number; cliente: [string, string, string]; data: string; preco: number; final: number; custo: number; dias: number; etapa: NovaVenda["etapa"]; pagar: (final: number, d: string) => Forma[]; comissao?: number }[] = [
    { marca: "Volkswagen", modelo: "Polo", versao: "Track", ano: 2024, categoria: "Hatch", cambio: "Manual", cor: "Branco", km: 18000, cliente: ["Ana Beatriz Souza", "(84) 99654-1020", "instagram"], data: "2026-09-12", preco: 86900, final: 84900, custo: 76100, dias: 19, etapa: "transferencia", pagar: (f, d) => [pix(20000, d), bancoFin(f - 20000, "Banco Pan", somarDias(d, 9))] },
    { marca: "Chevrolet", modelo: "Onix", versao: "Joy", ano: 2018, categoria: "Hatch", cambio: "Manual", cor: "Branco", km: 98000, cliente: ["Marcos Vinícius Lima", "(84) 98877-3301", "loja"], data: "2026-09-08", preco: 53900, final: 52000, custo: 45600, dias: 27, etapa: "entregue", pagar: (f, d) => [pix(f, d)] },
    { marca: "Volkswagen", modelo: "T-Cross", versao: "Highline TSI", ano: 2025, categoria: "SUV", cambio: "Automático", cor: "Cinza", km: 9000, cliente: ["Rafaela Costa", "(84) 99120-7788", "site"], data: "2026-09-03", preco: 152900, final: 149900, custo: 136900, dias: 34, etapa: "entregue", pagar: (f, d) => [pix(50000, d), bancoFin(f - 50000, "Santander", somarDias(d, 6))], comissao: 1500 },
    { marca: "Honda", modelo: "Civic", versao: "EX", ano: 2020, categoria: "Sedan", cambio: "CVT", cor: "Cinza", km: 61000, cliente: ["João Pedro Almeida", "(84) 99301-5566", "whatsapp"], data: "2026-08-27", preco: 115000, final: 112000, custo: 101200, dias: 41, etapa: "entregue", pagar: (f, d) => [{ forma: "troca", valor: R(58000), detalhes: { marca: "Chevrolet", modelo: "Cruze", versao: "LT", ano: 2017, km: 88000, cor: "Preto" } }, pix(f - 58000, d)] },
    { marca: "Toyota", modelo: "Hilux", versao: "SR", ano: 2021, categoria: "Picape", cambio: "Automático", cor: "Prata", km: 72000, cliente: ["Agropecuária Serra Verde", "(84) 3316-2200", "indicacao"], data: "2026-08-19", preco: 202000, final: 198000, custo: 181800, dias: 22, etapa: "entregue", pagar: (f, d) => [pix(60000, d), bancoFin(f - 60000, "Banco do Brasil", somarDias(d, 7))], comissao: 2000 },
    { marca: "Fiat", modelo: "Strada", versao: "Endurance", ano: 2024, categoria: "Picape", cambio: "Manual", cor: "Prata", km: 21000, cliente: ["Carlos Henrique Nunes", "(84) 98102-6655", "loja"], data: "2026-06-10", preco: 99900, final: 98500, custo: 88700, dias: 30, etapa: "entregue", pagar: (f, d) => [pix(40000, d), { forma: "financiamento_proprio", valor: R(f - 40000), detalhes: { parcelas: 12, jurosMensalPct: 1.8, primeiroVencimento: somarMeses(d, 1) } }] },
    { marca: "Volkswagen", modelo: "Saveiro", versao: "Robust", ano: 2024, categoria: "Picape", cambio: "Manual", cor: "Branco", km: 15000, cliente: ["Francisca Moura", "(84) 99433-8812", "instagram"], data: "2026-07-29", preco: 92900, final: 91000, custo: 82000, dias: 25, etapa: "entregue", pagar: (f, d) => [{ forma: "consorcio", valor: R(f), detalhes: { administradora: "Consórcio Embracon", previsaoLiberacao: somarDias(d, 12) } }] },
    { marca: "Volkswagen", modelo: "Saveiro", versao: "Robust", ano: 2024, categoria: "Picape", cambio: "Manual", cor: "Branco", km: 22000, cliente: ["Pedro Henrique Rocha", "(84) 99988-1203", "whatsapp"], data: "2026-07-18", preco: 91500, final: 89900, custo: 81700, dias: 18, etapa: "entregue", pagar: (f, d) => [pix(f, d)] },
    { marca: "Volkswagen", modelo: "Nivus", versao: "Highline", ano: 2024, categoria: "SUV", cambio: "Automático", cor: "Cinza", km: 17000, cliente: ["Luana Freitas", "(84) 99215-4040", "site"], data: "2026-07-04", preco: 121000, final: 118000, custo: 106800, dias: 38, etapa: "entregue", pagar: (f, d) => [pix(35000, d), bancoFin(f - 35000, "Banco Pan", somarDias(d, 8))] },
    { marca: "Hyundai", modelo: "HB20S", versao: "Comfort", ano: 2025, categoria: "Sedan", cambio: "Automático", cor: "Preto", km: 8000, cliente: ["Tiago Barbosa", "(84) 98760-3390", "loja"], data: "2026-06-21", preco: 98000, final: 96500, custo: 87600, dias: 15, etapa: "entregue", pagar: (f, d) => [pix(56500, d), { forma: "cartao", valor: R(40000), detalhes: { parcelas: 10, taxaPct: 8.5, antecipado: true, primeiroRecebimento: somarDias(d, 2) } }] },
    { marca: "Jeep", modelo: "Renegade", versao: "S", ano: 2022, categoria: "SUV", cambio: "Automático", cor: "Preto", km: 39000, cliente: ["Mariana Alves", "(84) 99650-7721", "instagram"], data: "2026-06-09", preco: 121500, final: 118500, custo: 106500, dias: 44, etapa: "entregue", pagar: (f, d) => [pix(30000, d), bancoFin(f - 30000, "Santander", somarDias(d, 6))] },
    { marca: "Toyota", modelo: "Corolla", versao: "XEi", ano: 2023, categoria: "Sedan", cambio: "CVT", cor: "Branco", km: 26000, cliente: ["Rodrigo Pinheiro", "(84) 99117-0055", "indicacao"], data: "2026-05-24", preco: 145000, final: 142000, custo: 128300, dias: 29, etapa: "entregue", pagar: (f, d) => [{ forma: "troca", valor: R(72000), detalhes: { marca: "Toyota", modelo: "Corolla", versao: "GLi", ano: 2019, km: 71000, cor: "Prata" } }, pix(f - 72000, d)], comissao: 1200 },
    { marca: "Honda", modelo: "HR-V", versao: "EXL", ano: 2020, categoria: "SUV", cambio: "CVT", cor: "Branco", km: 58000, cliente: ["Juliana Teixeira", "(84) 98845-6677", "whatsapp"], data: "2026-05-11", preco: 112000, final: 109000, custo: 98400, dias: 33, etapa: "entregue", pagar: (f, d) => [pix(25000, d), bancoFin(f - 25000, "Itaú", somarDias(d, 7))] },
    { marca: "Toyota", modelo: "Hilux", versao: "SRX", ano: 2021, categoria: "Picape", cambio: "Automático", cor: "Branco", km: 64000, cliente: ["Transportes Oeste Ltda", "(84) 3321-9090", "indicacao"], data: "2026-04-26", preco: 224000, final: 219000, custo: 200700, dias: 20, etapa: "entregue", pagar: (f, d) => [pix(50000, d), { forma: "leasing", valor: R(f - 50000), detalhes: { instituicao: "Bradesco Leasing", previsaoLiberacao: somarDias(d, 10) } }] },
    { marca: "Jeep", modelo: "Compass", versao: "Longitude", ano: 2017, categoria: "SUV", cambio: "Automático", cor: "Cinza", km: 97000, cliente: ["Fábio Moura", "(84) 99404-2121", "loja"], data: "2026-04-08", preco: 88000, final: 86000, custo: 78800, dias: 36, etapa: "entregue", pagar: (f, d) => [{ forma: "cheque", valor: R(20000), detalhes: { banco: "Caixa", numero: "000481", bomPara: somarDias(d, 30) } }, pix(f - 20000, d)] },
  ];

  for (const s of vendidos) {
    const dataVenda = D(s.data);
    const entrada = somarDias(dataVenda, -s.dias);
    const [v] = await db
      .insert(veiculos)
      .values({
        slug: "tmp-v-" + Math.random(), marca: s.marca, modelo: s.modelo, versao: s.versao ?? null, anoModelo: s.ano, anoFabricacao: s.ano, cor: s.cor, km: s.km,
        categoria: s.categoria, cambio: s.cambio, combustivel: "Flex", portas: 4, status: "disponivel", origem: "compra", fornecedor: "Particular",
        dataEntrada: entrada, custo: R(s.custo), preco: R(s.preco), descontoMaximoPct: 5,
      })
      .returning();
    await db.update(veiculos).set({ slug: `${slugify(`${s.marca} ${s.modelo} ${s.versao ?? ""} ${s.ano}`)}-${v.id}` }).where(eq(veiculos.id, v.id));
    await db.insert(lancamentos).values({ tipo: "saida", descricao: `Compra: ${s.marca} ${s.modelo} ${s.ano}`, categoria: "Compra de veículo", valor: R(s.custo), vencimento: entrada, pagoEm: entrada, contaId: bb.id, veiculoId: v.id });
    const gastoValor = 250 + Math.round((s.custo % 7) * 110);
    const [l] = await db.insert(lancamentos).values({ tipo: "saida", descricao: `Preparação (${s.modelo} ${s.ano})`, categoria: "Preparação de veículo", valor: R(gastoValor), vencimento: somarDias(entrada, 2), pagoEm: somarDias(entrada, 2), contaId: caixa.id, veiculoId: v.id }).returning();
    await db.insert(gastos).values({ veiculoId: v.id, data: somarDias(entrada, 2), categoria: "Preparação", descricao: "Higienização e polimento", valor: R(gastoValor), lancamentoId: l.id });

    const [c] = await db.insert(clientes).values({ nome: s.cliente[0], telefone: s.cliente[1], origem: s.cliente[2], cidade: "Mossoró/RN", criadoEm: new Date(somarDias(dataVenda, -7) + "T12:00:00-03:00") }).returning();
    const custos: NovaVenda["custos"] = [{ tipo: "despachante", valor: R(780) }];
    if (s.comissao) custos.push({ tipo: "comissao", descricao: "Indicação", valor: R(s.comissao) });
    const r = await registrarVenda({ veiculoId: v.id, cliente: { id: c.id }, precoFinal: R(s.final), dataVenda, etapa: s.etapa, pagamentos: s.pagar(s.final, dataVenda), custos });
    if (!r.ok) throw new Error(`${s.modelo}: ${r.erro}`);
    console.log(`  venda: ${s.marca} ${s.modelo} ${s.ano} → ${s.cliente[0]}`);
  }

  // Venda em andamento: Duster com ficha no banco
  const [lead] = await db.insert(clientes).values({ nome: "Gabriela Nogueira", telefone: "(84) 99870-1144", origem: "instagram", interesse: "SUV automático até R$ 90 mil" }).returning();
  const rDuster = await registrarVenda({
    veiculoId: idDuster, cliente: { id: lead.id }, precoFinal: R(83500), dataVenda: hoje, etapa: "ficha",
    pagamentos: [{ forma: "sinal", valor: R(2000), detalhes: { data: hoje, recebido: true, contaId: caixa.id } }, pix(21500, somarDias(hoje, 3)), bancoFin(60000, "Banco Pan", somarDias(hoje, 10))],
    custos: [{ tipo: "despachante", valor: R(780) }],
  });
  if (!rDuster.ok) throw new Error(rDuster.erro);
  await db.update(lancamentos).set({ pagoEm: null }).where(eq(lancamentos.vendaId, rDuster.id));
  await db.update(lancamentos).set({ pagoEm: hoje }).where(sql`${lancamentos.vendaId} = ${rDuster.id} and ${lancamentos.categoria} = 'Sinal'`);

  // Interessados sem compra
  await db.insert(clientes).values([
    { nome: "Diego Fernandes", telefone: "(84) 99612-3030", origem: "whatsapp", interesse: "Picape diesel", criadoEm: new Date(D("2026-09-10") + "T12:00:00-03:00") },
    { nome: "Patrícia Queiroz", telefone: "(84) 98111-2277", origem: "site", interesse: "Hatch automático para a filha", criadoEm: new Date(D("2026-09-14") + "T12:00:00-03:00") },
  ]);

  // Recebimentos passados já caíram; no carnê da Strada a parcela mais recente segue em aberto (atrasada)
  await db.update(lancamentos).set({ pagoEm: lancamentos.vencimento, contaId: bb.id }).where(sql`${lancamentos.vencimento} < ${hoje} and ${lancamentos.pagoEm} is null and (${lancamentos.vendaId} is null or ${lancamentos.vendaId} <> ${rDuster.id})`);
  const [atrasada] = await db.select().from(lancamentos).where(sql`${lancamentos.categoria} = 'Financiamento próprio' and ${lancamentos.vencimento} < ${hoje}`).orderBy(sql`${lancamentos.vencimento} desc`).limit(1);
  if (atrasada) await db.update(lancamentos).set({ pagoEm: null }).where(eq(lancamentos.id, atrasada.id));
  // Saídas de custo de venda antigas foram pagas no dia da venda
  await db.update(lancamentos).set({ contaId: caixa.id }).where(sql`${lancamentos.tipo} = 'saida' and ${lancamentos.contaId} is null and ${lancamentos.pagoEm} is not null`);

  // ---------- despesas fixas (6 meses para trás, 3 para frente) ----------
  const fixas: [string, string, number, number][] = [
    ["Aluguel do galpão", "Aluguel", 6500, 10],
    ["Salários e encargos", "Salários", 9800, 5],
    ["Energia, água e internet", "Contas (água, luz, internet)", 1150, 15],
    ["Anúncios no Instagram", "Marketing", 900, 20],
    ["Simples Nacional", "Impostos e taxas", 2100, 20],
  ];
  const inicio = somarMeses(hoje.slice(0, 7) + "-01", -6);
  for (const [descricao, categoria, valor, dia] of fixas) {
    const grupo = crypto.randomUUID();
    for (let m = 0; m < 10; m++) {
      const venc = somarDias(somarMeses(inicio, m), dia - 1);
      await db.insert(lancamentos).values({ tipo: "saida", descricao, categoria, valor: R(valor), vencimento: venc, pagoEm: venc < hoje ? venc : null, contaId: venc < hoje ? bb.id : null, grupoRecorrencia: grupo });
    }
  }

  // Saldo inicial calibrado para a loja fechar hoje com saldo realista nas contas
  for (const [conta, alvo] of [
    [bb, R(185000)],
    [caixa, R(12000)],
  ] as const) {
    const [{ movimento }] = await db
      .select({ movimento: sql<number>`coalesce(sum(case when ${lancamentos.tipo} = 'entrada' then ${lancamentos.valor} else -${lancamentos.valor} end), 0)::bigint` })
      .from(lancamentos)
      .where(sql`${lancamentos.contaId} = ${conta.id} and ${lancamentos.pagoEm} is not null`);
    await db.update(contas).set({ saldoInicial: alvo - Number(movimento) }).where(eq(contas.id, conta.id));
  }

  const [{ total }] = await db.select({ total: sql<number>`count(*)::int` }).from(vendas);
  // Dados fictícios da loja (endereço, contato, CNPJ) para a demonstração
  if (process.env.NEXT_PUBLIC_DEMO === "1")
    await db
      .insert(schema.configuracoes)
      .values({ chave: "loja", valor: { whatsapp: "5584900000000", telefone: "(84) 90000-0000", endereco: "Av. Principal, 1000", cidade: "Mossoró/RN", cep: "59600-000", cnpj: "00.000.000/0001-00" } })
      .onConflictDoNothing();

  console.log(`Pronto: ${estoque.length} carros em estoque, ${total} vendas, contas e despesas de demonstração.`);
}

// Rodando direto (npm run semear)
if (process.argv[1]?.split("\\").join("/").endsWith("scripts/semear.ts"))
  semear()
    .then(() => process.exit(0))
    .catch((e) => {
      console.error(e);
      process.exit(1);
    });
