"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Check, FileSignature, Loader2, Receipt, Undo2 } from "lucide-react";
import { BotaoAcao, CampoDinheiro, FormAcao, Modal } from "@/components/interativos";
import { Campo, classeBotao, classeCampo } from "@/components/ui";
import { cancelarVenda, completarDadosContrato, mudarEtapa } from "@/lib/acoes/vendas";
import { darBaixa, estornarBaixa } from "@/lib/acoes/caixa";
import { ETAPAS_VENDA, FLUXO_ETAPAS, type EtapaVenda, hojeISO } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export function EtapasVenda({ vendaId, etapa }: { vendaId: number; etapa: string }) {
  const [pendente, iniciar] = useTransition();
  const [erro, setErro] = useState<string | null>(null);
  const router = useRouter();
  const atual = FLUXO_ETAPAS.indexOf(etapa as EtapaVenda);
  if (etapa === "cancelada") return <p className="rounded-xl bg-perigo/10 px-3 py-2 text-sm text-perigo">Venda cancelada.</p>;
  return (
    <div>
      <ol className="flex flex-wrap gap-1.5">
        {FLUXO_ETAPAS.map((e, i) => (
          <li key={e}>
            <button
              disabled={pendente || i === atual}
              onClick={() =>
                iniciar(async () => {
                  const r = await mudarEtapa(vendaId, e);
                  setErro(r.ok ? null : r.erro);
                  router.refresh();
                })
              }
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs transition",
                i === atual ? "border-laranja bg-laranja font-semibold text-asfalto" : i < atual ? "border-laranja/40 text-laranja hover:bg-laranja/10" : "border-linha text-nevoa hover:text-giz",
              )}
            >
              {i < atual && <Check size={12} />}
              {ETAPAS_VENDA[e]}
            </button>
          </li>
        ))}
        {pendente && <Loader2 size={16} className="ml-1 animate-spin self-center text-nevoa" />}
      </ol>
      {erro && <p className="mt-2 text-xs text-perigo">{erro}</p>}
      <p className="mt-2 text-[11px] text-nevoa-2">Clique na etapa para mover a venda. Em “Contrato assinado” o carro passa a vendido e sai da vitrine.</p>
    </div>
  );
}

export function BaixaLancamento({ id, valor, tipo, pago, contas }: { id: number; valor: number; tipo: string; pago: boolean; contas: { id: number; nome: string }[] }) {
  const [aberto, setAberto] = useState(false);
  if (pago)
    return (
      <BotaoAcao acao={() => estornarBaixa(id)} confirmar="Desfazer a baixa?" variante="fantasma">
        <Undo2 size={13} /> Desfazer
      </BotaoAcao>
    );
  return (
    <>
      <button onClick={() => setAberto(true)} className={classeBotao("secundario", "sm")}>
        <Check size={13} /> {tipo === "entrada" ? "Recebido" : "Pago"}
      </button>
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo={tipo === "entrada" ? "Registrar recebimento" : "Registrar pagamento"} largura="max-w-sm">
        <FormAcao acao={darBaixa.bind(null, id)} rotulo="Confirmar" aoConcluir={() => setAberto(false)}>
          <Campo rotulo="Data">
            <input type="date" name="pagoEm" defaultValue={hojeISO()} className={cn(classeCampo, "num")} />
          </Campo>
          <Campo rotulo="Valor efetivo" dica="Ajuste se houve juros, multa ou desconto">
            <CampoDinheiro name="valor" defaultValue={valor} />
          </Campo>
          {contas.length > 0 && (
            <Campo rotulo="Conta">
              <select name="contaId" className={classeCampo}>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </Campo>
          )}
          <Campo rotulo="Comprovante (opcional)">
            <input name="comprovante" type="file" accept="application/pdf,image/*" className="block w-full text-sm text-nevoa file:mr-3 file:rounded-full file:border-0 file:bg-chumbo file:px-3 file:py-1.5 file:text-giz" />
          </Campo>
        </FormAcao>
      </Modal>
    </>
  );
}

type CampoFaltando = { campo: string; rotulo: string };

/** Gera contrato/recibo; se faltar dado, pede só o que falta e salva no carro/cliente */
export function DocumentosVenda({ vendaId, faltando }: { vendaId: number; faltando: CampoFaltando[] }) {
  const [aberto, setAberto] = useState<null | "contrato" | "recibo">(null);
  const router = useRouter();
  const abrirPdf = (tipo: string) => window.open(`/painel/vendas/${vendaId}/pdf?tipo=${tipo}`, "_blank");
  const pedir = (tipo: "contrato" | "recibo") => (faltando.length ? setAberto(tipo) : abrirPdf(tipo));
  return (
    <>
      <div className="flex flex-wrap gap-2">
        <button onClick={() => pedir("contrato")} className={classeBotao("secundario")}>
          <FileSignature size={16} /> Contrato de compra e venda
        </button>
        <button onClick={() => pedir("recibo")} className={classeBotao("secundario")}>
          <Receipt size={16} /> Recibo
        </button>
        <button onClick={() => abrirPdf("garantia")} className={classeBotao("secundario")}>
          <FileSignature size={16} /> Termo de garantia
        </button>
        <button onClick={() => abrirPdf("entrega")} className={classeBotao("secundario")}>
          <Check size={16} /> Checklist de entrega
        </button>
      </div>
      {faltando.length > 0 && <p className="mt-2 text-xs text-nevoa">Faltam {faltando.map((f) => f.rotulo.toLowerCase()).join(", ")} para o contrato. O sistema vai pedir na hora.</p>}
      <Modal aberto={aberto !== null} aoFechar={() => setAberto(null)} titulo="Completar dados do documento" largura="max-w-md">
        <p className="mb-4 text-sm text-nevoa">Preencha o que falta. Fica salvo no carro e no cadastro do cliente.</p>
        <FormAcao
          acao={completarDadosContrato.bind(null, vendaId)}
          rotulo="Salvar e gerar"
          limparAoConcluir={false}
          aoConcluir={() => {
            const tipo = aberto ?? "contrato";
            setAberto(null);
            router.refresh();
            abrirPdf(tipo);
          }}
        >
          {faltando.map((f) => (
            <Campo key={f.campo} rotulo={f.rotulo}>
              <input name={f.campo} className={classeCampo} required />
            </Campo>
          ))}
        </FormAcao>
      </Modal>
    </>
  );
}

export function CancelarVenda({ vendaId }: { vendaId: number }) {
  return (
    <BotaoAcao acao={() => cancelarVenda(vendaId)} confirmar="Cancelar a venda? Valores em aberto serão apagados e o carro volta ao estoque." variante="perigo" tamanho="md">
      Cancelar venda
    </BotaoAcao>
  );
}
