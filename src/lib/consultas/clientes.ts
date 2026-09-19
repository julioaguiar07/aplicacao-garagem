import "server-only";
import { asc, desc, eq } from "drizzle-orm";
import { banco, schema } from "@/db";
import { hojeISO, statusLancamento } from "@/lib/dominio";
import { vendasDoCliente } from "./vendas";

const { clientes, lancamentos, vendas, eventos, veiculos } = schema;

export type Cliente = typeof clientes.$inferSelect;

/** Clientes com compras, total comprado e o que ainda devem (parcelas em aberto) */
export async function listarClientes() {
  const db = await banco();
  const [lista, todasVendas, recebiveis] = await Promise.all([
    db.select().from(clientes).orderBy(asc(clientes.nome)),
    db.select({ clienteId: vendas.clienteId, precoFinal: vendas.precoFinal, etapa: vendas.etapa, dataVenda: vendas.dataVenda }).from(vendas),
    db.select().from(lancamentos).where(eq(lancamentos.tipo, "entrada")),
  ]);
  const hoje = hojeISO();
  return lista.map((c) => {
    const compras = todasVendas.filter((v) => v.clienteId === c.id && v.etapa !== "cancelada");
    const emAberto = recebiveis.filter((l) => l.clienteId === c.id && !l.pagoEm);
    return {
      ...c,
      compras: compras.length,
      totalComprado: compras.reduce((s, v) => s + v.precoFinal, 0),
      ultimaCompra: compras.map((v) => v.dataVenda).sort().at(-1) ?? null,
      aReceber: emAberto.reduce((s, l) => s + l.valor, 0),
      atrasado: emAberto.filter((l) => statusLancamento(l, hoje) === "atrasado").reduce((s, l) => s + l.valor, 0),
    };
  });
}
export type ItemCliente = Awaited<ReturnType<typeof listarClientes>>[number];

export async function clienteCompleto(id: number) {
  const db = await banco();
  const [c] = await db.select().from(clientes).where(eq(clientes.id, id));
  if (!c) return null;
  const hoje = hojeISO();
  const [listaVendas, parcelas, hist, trocas] = await Promise.all([
    vendasDoCliente(id),
    db.select().from(lancamentos).where(eq(lancamentos.clienteId, id)).orderBy(asc(lancamentos.vencimento)),
    db.select().from(eventos).where(eq(eventos.clienteId, id)).orderBy(desc(eventos.criadoEm)),
    db.select().from(veiculos).where(eq(veiculos.clienteOrigemId, id)),
  ]);
  return {
    cliente: c,
    vendas: listaVendas,
    parcelas: parcelas.filter((l) => l.tipo === "entrada").map((l) => ({ ...l, status: statusLancamento(l, hoje) })),
    eventos: hist,
    veiculosDoCliente: trocas,
  };
}

export async function opcoesClientes() {
  const db = await banco();
  return db.select({ id: clientes.id, nome: clientes.nome, telefone: clientes.telefone, cpf: clientes.cpf }).from(clientes).orderBy(asc(clientes.nome));
}
