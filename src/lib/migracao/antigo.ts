import bcrypt from "bcryptjs";
import { eq, sql } from "drizzle-orm";
import { banco, schema } from "@/db";
import { salvarArquivo } from "@/lib/armazenamento";
import { processarFoto } from "@/lib/fotos";
import { CATEGORIAS_SAIDA, slugify } from "@/lib/dominio";

/*
 * Importa os dados do sistema antigo (Streamlit, tabelas veiculos/vendas/gastos/fluxo_caixa/...) para o novo.
 * Roda uma única vez: grava "migracao_antiga" em configuracoes com o resumo do que foi importado.
 * O banco antigo não é alterado (só leitura).
 */

export type Consulta = (sqlTexto: string) => Promise<Record<string, unknown>[]>;

const { veiculos, fotos, gastos, lancamentos, documentos, clientes, vendas, pagamentos, eventos, configuracoes } = schema;

const txt = (v: unknown) => (v === null || v === undefined ? null : String(v).trim() || null);
const num = (v: unknown) => (v === null || v === undefined || v === "" ? null : Number(v));
const cent = (v: unknown) => Math.round((num(v) ?? 0) * 100);
const data = (v: unknown) => {
  if (!v) return null;
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  const s = String(v);
  return /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : null;
};
const hoje = () => new Date().toISOString().slice(0, 10);
const sem = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/** Marca padronizada: "VOLKSWGAGEN " → "Volkswagen", "HYUNDAI" → "Hyundai", "BMW" fica */
export function padronizarMarca(m: string) {
  const t = m.trim().replace(/\s+/g, " ");
  const correcoes: Record<string, string> = { volkswgagen: "Volkswagen", wolkswagen: "Volkswagen", vw: "Volkswagen", gm: "Chevrolet", chevrolet: "Chevrolet", mercedes: "Mercedes-Benz" };
  const c = correcoes[sem(t)];
  if (c) return c;
  if (/^(bmw|jac|ram|gwm|byd|mg|jeep)$/i.test(t)) return t.length <= 3 ? t.toUpperCase() : t[0].toUpperCase() + t.slice(1).toLowerCase();
  return t.toLowerCase().replace(/(^|[\s-])\S/g, (l) => l.toUpperCase());
}

/** Modelo: tira espaços extras e capitaliza palavras (mantém siglas como HB20S, XC40, T5, 4x4) */
export function padronizarModelo(m: string) {
  return m
    .trim()
    .replace(/\s+/g, " ")
    .split(" ")
    .map((p) => (/\d/.test(p) || p.length <= 3 ? p.toUpperCase() : p[0].toUpperCase() + p.slice(1).toLowerCase()))
    .join(" ");
}

const SUV = ["compass", "renegade", "duster", "tracker", "t-cross", "tcross", "t cross", "nivus", "hr-v", "hrv", "creta", "kicks", "xc40", "xc60", "tiggo", "ecosport", "commander", "pulse", "fastmback", "taos", "tiguan", "sportage", "tucson", "rav4", "corolla cross", "captur", "2008", "3008", "wr-v", "sw4", "pajero", "outlander", "territory", "equinox", "trailblazer"];
const PICAPE = ["hilux", "strada", "saveiro", "toro", "titano", "s10", "ranger", "montana", "oroch", "amarok", "frontier", "l200", "ram", "maverick"];
const SEDAN = ["hb20s", "corolla", "civic", "onix plus", "virtus", "cronos", "versa", "sentra", "city", "jetta", "cruze", "prisma", "voyage", "logan", "cobalt", "yaris sedan", "grand siena", "siena", "fluence", "focus sedan", "a3 sedan", "320i"];

const MARCAS = ["Toyota", "Hyundai", "Volkswagen", "Chevrolet", "Fiat", "Ford", "Honda", "Jeep", "Renault", "Nissan", "Peugeot", "Citroën", "Mitsubishi", "Kia", "Volvo", "BMW", "Audi", "Mercedes-Benz", "Caoa Chery", "Chery", "Suzuki", "Land Rover", "RAM", "BYD", "GWM"];
const CORRECAO_MODELO: Record<string, string> = { hillux: "Hilux", hilux: "Hilux", "t cross": "T-Cross", tcross: "T-Cross", hrv: "HR-V" };

