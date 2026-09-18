import { EmBreve } from "@/components/painel/em-breve";

export const metadata = { title: "Clientes" };

export default function Clientes() {
  return (
    <EmBreve
      titulo="Clientes"
      fase="Fase 5"
      itens={["Cadastro simples com telefone e interesse", "Histórico de compras, trocas e parcelas de cada cliente", "CPF e endereço opcionais até o contrato"]}
    />
  );
}
