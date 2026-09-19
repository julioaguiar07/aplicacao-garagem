"use client";

import { useActionState, useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import { classeBotao } from "@/components/ui";
import type { Resultado } from "@/lib/acoes/comum";

/** Janela modal com <dialog> nativo (Esc fecha, foco preso) */
export function Modal({
  aberto,
  aoFechar,
  titulo,
  children,
  largura = "max-w-lg",
}: {
  aberto: boolean;
  aoFechar: () => void;
  titulo: string;
  children: React.ReactNode;
  largura?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (aberto && !d.open) d.showModal();
    if (!aberto && d.open) d.close();
  }, [aberto]);
  return (
    <dialog
      ref={ref}
      onClose={aoFechar}
      onClick={(e) => e.target === ref.current && aoFechar()}
      className={cn(
        "m-auto w-[calc(100%-2rem)] rounded-[var(--radius-card)] border border-linha bg-grafite p-0 text-giz backdrop:bg-black/70 backdrop:backdrop-blur-sm",
        largura,
      )}
    >
      {aberto && (
        <div className="max-h-[85dvh] overflow-y-auto p-6 scrollbar-fina">
          <div className="mb-5 flex items-start justify-between gap-4">
            <h2 className="display text-xl font-bold">{titulo}</h2>
            <button onClick={aoFechar} className="rounded-lg p-1 text-nevoa hover:bg-chumbo hover:text-giz" aria-label="Fechar">
              <X size={18} />
            </button>
          </div>
          {children}
        </div>
      )}
    </dialog>
  );
}

/** Mensagem de resultado de uma ação */
export function Retorno({ estado }: { estado: Resultado<unknown> | null }) {
  if (!estado) return null;
  if (!estado.ok) return <p className="rounded-xl border border-perigo/30 bg-perigo/10 px-3 py-2 text-sm text-perigo">{estado.erro}</p>;
  if (estado.mensagem) return <p className="rounded-xl border border-sucesso/30 bg-sucesso/10 px-3 py-2 text-sm text-sucesso">{estado.mensagem}</p>;
  return null;
}

/** Formulário ligado a uma server action, com estado de envio e mensagem; fecha/limpa ao dar certo */
export function FormAcao({
  acao,
  children,
  className,
  rotulo,
  rotuloEnviando = "Salvando…",
  aoConcluir,
  limparAoConcluir = true,
  variante = "primario",
}: {
  acao: (estado: Resultado | null, form: FormData) => Promise<Resultado>;
  children: React.ReactNode;
  className?: string;
  rotulo: string;
  rotuloEnviando?: string;
  aoConcluir?: () => void;
  limparAoConcluir?: boolean;
  variante?: "primario" | "secundario" | "perigo";
}) {
  const [estado, despachar, enviando] = useActionState(acao, null);
  const ref = useRef<HTMLFormElement>(null);
  const ultimo = useRef<Resultado | null>(null);
  useEffect(() => {
    if (estado && estado !== ultimo.current && estado.ok) {
      if (limparAoConcluir) ref.current?.reset();
      aoConcluir?.();
    }
    ultimo.current = estado;
  }, [estado, aoConcluir, limparAoConcluir]);
  return (
    <form ref={ref} action={despachar} className={cn("space-y-3", className)}>
      {children}
      <Retorno estado={estado} />
      <button disabled={enviando} className={cn(classeBotao(variante), "w-full")}>
        {enviando ? rotuloEnviando : rotulo}
      </button>
    </form>
  );
}

/** Botão que chama uma ação simples (sem formulário), com confirmação opcional */
export function BotaoAcao({
  acao,
  children,
  confirmar,
  className,
  variante = "secundario",
  tamanho = "sm",
  aoConcluir,
}: {
  acao: () => Promise<Resultado>;
  children: React.ReactNode;
  confirmar?: string;
  className?: string;
  variante?: "primario" | "secundario" | "perigo" | "fantasma";
  tamanho?: "sm" | "md";
  aoConcluir?: () => void;
}) {
  const [pendente, iniciar] = useTransition();
  const [erro, setErro] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const router = useRouter();
  const executar = () =>
    iniciar(async () => {
      setErro(null);
      const r = await acao();
      if (!r.ok) setErro(r.erro);
      else {
        setConfirmando(false);
        aoConcluir?.();
        router.refresh();
      }
    });
  return (
    <span className="inline-flex flex-col items-start gap-1">
      {confirmando ? (
        <span className="inline-flex flex-wrap items-center gap-2 text-xs">
          <span className="text-nevoa">{confirmar}</span>
          <button onClick={executar} disabled={pendente} className={classeBotao("perigo", "sm")}>
            {pendente ? "Aguarde…" : "Confirmar"}
          </button>
          <button onClick={() => setConfirmando(false)} className={classeBotao("fantasma", "sm")}>
            Voltar
          </button>
        </span>
      ) : (
        <button onClick={() => (confirmar ? setConfirmando(true) : executar())} disabled={pendente} className={cn(classeBotao(variante, tamanho), className)}>
          {pendente ? "Aguarde…" : children}
        </button>
      )}
      {erro && <span className="text-xs text-perigo">{erro}</span>}
    </span>
  );
}

/** Campo de dinheiro que formata enquanto digita (R$ 1.234,56) */
export function CampoDinheiro({ name, defaultValue, placeholder = "0,00", className, onValor, required }: { name: string; defaultValue?: number | null; placeholder?: string; className?: string; onValor?: (centavos: number) => void; required?: boolean }) {
  const fmt = (c: number) => (c / 100).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const [valor, setValor] = useState(defaultValue ? fmt(defaultValue) : "");
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-nevoa">R$</span>
      <input
        name={name}
        inputMode="numeric"
        required={required}
        value={valor}
        placeholder={placeholder}
        onChange={(e) => {
          const digitos = e.target.value.replace(/\D/g, "").slice(0, 12);
          const c = Number(digitos || 0);
          setValor(digitos ? fmt(c) : "");
          onValor?.(c);
        }}
        className={cn(
          "num h-10 w-full rounded-xl border border-linha bg-asfalto pl-9 pr-3 text-sm focus:border-laranja/60 focus:outline-none",
          className,
        )}
      />
    </div>
  );
}
