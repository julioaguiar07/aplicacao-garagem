"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useRef, useState, useTransition } from "react";
import { Crop, Eye, EyeOff, ImagePlus, Loader2, Star, Trash2, Upload } from "lucide-react";
import { BotaoAcao, CampoDinheiro, FormAcao, Modal } from "@/components/interativos";
import { Campo, classeBotao, classeCampo } from "@/components/ui";
import {
  adicionarFotos,
  alterarStatus,
  alternarPublicado,
  definirCapa,
  enviarDocumento,
  excluirVeiculo,
  lancarGasto,
  reenquadrarFoto,
  removerFoto,
} from "@/lib/acoes/veiculos";
import { CATEGORIAS_GASTO, STATUS_VEICULO, TIPOS_DOCUMENTO, hojeISO } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export function ControlesVeiculo({ id, status, publicado, temVenda }: { id: number; status: string; publicado: boolean; temVenda: boolean }) {
  const [pendente, iniciar] = useTransition();
  const [erro, setErro] = useState<string | null>(null);
  const router = useRouter();
  const manual = ["disponivel", "em_preparacao", "consignado", "rascunho"];
  return (
    <div className="flex flex-wrap items-center gap-2">
      {manual.includes(status) || !temVenda ? (
        <select
          aria-label="Status do veículo"
          value={status}
          disabled={pendente}
          onChange={(e) =>
            iniciar(async () => {
              const r = await alterarStatus(id, e.target.value);
              setErro(r.ok ? null : r.erro);
              router.refresh();
            })
          }
          className={cn(classeCampo, "h-10 w-auto rounded-full")}
        >
          {(manual.includes(status) ? manual : [status, ...manual]).map((s) => (
            <option key={s} value={s} disabled={!manual.includes(s)}>
              {STATUS_VEICULO[s as keyof typeof STATUS_VEICULO]}
            </option>
          ))}
        </select>
      ) : null}
      {status !== "vendido" && status !== "rascunho" && (
        <BotaoAcao acao={() => alternarPublicado(id)} tamanho="md">
          {publicado ? <EyeOff size={16} /> : <Eye size={16} />}
          {publicado ? "Tirar da vitrine" : "Publicar na vitrine"}
        </BotaoAcao>
      )}
      {!temVenda && (
        <BotaoAcao acao={() => excluirVeiculo(id)} confirmar="Excluir o carro, fotos e documentos?" variante="fantasma" tamanho="md">
          <Trash2 size={16} /> Excluir
        </BotaoAcao>
      )}
      {pendente && <Loader2 size={16} className="animate-spin text-nevoa" />}
      {erro && <span className="basis-full text-xs text-perigo">{erro}</span>}
    </div>
  );
}

export function FormDocumento({ veiculoId, tipoInicial }: { veiculoId: number; tipoInicial?: string }) {
  const [tipo, setTipo] = useState(tipoInicial ?? TIPOS_DOCUMENTO[0]);
  return (
    <FormAcao acao={enviarDocumento.bind(null, veiculoId)} rotulo="Enviar documento" rotuloEnviando="Enviando…">
      <Campo rotulo="Tipo">
        <select name="tipo" className={classeCampo} value={tipo} onChange={(e) => setTipo(e.target.value)}>
          {TIPOS_DOCUMENTO.map((t) => (
            <option key={t}>{t}</option>
          ))}
          <option value="__outro">Outro…</option>
        </select>
      </Campo>
      {tipo === "__outro" && (
        <Campo rotulo="Nome do documento">
          <input name="tipoOutro" className={classeCampo} placeholder="Ex.: Manual do proprietário" required />
        </Campo>
      )}
      <Campo rotulo="Arquivo" dica="PDF, JPG, PNG ou WebP até 15 MB">
        <input name="arquivo" type="file" accept="application/pdf,image/*" required className="block w-full text-sm text-nevoa file:mr-3 file:rounded-full file:border-0 file:bg-chumbo file:px-3 file:py-1.5 file:text-giz" />
      </Campo>
      <Campo rotulo="Validade" dica="Opcional. Depois dessa data o documento aparece como vencido.">
        <input name="validade" type="date" className={cn(classeCampo, "num")} />
      </Campo>
    </FormAcao>
  );
}

