import { banco, schema } from "@/db";

/** Linha do tempo: tudo o que acontece com veículos, vendas e clientes */
export async function registrarEvento(e: { titulo: string; detalhe?: string; veiculoId?: number | null; vendaId?: number | null; clienteId?: number | null }) {
  const db = await banco();
  await db.insert(schema.eventos).values({ titulo: e.titulo, detalhe: e.detalhe ?? null, veiculoId: e.veiculoId ?? null, vendaId: e.vendaId ?? null, clienteId: e.clienteId ?? null });
}
