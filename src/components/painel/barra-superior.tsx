import Link from "next/link";
import { Bell, Plus, Search } from "lucide-react";

export function BarraSuperior({ titulo, trilha }: { titulo: string; trilha?: { rotulo: string; href?: string }[] }) {
  return (
    <header className="flex flex-wrap items-center gap-4 pb-6">
      <div className="min-w-0 flex-1">
        {trilha && (
          <nav aria-label="Trilha" className="mb-1 flex items-center gap-1.5 text-xs text-nevoa">
            {trilha.map((t, i) => (
              <span key={t.rotulo} className="flex items-center gap-1.5">
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

      <label className="group relative hidden w-72 items-center md:flex">
        <Search size={16} className="pointer-events-none absolute left-3.5 text-nevoa" />
        <input
          type="search"
          placeholder="Buscar carro, placa ou cliente"
          className="h-10 w-full rounded-full border border-linha bg-grafite pl-10 pr-14 text-sm placeholder:text-nevoa-2 focus:border-laranja/60 focus:outline-none"
        />
        <kbd className="pointer-events-none absolute right-3 rounded-md border border-linha px-1.5 font-mono text-[10px] text-nevoa">
          Ctrl K
        </kbd>
      </label>

      <button
        className="relative grid size-10 place-items-center rounded-full border border-linha bg-grafite text-nevoa transition hover:text-giz"
        aria-label="Notificações (3 novas)"
      >
        <Bell size={17} />
        <span className="absolute right-2.5 top-2.5 size-2 rounded-full bg-laranja ring-2 ring-grafite" />
      </button>

      <Link
        href="/painel/estoque/novo"
        className="flex h-10 items-center gap-2 rounded-full bg-laranja px-4 text-sm font-semibold text-asfalto transition hover:bg-ambar"
      >
        <Plus size={17} strokeWidth={2.4} />
        <span className="hidden sm:inline">Cadastrar veículo</span>
      </Link>
    </header>
  );
}