/** Corrige marca/modelo invertidos ("HILLUX" / "SRX TOYOTA" → Toyota / Hilux SRX) e erros comuns de digitação */
export function corrigirMarcaModelo(marca: string, modelo: string) {
  let m = marca;
  let mod = modelo;
  const conhecida = (x: string) => MARCAS.find((k) => sem(k) === sem(x));
  if (!conhecida(m)) {
    const palavras = sem(mod).split(" ");
    const achada = MARCAS.find((k) => palavras.includes(sem(k)));
    if (achada) {
      const resto = mod.split(" ").filter((p) => sem(p) !== sem(achada));
      mod = [m, ...resto].join(" ").trim();
      m = achada;
    }
  } else m = conhecida(m)!;
  const partes = mod.split(" ");
  for (let i = 0; i < partes.length; i++) {
    const dupla = sem(`${partes[i]} ${partes[i + 1] ?? ""}`.trim());
    if (CORRECAO_MODELO[dupla] && partes[i + 1]) partes.splice(i, 2, CORRECAO_MODELO[dupla]);
    else if (CORRECAO_MODELO[sem(partes[i])]) partes[i] = CORRECAO_MODELO[sem(partes[i])];
  }
  return { marca: m, modelo: partes.join(" ") };
}

export function categoriaPorModelo(modelo: string) {
  const m = sem(modelo);
  if (PICAPE.some((k) => m.includes(k))) return "Picape";
  if (SEDAN.some((k) => m.includes(k))) return "Sedan";
  if (SUV.some((k) => m.includes(k))) return "SUV";
  return "Hatch";
}

function cambio(v: unknown) {
  const s = sem(String(v ?? ""));
  return s.includes("auto") ? "Automático" : s.includes("cvt") ? "CVT" : "Manual";
}
function combustivel(v: unknown) {
  const s = sem(String(v ?? ""));
  if (s.includes("diesel")) return "Diesel";
  if (s.includes("alcool") || s.includes("etanol")) return "Etanol";
  if (s.includes("eletr")) return "Elétrico";
  if (s.includes("hibr")) return "Híbrido";
  if (s.includes("gasolina")) return "Gasolina";
  return "Flex";
}
function statusVeiculo(v: unknown) {
  const s = sem(String(v ?? ""));
  if (s.includes("vendid") || s.includes("financiad")) return "vendido";
  if (s.includes("reserv")) return "reservado";
  return "disponivel";
}
function categoriaGasto(tipo: string) {
  const s = sem(tipo);
  if (s.includes("pneu")) return "Pneus";
  if (s.includes("manut") || s.includes("pec") || s.includes("mecan")) return "Mecânica";
  if (s.includes("pint") || s.includes("funil")) return "Funilaria e pintura";
  if (s.includes("lav") || s.includes("estet") || s.includes("polim")) return "Estética";
  if (s.includes("doc") || s.includes("ipva") || s.includes("seguro") || s.includes("licenc")) return "Documentação";
  return "Outros";
}

/** Descobre o tipo do arquivo pelos primeiros bytes */
function tipoArquivo(b: Buffer) {
  if (b.subarray(0, 4).toString("latin1") === "%PDF") return { mime: "application/pdf", ext: ".pdf" };
  if (b[0] === 0xff && b[1] === 0xd8) return { mime: "image/jpeg", ext: ".jpg" };
  if (b[0] === 0x89 && b[1] === 0x50) return { mime: "image/png", ext: ".png" };
  if (b.subarray(8, 12).toString("latin1") === "WEBP") return { mime: "image/webp", ext: ".webp" };
  return { mime: "application/octet-stream", ext: ".bin" };
}

function bytes(v: unknown): Buffer | null {
  if (!v) return null;
  if (Buffer.isBuffer(v)) return v.length ? v : null;
  if (v instanceof Uint8Array) return v.length ? Buffer.from(v) : null;
  if (typeof v === "string" && v.startsWith("\\x")) return Buffer.from(v.slice(2), "hex");
  return null;
}

async function tabela(consulta: Consulta, nome: string, colunas = "*") {
  const existe = await consulta(`select to_regclass('public.${nome}') as t`);
  if (!existe[0]?.t) return [];
  return consulta(`select ${colunas} from ${nome} order by id`);
}

export async function jaMigrado() {
  const db = await banco();
  const [linha] = await db.select().from(configuracoes).where(eq(configuracoes.chave, "migracao_antiga"));
  return Boolean(linha);
}

