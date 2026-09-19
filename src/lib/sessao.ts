import { jwtVerify, SignJWT } from "jose";

// Sessão do administrador: JWT assinado num cookie httpOnly.
// O segredo vem de SESSAO_SEGREDO ou, se não existir, é gerado e guardado no banco (ver lib/auth.ts).

export const COOKIE_SESSAO = "carmelo_sessao";
const DURACAO_S = 60 * 60 * 24 * 14; // 14 dias

const chave = (segredo: string) => new TextEncoder().encode(segredo);

export async function criarToken(segredo: string) {
  return new SignJWT({ papel: "admin" }).setProtectedHeader({ alg: "HS256" }).setIssuedAt().setExpirationTime(`${DURACAO_S}s`).sign(chave(segredo));
}

export async function tokenValido(token: string | undefined, segredo: string) {
  if (!token) return false;
  try {
    await jwtVerify(token, chave(segredo));
    return true;
  } catch {
    return false;
  }
}

export const OPCOES_COOKIE = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
  maxAge: DURACAO_S,
};
