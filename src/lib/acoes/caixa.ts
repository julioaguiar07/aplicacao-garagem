"use server";

import { randomUUID } from "node:crypto";
import { and, eq, gte, isNull } from "drizzle-orm";
import { banco, schema } from "@/db";
import { exigirLogin } from "@/lib/auth";
import { apagarArquivo, salvarArquivo } from "@/lib/armazenamento";
import { CATEGORIAS_ENTRADA, CATEGORIAS_SAIDA, hojeISO, paraCentavos, somarMeses } from "@/lib/dominio";
import { type Resultado, arquivos, atualizarTelas, inteiro, paraBuffer, texto } from "./comum";

const { lancamentos, contas } = schema;

export async function novoLancamento(_: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const tipo = texto(form, "tipo") === "entrada" ? "entrada" : "saida";
  const descricao = texto(form, "descricao");
  const categoria = texto(form, "categoria");
  const valor = paraCentavos(texto(form, "valor"));
  const vencimento = texto(form, "vencimento") ?? hojeISO();
  if (!descricao) return { ok: false, erro: "Descreva o lançamento." };
  if (!valor) return { ok: false, erro: "Informe o valor." };
  if (!categoria || !(tipo === "entrada" ? CATEGORIAS_ENTRADA : CATEGORIAS_SAIDA).includes(categoria)) return { ok: false, erro: "Escolha a categoria." };
  const repetir = Math.min(36, Math.max(1, inteiro(form, "repetirMeses") ?? 1));
  const pago = form.get("pago") === "on";
  const [comprovante] = arquivos(form, "comprovante");
  const comprovanteChave = comprovante ? await salvarArquivo("privado/comprovantes", comprovante.name, await paraBuffer(comprovante)) : null;
  const grupo = repetir > 1 ? randomUUID() : null;
  const db = await banco();
  for (let i = 0; i < repetir; i++) {
    const venc = somarMeses(vencimento, i);
    await db.insert(lancamentos).values({
      tipo,
      descricao,
      categoria,
      valor,
      vencimento: venc,
      pagoEm: pago && i === 0 ? vencimento : null,
      contaId: inteiro(form, "contaId"),
      grupoRecorrencia: grupo,
      comprovanteChave: i === 0 ? comprovanteChave : null,
      observacoes: texto(form, "observacoes"),
    });
  }
  atualizarTelas();
  return { ok: true, mensagem: repetir > 1 ? `${repetir} lançamentos criados, um por mês.` : "Lançamento criado." };
}

export async function darBaixa(id: number, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [comprovante] = arquivos(form, "comprovante");
  const comprovanteChave = comprovante ? await salvarArquivo("privado/comprovantes", comprovante.name, await paraBuffer(comprovante)) : undefined;
  const valor = paraCentavos(texto(form, "valor"));
  await db
    .update(lancamentos)
    .set({
      pagoEm: texto(form, "pagoEm") ?? hojeISO(),
      contaId: inteiro(form, "contaId"),
      ...(valor ? { valor } : {}),
      ...(comprovanteChave ? { comprovanteChave } : {}),
    })
    .where(eq(lancamentos.id, id));
  atualizarTelas();
  return { ok: true, mensagem: "Baixa registrada." };
}

export async function estornarBaixa(id: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  await db.update(lancamentos).set({ pagoEm: null }).where(eq(lancamentos.id, id));
  atualizarTelas();
  return { ok: true };
}

/** Exclui um lançamento; com "futuros", apaga também as próximas repetições em aberto */
export async function excluirLancamento(id: number, futuros = false): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [l] = await db.select().from(lancamentos).where(eq(lancamentos.id, id));
  if (!l) return { ok: false, erro: "Lançamento não encontrado." };
  if (l.vendaId) return { ok: false, erro: "Este valor pertence a uma venda. Altere pela venda." };
  if (futuros && l.grupoRecorrencia) {
    await db
      .delete(lancamentos)
      .where(and(eq(lancamentos.grupoRecorrencia, l.grupoRecorrencia), gte(lancamentos.vencimento, l.vencimento), isNull(lancamentos.pagoEm)));
  }
  await db.delete(lancamentos).where(eq(lancamentos.id, id));
  await apagarArquivo(l.comprovanteChave);
  atualizarTelas();
  return { ok: true };
}

export async function salvarConta(_: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const nome = texto(form, "nome");
  if (!nome) return { ok: false, erro: "Dê um nome à conta." };
  const db = await banco();
  const id = inteiro(form, "id");
  const valores = { nome, tipo: texto(form, "tipo") === "caixa" ? "caixa" : "banco", saldoInicial: paraCentavos(texto(form, "saldoInicial")) ?? 0 };
  if (id) await db.update(contas).set(valores).where(eq(contas.id, id));
  else await db.insert(contas).values(valores);
  atualizarTelas();
  return { ok: true, mensagem: "Conta salva." };
}
