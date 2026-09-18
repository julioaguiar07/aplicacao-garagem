import type { StatusVeiculo } from "@/lib/tipos";
import { cn } from "@/lib/cn";

export const NOME_STATUS: Record<StatusVeiculo, string> = {
  rascunho: "Rascunho",
  em_preparacao: "Em preparação",
  disponivel: "Disponível",
  reservado: "Reservado",
  vendido: "Vendido",
  consignado: "Consignado",
};

const COR: Record<StatusVeiculo, string> = {
  rascunho: "bg-nevoa-2/20 text-nevoa",
  em_preparacao: "bg-alerta/15 text-alerta",
  disponivel: "bg-sucesso/15 text-sucesso",
  reservado: "bg-laranja/15 text-laranja",
  vendido: "bg-chumbo-2 text-nevoa",
  consignado: "bg-ambar/15 text-ambar",
};

export function StatusVeiculoSelo({ status, className }: { status: StatusVeiculo; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium", COR[status], className)}>
      <span className="size-1.5 rounded-full bg-current" />
      {NOME_STATUS[status]}
    </span>
  );
}

/** Selo da marca: iniciais em Archivo dentro de um círculo (sem logos de terceiros) */
export function SeloMarca({ marca, className }: { marca: string; className?: string }) {
  const iniciais = marca.slice(0, 2).toUpperCase();
  return (
    <span
      aria-hidden
      className={cn(
        "display grid size-10 shrink-0 place-items-center rounded-full border border-linha bg-chumbo text-[13px] font-bold tracking-wider text-giz",
        className,
      )}
    >
      {iniciais}
    </span>
  );
}
