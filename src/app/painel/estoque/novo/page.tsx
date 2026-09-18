import { EmBreve } from "@/components/painel/em-breve";

export const metadata = { title: "Cadastrar veículo" };

export default function NovoVeiculo() {
  return (
    <EmBreve
      titulo="Cadastrar veículo"
      fase="Fase 3"
      itens={[
        "Passo a passo com rascunho salvo: identificação pela FIPE, características, entrada, preço, fotos, documentos e revisão",
        "Obrigatórios só marca, modelo, ano, custo, preço e uma foto",
        "Recorte automático da foto de capa, com opção de usar a foto inteira",
      ]}
    />
  );
}
