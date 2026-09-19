"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  CarFront,
  Handshake,
  Users,
  Wallet,
  FileBarChart,
  Store,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
} from "lucide-react";
import { sair } from "@/app/entrar/acoes";
import { useState } from "react";
import { cn } from "@/lib/cn";

const SECOES = [
  {
    titulo: "Principal",
    itens: [
      { href: "/painel", rotulo: "Visão geral", icone: LayoutGrid },
      { href: "/painel/estoque", rotulo: "Estoque", icone: CarFront },
      { href: "/painel/vendas", rotulo: "Vendas", icone: Handshake },
      { href: "/painel/clientes", rotulo: "Clientes", icone: Users },
    ],
  },
  {
    titulo: "Financeiro",
    itens: [
      { href: "/painel/caixa", rotulo: "Fluxo de caixa", icone: Wallet },
      { href: "/painel/relatorios", rotulo: "Relatórios", icone: FileBarChart },
    ],
  },
  {
    titulo: "Sistema",
    itens: [
      { href: "/", rotulo: "Ver vitrine", icone: Store, externo: true },
      { href: "/painel/configuracoes", rotulo: "Configurações", icone: Settings },
    ],
  },
];

export function BarraLateral() {
  const caminho = usePathname();
  const [recolhida, setRecolhida] = useState(false);

  const ativo = (href: string) => (href === "/painel" ? caminho === href : caminho.startsWith(href));

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-linha/70 bg-grafite/60 py-5 transition-[width] duration-300 lg:flex",
        recolhida ? "w-[76px] px-3" : "w-[248px] px-4",
      )}
    >
      <div className={cn("flex items-center", recolhida ? "justify-center" : "justify-between px-2")}>
        {!recolhida && (
          <Link href="/painel" aria-label="Carmelo Multimarcas, visão geral">
            <Image src="/marca/logo-branca.png" alt="Carmelo Multimarcas" width={132} height={44} priority />
          </Link>
        )}
        <button
          onClick={() => setRecolhida((r) => !r)}
          className="rounded-lg p-1.5 text-nevoa transition hover:bg-chumbo hover:text-giz"
          aria-label={recolhida ? "Expandir menu" : "Recolher menu"}
        >
          {recolhida ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </div>

      <nav className="mt-8 flex-1 space-y-7 overflow-y-auto scrollbar-fina">
        {SECOES.map((secao) => (
          <div key={secao.titulo}>
            {!recolhida && (
              <p className="mb-2 px-3 text-[11px] font-medium uppercase tracking-[0.14em] text-nevoa-2">
                {secao.titulo}
              </p>
            )}
            <ul className="space-y-1">
              {secao.itens.map(({ href, rotulo, icone: Icone, ...item }) => {
                const on = !("externo" in item) && ativo(href);
                return (
                  <li key={href}>
                    <Link
                      href={href}
                      target={"externo" in item ? "_blank" : undefined}
                      title={recolhida ? rotulo : undefined}
                      className={cn(
                        "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                        recolhida && "justify-center px-0",
                        on
                          ? "bg-laranja font-semibold text-asfalto shadow-[0_6px_24px_-8px] shadow-laranja/60"
                          : "text-nevoa hover:bg-chumbo hover:text-giz",
                      )}
                    >
                      <Icone size={18} strokeWidth={on ? 2.2 : 1.8} />
                      {!recolhida && rotulo}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className={cn("mt-4 flex items-center gap-3 rounded-2xl border border-linha/70 bg-chumbo/50 p-2.5", recolhida && "flex-col")}>
        <Image src="/marca/logo-icone.png" alt="" width={36} height={36} className="rounded-full" />
        {!recolhida && (
          <div className="min-w-0 flex-1 leading-tight">
            <p className="truncate text-sm font-medium">Administrador</p>
            <p className="truncate text-xs text-nevoa">Carmelo Multimarcas</p>
          </div>
        )}
        <form action={sair}>
          <button className="rounded-lg p-1.5 text-nevoa transition hover:bg-chumbo hover:text-giz" aria-label="Sair do painel" title="Sair">
            <LogOut size={17} />
          </button>
        </form>
      </div>
    </aside>
  );
}
