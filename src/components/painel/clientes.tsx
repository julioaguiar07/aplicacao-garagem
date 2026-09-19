"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import { FormAcao, Modal } from "@/components/interativos";
import { Campo, classeBotao, classeCampo } from "@/components/ui";
import { salvarCliente } from "@/lib/acoes/clientes";
import { ORIGENS_CLIENTE, dataBR, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export type DadosCliente = {
  nome: string;
  telefone: string | null;
  email: string | null;
  cpf: string | null;
  endereco: string | null;
  cidade: string | null;
  origem: string | null;
  interesse: string | null;
  observacoes: string | null;
};

export function CamposCliente({ c }: { c?: Partial<DadosCliente> }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Campo rotulo="Nome" obrigatorio className="sm:col-span-2">
        <input name="nome" defaultValue={c?.nome ?? ""} required className={classeCampo} />
      </Campo>
      <Campo rotulo="Telefone / WhatsApp">
        <input name="telefone" defaultValue={c?.telefone ?? ""} className={classeCampo} placeholder="(84) 99999-9999" />
      </Campo>
      <Campo rotulo="E-mail">
        <input name="email" type="email" defaultValue={c?.email ?? ""} className={classeCampo} />
      </Campo>
      <Campo rotulo="CPF ou CNPJ" dica="Opcional: pedido na hora do contrato">
        <input name="cpf" defaultValue={c?.cpf ?? ""} className={classeCampo} />
      </Campo>
      <Campo rotulo="Como chegou">
        <select name="origem" defaultValue={c?.origem ?? "loja"} className={classeCampo}>
          {Object.entries(ORIGENS_CLIENTE).map(([k, n]) => (
            <option key={k} value={k}>
              {n}
            </option>
          ))}
        </select>
      </Campo>
      <Campo rotulo="Endereço">
        <input name="endereco" defaultValue={c?.endereco ?? ""} className={classeCampo} />
      </Campo>
      <Campo rotulo="Cidade">
        <input name="cidade" defaultValue={c?.cidade ?? ""} className={classeCampo} placeholder="Mossoró/RN" />
      </Campo>
      <Campo rotulo="Interesse" className="sm:col-span-2">
        <input name="interesse" defaultValue={c?.interesse ?? ""} className={classeCampo} placeholder="SUV automático até R$ 90 mil" />
      </Campo>
      <Campo rotulo="Observações" className="sm:col-span-2">
        <textarea name="observacoes" defaultValue={c?.observacoes ?? ""} className={cn(classeCampo, "h-20 py-2")} />
      </Campo>
    </div>
  );
}

export function NovoCliente() {
  const [aberto, setAberto] = useState(false);
  return (
    <>
      <button onClick={() => setAberto(true)} className={classeBotao("primario")}>
        <Plus size={17} /> Novo cliente
      </button>
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo="Novo cliente">
        <FormAcao acao={salvarCliente.bind(null, null)} rotulo="Cadastrar cliente">
          <CamposCliente />
        </FormAcao>
      </Modal>
    </>
  );
}

export function EditarCliente({ id, c }: { id: number; c: DadosCliente }) {
  return (
    <FormAcao acao={salvarCliente.bind(null, id)} rotulo="Salvar alterações" variante="secundario" limparAoConcluir={false}>
      <CamposCliente c={c} />
    </FormAcao>
  );
}

export interface LinhaCliente {
  id: number;
  nome: string;
  telefone: string | null;
  origem: string | null;
  interesse: string | null;
  compras: number;
  totalComprado: number;
  ultimaCompra: string | null;
  aReceber: number;
  atrasado: number;
}

const FILTROS = { todos: "Todos", compradores: "Compraram", interessados: "Interessados", devendo: "Com parcelas" } as const;

