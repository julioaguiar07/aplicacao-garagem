import Link from "next/link";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/cn";

// Peças visuais do painel (servidor e cliente). Mantêm o visual aprovado na Fase 0.

export function Cartao({ titulo, acao, className, children, id }: { titulo?: React.ReactNode; acao?: React.ReactNode; className?: string; children: React.ReactNode; id?: string }) {
  return (
    <section id={id} className={cn("min-w-0 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5", className)}>
      {(titulo || acao) && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          {titulo && <h2 className="display text-[17px] font-semibold">{titulo}</h2>}
          {acao}
        </div>
      )}
      {children}
    </section>
  );
}

const ESTILOS_BOTAO = {
  primario: "bg-laranja font-semibold text-asfalto hover:bg-ambar",
  secundario: "border border-linha text-nevoa hover:border-laranja/50 hover:text-giz",
  perigo: "border border-perigo/40 text-perigo hover:bg-perigo/10",
  fantasma: "text-nevoa hover:bg-chumbo hover:text-giz",
};

export function classeBotao(variante: keyof typeof ESTILOS_BOTAO = "secundario", tamanho: "sm" | "md" = "md") {
  return cn(
    "inline-flex items-center justify-center gap-1.5 rounded-full transition disabled:pointer-events-none disabled:opacity-50",
    tamanho === "sm" ? "h-8 px-3 text-xs" : "h-10 px-4 text-sm",
    ESTILOS_BOTAO[variante],
  );
}

export function LinkBotao({ href, variante, tamanho, className, children, ...resto }: React.ComponentProps<typeof Link> & { variante?: keyof typeof ESTILOS_BOTAO; tamanho?: "sm" | "md" }) {
  return (
    <Link href={href} className={cn(classeBotao(variante, tamanho), className)} {...resto}>
      {children}
    </Link>
  );
}

export const classeCampo =
  "h-10 w-full rounded-xl border border-linha bg-asfalto px-3 text-sm text-giz placeholder:text-nevoa-2 focus:border-laranja/60 focus:outline-none disabled:opacity-60";

export function Campo({ rotulo, dica, className, children, obrigatorio }: { rotulo: string; dica?: string; className?: string; children: React.ReactNode; obrigatorio?: boolean }) {
  return (
    <label className={cn("block", className)}>
      <span className="text-xs text-nevoa">
        {rotulo}
        {obrigatorio && <span className="text-laranja"> *</span>}
      </span>
      <div className="mt-1">{children}</div>
      {dica && <span className="mt-1 block text-[11px] text-nevoa-2">{dica}</span>}
    </label>
  );
}

/** Indicador (KPI) no padrão do Dashboard */
export function Indicador({
  rotulo,
  valor,
  icone: Icone,
  variacao,
  sufixoVariacao = "vs mês anterior",
  rodape,
  destaque,
  inverterCor,
}: {
  rotulo: string;
  valor: React.ReactNode;
  icone: React.ComponentType<{ size?: number }>;
  variacao?: number | null;
  sufixoVariacao?: string;
  rodape?: React.ReactNode;
  destaque?: boolean;
  inverterCor?: boolean;
}) {
  return (
    <Cartao className={cn("relative overflow-hidden", destaque && "brilho-laranja")}>
      <span className={cn("grid size-9 place-items-center rounded-xl", destaque ? "bg-laranja/15 text-laranja" : "bg-chumbo text-giz")}>
        <Icone size={18} />
      </span>
      <p className="mt-4 text-xs text-nevoa sm:mt-5 sm:text-sm">{rotulo}</p>
      <p className="display num mt-1 text-[17px] font-bold leading-tight sm:text-[26px] sm:leading-none">{valor}</p>
      {variacao !== undefined && variacao !== null && (
        <div className="mt-3">
          <SeloVariacao valor={variacao} sufixo={sufixoVariacao} inverter={inverterCor} />
        </div>
      )}
      {rodape && <div className="num mt-3 text-xs text-nevoa">{rodape}</div>}
    </Cartao>
  );
}

export function SeloVariacao({ valor, sufixo, inverter }: { valor: number; sufixo?: string; inverter?: boolean }) {
  const bom = inverter ? valor <= 0 : valor >= 0;
  return (
    <span className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-nevoa">
      <span className={cn("num inline-flex items-center gap-0.5 whitespace-nowrap rounded-md px-1.5 py-0.5 font-medium", bom ? "bg-sucesso/12 text-sucesso" : "bg-perigo/12 text-perigo")}>
        {valor >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
        {Math.abs(valor).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%
      </span>
      {sufixo}
    </span>
  );
}

/** KPI compacto (linha de indicadores secundários) */
export function MiniIndicador({ rotulo, valor, dica, tom }: { rotulo: string; valor: React.ReactNode; dica?: string; tom?: "bom" | "ruim" | "alerta" }) {
  return (
    <div className="min-w-0 break-words rounded-2xl border border-linha/60 bg-grafite p-4" title={dica}>
      <p className="text-xs text-nevoa">{rotulo}</p>
      <p className={cn("display num mt-1.5 text-xl font-bold", tom === "bom" && "text-sucesso", tom === "ruim" && "text-perigo", tom === "alerta" && "text-laranja")}>{valor}</p>
      {dica && <p className="mt-1 text-[11px] leading-snug text-nevoa-2">{dica}</p>}
    </div>
  );
}

export function Vazio({ children, acao }: { children: React.ReactNode; acao?: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-card)] border border-dashed border-linha p-10 text-center text-sm text-nevoa">
      {children}
      {acao && <div className="mt-4">{acao}</div>}
    </div>
  );
}

export function Tabela({ children, minimo = 640 }: { children: React.ReactNode; minimo?: number }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" style={{ minWidth: minimo }}>
        {children}
      </table>
    </div>
  );
}

export const th = "px-3 py-2.5 text-left text-xs font-medium text-nevoa first:pl-5 last:pr-5";
export const td = "px-3 py-3 first:pl-5 last:pr-5";

const CORES_STATUS_LANC = {
  realizado: "bg-sucesso/15 text-sucesso",
  previsto: "bg-chumbo-2 text-nevoa",
  atrasado: "bg-perigo/15 text-perigo",
};
export function SeloLancamento({ status, tipo }: { status: "realizado" | "previsto" | "atrasado"; tipo: string }) {
  const nome = status === "realizado" ? (tipo === "entrada" ? "Recebido" : "Pago") : status === "atrasado" ? "Atrasado" : tipo === "entrada" ? "A receber" : "A pagar";
  return <span className={cn("inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-medium", CORES_STATUS_LANC[status])}>{nome}</span>;
}
