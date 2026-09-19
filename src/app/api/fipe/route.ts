import { NextResponse, type NextRequest } from "next/server";
import { exigirLogin } from "@/lib/auth";

// Consulta a Tabela FIPE (API pública Parallelum) para o cadastro de veículos.
// Uso: ?etapa=marcas | modelos&marca= | anos&marca=&modelo= | valor&marca=&modelo=&ano=

const BASE = "https://parallelum.com.br/fipe/api/v1/carros/marcas";

export async function GET(req: NextRequest) {
  await exigirLogin();
  const p = req.nextUrl.searchParams;
  const etapa = p.get("etapa");
  const [marca, modelo, ano] = [p.get("marca"), p.get("modelo"), p.get("ano")].map((x) => (x ? encodeURIComponent(x) : null));
  const url =
    etapa === "marcas"
      ? BASE
      : etapa === "modelos" && marca
        ? `${BASE}/${marca}/modelos`
        : etapa === "anos" && marca && modelo
          ? `${BASE}/${marca}/modelos/${modelo}/anos`
          : etapa === "valor" && marca && modelo && ano
            ? `${BASE}/${marca}/modelos/${modelo}/anos/${ano}`
            : null;
  if (!url) return NextResponse.json({ erro: "Consulta inválida" }, { status: 400 });
  try {
    const r = await fetch(url, { next: { revalidate: 86_400 }, signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error(String(r.status));
    const dados = await r.json();
    return NextResponse.json(etapa === "modelos" ? dados.modelos : dados);
  } catch {
    return NextResponse.json({ erro: "A tabela FIPE não respondeu agora. Preencha manualmente." }, { status: 502 });
  }
}
