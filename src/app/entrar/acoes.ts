"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { conferirSenha } from "@/lib/auth";
import { COOKIE_SESSAO, OPCOES_COOKIE, criarToken } from "@/lib/sessao";

export async function entrar(_: string | null, form: FormData): Promise<string | null> {
  const senha = String(form.get("senha") ?? "");
  const voltar = String(form.get("voltar") ?? "/painel");
  if (!senha) return "Digite a senha.";
  if (!(await conferirSenha(senha))) return "Senha incorreta. Confira e tente de novo.";
  (await cookies()).set(COOKIE_SESSAO, await criarToken(), OPCOES_COOKIE);
  redirect(voltar.startsWith("/painel") ? voltar : "/painel");
}

export async function sair() {
  (await cookies()).delete(COOKIE_SESSAO);
  redirect("/entrar");
}
