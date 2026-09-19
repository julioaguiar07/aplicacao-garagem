"use server";

import { and, eq, isNull } from "drizzle-orm";
import { redirect } from "next/navigation";
import { z } from "zod";
import { type NovaVenda, esquemaVenda, registrarVenda } from "@/lib/negocio/venda";
import { banco, schema } from "@/db";
import { exigirLogin } from "@/lib/auth";
import { ETAPAS_VENDA, ETAPAS_VENDIDO, type EtapaVenda, hojeISO } from "@/lib/dominio";
import { type Resultado, atualizarTelas, registrarEvento, texto } from "./comum";

const { vendas, veiculos, clientes, pagamentos, lancamentos } = schema;

export async function criarVenda(_: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  let entrada: NovaVenda;
  try {
    entrada = esquemaVenda.parse(JSON.parse(String(form.get("payload") ?? "{}")));
  } catch (e) {
    const msg = e instanceof z.ZodError ? e.issues[0]?.message : null;
    return { ok: false, erro: msg && !msg.startsWith("Invalid") ? msg : "Confira os campos da venda." };
  }
  const r = await registrarVenda(entrada);
  if (!r.ok) return r;
  atualizarTelas();
  redirect(`/painel/vendas/${r.id}`);
}

export async function mudarEtapa(vendaId: number, etapa: EtapaVenda): Promise<Resultado> {
  await exigirLogin();
  if (etapa === "cancelada") return cancelarVenda(vendaId);
  const db = await banco();
  const [venda] = await db.select().from(vendas).where(eq(vendas.id, vendaId));
  if (!venda) return { ok: false, erro: "Venda não encontrada." };
  if (venda.etapa === "cancelada") return { ok: false, erro: "Venda cancelada não muda de etapa." };
  await db.update(vendas).set({ etapa }).where(eq(vendas.id, vendaId));
  const vendido = ETAPAS_VENDIDO.includes(etapa);
  await db.update(veiculos).set({ status: vendido ? "vendido" : "reservado", ...(vendido ? { publicado: false } : {}) }).where(eq(veiculos.id, venda.veiculoId));
  await registrarEvento({ vendaId, veiculoId: venda.veiculoId, clienteId: venda.clienteId, titulo: `Etapa: ${ETAPAS_VENDA[etapa]}` });
  atualizarTelas();
  return { ok: true };
}

/** Cancela: remove o que ainda não foi recebido/pago, devolve o carro ao estoque e desfaz trocas sem uso */
export async function cancelarVenda(vendaId: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [venda] = await db.select().from(vendas).where(eq(vendas.id, vendaId));
  if (!venda) return { ok: false, erro: "Venda não encontrada." };
  const [veiculo] = await db.select().from(veiculos).where(eq(veiculos.id, venda.veiculoId));
  await db.delete(lancamentos).where(and(eq(lancamentos.vendaId, vendaId), isNull(lancamentos.pagoEm)));
  const pags = await db.select().from(pagamentos).where(eq(pagamentos.vendaId, vendaId));
  let trocasRemovidas = 0;
  for (const p of pags) {
    const idTroca = Number(p.detalhes.veiculoTrocaId);
    if (!idTroca) continue;
    const [outraVenda] = await db.select({ id: vendas.id }).from(vendas).where(eq(vendas.veiculoId, idTroca));
    if (!outraVenda) {
      await db.delete(veiculos).where(eq(veiculos.id, idTroca));
      trocasRemovidas++;
    }
  }
  await db.update(vendas).set({ etapa: "cancelada" }).where(eq(vendas.id, vendaId));
  await db.update(veiculos).set({ status: veiculo?.origem === "consignacao" ? "consignado" : "disponivel" }).where(eq(veiculos.id, venda.veiculoId));
  const pagos = await db.select({ id: lancamentos.id }).from(lancamentos).where(eq(lancamentos.vendaId, vendaId));
  await registrarEvento({
    vendaId,
    veiculoId: venda.veiculoId,
    clienteId: venda.clienteId,
    titulo: "Venda cancelada",
    detalhe: [trocasRemovidas && `${trocasRemovidas} carro(s) da troca removido(s)`, pagos.length && `${pagos.length} valor(es) já recebido(s) continuam no caixa`].filter(Boolean).join(" · ") || undefined,
  });
  atualizarTelas();
  return { ok: true, mensagem: pagos.length ? "Venda cancelada. Valores já recebidos continuam no caixa: registre a devolução se houver." : "Venda cancelada." };
}

/** Completa dados que o contrato precisa (salvos no veículo e no cliente) */
export async function completarDadosContrato(vendaId: number, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [venda] = await db.select().from(vendas).where(eq(vendas.id, vendaId));
  if (!venda) return { ok: false, erro: "Venda não encontrada." };
  const veic: Partial<typeof veiculos.$inferInsert> = {};
  for (const campo of ["placa", "chassi", "renavam", "cor"] as const) {
    const v = texto(form, campo);
    if (v) veic[campo] = campo === "cor" || campo === "renavam" ? v : v.toUpperCase();
  }
  const cli: Partial<typeof clientes.$inferInsert> = {};
  for (const campo of ["cpf", "endereco", "cidade", "telefone"] as const) {
    const v = texto(form, campo);
    if (v) cli[campo] = v;
  }
  if (Object.keys(veic).length) await db.update(veiculos).set(veic).where(eq(veiculos.id, venda.veiculoId));
  if (Object.keys(cli).length) await db.update(clientes).set(cli).where(eq(clientes.id, venda.clienteId));
  atualizarTelas();
  return { ok: true, mensagem: "Dados salvos." };
}

export async function salvarObservacoes(vendaId: number, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  await db.update(vendas).set({ observacoes: texto(form, "observacoes"), dataVenda: texto(form, "dataVenda") ?? hojeISO() }).where(eq(vendas.id, vendaId));
  atualizarTelas();
  return { ok: true, mensagem: "Venda atualizada." };
}
