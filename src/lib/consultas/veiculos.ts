import "server-only";
import { and, asc, desc, eq, inArray, ne, sql } from "drizzle-orm";
import { banco, schema } from "@/db";
import { TIPOS_DOCUMENTO, diasEntre, hojeISO } from "@/lib/dominio";
import { urlArquivo } from "@/lib/armazenamento";

const { veiculos, fotos, gastos, documentos, eventos, vendas, clientes } = schema;

export type Veiculo = typeof veiculos.$inferSelect;
export type Foto = typeof fotos.$inferSelect & { urlCard: string; urlOriginal: string };

function comUrls(f: typeof fotos.$inferSelect): Foto {
  return { ...f, urlCard: urlArquivo(f.chaveCard), urlOriginal: urlArquivo(f.chaveOriginal) };
}

export function nomeVeiculo(v: Pick<Veiculo, "marca" | "modelo" | "versao">) {
  return [v.marca, v.modelo, v.versao].filter(Boolean).join(" ");
}

/** Situação do checklist de documentos de um veículo */
export function checklistDocumentos(docs: (typeof documentos.$inferSelect)[], hoje = hojeISO()) {
  const tipos = [...new Set([...TIPOS_DOCUMENTO, ...docs.map((d) => d.tipo)])];
  return tipos.map((tipo) => {
    const doTipo = docs.filter((d) => d.tipo === tipo).sort((a, b) => b.criadoEm.getTime() - a.criadoEm.getTime());
    const atual = doTipo[0];
    const status = !atual ? "pendente" : atual.validade && atual.validade < hoje ? "vencido" : "ok";
    return { tipo, status: status as "ok" | "pendente" | "vencido", atual, historico: doTipo.slice(1), obrigatorio: TIPOS_DOCUMENTO.includes(tipo) };
  });
}

export async function capas(ids: number[]) {
  if (!ids.length) return new Map<number, Foto>();
  const db = await banco();
  const linhas = await db.select().from(fotos).where(inArray(fotos.veiculoId, ids)).orderBy(asc(fotos.ordem), asc(fotos.id));
  const mapa = new Map<number, Foto>();
  for (const f of linhas) if (!mapa.has(f.veiculoId)) mapa.set(f.veiculoId, comUrls(f));
  return mapa;
}

/** Lista para a grade do estoque, com capa, dias no pátio, gastos e pendências */
export async function listarVeiculos(opcoes: { incluirVendidos?: boolean } = {}) {
  const db = await banco();
  const hoje = hojeISO();
  const lista = await db
    .select()
    .from(veiculos)
    .where(opcoes.incluirVendidos ? undefined : ne(veiculos.status, "vendido"))
    .orderBy(desc(veiculos.dataEntrada), desc(veiculos.id));
  const ids = lista.map((v) => v.id);
  const [mapaCapas, somaGastos, docs] = await Promise.all([
    capas(ids),
    ids.length
      ? db.select({ veiculoId: gastos.veiculoId, total: sql<number>`sum(${gastos.valor})::int` }).from(gastos).where(inArray(gastos.veiculoId, ids)).groupBy(gastos.veiculoId)
      : [],
    ids.length ? db.select().from(documentos).where(inArray(documentos.veiculoId, ids)) : [],
  ]);
  const gastoPor = new Map(somaGastos.map((g) => [g.veiculoId, g.total]));
  return lista.map((v) => {
    const pend = checklistDocumentos(docs.filter((d) => d.veiculoId === v.id), hoje).filter((c) => c.status !== "ok").length;
    return {
      ...v,
      capa: mapaCapas.get(v.id),
      dias: diasEntre(v.dataEntrada, hoje),
      totalGastos: gastoPor.get(v.id) ?? 0,
      pendencias: pend,
    };
  });
}
export type ItemEstoque = Awaited<ReturnType<typeof listarVeiculos>>[number];

export async function veiculoCompleto(id: number) {
  const db = await banco();
  const [v] = await db.select().from(veiculos).where(eq(veiculos.id, id));
  if (!v) return null;
  const [listaFotos, listaDocs, listaGastos, listaEventos, listaVendas, origem] = await Promise.all([
    db.select().from(fotos).where(eq(fotos.veiculoId, id)).orderBy(asc(fotos.ordem), asc(fotos.id)),
    db.select().from(documentos).where(eq(documentos.veiculoId, id)),
    db.select().from(gastos).where(eq(gastos.veiculoId, id)).orderBy(desc(gastos.data), desc(gastos.id)),
    db.select().from(eventos).where(eq(eventos.veiculoId, id)).orderBy(desc(eventos.criadoEm)),
    db
      .select({ venda: vendas, cliente: clientes })
      .from(vendas)
      .innerJoin(clientes, eq(clientes.id, vendas.clienteId))
      .where(and(eq(vendas.veiculoId, id), ne(vendas.etapa, "cancelada"))),
    v.clienteOrigemId ? db.select().from(clientes).where(eq(clientes.id, v.clienteOrigemId)) : [],
  ]);
  return {
    veiculo: v,
    fotos: listaFotos.map(comUrls),
    documentos: listaDocs,
    checklist: checklistDocumentos(listaDocs),
    gastos: listaGastos,
    totalGastos: listaGastos.reduce((s, g) => s + g.valor, 0),
    eventos: listaEventos,
    vendaAtiva: listaVendas[0] ?? null,
    clienteOrigem: origem[0] ?? null,
    dias: diasEntre(v.dataEntrada, hojeISO()),
  };
}

export function precoMinimo(v: Pick<Veiculo, "preco" | "descontoMaximoPct">) {
  return Math.round(v.preco * (1 - v.descontoMaximoPct / 100));
}

/** Veículos que podem entrar numa venda nova */
export async function veiculosVendaveis() {
  const db = await banco();
  return db
    .select()
    .from(veiculos)
    .where(inArray(veiculos.status, ["disponivel", "em_preparacao", "consignado"]))
    .orderBy(asc(veiculos.marca), asc(veiculos.modelo));
}
