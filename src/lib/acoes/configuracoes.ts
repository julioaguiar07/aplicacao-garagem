"use server";

import { banco, schema } from "@/db";
import { conferirSenha, exigirLogin, trocarSenha } from "@/lib/auth";
import { type Resultado, atualizarTelas, texto } from "./comum";
import type { DadosLoja } from "@/lib/consultas/configuracoes";

export async function alterarSenha(_: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const atual = String(form.get("atual") ?? "");
  const nova = String(form.get("nova") ?? "");
  const confirmar = String(form.get("confirmar") ?? "");
  if (!(await conferirSenha(atual))) return { ok: false, erro: "A senha atual não confere." };
  if (nova.length < 8) return { ok: false, erro: "A nova senha precisa ter ao menos 8 caracteres." };
  if (nova !== confirmar) return { ok: false, erro: "A confirmação não é igual à nova senha." };
  await trocarSenha(nova);
  return { ok: true, mensagem: "Senha alterada." };
}

export async function salvarLoja(_: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const num = (c: string, padrao: number) => {
    const n = Number(texto(form, c)?.replace(",", "."));
    return Number.isFinite(n) && n >= 0 ? n : padrao;
  };
  const loja: DadosLoja = {
    whatsapp: (texto(form, "whatsapp") ?? "").replace(/\D/g, ""),
    telefone: texto(form, "telefone") ?? "",
    endereco: texto(form, "endereco") ?? "",
    cidade: texto(form, "cidade") ?? "",
    cep: texto(form, "cep") ?? "",
    cnpj: texto(form, "cnpj") ?? "",
    razaoSocial: texto(form, "razaoSocial") ?? "",
    simulacao: { entradaPct: num("entradaPct", 30), taxaMensalPct: num("taxaMensalPct", 1.99), meses: Math.round(num("meses", 48)) },
  };
  if (!loja.whatsapp || loja.whatsapp.length < 12) return { ok: false, erro: "Informe o WhatsApp com DDI e DDD, ex.: 55 84 3062-2434." };
  const db = await banco();
  await db
    .insert(schema.configuracoes)
    .values({ chave: "loja", valor: loja })
    .onConflictDoUpdate({ target: schema.configuracoes.chave, set: { valor: loja } });
  atualizarTelas();
  return { ok: true, mensagem: "Dados da loja salvos." };
}
