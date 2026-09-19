import Link from "next/link";
import { Plus, Search } from "lucide-react";

export function BarraSuperior({
  titulo,
  trilha,
  acoes,
}: {
  titulo: string;
  trilha?: { rotulo: string; href?: string }[];
  acoes?: React.ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-center gap-4 pb-6">
      <div className="min-w-0 flex-1">
        {trilha && (
          <nav aria-label="Trilha" className="mb-1 flex items-center gap-1.5 text-xs text-nevoa">
            {trilha.map((t, i) => (
              <span key={t.rotulo + i} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-nevoa-2">/</span>}
                {t.href ? (
                  <Link href={t.href} className="hover:text-giz">
                    {t.rotulo}
                  </Link>
                ) : (
                  <span className="text-giz/80">{t.rotulo}</span>
                )}
              </span>
            ))}
          </nav>
        )}
        <h1 className="display truncate text-2xl font-bold md:text-[28px]">{titulo}</h1>
      </div>

      <form action="/painel/busca" className="relative hidden w-72 items-center md:flex" role="search">
        <Search size={16} className="pointer-events-none absolute left-3.5 text-nevoa" />
        <input
          type="search"
          name="q"
          placeholder="Buscar carro, placa ou cliente"
          className="h-10 w-full rounded-full border border-linha bg-grafite pl-10 pr-4 text-sm placeholder:text-nevoa-2 focus:border-laranja/60 focus:outline-none"
        />
      </form>

      {acoes ?? (
        <Link
          href="/painel/estoque/novo"
          className="flex h-10 items-center gap-2 rounded-full bg-laranja px-4 text-sm font-semibold text-asfalto transition hover:bg-ambar"
        >
          <Plus size={17} strokeWidth={2.4} />
          <span className="hidden sm:inline">Cadastrar veículo</span>
        </Link>
      )}
    </header>
  );
}
