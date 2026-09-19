"use client";

import { useActionState } from "react";
import { entrar } from "./acoes";

export function FormEntrar({ voltar }: { voltar: string }) {
  const [erro, acao, enviando] = useActionState(entrar, null);
  return (
    <form action={acao} className="mt-6 space-y-3">
      <input type="hidden" name="voltar" value={voltar} />
      <label className="block">
        <span className="text-xs text-nevoa">Senha</span>
        <input
          name="senha"
          type="password"
          autoComplete="current-password"
          autoFocus
          required
          className="mt-1 h-11 w-full rounded-xl border border-linha bg-asfalto px-3 text-sm focus:border-laranja/60 focus:outline-none"
        />
      </label>
      {erro && <p className="text-sm text-perigo">{erro}</p>}
      <button
        disabled={enviando}
        className="h-11 w-full rounded-xl bg-laranja text-sm font-semibold text-asfalto transition hover:bg-ambar disabled:opacity-60"
      >
        {enviando ? "Entrando…" : "Entrar"}
      </button>
    </form>
  );
}
