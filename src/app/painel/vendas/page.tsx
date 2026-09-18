import { EmBreve } from "@/components/painel/em-breve";

export const metadata = { title: "Vendas" };

export default function Vendas() {
  return (
    <EmBreve
      titulo="Vendas"
      fase="Fase 5"
      itens={[
        "Quadro de negociações: negociação, reservado, ficha em análise, aprovado, contrato, transferência e entregue",
        "Venda com várias formas de pagamento somadas: sinal, PIX/dinheiro, cartão, financiamento bancário, leasing, financiamento próprio, cheque, consórcio e troca",
        "Veículo na troca entra sozinho no estoque, em preparação",
        "Contrato, recibo, termo de garantia e checklist de entrega em PDF, pedindo só os dados que faltarem",
      ]}
    />
  );
}
