"use client";

import { useState } from "react";
import { parcelaPrice, reais } from "@/lib/formato";
import { SIMULACAO } from "@/lib/vitrine";

const PRAZOS = [24, 36, 48, 60];

export function Simulador({ preco }: { preco: number }) {
  const [entradaPct, setEntradaPct] = useState(SIMULACAO.entradaPct);
  const [meses, setMeses] = useState(SIMULACAO.meses);
  const entrada = (preco * entradaPct) / 100;
  const parcela = parcelaPrice(preco - entrada, SIMULACAO.taxaMensalPct, meses);

  return (
    <div className="rounded-md border border-linha/70 bg-[#141518] p-5">
      <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-nevoa">Simule a parcela</p>

      <label className="mt-4 block">
        <span className="flex justify-between text-sm">
          Entrada <span className="num text-nevoa">{reais(entrada)} ({entradaPct}%)</span>
        </span>
        <input
          type="range"
          min={0}
          max={80}
          step={5}
          value={entradaPct}
          onChange={(e) => setEntradaPct(Number(e.target.value))}
          className="mt-2 w-full accent-[#ff7a1a]"
        />
      </label>

      <div className="mt-4">
        <span className="text-sm">Prazo</span>
        <div className="mt-2 grid grid-cols-4 gap-1.5">
          {PRAZOS.map((p) => (
            <button
              key={p}
              onClick={() => setMeses(p)}
              aria-pressed={meses === p}
              className={`num rounded-md border py-2 text-sm ${meses === p ? "border-laranja bg-laranja/10 text-laranja" : "border-linha text-nevoa hover:text-giz"}`}
            >
              {p}x
            </button>
          ))}
        </div>
      </div>

      <p className="mt-5 text-sm text-nevoa">Parcela estimada</p>
      <p className="display num text-3xl font-bold">
        {meses}x {reais(parcela)}
      </p>
      <p className="mt-2 text-[11px] leading-relaxed text-nevoa-2">
        Taxa de referência de {SIMULACAO.taxaMensalPct.toLocaleString("pt-BR")}% ao mês. Valor ilustrativo, sujeito à aprovação de crédito.
      </p>
    </div>
  );
}
