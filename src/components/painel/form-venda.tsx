"use client";

import { startTransition, useActionState, useMemo, useState } from "react";
import { AlertTriangle, Check, Loader2, Plus, Trash2 } from "lucide-react";
import { CampoDinheiro, Retorno } from "@/components/interativos";
import { Campo, classeBotao, classeCampo } from "@/components/ui";
import { criarVenda } from "@/lib/acoes/vendas";
import {
  ETAPAS_VENDA,
  FLUXO_ETAPAS,
  FORMAS_PAGAMENTO,
  ORIGENS_CLIENTE,
  TIPOS_CUSTO_VENDA,
  type FormaPagamento,
  hojeISO,
  parcelaPrice,
  reais,
  somarDias,
  somarMeses,
} from "@/lib/dominio";
import { cn } from "@/lib/cn";

type VeiculoOpcao = { id: number; nome: string; preco: number; minimo: number; custo: number; gastos: number; consignado: boolean };
type ClienteOpcao = { id: number; nome: string; telefone: string | null };
type Det = Record<string, string | number | boolean | null>;
type Pag = { id: string; forma: FormaPagamento; valor: number; detalhes: Det };
type Custo = { id: string; tipo: keyof typeof TIPOS_CUSTO_VENDA; descricao: string; valor: number };

const uid = () => Math.random().toString(36).slice(2);

function padrao(forma: FormaPagamento, data: string, contaId?: number): Det {
  switch (forma) {
    case "sinal":
    case "pix_dinheiro":
      return { data, recebido: true, contaId: contaId ?? null };
    case "cartao":
      return { parcelas: 10, taxaPct: 8, antecipado: true, primeiroRecebimento: somarDias(data, 30) };
    case "financiamento_bancario":
      return { banco: "", parcelas: 48, taxaMensal: 1.99, retorno: 0, previsaoLiberacao: somarDias(data, 7), ficha: "em_analise" };
    case "leasing":
      return { instituicao: "", previsaoLiberacao: somarDias(data, 10) };
    case "financiamento_proprio":
      return { parcelas: 12, jurosMensalPct: 2, primeiroVencimento: somarMeses(data, 1) };
    case "cheque":
      return { banco: "", numero: "", bomPara: somarDias(data, 30) };
    case "consorcio":
      return { administradora: "", previsaoLiberacao: somarDias(data, 15) };
    case "troca":
      return { marca: "", modelo: "", versao: "", ano: "", km: "", cor: "", placa: "" };
  }
}

