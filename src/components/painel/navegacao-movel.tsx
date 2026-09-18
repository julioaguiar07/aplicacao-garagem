"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CarFront, Handshake, LayoutGrid, Wallet, Settings } from "lucide-react";
import { cn } from "@/lib/cn";

const ITENS = [
  { href: "/painel", rotulo: "Início", icone: LayoutGrid },
  { href: "/painel/estoque", rotulo: "Estoque", icone: CarFront },
  { href: "/painel/vendas", rotulo: "Vendas", icone: Handshake },
  { href: "/painel/caixa", rotulo: "Caixa", icone: Wallet },
  { href: "/painel/configuracoes", rotulo: "Ajustes", icone: Settings },
];

/** Barra inferior no celular (vendedor no pátio) */
export function NavegacaoMovel() {
  const caminho = usePathname();
  return (
    <nav className="fixed inset-x-3 bottom-3 z-40 flex justify-around rounded-2xl border border-linha bg-grafite/95 p-1.5 backdrop-blur lg:hidden">
      {ITENS.map(({ href, rotulo, icone: Icone }) => {
        const on = href === "/painel" ? caminho === href : caminho.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[11px]",
              on ? "bg-laranja font-semibold text-asfalto" : "text-nevoa",
            )}
          >
            <Icone size={18} />
            {rotulo}
          </Link>
        );
      })}
    </nav>
  );
}
