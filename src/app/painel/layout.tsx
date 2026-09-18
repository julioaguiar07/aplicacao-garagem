import type { Metadata } from "next";
import { BarraLateral } from "@/components/painel/barra-lateral";
import { NavegacaoMovel } from "@/components/painel/navegacao-movel";

export const metadata: Metadata = {
  title: { default: "Painel", template: "%s · Painel Carmelo" },
  robots: { index: false, follow: false },
};

export default function PainelLayout({ children }: LayoutProps<"/painel">) {
  return (
    <div className="flex min-h-dvh bg-asfalto">
      <BarraLateral />
      <div className="min-w-0 flex-1">
        <div className="bg-alerta/10 px-4 py-1.5 text-center text-xs text-alerta">
          Protótipo · custos, gastos, vendas e documentos são dados de demonstração
        </div>
        <main className="mx-auto w-full max-w-[1500px] px-4 pb-28 pt-6 md:px-8 lg:pb-10">{children}</main>
      </div>
      <NavegacaoMovel />
    </div>
  );
}
