import { EmBreve } from "@/components/painel/em-breve";

export const metadata = { title: "Relatórios" };

export default function Relatorios() {
  return (
    <EmBreve
      titulo="Relatórios"
      fase="Fase 6"
      itens={["Resultado do mês (DRE)", "Rentabilidade por veículo", "Exportação em CSV e PDF"]}
    />
  );
}
