import { DEMO, MARCA } from "@/lib/marca";

/** Faixa fina no topo da demonstração: avisa que os dados são fictícios e assina o sistema */
export function SeloDemo() {
  if (!DEMO) return null;
  return (
    <div className="relative z-50 flex flex-wrap items-center justify-center gap-x-2 gap-y-0.5 border-b border-laranja/30 bg-[#0d0e10] px-4 py-1.5 text-center text-[11px] text-nevoa">
      <span className="rounded-full bg-laranja px-2 py-px text-[10px] font-bold uppercase tracking-wider text-asfalto">Demo</span>
      <span>
        {MARCA.nome}: sistema de gestão e vitrine para lojas de veículos, com dados fictícios.
      </span>
      <span className="text-giz">
        Developed by <strong className="font-semibold">Julio Aguiar</strong>
      </span>
    </div>
  );
}
