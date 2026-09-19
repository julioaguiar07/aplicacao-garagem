"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ExternalLink, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { BotaoAcao, CampoDinheiro, FormAcao, Modal } from "@/components/interativos";
import { BaixaLancamento } from "@/components/painel/venda";
import { Campo, SeloLancamento, classeBotao, classeCampo } from "@/components/ui";
import { excluirLancamento, novoLancamento, salvarConta } from "@/lib/acoes/caixa";
import { CATEGORIAS_ENTRADA, CATEGORIAS_SAIDA, dataBR, hojeISO, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

type Conta = { id: number; nome: string; tipo: string; saldoInicial: number; saldo: number };

export function NovoLancamento({ contas }: { contas: Conta[] }) {
  const [aberto, setAberto] = useState(false);
  const [tipo, setTipo] = useState<"entrada" | "saida">("saida");
  return (
    <>
      <button onClick={() => setAberto(true)} className={classeBotao("primario")}>
        <Plus size={17} /> <span className="hidden sm:inline">Novo lançamento</span>
      </button>
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo="Novo lançamento">
        <FormAcao acao={novoLancamento} rotulo="Salvar lançamento" aoConcluir={() => setAberto(false)}>
          <div className="flex rounded-full border border-linha p-0.5" role="group">
            {(["saida", "entrada"] as const).map((t) => (
              <button type="button" key={t} onClick={() => setTipo(t)} className={cn("flex-1 rounded-full py-1.5 text-sm", tipo === t ? (t === "entrada" ? "bg-sucesso/20 text-sucesso" : "bg-perigo/20 text-perigo") : "text-nevoa")}>
                {t === "entrada" ? "Entrada (a receber)" : "Saída (a pagar)"}
              </button>
            ))}
          </div>
          <input type="hidden" name="tipo" value={tipo} />
          <Campo rotulo="Descrição" obrigatorio>
            <input name="descricao" required className={classeCampo} placeholder={tipo === "saida" ? "Ex.: aluguel de outubro" : "Ex.: venda de acessório"} />
          </Campo>
          <div className="grid grid-cols-2 gap-3">
            <Campo rotulo="Categoria" obrigatorio>
              <select name="categoria" className={classeCampo} key={tipo}>
                {(tipo === "entrada" ? CATEGORIAS_ENTRADA : CATEGORIAS_SAIDA).map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </Campo>
            <Campo rotulo="Valor" obrigatorio>
              <CampoDinheiro name="valor" required />
            </Campo>
            <Campo rotulo="Vencimento">
              <input type="date" name="vencimento" defaultValue={hojeISO()} className={cn(classeCampo, "num")} />
            </Campo>
            <Campo rotulo="Conta">
              <select name="contaId" className={classeCampo}>
                <option value="">—</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </Campo>
            <Campo rotulo="Repetir todo mês" dica="1 = só este mês">
              <input type="number" name="repetirMeses" min={1} max={36} defaultValue={1} className={cn(classeCampo, "num")} />
            </Campo>
            <label className="flex items-center gap-2 self-end pb-2.5 text-sm text-nevoa">
              <input type="checkbox" name="pago" className="accent-[#ff7a1a]" /> Já {tipo === "entrada" ? "recebido" : "pago"}
            </label>
          </div>
          <Campo rotulo="Comprovante (opcional)">
            <input name="comprovante" type="file" accept="application/pdf,image/*" className="block w-full text-sm text-nevoa file:mr-3 file:rounded-full file:border-0 file:bg-chumbo file:px-3 file:py-1.5 file:text-giz" />
          </Campo>
          <Campo rotulo="Observações">
            <input name="observacoes" className={classeCampo} />
          </Campo>
        </FormAcao>
      </Modal>
    </>
  );
}

export function EditarConta({ conta }: { conta?: Conta }) {
  const [aberto, setAberto] = useState(false);
  return (
    <>
      {conta ? (
        <button onClick={() => setAberto(true)} className="rounded-lg p-1 text-nevoa hover:bg-chumbo hover:text-giz" aria-label={`Editar ${conta.nome}`}>
          <Pencil size={14} />
        </button>
      ) : (
        <button onClick={() => setAberto(true)} className="grid h-full min-h-[110px] w-full place-items-center rounded-[var(--radius-card)] border border-dashed border-linha text-sm text-nevoa hover:border-laranja/50">
          <span className="flex items-center gap-1.5">
            <Plus size={15} /> Nova conta
          </span>
        </button>
      )}
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo={conta ? "Editar conta" : "Nova conta"} largura="max-w-sm">
        <FormAcao acao={salvarConta} rotulo="Salvar" aoConcluir={() => setAberto(false)} limparAoConcluir={!conta}>
          {conta && <input type="hidden" name="id" value={conta.id} />}
          <Campo rotulo="Nome">
            <input name="nome" defaultValue={conta?.nome} required className={classeCampo} placeholder="Ex.: Nubank" />
          </Campo>
          <Campo rotulo="Tipo">
            <select name="tipo" defaultValue={conta?.tipo ?? "banco"} className={classeCampo}>
              <option value="banco">Conta bancária</option>
              <option value="caixa">Dinheiro em caixa</option>
            </select>
          </Campo>
          <Campo rotulo="Saldo inicial" dica="Saldo antes do primeiro lançamento no sistema">
            <CampoDinheiro name="saldoInicial" defaultValue={conta?.saldoInicial} />
          </Campo>
        </FormAcao>
      </Modal>
    </>
  );
}

export interface LinhaLancamento {
  id: number;
  tipo: string;
  descricao: string;
  categoria: string;
  valor: number;
  vencimento: string;
  pagoEm: string | null;
  status: "previsto" | "realizado" | "atrasado";
  contaNome: string | null;
  vendaId: number | null;
  veiculo: { id: number; nome: string } | null;
  cliente: { id: number; nome: string } | null;
  recorrente: boolean;
  comprovante: string | null;
}

const FILTROS = { todos: "Todos", receber: "A receber", pagar: "A pagar", atrasados: "Atrasados", realizados: "Realizados" } as const;
export type FiltroCaixa = keyof typeof FILTROS;

export function TabelaLancamentos({ linhas, contas, filtroInicial }: { linhas: LinhaLancamento[]; contas: Conta[]; filtroInicial: FiltroCaixa }) {
  const [filtro, setFiltro] = useState<FiltroCaixa>(filtroInicial);
  const [busca, setBusca] = useState("");
  const passa = (l: LinhaLancamento, f: FiltroCaixa) =>
    f === "receber" ? l.tipo === "entrada" && !l.pagoEm : f === "pagar" ? l.tipo === "saida" && !l.pagoEm : f === "atrasados" ? l.status === "atrasado" : f === "realizados" ? Boolean(l.pagoEm) : true;
  const lista = useMemo(() => {
    const t = busca.toLowerCase();
    return linhas.filter((l) => passa(l, filtro) && (!t || `${l.descricao} ${l.categoria} ${l.cliente?.nome ?? ""}`.toLowerCase().includes(t)));
  }, [linhas, filtro, busca]);
  const entradas = lista.filter((l) => l.tipo === "entrada").reduce((s, l) => s + l.valor, 0);
  const saidas = lista.filter((l) => l.tipo === "saida").reduce((s, l) => s + l.valor, 0);
  const contasSimples = contas.map((c) => ({ id: c.id, nome: c.nome }));

  return (
    <>
      <div className="flex flex-wrap items-center gap-3 px-5 pb-4">
        <div className="flex gap-1.5 overflow-x-auto">
          {(Object.keys(FILTROS) as FiltroCaixa[]).map((f) => (
            <button key={f} onClick={() => setFiltro(f)} className={cn("shrink-0 rounded-full border px-3 py-1.5 text-xs", filtro === f ? "border-laranja bg-laranja/10 text-laranja" : "border-linha text-nevoa hover:text-giz")}>
              {FILTROS[f]} <span className="num opacity-70">{linhas.filter((l) => passa(l, f)).length}</span>
            </button>
          ))}
        </div>
        <label className="relative ml-auto flex items-center">
          <Search size={15} className="pointer-events-none absolute left-3 text-nevoa" />
          <input value={busca} onChange={(e) => setBusca(e.target.value)} type="search" placeholder="Descrição, categoria, cliente" className="h-9 w-60 rounded-full border border-linha bg-asfalto pl-9 pr-3 text-sm focus:border-laranja/60 focus:outline-none" />
        </label>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-sm">
          <thead>
            <tr className="border-y border-linha/60 text-left text-xs text-nevoa">
              <th className="px-5 py-2.5 font-medium">Vencimento</th>
              <th className="px-3 py-2.5 font-medium">Descrição</th>
              <th className="px-3 py-2.5 font-medium">Categoria</th>
              <th className="px-3 py-2.5 font-medium">Situação</th>
              <th className="px-3 py-2.5 text-right font-medium">Valor</th>
              <th className="px-5 py-2.5 text-right font-medium">Ações</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((l) => (
              <tr key={l.id} className="border-b border-linha/40 hover:bg-chumbo/30">
                <td className="num px-5 py-3 text-nevoa">
                  {dataBR(l.vencimento)}
                  {l.pagoEm && l.pagoEm !== l.vencimento && <span className="block text-[11px] text-nevoa-2">pago {dataBR(l.pagoEm).slice(0, 5)}</span>}
                </td>
                <td className="px-3 py-3">
                  <p>{l.descricao}</p>
                  <p className="text-[11px] text-nevoa">
                    {[
                      l.contaNome,
                      l.recorrente && "mensal",
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                    {l.vendaId && (
                      <Link href={`/painel/vendas/${l.vendaId}`} className="ml-1 text-laranja hover:underline">
                        ver venda
                      </Link>
                    )}
                    {!l.vendaId && l.veiculo && (
                      <Link href={`/painel/estoque/${l.veiculo.id}`} className="ml-1 text-laranja hover:underline">
                        {l.veiculo.nome}
                      </Link>
                    )}
                  </p>
                </td>
                <td className="px-3 py-3 text-nevoa">{l.categoria}</td>
                <td className="px-3 py-3">
                  <SeloLancamento status={l.status} tipo={l.tipo} />
                </td>
                <td className={cn("num whitespace-nowrap px-3 py-3 text-right", l.tipo === "entrada" ? "text-sucesso" : "")}>
                  {l.tipo === "entrada" ? "+" : "−"}
                  {reais(l.valor)}
                </td>
                <td className="px-5 py-3">
                  <span className="flex items-center justify-end gap-1">
                    {l.comprovante && (
                      <a href={l.comprovante} target="_blank" rel="noopener" className="rounded-lg p-1.5 text-nevoa hover:text-giz" aria-label="Abrir comprovante">
                        <ExternalLink size={14} />
                      </a>
                    )}
                    <BaixaLancamento id={l.id} valor={l.valor} tipo={l.tipo} pago={Boolean(l.pagoEm)} contas={contasSimples} />
                    {!l.vendaId && (
                      <BotaoAcao acao={() => excluirLancamento(l.id, l.recorrente)} confirmar={l.recorrente ? "Excluir este e os próximos em aberto?" : "Excluir?"} variante="fantasma">
                        <Trash2 size={13} />
                      </BotaoAcao>
                    )}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
          {lista.length > 0 && (
            <tfoot>
              <tr>
                <td colSpan={4} className="px-5 py-3 text-right text-xs text-nevoa">
                  Entradas <span className="num text-sucesso">{reais(entradas)}</span> · Saídas <span className="num text-giz">{reais(saidas)}</span>
                </td>
                <td className={cn("num whitespace-nowrap px-3 py-3 text-right font-semibold", entradas - saidas >= 0 ? "text-sucesso" : "text-perigo")}>{reais(entradas - saidas)}</td>
                <td />
              </tr>
            </tfoot>
          )}
        </table>
        {lista.length === 0 && <p className="p-8 text-center text-sm text-nevoa">Nenhum lançamento neste filtro.</p>}
      </div>
    </>
  );
}
