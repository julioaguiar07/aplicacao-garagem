import { STATUS_VEICULO, type StatusVeiculo } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export const NOME_STATUS = STATUS_VEICULO;

const COR: Record<StatusVeiculo, string> = {
  rascunho: "bg-nevoa-2/20 text-nevoa",
  em_preparacao: "bg-alerta/15 text-alerta",
  disponivel: "bg-sucesso/15 text-sucesso",
  reservado: "bg-laranja/15 text-laranja",
  vendido: "bg-chumbo-2 text-nevoa",
  consignado: "bg-ambar/15 text-ambar",
};

export function StatusVeiculoSelo({ status, className }: { status: string; className?: string }) {
  const s = (status in COR ? status : "rascunho") as StatusVeiculo;
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium", COR[s], className)}>
      <span className="size-1.5 rounded-full bg-current" />
      {STATUS_VEICULO[s]}
    </span>
  );
}

/** Selo da marca: iniciais em Archivo dentro de um círculo (sem logos de terceiros) */
export function SeloMarca({ marca, className }: { marca: string; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn("display grid size-10 shrink-0 place-items-center rounded-full border border-linha bg-chumbo text-[13px] font-bold tracking-wider text-giz", className)}
    >
      {marca.slice(0, 2).toUpperCase()}
    </span>
  );
}
