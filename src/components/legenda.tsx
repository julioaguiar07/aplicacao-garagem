import { TONS_GRAFICO } from "@/lib/cores";

/** Legenda em lista (servidor), com a mesma sequência de cores dos gráficos de rosca */
export function Legenda({ itens }: { itens: { nome: string; valor: string; cor?: string }[] }) {
  return (
    <ul className="mt-5 space-y-2">
      {itens.map((d, i) => (
        <li key={d.nome} className="flex items-center gap-2 text-sm">
          <span className="size-2 shrink-0 rounded-full" style={{ background: d.cor ?? TONS_GRAFICO[i % TONS_GRAFICO.length] }} />
          <span className="flex-1 text-nevoa">{d.nome}</span>
          <span className="num font-medium">{d.valor}</span>
        </li>
      ))}
    </ul>
  );
}