function CamposForma({ p, set, contas }: { p: Pag; set: (d: Det) => void; contas: { id: number; nome: string }[] }) {
  const d = p.detalhes;
  const txt = (k: string, rotulo: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <Campo rotulo={rotulo}>
      <input className={classeCampo} value={String(d[k] ?? "")} onChange={(e) => set({ ...d, [k]: e.target.value })} {...props} />
    </Campo>
  );
  const num = (k: string, rotulo: string, passo = "1") => (
    <Campo rotulo={rotulo}>
      <input type="number" step={passo} min={0} className={cn(classeCampo, "num")} value={String(d[k] ?? "")} onChange={(e) => set({ ...d, [k]: e.target.value === "" ? null : Number(e.target.value) })} />
    </Campo>
  );
  const dataCampo = (k: string, rotulo: string) => (
    <Campo rotulo={rotulo}>
      <input type="date" className={cn(classeCampo, "num")} value={String(d[k] ?? "")} onChange={(e) => set({ ...d, [k]: e.target.value })} />
    </Campo>
  );
  const marcar = (k: string, rotulo: string) => (
    <label className="flex items-center gap-2 self-end pb-2.5 text-sm text-nevoa">
      <input type="checkbox" className="accent-[#ff7a1a]" checked={Boolean(d[k])} onChange={(e) => set({ ...d, [k]: e.target.checked })} /> {rotulo}
    </label>
  );

  switch (p.forma) {
    case "sinal":
    case "pix_dinheiro":
      return (
        <>
          {dataCampo("data", "Data")}
          {contas.length > 0 && (
            <Campo rotulo="Conta">
              <select className={classeCampo} value={String(d.contaId ?? "")} onChange={(e) => set({ ...d, contaId: e.target.value ? Number(e.target.value) : null })}>
                <option value="">—</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>{c.nome}</option>
                ))}
              </select>
            </Campo>
          )}
          {marcar("recebido", "Já recebido")}
        </>
      );
    case "cartao": {
      const liquido = Math.round(p.valor * (1 - Number(d.taxaPct ?? 0) / 100));
      return (
        <>
          {num("parcelas", "Parcelas no cartão")}
          {num("taxaPct", "Taxa da maquininha (%)", "0.01")}
          {dataCampo("primeiroRecebimento", "Primeiro recebimento")}
          {marcar("antecipado", "Recebimento antecipado (tudo de uma vez)")}
          <p className="text-xs text-nevoa sm:col-span-2">Líquido para a loja: <span className="num text-giz">{reais(liquido)}</span></p>
        </>
      );
    }
    case "financiamento_bancario": {
      const parcela = parcelaPrice(p.valor, Number(d.taxaMensal ?? 0), Number(d.parcelas ?? 1));
      return (
        <>
          {txt("banco", "Banco / financeira", { placeholder: "Banco Pan, Santander, BV…" })}
          {num("parcelas", "Parcelas do cliente")}
          {num("taxaMensal", "Taxa ao mês (%)", "0.01")}
          <Campo rotulo="Retorno pago à loja">
            <CampoDinheiro name={`retorno-${p.id}`} defaultValue={Number(d.retorno ?? 0)} onValor={(c) => set({ ...d, retorno: c })} />
          </Campo>
          {dataCampo("previsaoLiberacao", "Previsão de liberação")}
          <Campo rotulo="Situação da ficha">
            <select className={classeCampo} value={String(d.ficha ?? "")} onChange={(e) => set({ ...d, ficha: e.target.value })}>
              <option value="em_analise">Em análise</option>
              <option value="aprovada">Aprovada</option>
              <option value="recusada">Recusada</option>
            </select>
          </Campo>
          <p className="text-xs text-nevoa sm:col-span-2">Parcela estimada do cliente: <span className="num text-giz">{Number(d.parcelas ?? 0)}x {reais(parcela)}</span></p>
        </>
      );
    }
    case "leasing":
      return (
        <>
          {txt("instituicao", "Instituição")}
          {dataCampo("previsaoLiberacao", "Previsão de liberação")}
        </>
      );
    case "consorcio":
      return (
        <>
          {txt("administradora", "Administradora")}
          {txt("grupoCota", "Grupo / cota")}
          {dataCampo("previsaoLiberacao", "Previsão de liberação da carta")}
        </>
      );
    case "financiamento_proprio": {
      const parcela = parcelaPrice(p.valor, Number(d.jurosMensalPct ?? 0), Number(d.parcelas ?? 1));
      return (
        <>
          {num("parcelas", "Parcelas")}
          {num("jurosMensalPct", "Juros ao mês (%)", "0.01")}
          {dataCampo("primeiroVencimento", "1º vencimento")}
          <p className="text-xs text-nevoa sm:col-span-2">
            {Number(d.parcelas ?? 0)}x de <span className="num text-giz">{reais(parcela)}</span> · total <span className="num text-giz">{reais(parcela * Number(d.parcelas ?? 0))}</span> · as parcelas entram no caixa como a receber
          </p>
        </>
      );
    }
    case "cheque":
      return (
        <>
          {txt("banco", "Banco")}
          {txt("numero", "Número do cheque")}
          {dataCampo("bomPara", "Bom para")}
        </>
      );
    case "troca":
      return (
        <>
          {txt("marca", "Marca")}
          {txt("modelo", "Modelo")}
          {txt("versao", "Versão")}
          {txt("ano", "Ano", { inputMode: "numeric", maxLength: 4 })}
          {txt("km", "Km", { inputMode: "numeric" })}
          {txt("cor", "Cor")}
          {txt("placa", "Placa")}
          <p className="text-xs text-nevoa sm:col-span-2">O valor é a avaliação. O carro entra no estoque como “Em preparação”, com esse valor de custo.</p>
        </>
      );
  }
}

