import { NextResponse, type NextRequest } from "next/server";
import { COOKIE_SESSAO, tokenValido } from "@/lib/sessao";

// Checagem rápida de login antes de abrir o painel ou arquivos privados.
// Arquivos em /arquivos/publico/ (fotos da vitrine) não exigem login.
export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/arquivos/publico/")) return NextResponse.next();

  if (await tokenValido(request.cookies.get(COOKIE_SESSAO)?.value)) return NextResponse.next();

  if (pathname.startsWith("/arquivos/")) return new NextResponse("Não autorizado", { status: 401 });
  const destino = new URL("/entrar", request.url);
  destino.searchParams.set("voltar", pathname + request.nextUrl.search);
  return NextResponse.redirect(destino);
}

export const config = {
  matcher: ["/painel/:path*", "/arquivos/:path*"],
};
