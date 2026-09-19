import { NextResponse, type NextRequest } from "next/server";
import { COOKIE_SESSAO } from "@/lib/sessao";

// Endereço do painel (adm-carmelo-multimarcas.up.railway.app): a raiz abre o painel, não a vitrine.
function enderecoDoPainel(request: NextRequest) {
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? "";
  return host.startsWith("adm-");
}

// Checagem rápida: sem o cookie de sessão, vai para a tela de entrada.
// A assinatura do cookie é conferida no servidor (exigirLogin) em cada página e ação do painel.
// Arquivos em /arquivos/publico/ (fotos da vitrine) não exigem login.
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname === "/") {
    return enderecoDoPainel(request) ? NextResponse.redirect(new URL("/painel", request.url)) : NextResponse.next();
  }
  if (pathname.startsWith("/arquivos/publico/")) return NextResponse.next();
  if (request.cookies.get(COOKIE_SESSAO)?.value) return NextResponse.next();
  if (pathname.startsWith("/arquivos/")) return new NextResponse("Não autorizado", { status: 401 });
  const destino = new URL("/entrar", request.url);
  destino.searchParams.set("voltar", pathname + request.nextUrl.search);
  return NextResponse.redirect(destino);
}

export const config = {
  matcher: ["/", "/painel/:path*", "/arquivos/:path*"],
};