export function FormVenda({
  veiculos,
  clientes,
  contas,
  veiculoInicial,
  clienteInicial,
}: {
  veiculos: VeiculoOpcao[];
  clientes: ClienteOpcao[];
  contas: { id: number; nome: string }[];
  veiculoInicial?: number;
  clienteInicial?: number;
}) {
  const hoje = hojeISO();
  const [veiculoId, setVeiculoId] = useState<number | "">(veiculoInicial && veiculos.some((v) => v.id === veiculoInicial) ? veiculoInicial : "");
  const veiculo = veiculos.find((v) => v.id === veiculoId);
  const [modoCliente, setModoCliente] = useState<"existente" | "novo">(clientes.length ? "existente" : "novo");
  const [clienteId, setClienteId] = useState<number | "">(clienteInicial && clientes.some((c) => c.id === clienteInicial) ? clienteInicial : "");
  const [buscaCliente, setBuscaCliente] = useState("");
  const [novo, setNovo] = useState({ nome: "", telefone: "", cpf: "", origem: "loja" });
  const [preco, setPreco] = useState(veiculo?.preco ?? 0);
  const [precoKey, setPrecoKey] = useState(0);
  const [data, setData] = useState(hoje);
  const [etapa, setEtapa] = useState<keyof typeof ETAPAS_VENDA>("negociacao");
  const [pags, setPags] = useState<Pag[]>([]);
  const [custos, setCustos] = useState<Custo[]>([{ id: "inicial", tipo: "despachante", descricao: "", valor: 0 }]);
  const [obs, setObs] = useState("");
  const [novaForma, setNovaForma] = useState<FormaPagamento>("pix_dinheiro");
  const [erro, setErro] = useState<string | null>(null);
  const [estado, despachar, enviando] = useActionState(criarVenda, null);

  const somaPags = pags.reduce((s, p) => s + p.valor, 0);
  const falta = preco - somaPags;
  const somaCustos = custos.reduce((s, c) => s + c.valor, 0);
  const lucro = useMemo(() => {
    if (!veiculo) return 0;
    const taxas = pags.filter((p) => p.forma === "cartao").reduce((s, p) => s + Math.round((p.valor * Number(p.detalhes.taxaPct ?? 0)) / 100), 0);
    const retorno = pags.filter((p) => p.forma === "financiamento_bancario").reduce((s, p) => s + Number(p.detalhes.retorno ?? 0), 0);
    return preco - veiculo.custo - veiculo.gastos - somaCustos - taxas + retorno;
  }, [veiculo, preco, pags, somaCustos]);
  const clientesFiltrados = clientes.filter((c) => `${c.nome} ${c.telefone ?? ""}`.toLowerCase().includes(buscaCliente.toLowerCase())).slice(0, 50);

  const escolherVeiculo = (id: number | "") => {
    setVeiculoId(id);
    const v = veiculos.find((x) => x.id === id);
    if (v) {
      setPreco(v.preco);
      setPrecoKey((k) => k + 1);
    }
  };

  const adicionar = () => {
    const valor = Math.max(0, falta);
    setPags((a) => [...a, { id: uid(), forma: novaForma, valor, detalhes: padrao(novaForma, data, contas[0]?.id) }]);
  };

  const salvar = () => {
    if (!veiculo) return setErro("Escolha o veículo.");
    if (modoCliente === "existente" && !clienteId) return setErro("Escolha o cliente ou cadastre um novo.");
    if (modoCliente === "novo" && novo.nome.trim().length < 2) return setErro("Informe o nome do cliente.");
    if (!preco) return setErro("Informe o preço final.");
    if (!pags.length) return setErro("Adicione ao menos uma forma de pagamento.");
    if (falta !== 0) return setErro(falta > 0 ? `Faltam ${reais(falta)} nas formas de pagamento.` : `As formas de pagamento passam ${reais(-falta)} do preço.`);
    const troca = pags.find((p) => p.forma === "troca" && (!p.detalhes.marca || !p.detalhes.modelo));
    if (troca) return setErro("Informe marca e modelo do carro da troca.");
    setErro(null);
    const payload = {
      veiculoId: veiculo.id,
      cliente: modoCliente === "existente" ? { id: clienteId } : { novo: { nome: novo.nome.trim(), telefone: novo.telefone || undefined, cpf: novo.cpf || undefined, origem: novo.origem } },
      precoFinal: preco,
      dataVenda: data,
      etapa,
      observacoes: obs || undefined,
      pagamentos: pags.map((p) => ({
        forma: p.forma,
        valor: p.valor,
        detalhes: Object.fromEntries(Object.entries(p.detalhes).map(([k, x]) => [k, k === "ano" || k === "km" ? (x === "" ? null : Number(x)) : x])),
      })),
      custos: custos.filter((c) => c.valor > 0).map((c) => ({ tipo: c.tipo, descricao: c.descricao || undefined, valor: c.valor })),
    };
    const fd = new FormData();
    fd.append("payload", JSON.stringify(payload));
    startTransition(() => despachar(fd));
  };

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_340px]">
      <div className="min-w-0 space-y-5">
        <section className="min-w-0 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5">
          <h2 className="display mb-4 text-[17px] font-semibold">Carro e cliente</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <Campo rotulo="Veículo" obrigatorio>
              <select className={classeCampo} value={veiculoId} onChange={(e) => escolherVeiculo(e.target.value ? Number(e.target.value) : "")}>
                <option value="">Escolha o carro</option>
                {veiculos.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.nome} · {reais(v.preco)}
                  </option>
                ))}
              </select>
            </Campo>
            <div>
              <div className="mb-1 flex gap-3 text-xs">
                {(["existente", "novo"] as const).map((m) => (
                  <button key={m} type="button" onClick={() => setModoCliente(m)} className={cn(modoCliente === m ? "text-laranja" : "text-nevoa hover:text-giz")}>
                    {m === "existente" ? "Cliente cadastrado" : "+ Cliente novo"}
                  </button>
                ))}
              </div>
              {modoCliente === "existente" ? (
                <div className="space-y-2">
                  <input className={classeCampo} placeholder="Buscar por nome ou telefone" value={buscaCliente} onChange={(e) => setBuscaCliente(e.target.value)} />
                  <select className={classeCampo} value={clienteId} onChange={(e) => setClienteId(e.target.value ? Number(e.target.value) : "")}>
                    <option value="">Escolha o cliente</option>
                    {clientesFiltrados.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nome}
                        {c.telefone ? ` · ${c.telefone}` : ""}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2">
                  <input className={cn(classeCampo, "sm:col-span-2")} placeholder="Nome completo *" value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} />
                  <input className={classeCampo} placeholder="Telefone" value={novo.telefone} onChange={(e) => setNovo({ ...novo, telefone: e.target.value })} />
                  <input className={classeCampo} placeholder="CPF (opcional)" value={novo.cpf} onChange={(e) => setNovo({ ...novo, cpf: e.target.value })} />
                  <select className={cn(classeCampo, "sm:col-span-2")} value={novo.origem} onChange={(e) => setNovo({ ...novo, origem: e.target.value })}>
                    {Object.entries(ORIGENS_CLIENTE).map(([k, n]) => (
                      <option key={k} value={k}>Como chegou: {n}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
          {veiculo?.consignado && <p className="mt-3 text-xs text-ambar">Carro em consignação: o repasse de {reais(veiculo.custo)} ao dono entra no caixa como a pagar.</p>}
        </section>

        <section className="min-w-0 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5">
          <h2 className="display mb-4 text-[17px] font-semibold">Negócio</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <Campo rotulo="Preço final" obrigatorio>
              <CampoDinheiro key={precoKey} name="precoFinal" defaultValue={preco} onValor={setPreco} />
            </Campo>
            <Campo rotulo="Data da venda">
              <input type="date" className={cn(classeCampo, "num")} value={data} onChange={(e) => setData(e.target.value)} />
            </Campo>
            <Campo rotulo="Etapa" dica="A partir de “Contrato assinado” o carro fica como vendido">
              <select className={classeCampo} value={etapa} onChange={(e) => setEtapa(e.target.value as keyof typeof ETAPAS_VENDA)}>
                {FLUXO_ETAPAS.map((e) => (
                  <option key={e} value={e}>{ETAPAS_VENDA[e]}</option>
                ))}
              </select>
            </Campo>
          </div>
          {veiculo && preco > 0 && preco < veiculo.minimo && (
            <p className="mt-3 flex items-center gap-2 text-sm text-alerta">
              <AlertTriangle size={15} /> Abaixo do mínimo combinado ({reais(veiculo.minimo)}).
            </p>
          )}
        </section>

        <section className="min-w-0 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="display text-[17px] font-semibold">Formas de pagamento</h2>
            <div className="flex gap-2">
              <select className={cn(classeCampo, "h-9 w-auto")} value={novaForma} onChange={(e) => setNovaForma(e.target.value as FormaPagamento)}>
                {Object.entries(FORMAS_PAGAMENTO).map(([k, n]) => (
                  <option key={k} value={k}>{n}</option>
                ))}
              </select>
              <button type="button" onClick={adicionar} className={classeBotao("secundario", "sm")}>
                <Plus size={14} /> Adicionar
              </button>
            </div>
          </div>
          {pags.length === 0 ? (
            <p className="rounded-xl border border-dashed border-linha p-6 text-center text-sm text-nevoa">
              Escolha a forma e clique em Adicionar. Combine quantas quiser: entrada em PIX + financiamento + carro na troca, por exemplo.
            </p>
          ) : (
            <ul className="space-y-3">
              {pags.map((p) => (
                <li key={p.id} className="rounded-2xl border border-linha/70 p-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <p className="flex-1 font-medium">{FORMAS_PAGAMENTO[p.forma]}</p>
                    <div className="w-44">
                      <CampoDinheiro name={`valor-${p.id}`} defaultValue={p.valor} onValor={(c) => setPags((a) => a.map((x) => (x.id === p.id ? { ...x, valor: c } : x)))} />
                    </div>
                    <button type="button" onClick={() => setPags((a) => a.filter((x) => x.id !== p.id))} className="text-nevoa hover:text-perigo" aria-label="Remover forma">
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <CamposForma p={p} contas={contas} set={(d) => setPags((a) => a.map((x) => (x.id === p.id ? { ...x, detalhes: d } : x)))} />
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className={cn("mt-4 text-sm", falta === 0 && pags.length ? "text-sucesso" : "text-nevoa")}>
            {falta === 0 && pags.length ? (
              <span className="flex items-center gap-1.5"><Check size={15} /> Pagamento fecha com o preço final.</span>
            ) : falta > 0 ? (
              <>Falta distribuir <span className="num font-semibold text-laranja">{reais(falta)}</span></>
            ) : (
              <>Passou <span className="num font-semibold text-perigo">{reais(-falta)}</span> do preço final</>
            )}
          </p>
        </section>

        <section className="min-w-0 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="display text-[17px] font-semibold">Custos da venda</h2>
            <button type="button" onClick={() => setCustos((a) => [...a, { id: uid(), tipo: "comissao", descricao: "", valor: 0 }])} className={classeBotao("secundario", "sm")}>
              <Plus size={14} /> Adicionar custo
            </button>
          </div>
          <ul className="space-y-2">
            {custos.map((c) => (
              <li key={c.id} className="grid gap-2 sm:grid-cols-[200px_1fr_160px_auto] sm:items-center">
                <select className={classeCampo} value={c.tipo} onChange={(e) => setCustos((a) => a.map((x) => (x.id === c.id ? { ...x, tipo: e.target.value as Custo["tipo"] } : x)))}>
                  {Object.entries(TIPOS_CUSTO_VENDA).map(([k, n]) => (
                    <option key={k} value={k}>{n}</option>
                  ))}
                </select>
                <input className={classeCampo} placeholder="Detalhe (opcional)" value={c.descricao} onChange={(e) => setCustos((a) => a.map((x) => (x.id === c.id ? { ...x, descricao: e.target.value } : x)))} />
                <CampoDinheiro name={`custo-${c.id}`} defaultValue={c.valor} onValor={(v) => setCustos((a) => a.map((x) => (x.id === c.id ? { ...x, valor: v } : x)))} />
                <button type="button" onClick={() => setCustos((a) => a.filter((x) => x.id !== c.id))} className="justify-self-end text-nevoa hover:text-perigo" aria-label="Remover custo">
                  <Trash2 size={16} />
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-nevoa">Cada custo entra no caixa como a pagar na data da venda.</p>
          <Campo rotulo="Observações" className="mt-4">
            <textarea className={cn(classeCampo, "h-20 py-2")} value={obs} onChange={(e) => setObs(e.target.value)} placeholder="Combinados com o cliente, acessórios, prazo de entrega…" />
          </Campo>
        </section>
      </div>

      <aside className="h-fit space-y-4 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5 xl:sticky xl:top-6">
        <h2 className="display text-[17px] font-semibold">Resumo</h2>
        {veiculo ? (
          <dl className="space-y-2.5 text-sm">
            <div className="flex justify-between"><dt className="text-nevoa">Anunciado</dt><dd className="num">{reais(veiculo.preco)}</dd></div>
            <div className="flex justify-between"><dt className="text-nevoa">Preço final</dt><dd className="num font-semibold">{reais(preco)}</dd></div>
            <div className="flex justify-between"><dt className="text-nevoa">Desconto</dt><dd className="num">{reais(Math.max(0, veiculo.preco - preco))}</dd></div>
            <div className="flex justify-between"><dt className="text-nevoa">{veiculo.consignado ? "Repasse" : "Custo"} + gastos</dt><dd className="num">{reais(veiculo.custo + veiculo.gastos)}</dd></div>
            <div className="flex justify-between"><dt className="text-nevoa">Custos da venda</dt><dd className="num">{reais(somaCustos)}</dd></div>
            <div className="flex justify-between border-t border-linha pt-2.5 font-semibold"><dt>Lucro estimado</dt><dd className={cn("num", lucro >= 0 ? "text-sucesso" : "text-perigo")}>{reais(lucro)}</dd></div>
          </dl>
        ) : (
          <p className="text-sm text-nevoa">Escolha o carro para ver o resultado.</p>
        )}
        {erro ? <p className="rounded-xl border border-perigo/30 bg-perigo/10 px-3 py-2 text-sm text-perigo">{erro}</p> : <Retorno estado={estado} />}
        <button type="button" onClick={salvar} disabled={enviando} className={cn(classeBotao("primario"), "w-full")}>
          {enviando ? <><Loader2 size={16} className="animate-spin" /> Registrando…</> : "Registrar venda"}
        </button>
        <p className="text-[11px] leading-relaxed text-nevoa-2">
          Ao registrar, as parcelas e liberações entram no caixa como a receber, os custos como a pagar, o carro da troca vai para o estoque e o carro vendido sai da vitrine quando o contrato for assinado.
        </p>
      </aside>
    </div>
  );
}
