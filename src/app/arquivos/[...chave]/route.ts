import path from "node:path";
import { MIME, lerArquivo } from "@/lib/armazenamento";
import { exigirLogin } from "@/lib/auth";

// Entrega fotos (públicas) e documentos (só com login; o proxy já barra antes).
export async function GET(_: Request, { params }: RouteContext<"/arquivos/[...chave]">) {
  const chave = (await params).chave.join("/");
  if (!chave.startsWith("publico/")) await exigirLogin();
  try {
    const dados = await lerArquivo(chave);
    return new Response(new Uint8Array(dados), {
      headers: {
        "Content-Type": MIME[path.extname(chave).toLowerCase()] ?? "application/octet-stream",
        // cada arquivo tem nome único (uuid), então pode ficar em cache para sempre
        "Cache-Control": chave.startsWith("publico/") ? "public, max-age=31536000, immutable" : "private, max-age=3600",
      },
    });
  } catch {
    return new Response("Arquivo não encontrado", { status: 404 });
  }
}
