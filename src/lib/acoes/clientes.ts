"use server";

import { eq } from "drizzle-orm";
import { redirect } from "next/navigation";
import { banco, schema } from "@/db";
import { exigirLogin } from "@/lib/auth";
import { type Resultado, atualizarTelas, registrarEvento, texto } from "./comum";

const { clientes, vendas } = schema;

function lerCliente(form: FormData) {
  return {
    nome: texto(form, "nome") ?? "",
    telefone: texto(form, "telefone"),
    email: texto(form, "email"),
    cpf: texto(form, "cpf"),
    endereco: texto(form, "endereco"),
    cidade: texto(form, "cidade"),
    origem: texto(form, "origem"),
    interesse: texto(form, "interesse"),
    observacoes: texto(form, "observacoes"),
  };
}

export async function salvarCliente(id: number | null, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const dados = lerCliente(form);
  if (dados.nome.length < 2) return { ok: false, erro: "Informe o nome do cliente." };
  const db = await banco();
  if (id) {
    await db.update(clientes).set(dados).where(eq(clientes.id, id));
    atualizarTelas();
    return { ok: true, mensagem: "Cliente atualizado." };
  }
  const [novo] = await db.insert(clientes).values(dados).returning({ id: clientes.id });
  await registrarEvento({ clienteId: novo.id, titulo: "Cliente cadastrado" });
  atualizarTelas();
  redirect(`/painel/clientes/${novo.id}`);
}

export async function excluirCliente(id: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [venda] = await db.select({ id: vendas.id }).from(vendas).where(eq(vendas.clienteId, id));
  if (venda) return { ok: false, erro: "Este cliente tem venda registrada e não pode ser excluído." };
  await db.delete(clientes).where(eq(clientes.id, id));
  atualizarTelas();
  redirect("/painel/clientes");
}
