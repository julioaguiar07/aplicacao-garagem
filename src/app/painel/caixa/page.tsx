import { EmBreve } from "@/components/painel/em-breve";

export const metadata = { title: "Fluxo de caixa" };

export default function Caixa() {
  return (
    <EmBreve
      titulo="Fluxo de caixa"
      fase="Fase 6"
      itens={[
        "Contas: caixa e bancos",
        "Lançamentos a pagar e a receber, previstos e realizados, com comprovante",
        "Despesas recorrentes (aluguel, salários)",
        "Calendário de vencimentos e saldo projetado para 90 dias",
      ]}
    />
  );
}
