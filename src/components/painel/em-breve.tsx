import Link from "next/link";
import { BarraSuperior } from "@/components/painel/barra-superior";

/** Tela provisória para módulos que chegam nas próximas fases */
export function EmBreve({ titulo, fase, itens }: { titulo: string; fase: string; itens: string[] }) {
  return (
    <>
      <BarraSuperior titulo={titulo} trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: titulo }]} />
      <section className="max-w-2xl rounded-[var(--radius-card)] border border-dashed border-linha p-8">
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-laranja">{fase}</p>
        <h2 className="display mt-2 text-2xl font-bold">Esta tela entra numa próxima fase</h2>
        <p className="mt-2 text-sm text-nevoa">O que ela vai ter:</p>
        <ul className="mt-4 space-y-2 text-sm">
          {itens.map((i) => (
            <li key={i} className="flex gap-2.5">
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-laranja" />
              {i}
            </li>
          ))}
        </ul>
        <Link href="/painel/estoque" className="mt-6 inline-block text-sm text-laranja hover:underline">
          Voltar ao estoque
        </Link>
      </section>
    </>
  );
}