export async function migrarSistemaAntigo(consulta: Consulta, log: (m: string) => void = console.log) {
  const db = await banco();
  if (await jaMigrado()) {
    log("Migração já feita antes; nada a fazer.");
    return null;
  }
  const [{ total }] = await db.select({ total: sql<number>`count(*)::int` }).from(veiculos);
  if (total > 0) {
    log(`O banco novo já tem ${total} veículos; migração cancelada para não duplicar.`);
    return null;
  }

  const resumo = { veiculos: 0, fotos: 0, fotosComErro: 0, gastos: 0, documentos: 0, clientes: 0, vendas: 0, parcelas: 0, lancamentos: 0, vendidosSemVenda: 0 };
  const idVeiculo = new Map<number, number>();
  const clientePorNome = new Map<string, number>();

  // Conta padrão (o sistema antigo não guardava saldo; ajuste o saldo inicial em Fluxo de caixa)
  await db.insert(schema.contas).values({ nome: "Caixa da loja", tipo: "caixa", saldoInicial: 0 });

  // Senha do administrador: a mesma do sistema antigo, agora guardada com hash
  const usuarios = await tabela(consulta, "usuarios");
  const admin = usuarios.find((u) => u.username === "admin") ?? usuarios[0];
  if (admin?.password_hash) {
    const s = String(admin.password_hash);
    const hash = s.startsWith("$2") ? s : await bcrypt.hash(s, 12);
    await db.insert(configuracoes).values({ chave: "senha_admin", valor: hash }).onConflictDoUpdate({ target: configuracoes.chave, set: { valor: hash } });
    log("Senha do administrador importada.");
  }

  // Veículos (sem a coluna foto na listagem, para não carregar tudo na memória)
  const colunasVeic = (await consulta(`select column_name from information_schema.columns where table_name = 'veiculos'`)).map((c) => String(c.column_name));
  const tem = (c: string) => colunasVeic.includes(c);
  const lista = await consulta(
    `select id, marca, modelo, ano, cor, preco_entrada, preco_venda, fornecedor, km, placa, chassi, combustivel, cambio, portas, observacoes, data_cadastro, status${tem("renavam") ? ", renavam" : ""}${tem("margem_negociacao") ? ", margem_negociacao" : ""} from veiculos order by id`,
  );
  for (const a of lista) {
    const corrigido = corrigirMarcaModelo(padronizarMarca(txt(a.marca) ?? "Sem marca"), padronizarModelo(txt(a.modelo) ?? "Sem modelo"));
    const marcaFinal = corrigido.marca;
    const modelo = corrigido.modelo;
    const status = statusVeiculo(a.status);
    const desconto = num(a.margem_negociacao);
    const entrada = data(a.data_cadastro) ?? hoje();
    const [novo] = await db
      .insert(veiculos)
      .values({
        slug: `tmp-${a.id}`,
        marca: marcaFinal,
        modelo,
        anoModelo: num(a.ano) ?? new Date().getFullYear(),
        cor: txt(a.cor),
        km: num(a.km),
        categoria: categoriaPorModelo(modelo),
        cambio: cambio(a.cambio),
        combustivel: combustivel(a.combustivel),
        portas: num(a.portas),
        placa: txt(a.placa)?.toUpperCase().replace(/[^A-Z0-9]/g, "") || null,
        chassi: txt(a.chassi)?.toUpperCase() || null,
        renavam: txt(a.renavam),
        descricao: txt(a.observacoes),
        status,
        publicado: false,
        origem: "compra",
        fornecedor: txt(a.fornecedor),
        dataEntrada: entrada,
        custo: cent(a.preco_entrada),
        preco: cent(a.preco_venda),
        descontoMaximoPct: desconto !== null && desconto >= 0 && desconto <= 30 ? desconto : 5,
      })
      .returning({ id: veiculos.id });
    await db.update(veiculos).set({ slug: `${slugify(`${marcaFinal} ${modelo} ${a.ano ?? ""}`)}-${novo.id}` }).where(eq(veiculos.id, novo.id));
    idVeiculo.set(Number(a.id), novo.id);
    resumo.veiculos++;

    // Foto (lida uma por vez)
    if (tem("foto")) {
      const [linhaFoto] = await consulta(`select foto from veiculos where id = ${Number(a.id)}`);
      const b = bytes(linhaFoto?.foto);
      if (b) {
        try {
          const p = await processarFoto(novo.id, b);
          await db.insert(fotos).values({ veiculoId: novo.id, ...p, ordem: 0 });
          resumo.fotos++;
          // No site antigo, todo carro "Em estoque" com foto aparecia na vitrine
          if (status === "disponivel" || status === "reservado") await db.update(veiculos).set({ publicado: true }).where(eq(veiculos.id, novo.id));
        } catch {
          resumo.fotosComErro++;
          log(`Foto do veículo antigo ${a.id} não pôde ser lida.`);
        }
      }
    }
    if (status === "vendido") resumo.vendidosSemVenda++;
    await db.insert(eventos).values({ veiculoId: novo.id, titulo: "Importado do sistema antigo", detalhe: `Cadastrado em ${entrada.split("-").reverse().join("/")}` });
  }
  log(`${resumo.veiculos} veículos importados (${resumo.fotos} fotos).`);

  // Gastos → gasto + saída paga no caixa
  for (const g of await tabela(consulta, "gastos")) {
    const vId = idVeiculo.get(Number(g.veiculo_id));
    if (!vId) continue;
    const dia = data(g.data) ?? data(g.data_registro) ?? hoje();
    const tipo = txt(g.tipo_gasto) ?? "Outros";
    const descricao = txt(g.descricao) ?? tipo;
    const valor = cent(g.valor);
    const [l] = await db
      .insert(lancamentos)
      .values({ tipo: "saida", descricao: `${descricao} (gasto)`, categoria: "Preparação de veículo", valor, vencimento: dia, pagoEm: dia, veiculoId: vId })
      .returning({ id: lancamentos.id });
    await db.insert(gastos).values({ veiculoId: vId, data: dia, categoria: categoriaGasto(tipo), descricao, valor, lancamentoId: l.id });
    resumo.gastos++;
  }

  // Documentos (arquivos no banco antigo → volume de arquivos)
  async function importarDoc(d: Record<string, unknown>, nomeCampo: string) {
    const vId = idVeiculo.get(Number(d.veiculo_id));
    const b = bytes(d.arquivo);
    if (!vId || !b) return;
    const { mime, ext } = tipoArquivo(b);
    const nome = `${slugify(txt(d[nomeCampo]) ?? "documento")}${ext}`;
    const chave = await salvarArquivo(`privado/veiculos/${vId}`, nome, b);
    await db.insert(documentos).values({ veiculoId: vId, tipo: txt(d.tipo_documento) ?? "Outro", nomeArquivo: nome, chave, mime, tamanho: b.length });
    resumo.documentos++;
  }
  for (const d of await tabela(consulta, "documentos")) await importarDoc(d, "nome_documento");
  for (const d of await tabela(consulta, "documentos_financeiros")) await importarDoc(d, "nome_arquivo");

  // Clientes: compradores das vendas e contatos
  async function cliente(nome: string, extra: Partial<typeof clientes.$inferInsert> = {}) {
    const chave = sem(nome.trim());
    const existente = clientePorNome.get(chave);
    if (existente) {
      const preenchidos = Object.fromEntries(Object.entries(extra).filter(([, v]) => v));
      if (Object.keys(preenchidos).length) await db.update(clientes).set(preenchidos).where(eq(clientes.id, existente));
      return existente;
    }
    const [c] = await db.insert(clientes).values({ nome: nome.trim(), ...extra }).returning({ id: clientes.id });
    clientePorNome.set(chave, c.id);
    resumo.clientes++;
    return c.id;
  }

  // Vendas (com entrada e parcelas do financiamento, quando houver)
  const financiamentos = await tabela(consulta, "financiamentos");
  const parcelas = await tabela(consulta, "parcelas");
  for (const v of await tabela(consulta, "vendas")) {
    const vId = idVeiculo.get(Number(v.veiculo_id));
    if (!vId || sem(String(v.status ?? "")).includes("cancel")) continue;
    const cId = await cliente(txt(v.comprador_nome) ?? "Comprador não informado", { cpf: txt(v.comprador_cpf), endereco: txt(v.comprador_endereco) });
    const valor = cent(v.valor_venda);
    const dia = data(v.data_venda) ?? hoje();
    const [venda] = await db.insert(vendas).values({ veiculoId: vId, clienteId: cId, etapa: "entregue", precoFinal: valor, dataVenda: dia, observacoes: "Importada do sistema antigo" }).returning({ id: vendas.id });
    const fin = financiamentos.find((f) => Number(f.veiculo_id) === Number(v.veiculo_id));
    if (fin) {
      const entradaV = Math.min(valor, cent(fin.valor_entrada));
      const tipoFin = sem(String(fin.tipo_financiamento ?? ""));
      const forma = tipoFin.includes("propri") || tipoFin.includes("carne") || tipoFin.includes("promiss") ? "financiamento_proprio" : tipoFin.includes("cart") ? "cartao" : tipoFin.includes("consorc") ? "consorcio" : "financiamento_bancario";
      if (entradaV > 0) await db.insert(pagamentos).values({ vendaId: venda.id, forma: "pix_dinheiro", valor: entradaV, detalhes: { recebido: true, data: dia, importado: true } });
      const [pag] = await db
        .insert(pagamentos)
        .values({ vendaId: venda.id, forma, valor: valor - entradaV, detalhes: { parcelas: num(fin.num_parcelas), descricaoAntiga: txt(fin.tipo_financiamento), importado: true } })
        .returning({ id: pagamentos.id });
      const doFin = parcelas.filter((p) => Number(p.financiamento_id) === Number(fin.id));
      for (const p of doFin) {
        const venc = data(p.data_vencimento) ?? dia;
        const paga = sem(String(p.status ?? "")).match(/pag|quit|receb/);
        await db.insert(lancamentos).values({
          tipo: "entrada",
          descricao: `Parcela ${p.numero_parcela}/${doFin.length}: ${txt(v.comprador_nome) ?? "cliente"}`,
          categoria: forma === "financiamento_proprio" ? "Financiamento próprio" : "Venda de veículo",
          valor: cent(p.valor_parcela),
          vencimento: venc,
          pagoEm: paga ? (data(p.data_pagamento) ?? venc) : null,
          vendaId: venda.id,
          pagamentoId: pag.id,
          clienteId: cId,
          veiculoId: vId,
          parcela: num(p.numero_parcela),
          totalParcelas: doFin.length,
        });
        resumo.parcelas++;
      }
    } else {
      await db.insert(pagamentos).values({ vendaId: venda.id, forma: "pix_dinheiro", valor, detalhes: { recebido: true, data: dia, importado: true } });
    }
    await db.update(veiculos).set({ status: "vendido", publicado: false }).where(eq(veiculos.id, vId));
    await db.insert(eventos).values({ vendaId: venda.id, veiculoId: vId, clienteId: cId, titulo: "Venda importada do sistema antigo" });
    resumo.vendas++;
  }
  resumo.vendidosSemVenda = Math.max(0, resumo.vendidosSemVenda - resumo.vendas);

  // Contatos → clientes
  for (const c of await tabela(consulta, "contatos")) {
    const nome = txt(c.nome);
    if (!nome) continue;
    await cliente(nome, { telefone: txt(c.telefone), email: txt(c.email), interesse: txt(c.veiculo_interesse), observacoes: txt(c.observacoes) });
  }

  // Fluxo de caixa → lançamentos
  for (const f of await tabela(consulta, "fluxo_caixa")) {
    const entrada = sem(String(f.tipo ?? "")).startsWith("entr");
    const catAntiga = txt(f.categoria) ?? "";
    const categoria = entrada
      ? sem(catAntiga).includes("venda")
        ? "Venda de veículo"
        : "Outras receitas"
      : (CATEGORIAS_SAIDA.find((c) => sem(c).startsWith(sem(catAntiga).slice(0, 5)) && catAntiga.length >= 4) ?? "Outras despesas");
    const dia = data(f.data) ?? hoje();
    const pago = !sem(String(f.status ?? "pendente")).includes("pendent");
    await db.insert(lancamentos).values({
      tipo: entrada ? "entrada" : "saida",
      descricao: txt(f.descricao) ?? catAntiga ?? "Lançamento importado",
      categoria,
      valor: cent(f.valor),
      vencimento: dia,
      pagoEm: pago ? dia : null,
      veiculoId: f.veiculo_id ? (idVeiculo.get(Number(f.veiculo_id)) ?? null) : null,
      observacoes: catAntiga ? `Categoria no sistema antigo: ${catAntiga}` : null,
    });
    resumo.lancamentos++;
  }

  await db.insert(configuracoes).values({ chave: "migracao_antiga", valor: { em: new Date().toISOString(), ...resumo } });
  log(`Migração concluída: ${JSON.stringify(resumo)}`);
  return resumo;
}
