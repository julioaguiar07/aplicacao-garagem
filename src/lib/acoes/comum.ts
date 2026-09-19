import "server-only";
import { revalidatePath } from "next/cache";
export { registrarEvento } from "@/lib/negocio/eventos";

export type Resultado<T = undefined> = { ok: true; dados?: T; mensagem?: string } | { ok: false; erro: string };

/** Atualiza painel e vitrine depois de qualquer gravação */
export function atualizarTelas() {
  revalidatePath("/painel", "layout");
  revalidatePath("/", "layout");
}

export function texto(form: FormData, campo: string) {
  const v = form.get(campo);
  if (typeof v !== "string") return null;
  const t = v.trim();
  return t === "" ? null : t;
}

export function inteiro(form: FormData, campo: string) {
  const t = texto(form, campo);
  if (t === null) return null;
  const n = Number(t.replace(/\./g, ""));
  return Number.isFinite(n) ? Math.round(n) : null;
}

export function arquivos(form: FormData, campo: string) {
  return form.getAll(campo).filter((f): f is File => f instanceof File && f.size > 0);
}

export async function paraBuffer(f: File) {
  return Buffer.from(await f.arrayBuffer());
}