export function FormGasto({ veiculoId, contas }: { veiculoId: number; contas: { id: number; nome: string }[] }) {
  return (
    <FormAcao acao={lancarGasto.bind(null, veiculoId)} rotulo="Lançar gasto">
      <Campo rotulo="Descrição">
        <input name="descricao" className={classeCampo} placeholder="Ex.: polimento completo" required />
      </Campo>
      <div className="grid grid-cols-2 gap-3">
        <Campo rotulo="Valor">
          <CampoDinheiro name="valor" required />
        </Campo>
        <Campo rotulo="Data">
          <input type="date" name="data" defaultValue={hojeISO()} className={cn(classeCampo, "num")} />
        </Campo>
      </div>
      <Campo rotulo="Categoria">
        <select name="categoria" className={classeCampo}>
          {CATEGORIAS_GASTO.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </Campo>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label className="flex items-center gap-2 text-nevoa">
          <input type="checkbox" name="pago" defaultChecked className="accent-[#ff7a1a]" /> Já foi pago
        </label>
        {contas.length > 0 && (
          <select name="contaId" className={cn(classeCampo, "h-9 w-auto")}>
            {contas.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
        )}
      </div>
      <Campo rotulo="Nota fiscal (opcional)">
        <input name="nota" type="file" accept="application/pdf,image/*" className="block w-full text-sm text-nevoa file:mr-3 file:rounded-full file:border-0 file:bg-chumbo file:px-3 file:py-1.5 file:text-giz" />
      </Campo>
      <p className="text-xs text-nevoa">O gasto entra no fluxo de caixa e no custo do carro.</p>
    </FormAcao>
  );
}

type FotoCentral = { id: number; urlCard: string; urlOriginal: string; focoY: number };

export function GaleriaFotos({ veiculoId, fotos }: { veiculoId: number; fotos: FotoCentral[] }) {
  const input = useRef<HTMLInputElement>(null);
  const [enviando, iniciar] = useTransition();
  const [erro, setErro] = useState<string | null>(null);
  const [enquadrando, setEnquadrando] = useState<FotoCentral | null>(null);
  const router = useRouter();

  const enviar = (lista: FileList | null) => {
    if (!lista?.length) return;
    const fd = new FormData();
    let total = 0;
    for (const f of lista) {
      total += f.size;
      fd.append("fotos", f);
    }
    if (total > 24 * 1024 * 1024) {
      setErro("Envie até 24 MB por vez (umas 5 fotos de celular).");
      return;
    }
    iniciar(async () => {
      const r = await adicionarFotos(veiculoId, fd);
      setErro(r.ok ? null : r.erro);
      router.refresh();
    });
  };

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-nevoa">{fotos.length ? "A primeira foto é a capa na vitrine e nos cards." : "Nenhuma foto ainda."}</p>
        <button className={classeBotao("secundario", "sm")} onClick={() => input.current?.click()} disabled={enviando}>
          {enviando ? <Loader2 size={14} className="animate-spin" /> : <ImagePlus size={14} />} {enviando ? "Enviando…" : "Adicionar fotos"}
        </button>
        <input ref={input} type="file" accept="image/*" multiple hidden onChange={(e) => { enviar(e.target.files); e.target.value = ""; }} />
      </div>
      {erro && <p className="mb-3 text-sm text-perigo">{erro}</p>}
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
        {fotos.map((f, i) => (
          <li key={f.id} className={cn("group relative aspect-[4/3] overflow-hidden rounded-xl", i === 0 && "ring-2 ring-laranja")}>
            <Image src={f.urlCard} alt="" fill sizes="300px" className="object-cover" />
            {i === 0 && <span className="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-laranja px-2 py-0.5 text-[10px] font-semibold text-asfalto"><Star size={10} /> Capa</span>}
            <div className="absolute inset-x-0 bottom-0 flex flex-wrap justify-end gap-1 bg-gradient-to-t from-black/85 to-transparent p-2 pt-8">
              {i > 0 && (
                <BotaoAcao acao={() => definirCapa(f.id)} variante="fantasma" className="h-7 bg-black/50 px-2 text-[11px] text-giz">
                  <Star size={12} /> Capa
                </BotaoAcao>
              )}
              <button onClick={() => setEnquadrando(f)} className={cn(classeBotao("fantasma", "sm"), "h-7 bg-black/50 px-2 text-[11px] text-giz")}>
                <Crop size={12} /> Enquadrar
              </button>
              <BotaoAcao acao={() => removerFoto(f.id)} confirmar="Remover?" variante="fantasma" className="h-7 bg-black/50 px-2 text-[11px] text-perigo">
                <Trash2 size={12} />
              </BotaoAcao>
            </div>
          </li>
        ))}
        <li>
          <button
            onClick={() => input.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); enviar(e.dataTransfer.files); }}
            className="grid aspect-[4/3] w-full place-items-center rounded-xl border border-dashed border-linha text-xs text-nevoa-2 hover:border-laranja/50 hover:text-nevoa"
          >
            <span className="flex flex-col items-center gap-1">
              <Upload size={20} /> Solte fotos aqui
            </span>
          </button>
        </li>
      </ul>
      {enquadrando && <Enquadramento foto={enquadrando} aoFechar={() => setEnquadrando(null)} />}
    </>
  );
}

