import { NextResponse, type NextRequest } from "next/server";
import { MARCA, logo } from "@/lib/marca";
import { COOKIE_SESSAO } from "@/lib/sessao";

function hostDe(request: NextRequest) {
  return request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? "";
}

// Endereço do painel (adm-carmelo-multimarcas.up.railway.app): a raiz abre o painel, não a vitrine.
function enderecoDoPainel(host: string) {
  return host.startsWith("adm-");
}

// Endereços antigos do Railway (ex.: carmelo-multimarcas.up.railway.app) levam ao domínio da loja.
// Sem domínio próprio (demonstração), o endereço do Railway é o próprio site.
function enderecoAntigo(host: string) {
  return !!MARCA.site && host.endsWith(".up.railway.app") && !enderecoDoPainel(host);
}

// Checagem rápida: sem o cookie de sessão, vai para a tela de entrada.
// A assinatura do cookie é conferida no servidor (exigirLogin) em cada página e ação do painel.
// Arquivos em /arquivos/publico/ (fotos da vitrine) não exigem login.
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const host = hostDe(request);
  if (enderecoAntigo(host)) return NextResponse.redirect(`${MARCA.site}${pathname}${search}`, 308);
  if (pathname === "/favicon.ico") return NextResponse.redirect(new URL(logo("favicon.ico"), request.url), 308);
  const areaRestrita = pathname.startsWith("/painel") || pathname.startsWith("/arquivos/");
  if (!areaRestrita) {
    return pathname === "/" && enderecoDoPainel(host) ? NextResponse.redirect(new URL("/painel", request.url)) : NextResponse.next();
  }
  if (pathname.startsWith("/arquivos/publico/")) return NextResponse.next();
  if (request.cookies.get(COOKIE_SESSAO)?.value) return NextResponse.next();
  if (pathname.startsWith("/arquivos/")) return new NextResponse("Não autorizado", { status: 401 });
  const destino = new URL("/entrar", request.url);
  destino.searchParams.set("voltar", pathname + search);
  return NextResponse.redirect(destino);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image).*)"],
};
