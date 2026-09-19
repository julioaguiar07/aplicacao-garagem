import "server-only";
import { randomBytes } from "node:crypto";
import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { banco, schema } from "@/db";
import { COOKIE_SESSAO, tokenValido } from "@/lib/sessao";

const CHAVE_SENHA = "senha_admin";
const CHAVE_SEGREDO = "segredo_sessao";

async function lerConfig(chave: string) {
  const db = await banco();
  const [linha] = await db.select().from(schema.configuracoes).where(eq(schema.configuracoes.chave, chave));
  return linha?.valor as string | undefined;
}

/** Segredo que assina o cookie: SESSAO_SEGREDO ou um valor aleatório gerado uma vez e guardado no banco */
export async function segredoSessao() {
  if (process.env.SESSAO_SEGREDO) return process.env.SESSAO_SEGREDO;
  const salvo = await lerConfig(CHAVE_SEGREDO);
  if (salvo) return salvo;
  const db = await banco();
  await db.insert(schema.configuracoes).values({ chave: CHAVE_SEGREDO, valor: randomBytes(48).toString("base64url") }).onConflictDoNothing();
  return (await lerConfig(CHAVE_SEGREDO))!;
}

/**
 * Hash da senha do administrador. Em produção vem da migração do sistema antigo (mesma senha de antes)
 * ou de ADMIN_SENHA_INICIAL; em desenvolvimento, "carmelo".
 */
export async function hashSenhaAtual() {
  const salvo = await lerConfig(CHAVE_SENHA);
  if (salvo) return salvo;
  const inicial = process.env.ADMIN_SENHA_INICIAL ?? (process.env.NODE_ENV === "production" ? null : "carmelo");
  if (!inicial) throw new Error("Senha do administrador não definida: rode a migração ou defina ADMIN_SENHA_INICIAL");
  await trocarSenha(inicial, false);
  return (await lerConfig(CHAVE_SENHA))!;
}

export async function conferirSenha(senha: string) {
  return bcrypt.compare(senha, await hashSenhaAtual());
}

export async function trocarSenha(nova: string, sobrescrever = true) {
  const db = await banco();
  const hash = await bcrypt.hash(nova, 12);
  const insert = db.insert(schema.configuracoes).values({ chave: CHAVE_SENHA, valor: hash });
  await (sobrescrever ? insert.onConflictDoUpdate({ target: schema.configuracoes.chave, set: { valor: hash } }) : insert.onConflictDoNothing());
}

/** Garante login em páginas e ações do painel */
export async function exigirLogin() {
  const token = (await cookies()).get(COOKIE_SESSAO)?.value;
  if (!(await tokenValido(token, await segredoSessao()))) redirect("/entrar");
}
