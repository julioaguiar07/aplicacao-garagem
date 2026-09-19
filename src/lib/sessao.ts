import { jwtVerify, SignJWT } from "jose";

// Sessão do administrador: JWT assinado num cookie httpOnly.
// Usado pelo proxy (checagem rápida) e pelo layout do painel (checagem definitiva).

export const COOKIE_SESSAO = "carmelo_sessao";
const DURACAO_S = 60 * 60 * 24 * 14; // 14 dias

function segredo() {
  const s = process.env.SESSAO_SEGREDO;
  if (!s && process.env.NODE_ENV === "production") throw new Error("Defina SESSAO_SEGREDO em produção");
  return new TextEncoder().encode(s ?? "segredo-local-de-desenvolvimento-carmelo");
}

export async function criarToken() {
  return new SignJWT({ papel: "admin" })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${DURACAO_S}s`)
    .sign(segredo());
}

export async function tokenValido(token: string | undefined) {
  if (!token) return false;
  try {
    await jwtVerify(token, segredo());
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
