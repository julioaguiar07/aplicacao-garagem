import "server-only";
import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { banco, schema } from "@/db";
import { COOKIE_SESSAO, tokenValido } from "@/lib/sessao";

const CHAVE_SENHA = "senha_admin";

/** Hash da senha do administrador; na primeira vez usa ADMIN_SENHA_INICIAL (ou "carmelo" em desenvolvimento) */
export async function hashSenhaAtual() {
  const db = await banco();
  const [linha] = await db.select().from(schema.configuracoes).where(eq(schema.configuracoes.chave, CHAVE_SENHA));
  if (linha) return linha.valor as string;
  const inicial = process.env.ADMIN_SENHA_INICIAL ?? (process.env.NODE_ENV === "production" ? null : "carmelo");
  if (!inicial) throw new Error("Defina ADMIN_SENHA_INICIAL para o primeiro acesso");
  const hash = await bcrypt.hash(inicial, 12);
  await db.insert(schema.configuracoes).values({ chave: CHAVE_SENHA, valor: hash }).onConflictDoNothing();
  return hash;
}

export async function conferirSenha(senha: string) {
  return bcrypt.compare(senha, await hashSenhaAtual());
}

export async function trocarSenha(nova: string) {
  const db = await banco();
  const hash = await bcrypt.hash(nova, 12);
  await db
    .insert(schema.configuracoes)
    .values({ chave: CHAVE_SENHA, valor: hash })
    .onConflictDoUpdate({ target: schema.configuracoes.chave, set: { valor: hash } });
}

/** Garante login em páginas e ações do painel */
export async function exigirLogin() {
  const token = (await cookies()).get(COOKIE_SESSAO)?.value;
  if (!(await tokenValido(token))) redirect("/entrar");
}
