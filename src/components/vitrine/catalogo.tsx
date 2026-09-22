"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Check, ChevronDown, Gauge, Settings2, Calendar, SlidersHorizontal, X } from "lucide-react";
import type { VeiculoPublico } from "@/lib/vitrine";
import { FotoCarro } from "@/components/foto-carro";
import { km, precoPartido, reais } from "@/lib/formato";
import { cn } from "@/lib/cn";

const FAIXAS = [
  { id: "ate50", rotulo: "Até R$ 50 mil", min: 0, max: 50_000 },
  { id: "50a80", rotulo: "R$ 50 a 80 mil", min: 50_000, max: 80_000 },
  { id: "80a120", rotulo: "R$ 80 a 120 mil", min: 80_000, max: 120_000 },
  { id: "120a200", rotulo: "R$ 120 a 200 mil", min: 120_000, max: 200_000 },
  { id: "200mais", rotulo: "Acima de R$ 200 mil", min: 200_000, max: Infinity },
];

const ORDENS = {
  recentes: { rotulo: "Mais recentes", fn: (a: VeiculoPublico, b: VeiculoPublico) => b.entrada.localeCompare(a.entrada) },
  menorPreco: { rotulo: "Menor preço", fn: (a: VeiculoPublico, b: VeiculoPublico) => a.preco - b.preco },
  maiorPreco: { rotulo: "Maior preço", fn: (a: VeiculoPublico, b: VeiculoPublico) => b.preco - a.preco },
  menorKm: { rotulo: "Menor km", fn: (a: VeiculoPublico, b: VeiculoPublico) => (a.km ?? Infinity) - (b.km ?? Infinity) },
};
type Ordem = keyof typeof ORDENS;

/** Silhuetas simples por categoria (traço único, no estilo dos ícones da referência) */
function IconeCategoria({ categoria }: { categoria: string }) {
  const caminhos: Record<string, string> = {
    Hatch: "M3 15h18v-3l-3-1-3-4H8L5 11l-2 1z",
    Sedan: "M2 15h20v-2.5l-4-1.5-3-4H9l-3 4-4 1.5z",
    SUV: "M3 15h18v-4l-2-1-2-4H6L4 10l-1 1z",
    Picape: "M2 15h20v-4h-8V7H8l-3 4H2z",
  };
  return (
    <svg viewBox="0 0 24 20" className="h-4 w-6" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinejoin="round" aria-hidden>
      <path d={caminhos[categoria] ?? caminhos.Hatch} />
      <circle cx="7" cy="15.5" r="1.8" fill="currentColor" />
      <circle cx="17" cy="15.5" r="1.8" fill="currentColor" />
    </svg>
  );
}

function Grupo({ titulo, children, inicial = true }: { titulo: string; children: React.ReactNode; inicial?: boolean }) {
  const [aberto, setAberto] = useState(inicial);
  return (
    <div className="border-b border-linha/70">
      <button
        onClick={() => setAberto((a) => !a)}
        aria-expanded={aberto}
        className="flex w-full items-center justify-between px-5 py-4 text-[13px] font-semibold uppercase tracking-[0.08em]"
      >
        {titulo}
        <ChevronDown size={16} className={cn("text-nevoa transition", aberto && "rotate-180")} />
      </button>
      {aberto && <div className="px-3 pb-4">{children}</div>}
    </div>
  );
}

function Opcao({ ativo, onClick, children }: { ativo: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={ativo}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left text-sm transition",
        ativo ? "bg-chumbo text-giz" : "text-giz/75 hover:bg-grafite hover:text-giz",
      )}
    >
      {children}
    </button>
  );
}

function Caixa({ ativo }: { ativo: boolean }) {
  return (
    <span className={cn("grid size-4 shrink-0 place-items-center rounded-[4px] border", ativo ? "border-laranja bg-laranja text-asfalto" : "border-nevoa-2")}>
      {ativo && <Check size={12} strokeWidth={3} />}
    </span>
  );
}

