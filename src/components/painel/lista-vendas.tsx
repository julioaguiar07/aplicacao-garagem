"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { ETAPAS_VENDA, FORMAS_PAGAMENTO, type EtapaVenda, type FormaPagamento, dataBR, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export interface LinhaVenda {
  id: number;
  veiculo: string;
  cliente: string;
  etapa: string;
  data: string;
  valor: number;
  lucro: number;
  forma: string | null;
  dias: number;
}

const FILTROS = ["todas", "andamento", "fechadas", "cancelada"] as const;
const NOME = { todas: "Todas", andamento: "Em andamento", fechadas: "Fechadas", cancelada: "Canceladas" };
const FECHADAS: string[] = ["contrato", "transferencia", "entregue"];

export function ListaVendas({ vendas }: { vendas: LinhaVenda[] }) {
  const [filtro, setFiltro] = useState<(typeof FILTROS)[number]>("todas");
  const [busca, setBusca] = useState("");
  const passa = (v: LinhaVenda, f: (typeof FILTROS)[number]) =>
    f === "todas" ? v.etapa !== "cancelada" : f === "cancelada" ? v.etapa === "cancelada" : f === "fechadas" ? FECHADAS.includes(v.etapa) : !FECHADAS.includes(v.etapa) && v.etapa !== "cancelada";
  const lista = useMemo(() => {
    const t = busca.toLowerCase();
    return vendas.filter((v) => passa(v, filtro) && (!t || `${v.veiculo} ${v.cliente}`.toLowerCase().includes(t)));
  }, [vendas, filtro, busca]);
  const total = lista.reduce((s, v) => s + v.valor, 0);
  const lucro = lista.reduce((s, v) => s + v.lucro, 0);

  return (
    <section className="rounded-[var(--radius-card)] border border-linha/60 bg-grafite">
      <div className="flex flex-wrap items-center gap-3 p-5 pb-4">
        <h2 className="display mr-auto text-[17px] font-semibold">Todas as vendas</h2>
        <div className="flex gap-1.5 overflow-x-auto">
          {FILTROS.map((f) => (
            <button
              key={f}
              onClick={() => setFiltro(f)}
              className={cn("shrink-0 rounded-full border px-3 py-1.5 text-xs", filtro === f ? "border-laranja bg-laranja/10 text-laranja" : "border-linha text-nevoa hover:text-giz")}
            >
              {NOME[f]} <span className="num opacity-70">{vendas.filter((v) => passa(v, f)).length}</span>
            </button>
          ))}
        </div>
        <label className="relative flex items-center">
          <Search size={15} className="pointer-events-none absolute left-3 text-nevoa" />
          <input value={busca} onChange={(e) => setBusca(e.target.value)} type="search" placeholder="Carro ou cliente" className="h-9 w-52 rounded-full border border-linha bg-asfalto pl-9 pr-3 text-sm focus:border-laranja/60 focus:outline-none" />
        </label>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[820px] text-sm">
          <thead>
            <tr className="border-y border-linha/60 text-left text-xs text-nevoa">
              <th className="px-5 py-2.5 font-medium">Veículo</th>
              <th className="px-3 py-2.5 font-medium">Cliente</th>
              <th className="px-3 py-2.5 font-medium">Pagamento</th>
              <th className="px-3 py-2.5 font-medium">Etapa</th>
              <th className="px-3 py-2.5 font-medium">Data</th>
              <th className="px-3 py-2.5 text-right font-medium">Giro</th>
              <th className="px-3 py-2.5 text-right font-medium">Valor</th>
              <th className="px-5 py-2.5 text-right font-medium">Lucro</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((v) => (
              <tr key={v.id} className="border-b border-linha/40 hover:bg-chumbo/40">
                <td className="px-5 py-3 font-medium">
                  <Link href={`/painel/vendas/${v.id}`} className="hover:text-laranja">
                    {v.veiculo}
                  </Link>
                </td>
                <td className="px-3 py-3 text-nevoa">{v.cliente}</td>
                <td className="px-3 py-3 text-xs text-nevoa">{v.forma ? FORMAS_PAGAMENTO[v.forma as FormaPagamento] : "—"}</td>
                <td className="px-3 py-3">
                  <span className={cn("whitespace-nowrap rounded-full border px-2 py-0.5 text-xs", v.etapa === "cancelada" ? "border-perigo/40 text-perigo" : FECHADAS.includes(v.etapa) ? "border-linha text-nevoa" : "border-laranja/40 text-laranja")}>
                    {ETAPAS_VENDA[v.etapa as EtapaVenda]}
                  </span>
                </td>
                <td className="num px-3 py-3 text-nevoa">{dataBR(v.data)}</td>
                <td className="num whitespace-nowrap px-3 py-3 text-right text-nevoa">{v.dias} dias</td>
                <td className="num px-3 py-3 text-right">{reais(v.valor)}</td>
                <td className={cn("num px-5 py-3 text-right", v.etapa === "cancelada" ? "text-nevoa-2 line-through" : v.lucro >= 0 ? "text-sucesso" : "text-perigo")}>{reais(v.lucro)}</td>
              </tr>
            ))}
          </tbody>
          {lista.length > 0 && (
            <tfoot>
              <tr className="text-sm">
                <td colSpan={6} className="px-5 py-3 text-right text-nevoa">{lista.length} vendas</td>
                <td className="num px-3 py-3 text-right font-semibold">{reais(total)}</td>
                <td className="num px-5 py-3 text-right font-semibold text-sucesso">{reais(lucro)}</td>
              </tr>
            </tfoot>
          )}
        </table>
        {lista.length === 0 && <p className="p-8 text-center text-sm text-nevoa">Nenhuma venda com esse filtro.</p>}
      </div>
    </section>
  );
}
