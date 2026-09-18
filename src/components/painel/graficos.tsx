"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { reais, numeroCompacto } from "@/lib/formato";
import { TONS_GRAFICO as TONS } from "@/lib/cores";

const LARANJA = "#ff7a1a";
const AMBAR = "#ffb45c";

type PontoMensal = { mes: string; faturamento: number; lucro: number; vendas: number };

function Dica({ active, payload, label }: { active?: boolean; payload?: { value: number; dataKey: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-linha bg-asfalto/95 px-3 py-2 text-xs shadow-xl">
      <p className="mb-1 font-medium text-giz">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="num flex items-center gap-2 text-nevoa">
          <span className="size-2 rounded-full" style={{ background: p.dataKey === "faturamento" ? LARANJA : AMBAR }} />
          {p.dataKey === "faturamento" ? "Faturamento" : "Lucro"}
          <span className="ml-auto pl-3 text-giz">{reais(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

export function GraficoVendas({ dados }: { dados: PontoMensal[] }) {
  return (
    <ResponsiveContainer width="100%" height={330}>
      <AreaChart data={dados} margin={{ top: 10, right: 6, left: -8, bottom: 0 }}>
        <defs>
          <linearGradient id="gFat" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={LARANJA} stopOpacity={0.45} />
            <stop offset="100%" stopColor={LARANJA} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gLucro" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={AMBAR} stopOpacity={0.3} />
            <stop offset="100%" stopColor={AMBAR} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#31363d" strokeDasharray="3 6" vertical={false} />
        <XAxis dataKey="mes" tickLine={false} axisLine={false} tick={{ fill: "#8c939c", fontSize: 12 }} />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={58}
          tick={{ fill: "#8c939c", fontSize: 11 }}
          tickFormatter={(v: number) => numeroCompacto(v)}
        />
        <Tooltip content={<Dica />} cursor={{ stroke: "#ffb45c", strokeDasharray: "4 4" }} />
        <Area type="monotone" dataKey="faturamento" stroke={LARANJA} strokeWidth={2.4} fill="url(#gFat)" />
        <Area type="monotone" dataKey="lucro" stroke={AMBAR} strokeWidth={1.8} fill="url(#gLucro)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function GraficoFormas({ dados, total }: { dados: { nome: string; qtd: number }[]; total: number }) {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[190px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={dados}
            dataKey="qtd"
            nameKey="nome"
            innerRadius="68%"
            outerRadius="100%"
            paddingAngle={3}
            stroke="none"
            cornerRadius={4}
          >
            {dados.map((d, i) => (
              <Cell key={d.nome} fill={TONS[i % TONS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="display num text-3xl font-bold">{total}</p>
          <p className="text-xs text-nevoa">vendas</p>
        </div>
      </div>
    </div>
  );
}

export function GraficoSaldo({ dados }: { dados: { dia: string; saldo: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={110}>
      <AreaChart data={dados} margin={{ top: 6, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gSaldo" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={LARANJA} stopOpacity={0.55} />
            <stop offset="100%" stopColor={LARANJA} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Tooltip
          cursor={false}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <div className="num rounded-lg border border-linha bg-asfalto px-2 py-1 text-xs">
                {payload[0].payload.dia} · {reais(payload[0].value as number)}
              </div>
            ) : null
          }
        />
        <Area type="monotone" dataKey="saldo" stroke={LARANJA} strokeWidth={2} fill="url(#gSaldo)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