export function TabelaClientes({ clientes }: { clientes: LinhaCliente[] }) {
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState<keyof typeof FILTROS>("todos");
  const passa = (c: LinhaCliente, f: keyof typeof FILTROS) => (f === "compradores" ? c.compras > 0 : f === "interessados" ? c.compras === 0 : f === "devendo" ? c.aReceber > 0 : true);
  const lista = useMemo(() => {
    const t = busca.toLowerCase();
    return clientes.filter((c) => passa(c, filtro) && (!t || `${c.nome} ${c.telefone ?? ""} ${c.interesse ?? ""}`.toLowerCase().includes(t)));
  }, [clientes, busca, filtro]);
  return (
    <section className="rounded-[var(--radius-card)] border border-linha/60 bg-grafite">
      <div className="flex flex-wrap items-center gap-3 p-5 pb-4">
        <h2 className="display mr-auto text-[17px] font-semibold">Clientes</h2>
        <div className="flex gap-1.5 overflow-x-auto">
          {(Object.keys(FILTROS) as (keyof typeof FILTROS)[]).map((f) => (
            <button key={f} onClick={() => setFiltro(f)} className={cn("shrink-0 rounded-full border px-3 py-1.5 text-xs", filtro === f ? "border-laranja bg-laranja/10 text-laranja" : "border-linha text-nevoa hover:text-giz")}>
              {FILTROS[f]} <span className="num opacity-70">{clientes.filter((c) => passa(c, f)).length}</span>
            </button>
          ))}
        </div>
        <label className="relative flex items-center">
          <Search size={15} className="pointer-events-none absolute left-3 text-nevoa" />
          <input value={busca} onChange={(e) => setBusca(e.target.value)} type="search" placeholder="Nome, telefone, interesse" className="h-9 w-56 rounded-full border border-linha bg-asfalto pl-9 pr-3 text-sm focus:border-laranja/60 focus:outline-none" />
        </label>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[820px] text-sm">
          <thead>
            <tr className="border-y border-linha/60 text-left text-xs text-nevoa">
              <th className="px-5 py-2.5 font-medium">Nome</th>
              <th className="px-3 py-2.5 font-medium">Telefone</th>
              <th className="px-3 py-2.5 font-medium">Origem</th>
              <th className="px-3 py-2.5 font-medium">Interesse / última compra</th>
              <th className="px-3 py-2.5 text-right font-medium">Compras</th>
              <th className="px-3 py-2.5 text-right font-medium">Total</th>
              <th className="px-5 py-2.5 text-right font-medium">A receber</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((c) => (
              <tr key={c.id} className="border-b border-linha/40 hover:bg-chumbo/40">
                <td className="px-5 py-3 font-medium">
                  <Link href={`/painel/clientes/${c.id}`} className="hover:text-laranja">
                    {c.nome}
                  </Link>
                </td>
                <td className="num px-3 py-3 text-nevoa">
                  {c.telefone ? (
                    <a href={`https://wa.me/55${c.telefone.replace(/\D/g, "")}`} target="_blank" rel="noopener" className="hover:text-laranja">
                      {c.telefone}
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-3 py-3 text-nevoa">{c.origem ? ORIGENS_CLIENTE[c.origem as keyof typeof ORIGENS_CLIENTE] ?? c.origem : "—"}</td>
                <td className="px-3 py-3 text-nevoa">{c.ultimaCompra ? `Comprou em ${dataBR(c.ultimaCompra)}` : c.interesse ?? "—"}</td>
                <td className="num px-3 py-3 text-right">{c.compras}</td>
                <td className="num px-3 py-3 text-right">{c.totalComprado ? reais(c.totalComprado) : "—"}</td>
                <td className={cn("num px-5 py-3 text-right", c.atrasado ? "text-perigo" : c.aReceber ? "text-giz" : "text-nevoa-2")}>
                  {c.aReceber ? reais(c.aReceber) : "—"}
                  {c.atrasado > 0 && <span className="block text-[11px]">{reais(c.atrasado)} atrasado</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {lista.length === 0 && <p className="p-8 text-center text-sm text-nevoa">Nenhum cliente encontrado.</p>}
      </div>
    </section>
  );
}