/** Ajuste do recorte 4:3: move a janela para cima/baixo sobre a foto original */
function Enquadramento({ foto, aoFechar }: { foto: FotoCentral; aoFechar: () => void }) {
  const [foco, setFoco] = useState(foto.focoY);
  const [dim, setDim] = useState<{ w: number; h: number } | null>(null);
  const [salvando, iniciar] = useTransition();
  const router = useRouter();
  const alturaJanela = dim ? Math.min(1, (dim.w * 3) / 4 / dim.h) : 0.5;
  const topo = Math.min(Math.max(0, foco - alturaJanela / 2), 1 - alturaJanela);
  return (
    <Modal aberto aoFechar={aoFechar} titulo="Ajustar enquadramento" largura="max-w-md">
      <div className="relative mx-auto w-full max-w-[320px] overflow-hidden rounded-xl bg-chumbo">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={foto.urlOriginal} alt="" className="block w-full" onLoad={(e) => setDim({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })} />
        {dim && (
          <>
            <div className="absolute inset-x-0 top-0 bg-black/65" style={{ height: `${topo * 100}%` }} />
            <div className="absolute inset-x-0 bottom-0 bg-black/65" style={{ height: `${(1 - topo - alturaJanela) * 100}%` }} />
            <div className="absolute inset-x-0 border-2 border-laranja" style={{ top: `${topo * 100}%`, height: `${alturaJanela * 100}%` }} />
          </>
        )}
      </div>
      {dim && alturaJanela >= 1 ? (
        <p className="mt-4 text-sm text-nevoa">Esta foto já está no formato do card; não há o que ajustar.</p>
      ) : (
        <label className="mt-4 block text-sm">
          Posição do corte
          <input type="range" min={0} max={1} step={0.01} value={foco} onChange={(e) => setFoco(Number(e.target.value))} className="mt-2 w-full accent-[#ff7a1a]" />
        </label>
      )}
      <button
        disabled={salvando}
        className={cn(classeBotao("primario"), "mt-5 w-full")}
        onClick={() =>
          iniciar(async () => {
            await reenquadrarFoto(foto.id, foco);
            router.refresh();
            aoFechar();
          })
        }
      >
        {salvando ? "Salvando…" : "Salvar enquadramento"}
      </button>
    </Modal>
  );
}
