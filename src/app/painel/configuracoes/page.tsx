import { EmBreve } from "@/components/painel/em-breve";

export const metadata = { title: "Configurações" };

export default function Configuracoes() {
  return (
    <EmBreve
      titulo="Configurações"
      fase="Fase 1 e 6"
      itens={[
        "Trocar senha do administrador",
        "Dados da loja: WhatsApp, endereço, logo e papel timbrado",
        "Premissas da simulação de parcela da vitrine",
        "Gerador de stories para o Instagram",
      ]}
    />
  );
}