export function Catalogo({ veiculos, simulacao }: { veiculos: VeiculoPublico[]; simulacao: { entradaPct: number; taxaMensalPct: number; meses: number } }) {
  const [faixas, setFaixas] = useState<string[]>([]);
  const [categoria, setCategoria] = useState<string | null>(null);
  const [marcas, setMarcas] = useState<string[]>([]);
  const [cambio, setCambio] = useState<string | null>(null);
  const [ordem, setOrdem] = useState<Ordem>("recentes");
  const [filtrosAbertos, setFiltrosAbertos] = useState(false);

  const alternar = (lista: string[], item: string) => (lista.includes(item) ? lista.filter((x) => x !== item) : [...lista, item]);
  const categorias = [...new Set(veiculos.map((v) => v.categoria))];
  const todasMarcas = [...new Set(veiculos.map((v) => v.marca))].sort();
  const cambios = [...new Set(veiculos.map((v) => v.cambio))];
  const temFiltro = faixas.length > 0 || categoria || marcas.length > 0 || cambio;

  const lista = useMemo(
    () =>
      veiculos
        .filter((v) => !faixas.length || faixas.some((id) => { const f = FAIXAS.find((x) => x.id === id)!; return v.preco >= f.min && v.preco < f.max; }))
        .filter((v) => !categoria || v.categoria === categoria)
        .filter((v) => !marcas.length || marcas.includes(v.marca))
        .filter((v) => !cambio || v.cambio === cambio)
        .sort(ORDENS[ordem].fn),
    [veiculos, faixas, categoria, marcas, cambio, ordem],
  );

  const limpar = () => {
    setFaixas([]);
    setCategoria(null);
    setMarcas([]);
    setCambio(null);
  };

  return (
    <div id="estoque" className="mx-auto grid max-w-[1440px] lg:grid-cols-[280px_1fr]">
      {/* Filtros */}
      <aside
        className={cn(
          "border-r border-linha/70 bg-[#101114] lg:block",
          filtrosAbertos ? "fixed inset-0 z-50 block overflow-y-auto" : "hidden",
        )}
      >
        <div className="flex items-baseline justify-between border-b border-linha/70 px-5 py-5">
          <h2 className="display text-2xl font-bold">Filtros</h2>
          <div className="flex items-center gap-3">
            {temFiltro && (
              <button onClick={limpar} className="text-[11px] font-medium uppercase tracking-[0.1em] text-nevoa hover:text-laranja">
                Limpar filtros
              </button>
            )}
            <button className="lg:hidden" onClick={() => setFiltrosAbertos(false)} aria-label="Fechar filtros">
              <X size={20} />
            </button>
          </div>
        </div>

        <Grupo titulo="Faixa de preço">
          {FAIXAS.map((f) => (
            <Opcao key={f.id} ativo={faixas.includes(f.id)} onClick={() => setFaixas((l) => alternar(l, f.id))}>
              <Caixa ativo={faixas.includes(f.id)} />
              {f.rotulo}
            </Opcao>
          ))}
        </Grupo>

        <Grupo titulo="Categoria">
          {categorias.map((c) => (
            <Opcao key={c} ativo={categoria === c} onClick={() => setCategoria((a) => (a === c ? null : c))}>
              <IconeCategoria categoria={c} />
              <span className="flex-1">{c}</span>
              {categoria === c && <Check size={15} className="text-laranja" />}
            </Opcao>
          ))}
        </Grupo>

        <Grupo titulo="Marca">
          {todasMarcas.map((m) => (
            <Opcao key={m} ativo={marcas.includes(m)} onClick={() => setMarcas((l) => alternar(l, m))}>
              <Caixa ativo={marcas.includes(m)} />
              <span className="flex-1">{m}</span>
              <span className="num text-xs text-nevoa">{veiculos.filter((v) => v.marca === m).length}</span>
            </Opcao>
          ))}
        </Grupo>

        <Grupo titulo="Câmbio">
          {cambios.map((c) => (
            <Opcao key={c} ativo={cambio === c} onClick={() => setCambio((a) => (a === c ? null : c))}>
              <Caixa ativo={cambio === c} />
              {c}
            </Opcao>
          ))}
        </Grupo>

        {filtrosAbertos && (
          <div className="sticky bottom-0 border-t border-linha bg-[#101114] p-4 lg:hidden">
            <button onClick={() => setFiltrosAbertos(false)} className="h-11 w-full rounded-full bg-laranja font-semibold text-asfalto">
              Ver {lista.length} {lista.length === 1 ? "carro" : "carros"}
            </button>
          </div>
        )}
      </aside>

      {/* Resultados */}
      <section className="min-w-0 px-4 py-7 md:px-8">
        <div className="mb-6 flex flex-wrap items-end gap-x-4 gap-y-3">
          <h1 className="display text-[28px] font-bold leading-none md:text-[34px]">Escolha seu próximo carro</h1>
          <span className="num pb-1 text-[11px] font-medium uppercase tracking-[0.12em] text-nevoa">
            {lista.length} {lista.length === 1 ? "disponível" : "disponíveis"}
          </span>
          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={() => setFiltrosAbertos(true)}
              className="flex h-9 items-center gap-2 rounded-full border border-linha px-3.5 text-sm lg:hidden"
            >
              <SlidersHorizontal size={15} /> Filtros
            </button>
            <label className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.1em] text-nevoa">
              <span className="hidden sm:inline">Ordenar</span>
              <select
                value={ordem}
                onChange={(e) => setOrdem(e.target.value as Ordem)}
                className="h-9 rounded-md border border-linha bg-[#101114] px-3 text-xs font-semibold uppercase tracking-[0.06em] text-giz focus:border-laranja/60 focus:outline-none"
              >
                {Object.entries(ORDENS).map(([id, o]) => (
                  <option key={id} value={id}>
                    {o.rotulo}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {lista.length === 0 ? (
          <div className="rounded-xl border border-dashed border-linha p-12 text-center">
            <p className="text-giz">Nenhum carro com esses filtros agora.</p>
            <button onClick={limpar} className="mt-3 text-sm text-laranja hover:underline">
              Limpar filtros e ver todo o estoque
            </button>
          </div>
        ) : (
          <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {lista.map((v, i) => {
              const { inteiros, centavos } = precoPartido(v.preco / 100);
              return (
                <li key={v.slug}>
                  <Link
                    href={`/carros/${v.slug}`}
                    className="group relative block overflow-hidden rounded-md bg-[#1a1c20] ring-1 ring-linha/50 transition hover:ring-laranja/60"
                  >
                    <div className="relative z-10 px-5 pt-5">
                      <h2 className="display text-[22px] font-bold leading-tight">
                        {v.marca} {v.modelo}
                      </h2>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <span className="rounded-full border border-linha px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em] text-giz/75">
                          {v.versao ?? v.categoria}
                        </span>
                        {v.reservado && (
                          <span className="rounded-full bg-laranja px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-asfalto">Reservado</span>
                        )}
                        {v.destaques.slice(0, 1).map((d) => (
                          <span key={d} className="rounded-full border border-laranja/50 px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em] text-laranja">
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>

                    <FotoCarro
                      src={v.capa}
                      alt={`${v.marca} ${v.modelo} ${v.ano}`}
                      prioridade={i < 3}
                      className="mt-4 aspect-[4/3]"
                      sizes="(min-width: 1280px) 28vw, (min-width: 640px) 45vw, 92vw"
                    />

                    <div className="px-5 pb-5 pt-4">
                      <p className="num leading-none">
                        <span className="mr-1 text-sm font-semibold text-nevoa">R$</span>
                        <span className="display text-[32px] font-bold">{inteiros.replace(/R\$\s?/, "")}</span>
                        <span className="text-lg font-semibold">{centavos}</span>
                        <span className="ml-2 text-[11px] font-medium uppercase tracking-[0.08em] text-nevoa">à vista</span>
                      </p>
                      <p className="num mt-1.5 flex justify-between text-[11px] font-medium uppercase tracking-[0.06em] text-nevoa">
                        <span>ou {simulacao.meses}x de {reais(v.parcela / 100)}*</span>
                        <span>{v.cor}</span>
                      </p>
                      <div className="mt-3.5 flex flex-wrap gap-1.5">
                        {[
                          { i: Calendar, t: v.ano },
                          { i: Gauge, t: v.km === null ? "km a consultar" : km(v.km) },
                          { i: Settings2, t: v.cambio },
                        ].map(({ i: Icone, t }) => (
                          <span key={String(t)} className="num flex items-center gap-1.5 rounded-full bg-[#2a2d32] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.04em] text-giz/85">
                            <Icone size={13} /> {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}

        <p id="financiamento" className="mt-8 max-w-3xl text-xs leading-relaxed text-nevoa">
          *Simulação com {simulacao.entradaPct}% de entrada, {simulacao.meses} parcelas e taxa de {simulacao.taxaMensalPct.toLocaleString("pt-BR")}% ao mês pela Tabela Price. Parcelas ilustrativas, apenas para você ter uma ideia: o valor
          final, a taxa e a aprovação dependem da análise de crédito de cada CPF e das condições do banco. Aceitamos financiamento bancário, consórcio, cartão e seu usado na troca.
        </p>
      </section>
    </div>
  );
}
