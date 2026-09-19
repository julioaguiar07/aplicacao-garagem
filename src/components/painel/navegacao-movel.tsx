"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { CarFront, FileBarChart, Handshake, LayoutGrid, LogOut, Menu, Search, Settings, Store, Users, Wallet, X } from "lucide-react";
import { sair } from "@/app/entrar/acoes";
import { cn } from "@/lib/cn";

const ITENS = [
  { href: "/painel", rotulo: "Início", icone: LayoutGrid },
  { href: "/painel/estoque", rotulo: "Estoque", icone: CarFront },
  { href: "/painel/vendas", rotulo: "Vendas", icone: Handshake },
  { href: "/painel/caixa", rotulo: "Caixa", icone: Wallet },
];

const MAIS = [
  { href: "/painel/clientes", rotulo: "Clientes", icone: Users },
  { href: "/painel/relatorios", rotulo: "Relatórios", icone: FileBarChart },
  { href: "/painel/configuracoes", rotulo: "Configurações", icone: Settings },
  { href: "/", rotulo: "Ver vitrine", icone: Store },
];

/** Barra inferior no celular (vendedor no pátio) */
export function NavegacaoMovel() {
  const caminho = usePathname();
  const [aberto, setAberto] = useState(false);
  const ativo = (href: string) => (href === "/painel" ? caminho === href : caminho.startsWith(href));
  return (
    <>
      {aberto && (
        <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setAberto(false)}>
          <div className="absolute inset-x-3 bottom-24 rounded-2xl border border-linha bg-grafite p-3" onClick={(e) => e.stopPropagation()}>
            <form action="/painel/busca" className="relative mb-3" role="search">
              <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-nevoa" />
              <input name="q" type="search" placeholder="Buscar carro, placa ou cliente" className="h-11 w-full rounded-xl border border-linha bg-asfalto pl-10 pr-3 text-sm focus:border-laranja/60 focus:outline-none" />
            </form>
            <ul className="grid grid-cols-2 gap-2">
              {MAIS.map(({ href, rotulo, icone: Icone }) => (
                <li key={href}>
                  <Link href={href} onClick={() => setAberto(false)} className={cn("flex items-center gap-2 rounded-xl px-3 py-3 text-sm", ativo(href) && href !== "/" ? "bg-laranja font-semibold text-asfalto" : "bg-chumbo/60")}>
                    <Icone size={17} /> {rotulo}
                  </Link>
                </li>
              ))}
            </ul>
            <form action={sair} className="mt-2">
              <button className="flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm text-nevoa hover:text-giz">
                <LogOut size={16} /> Sair do painel
              </button>
            </form>
          </div>
        </div>
      )}
      <nav className="fixed inset-x-3 bottom-3 z-50 flex justify-around rounded-2xl border border-linha bg-grafite/95 p-1.5 backdrop-blur lg:hidden">
        {ITENS.map(({ href, rotulo, icone: Icone }) => (
          <Link key={href} href={href} onClick={() => setAberto(false)} className={cn("flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[11px]", ativo(href) ? "bg-laranja font-semibold text-asfalto" : "text-nevoa")}>
            <Icone size={18} />
            {rotulo}
          </Link>
        ))}
        <button onClick={() => setAberto((a) => !a)} className={cn("flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[11px]", aberto || MAIS.some((m) => m.href !== "/" && ativo(m.href)) ? "bg-chumbo text-giz" : "text-nevoa")} aria-expanded={aberto}>
          {aberto ? <X size={18} /> : <Menu size={18} />}
          Mais
        </button>
      </nav>
    </>
  );
}
