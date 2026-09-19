"use client";

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TONS_GRAFICO as TONS } from "@/lib/cores";

// Todos os valores monetários chegam em REAIS (não centavos) para os eixos ficarem legíveis.

const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const compacto = (v: number) => new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 }).format(v);

export interface Serie {
  chave: string;
  nome: string;
  cor: string;
}

function Dica({ active, payload, label, series, moeda }: { active?: boolean; payload?: { value: number; dataKey: string }[]; label?: string; series: Serie[]; moeda: boolean }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-linha bg-asfalto/95 px-3 py-2 text-xs shadow-xl">
      <p className="mb-1 font-medium text-giz">{label}</p>
      {payload.map((p) => {
        const s = series.find((x) => x.chave === p.dataKey);
        return (
          <p key={p.dataKey} className="num flex items-center gap-2 text-nevoa">
            <span className="size-2 rounded-full" style={{ background: s?.cor }} />
            {s?.nome}
            <span className="ml-auto pl-3 text-giz">{moeda ? brl(p.value) : p.value.toLocaleString("pt-BR")}</span>
          </p>
        );
      })}
    </div>
  );
}

export function GraficoArea({ dados, eixoX, series, altura = 300, moeda = true }: { dados: Record<string, string | number>[]; eixoX: string; series: Serie[]; altura?: number; moeda?: boolean }) {
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <AreaChart data={dados} margin={{ top: 10, right: 6, left: -8, bottom: 0 }}>
        <defs>
          {series.map((s) => (
            <linearGradient key={s.chave} id={`g-${s.chave}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={s.cor} stopOpacity={0.4} />
              <stop offset="100%" stopColor={s.cor} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid stroke="#31363d" strokeDasharray="3 6" vertical={false} />
        <XAxis dataKey={eixoX} tickLine={false} axisLine={false} tick={{ fill: "#8c939c", fontSize: 12 }} />
        <YAxis tickLine={false} axisLine={false} width={58} tick={{ fill: "#8c939c", fontSize: 11 }} tickFormatter={compacto} />
        <Tooltip content={<Dica series={series} moeda={moeda} />} cursor={{ stroke: "#ffb45c", strokeDasharray: "4 4" }} />
        {series.map((s, i) => (
          <Area key={s.chave} type="monotone" dataKey={s.chave} stroke={s.cor} strokeWidth={i === 0 ? 2.4 : 1.8} fill={`url(#g-${s.chave})`} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function GraficoBarras({ dados, eixoX, series, altura = 280, moeda = true, empilhado }: { dados: Record<string, string | number>[]; eixoX: string; series: Serie[]; altura?: number; moeda?: boolean; empilhado?: boolean }) {
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart data={dados} margin={{ top: 10, right: 6, left: -8, bottom: 0 }} barGap={4}>
        <CartesianGrid stroke="#31363d" strokeDasharray="3 6" vertical={false} />
        <XAxis dataKey={eixoX} tickLine={false} axisLine={false} tick={{ fill: "#8c939c", fontSize: 12 }} />
        <YAxis tickLine={false} axisLine={false} width={58} tick={{ fill: "#8c939c", fontSize: 11 }} tickFormatter={compacto} allowDecimals={false} />
        <Tooltip content={<Dica series={series} moeda={moeda} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        {series.map((s) => (
          <Bar key={s.chave} dataKey={s.chave} fill={s.cor} radius={[6, 6, 0, 0]} maxBarSize={34} stackId={empilhado ? "a" : undefined} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function GraficoRosca({ dados, centro, legendaCentro, moeda = false }: { dados: { nome: string; valor: number }[]; centro: string; legendaCentro: string; moeda?: boolean }) {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[190px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={dados} dataKey="valor" nameKey="nome" innerRadius="68%" outerRadius="100%" paddingAngle={3} stroke="none" cornerRadius={4}>
            {dados.map((d, i) => (
              <Cell key={d.nome} fill={TONS[i % TONS.length]} />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) =>
              active && payload?.length ? (
                <div className="num rounded-lg border border-linha bg-asfalto px-2 py-1 text-xs">
                  {payload[0].name}: {moeda ? brl(payload[0].value as number) : String(payload[0].value)}
                </div>
              ) : null
            }
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
        <div>
          <p className={`display num font-bold ${centro.length > 9 ? "text-base" : centro.length > 6 ? "text-xl" : "text-2xl"}`}>{centro}</p>
          <p className="text-xs text-nevoa">{legendaCentro}</p>
        </div>
      </div>
    </div>
  );
}

export function GraficoSaldo({ dados, altura = 110 }: { dados: { dia: string; saldo: number }[]; altura?: number }) {
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <AreaChart data={dados} margin={{ top: 6, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gSaldo" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ff7a1a" stopOpacity={0.55} />
            <stop offset="100%" stopColor="#ff7a1a" stopOpacity={0} />
          </linearGradient>
        </defs>
        <Tooltip
          cursor={false}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <div className="num rounded-lg border border-linha bg-asfalto px-2 py-1 text-xs">
                {String(payload[0].payload.dia)} · {brl(payload[0].value as number)}
              </div>
            ) : null
          }
        />
        <Area type="monotone" dataKey="saldo" stroke="#ff7a1a" strokeWidth={2} fill="url(#gSaldo)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
