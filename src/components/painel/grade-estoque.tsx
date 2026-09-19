"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowUpRight, Calendar, CircleAlert, Clock, EyeOff, Fuel, Gauge, LayoutGrid, List, Plus, Search, Settings2 } from "lucide-react";
import { FotoCarro } from "@/components/foto-carro";
import { SeloMarca, StatusVeiculoSelo } from "@/components/status-veiculo";
import { LinkBotao } from "@/components/ui";
import { STATUS_VEICULO, type StatusVeiculo, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export interface CartaoEstoque {
  id: number;
  marca: string;
  modelo: string;
  versao: string | null;
  ano: number;
  km: number | null;
  cambio: string;
  combustivel: string;
  categoria: string;
  preco: number;
  status: string;
  publicado: boolean;
  dias: number;
  pendencias: number;
  foto: string | null;
}

type Filtro = StatusVeiculo | "estoque" | "pendencias";
const FILTROS: Filtro[] = ["estoque", "disponivel", "em_preparacao", "reservado", "consignado", "rascunho", "vendido", "pendencias"];
const NOME_FILTRO = (f: Filtro) => (f === "estoque" ? "Em estoque" : f === "pendencias" ? "Com pendências" : STATUS_VEICULO[f]);
const km = (v: number | null) => (v === null ? "km não informado" : `${v.toLocaleString("pt-BR")} km`);

function Chip({ icone: Icone, children, alerta }: { icone: typeof Gauge; children: React.ReactNode; alerta?: boolean }) {
  return (
    <span className={cn("flex min-w-0 items-center gap-2 rounded-xl border px-2.5 py-2 text-xs", alerta ? "border-laranja/40 bg-laranja/10 text-laranja" : "border-linha/70 bg-chumbo/60 text-nevoa")}>
      <Icone size={14} className="shrink-0" />
      <span className="num truncate">{children}</span>
    </span>
  );
}

export function GradeEstoque({ veiculos, soPendencias }: { veiculos: CartaoEstoque[]; soPendencias?: boolean }) {
  const [filtro, setFiltro] = useState<Filtro>(soPendencias ? "pendencias" : "estoque");
  const [busca, setBusca] = useState("");
  const [modo, setModo] = useState<"grade" | "lista">("grade");

  const passa = (v: CartaoEstoque, f: Filtro) =>
    f === "estoque" ? v.status !== "vendido" : f === "pendencias" ? v.status !== "vendido" && v.pendencias > 0 : v.status === f;

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return veiculos.filter((v) => passa(v, filtro) && (!termo || `${v.marca} ${v.modelo} ${v.versao ?? ""} ${v.ano}`.toLowerCase().includes(termo)));
  }, [veiculos, filtro, busca]);

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <div className="-mx-1 flex basis-full gap-1.5 overflow-x-auto px-1 scrollbar-fina lg:basis-auto lg:flex-1">
          {FILTROS.map((f) => {
            const n = veiculos.filter((v) => passa(v, f)).length;
            if (!n && f !== "estoque" && f !== filtro) return null;
            return (
              <button
                key={f}
                onClick={() => setFiltro(f)}
                className={cn(
                  "flex shrink-0 items-center gap-2 rounded-full border px-3.5 py-1.5 text-sm transition",
                  filtro === f ? "border-laranja bg-laranja/10 text-laranja" : "border-linha text-nevoa hover:text-giz",
                )}
              >
                {NOME_FILTRO(f)}
                <span className="num text-xs opacity-70">{n}</span>
              </button>
            );
          })}
        </div>

        <label className="relative flex flex-1 items-center lg:flex-none">
          <Search size={15} className="pointer-events-none absolute left-3 text-nevoa" />
          <input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            type="search"
            placeholder="Filtrar por modelo"
            className="h-9 w-full rounded-full border border-linha bg-grafite pl-9 pr-3 text-sm placeholder:text-nevoa-2 focus:border-laranja/60 focus:outline-none lg:w-52"
          />
        </label>

        <div className="flex rounded-full border border-linha p-0.5" role="group" aria-label="Modo de exibição">
          {(["grade", "lista"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setModo(m)}
              aria-pressed={modo === m}
              className={cn("flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs", modo === m ? "bg-chumbo text-giz" : "text-nevoa")}
            >
              {m === "grade" ? <LayoutGrid size={14} /> : <List size={14} />}
              {m === "grade" ? "Cards" : "Lista"}
            </button>
          ))}
        </div>
      </div>

      {visiveis.length === 0 ? (
        <div className="rounded-[var(--radius-card)] border border-dashed border-linha p-12 text-center text-sm text-nevoa">
          {veiculos.length === 0 ? "Nenhum carro cadastrado ainda." : "Nenhum carro com esse filtro. Troque o status ou limpe a busca."}
          {veiculos.length === 0 && (
            <div className="mt-4">
              <LinkBotao href="/painel/estoque/novo" variante="primario">
                <Plus size={16} /> Cadastrar o primeiro carro
              </LinkBotao>
            </div>
          )}
        </div>
      ) : modo === "grade" ? (
        <ul className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {visiveis.map((v) => (
            <li key={v.id}>
              <Link
                href={`/painel/estoque/${v.id}`}
                className="group block rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-4 transition hover:border-laranja/50 hover:bg-[#1f2227]"
              >
                <div className="flex items-start gap-3">
                  <SeloMarca marca={v.marca} />
                  <div className="min-w-0 flex-1">
                    <h3 className="display truncate text-lg font-semibold leading-tight">
                      {v.marca} {v.modelo}
                    </h3>
                    <p className="truncate text-sm text-nevoa">{[v.versao, v.categoria].filter(Boolean).join(" · ")}</p>
                  </div>
                  <span className="flex items-center gap-0.5 text-sm font-medium text-laranja opacity-80 transition group-hover:opacity-100">
                    Abrir <ArrowUpRight size={15} />
                  </span>
                </div>

                <div className="mt-3 flex items-end justify-between gap-2">
                  <div>
                    <p className="text-xs text-nevoa">Preço anunciado</p>
                    <p className="display num text-[22px] font-bold">{reais(v.preco)}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <StatusVeiculoSelo status={v.status} />
                    {!v.publicado && v.status !== "vendido" && (
                      <span className="flex items-center gap-1 text-[11px] text-nevoa-2">
                        <EyeOff size={12} /> fora da vitrine
                      </span>
                    )}
                  </div>
                </div>

                <FotoCarro src={v.foto} alt={`${v.marca} ${v.modelo} ${v.ano}`} className="mt-3 aspect-[4/3] rounded-2xl" />

                <div className="mt-3 grid grid-cols-2 gap-2">
                  <Chip icone={Calendar}>{v.ano}</Chip>
                  <Chip icone={Gauge}>{km(v.km)}</Chip>
                  <Chip icone={Settings2}>{v.cambio}</Chip>
                  <Chip icone={Fuel}>{v.combustivel}</Chip>
                  <Chip icone={Clock} alerta={v.status !== "vendido" && v.dias >= 45}>
                    {v.status === "vendido" ? "Vendido" : v.dias === 0 ? "Chegou hoje" : `${v.dias} ${v.dias === 1 ? "dia" : "dias"} no pátio`}
                  </Chip>
                  <Chip icone={CircleAlert} alerta={v.pendencias > 0}>
                    {v.pendencias ? `${v.pendencias} doc${v.pendencias > 1 ? "s" : ""} pendente${v.pendencias > 1 ? "s" : ""}` : "Docs ok"}
                  </Chip>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="overflow-x-auto rounded-[var(--radius-card)] border border-linha/60 bg-grafite">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="border-b border-linha/60 text-left text-xs text-nevoa">
                <th className="px-4 py-3 font-medium">Veículo</th>
                <th className="px-3 py-3 font-medium">Ano</th>
                <th className="px-3 py-3 font-medium">Km</th>
                <th className="px-3 py-3 font-medium">No pátio</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-3 py-3 font-medium">Docs pendentes</th>
                <th className="px-4 py-3 text-right font-medium">Preço</th>
              </tr>
            </thead>
            <tbody>
              {visiveis.map((v) => (
                <tr key={v.id} className="border-b border-linha/40 last:border-0 hover:bg-chumbo/40">
                  <td className="px-4 py-2.5">
                    <Link href={`/painel/estoque/${v.id}`} className="flex items-center gap-3 hover:text-laranja">
                      <FotoCarro src={v.foto} alt="" className="h-10 w-14 shrink-0 rounded-lg" sizes="56px" />
                      <span className="font-medium">
                        {v.marca} {v.modelo} <span className="text-nevoa">{v.versao}</span>
                      </span>
                    </Link>
                  </td>
                  <td className="num px-3 py-2.5 text-nevoa">{v.ano}</td>
                  <td className="num px-3 py-2.5 text-nevoa">{km(v.km)}</td>
                  <td className={cn("num px-3 py-2.5", v.dias >= 45 && v.status !== "vendido" ? "text-laranja" : "text-nevoa")}>{v.status === "vendido" ? "—" : `${v.dias} dias`}</td>
                  <td className="px-3 py-2.5">
                    <StatusVeiculoSelo status={v.status} />
                  </td>
                  <td className={cn("px-3 py-2.5", v.pendencias ? "text-laranja" : "text-nevoa")}>{v.pendencias || "—"}</td>
                  <td className="num px-4 py-2.5 text-right font-medium">{reais(v.preco)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
