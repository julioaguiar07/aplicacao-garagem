"use client";

import Image from "next/image";
import { startTransition, useActionState, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, ChevronLeft, ChevronRight, FileText, ImagePlus, Loader2, Plus, Search, Star, Trash2, X } from "lucide-react";
import { CampoDinheiro, Retorno } from "@/components/interativos";
import { Campo, classeBotao, classeCampo } from "@/components/ui";
import type { Resultado } from "@/lib/acoes/comum";
import { CAMBIOS, CATEGORIAS, COMBUSTIVEIS, CORES, DESTAQUES, OPCIONAIS, ORIGEM_VEICULO, TIPOS_DOCUMENTO, hojeISO, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export interface ValoresVeiculo {
  marca: string;
  modelo: string;
  versao: string;
  anoModelo: string;
  anoFabricacao: string;
  cor: string;
  km: string;
  placa: string;
  chassi: string;
  renavam: string;
  categoria: string;
  cambio: string;
  combustivel: string;
  portas: string;
  opcionais: string[];
  destaques: string[];
  descricao: string;
  origem: string;
  fornecedor: string;
  dataEntrada: string;
  custo: number;
  preco: number;
  descontoMaximoPct: string;
  precoFipe: number;
  codigoFipe: string;
}

export const VALORES_VAZIOS: ValoresVeiculo = {
  marca: "", modelo: "", versao: "", anoModelo: "", anoFabricacao: "", cor: "", km: "", placa: "", chassi: "", renavam: "",
  categoria: "Hatch", cambio: "Manual", combustivel: "Flex", portas: "4", opcionais: [], destaques: [], descricao: "",
  origem: "compra", fornecedor: "", dataEntrada: "", custo: 0, preco: 0, descontoMaximoPct: "5", precoFipe: 0, codigoFipe: "",
};

const PASSOS_NOVO = ["Identificação", "Características", "Entrada e preço", "Fotos e documentos", "Revisão"];
const PASSOS_EDICAO = ["Identificação", "Características", "Entrada e preço"];
const CHAVE_RASCUNHO = "carmelo:rascunho-veiculo";

type OpcaoFipe = { codigo: string; nome: string };

/** "VW - VolksWagen" → "Volkswagen"; "GM - Chevrolet" → "Chevrolet"; "BMW" → "BMW" */
function limparMarca(nome: string) {
  const base = (nome.includes(" - ") ? nome.split(" - ").pop()! : nome).trim();
  // Siglas (BMW, JAC, RAM, GWM) ficam como estão
  if (/^[A-Z0-9]{2,4}$/.test(base)) return base;
  return base.toLowerCase().replace(/(^|[\s-])\S/g, (l) => l.toUpperCase());
}

function Chips({ opcoes, marcados, alternar, simples }: { opcoes: readonly string[]; marcados: string[]; alternar: (o: string) => void; simples?: boolean }) {
  return (
    <div className="flex flex-wrap gap-2">
      {opcoes.map((o) => {
        const on = marcados.includes(o);
        return (
          <button
            type="button"
            key={o}
            onClick={() => alternar(o)}
            aria-pressed={on}
            className={cn(
              "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition",
              on ? "border-laranja bg-laranja/10 text-laranja" : "border-linha text-nevoa hover:text-giz",
            )}
          >
            {on && !simples && <Check size={14} />}
            {o}
          </button>
        );
      })}
    </div>
  );
}

function BuscaFipe({ aoEscolher }: { aoEscolher: (d: { marca: string; modelo: string; versao: string; ano: string; combustivel: string; cambio: string | null; precoFipe: number; codigoFipe: string }) => void }) {
  const [marcas, setMarcas] = useState<OpcaoFipe[]>([]);
  const [modelos, setModelos] = useState<OpcaoFipe[]>([]);
  const [anos, setAnos] = useState<OpcaoFipe[]>([]);
  const [sel, setSel] = useState({ marca: "", modelo: "", ano: "" });
  const [filtroModelo, setFiltroModelo] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<string | null>(null);

  const buscar = async (q: string) => {
    setCarregando(true);
    setErro(null);
    try {
      const r = await fetch(`/api/fipe?${q}`);
      const j = await r.json();
      if (!r.ok) throw new Error(j.erro);
      return j;
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao consultar a FIPE.");
      return null;
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    fetch("/api/fipe?etapa=marcas")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setMarcas)
      .catch(() => setErro("A tabela FIPE não respondeu agora. Preencha manualmente."));
  }, []);

  const modelosFiltrados = modelos.filter((m) => m.nome.toLowerCase().includes(filtroModelo.toLowerCase())).slice(0, 200);

  return (
    <div className="rounded-2xl border border-laranja/30 bg-laranja/5 p-4">
      <p className="flex items-center gap-2 text-sm font-medium">
        <Search size={15} className="text-laranja" /> Preencher pela Tabela FIPE
        {carregando && <Loader2 size={14} className="animate-spin text-nevoa" />}
      </p>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <select
          className={classeCampo}
          value={sel.marca}
          onChange={async (e) => {
            setSel({ marca: e.target.value, modelo: "", ano: "" });
            setModelos([]);
            setAnos([]);
            if (e.target.value) setModelos((await buscar(`etapa=modelos&marca=${e.target.value}`)) ?? []);
          }}
        >
          <option value="">Marca</option>
          {marcas.map((m) => (
            <option key={m.codigo} value={m.codigo}>
              {limparMarca(m.nome)}
            </option>
          ))}
        </select>
        <div className="space-y-2">
          <input className={classeCampo} placeholder="Filtrar modelo (ex.: HB20)" value={filtroModelo} onChange={(e) => setFiltroModelo(e.target.value)} disabled={!modelos.length} />
          <select
            className={classeCampo}
            value={sel.modelo}
            disabled={!modelos.length}
            onChange={async (e) => {
              setSel((s) => ({ ...s, modelo: e.target.value, ano: "" }));
              setAnos([]);
              if (e.target.value) setAnos((await buscar(`etapa=anos&marca=${sel.marca}&modelo=${e.target.value}`)) ?? []);
            }}
          >
            <option value="">Modelo e versão</option>
            {modelosFiltrados.map((m) => (
              <option key={m.codigo} value={m.codigo}>
                {m.nome}
              </option>
            ))}
          </select>
        </div>
        <select
          className={classeCampo}
          value={sel.ano}
          disabled={!anos.length}
          onChange={async (e) => {
            setSel((s) => ({ ...s, ano: e.target.value }));
            if (!e.target.value) return;
            const v = await buscar(`etapa=valor&marca=${sel.marca}&modelo=${sel.modelo}&ano=${e.target.value}`);
            if (!v) return;
            const [modelo, ...resto] = String(v.Modelo).split(" ");
            const precoFipe = Math.round(Number(String(v.Valor).replace(/[^\d,]/g, "").replace(",", ".")) * 100);
            const combustivel = /diesel/i.test(v.Combustivel) ? "Diesel" : /(álcool|alcool|etanol)/i.test(v.Combustivel) ? "Etanol" : "Flex";
            const cambio = /CVT/i.test(v.Modelo) ? "CVT" : /Aut/i.test(v.Modelo) ? "Automático" : /Mec/i.test(v.Modelo) ? "Manual" : null;
            aoEscolher({ cambio, marca: limparMarca(String(v.Marca)), modelo, versao: resto.join(" "), ano: String(v.AnoModelo === 32000 ? new Date().getFullYear() : v.AnoModelo), combustivel, precoFipe, codigoFipe: String(v.CodigoFipe) });
            setResultado(`${v.Marca} ${v.Modelo} ${v.AnoModelo === 32000 ? "0 km" : v.AnoModelo}: FIPE ${v.Valor}`);
          }}
        >
          <option value="">Ano</option>
          {anos.map((a) => (
            <option key={a.codigo} value={a.codigo}>
              {a.nome}
            </option>
          ))}
        </select>
      </div>
      {erro && <p className="mt-2 text-xs text-perigo">{erro}</p>}
      {resultado && (
        <p className="mt-2 flex items-center gap-1.5 text-xs text-sucesso">
          <Check size={13} /> {resultado}. Confira e ajuste os campos abaixo.
        </p>
      )}
    </div>
  );
}

type FotoLocal = { id: string; arquivo: File; url: string };
type DocLocal = { id: string; arquivo: File; tipo: string };

export function FormVeiculo({
  acao,
  inicial = VALORES_VAZIOS,
  edicao,
  contas = [],
}: {
  acao: (estado: Resultado<number> | null, form: FormData) => Promise<Resultado<number>>;
  inicial?: ValoresVeiculo;
  edicao?: boolean;
  contas?: { id: number; nome: string }[];
}) {
  const passos = edicao ? PASSOS_EDICAO : PASSOS_NOVO;
  const [passo, setPasso] = useState(0);
  const [v, setV] = useState<ValoresVeiculo>(() => ({ ...inicial, dataEntrada: inicial.dataEntrada || hojeISO() }));
  const [fotosLocais, setFotos] = useState<FotoLocal[]>([]);
  const [docs, setDocs] = useState<DocLocal[]>([]);
  const [publicar, setPublicar] = useState(true);
  const [compra, setCompra] = useState({ lancar: true, paga: true, conta: contas[0]?.id ? String(contas[0].id) : "" });
  const [novoOpcional, setNovoOpcional] = useState("");
  const [erroLocal, setErroLocal] = useState<string | null>(null);
  const [rascunhoRestaurado, setRascunhoRestaurado] = useState(false);
  const [estado, despachar, enviando] = useActionState(acao, null);
  const inputFotos = useRef<HTMLInputElement>(null);

  // Rascunho (só no cadastro novo; fotos e arquivos não entram)
  useEffect(() => {
    if (edicao) return;
    try {
      const salvo = localStorage.getItem(CHAVE_RASCUNHO);
      if (salvo) {
        // Restaurar o rascunho só é possível depois de montar (localStorage não existe no servidor)
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setV((atual) => ({ ...atual, ...JSON.parse(salvo) }));
        setRascunhoRestaurado(true);
      }
    } catch {}
  }, [edicao]);
  useEffect(() => {
    if (edicao) return;
    try {
      if (v.marca || v.modelo || v.preco) localStorage.setItem(CHAVE_RASCUNHO, JSON.stringify(v));
    } catch {}
  }, [v, edicao]);

  const set = <K extends keyof ValoresVeiculo>(k: K, valor: ValoresVeiculo[K]) => setV((a) => ({ ...a, [k]: valor }));
  const alternar = (k: "opcionais" | "destaques", o: string) => set(k, v[k].includes(o) ? v[k].filter((x) => x !== o) : [...v[k], o]);

  const calc = useMemo(() => {
    const desconto = Number(v.descontoMaximoPct.replace(",", ".")) || 0;
    const minimo = Math.round(v.preco * (1 - desconto / 100));
    return {
      minimo,
      lucro: v.preco - v.custo,
      lucroMinimo: minimo - v.custo,
      margem: v.preco ? ((v.preco - v.custo) / v.preco) * 100 : 0,
      vsFipe: v.precoFipe ? ((v.preco - v.precoFipe) / v.precoFipe) * 100 : null,
    };
  }, [v.preco, v.custo, v.descontoMaximoPct, v.precoFipe]);

  const validarPasso = (p: number) => {
    if (p === 0) {
      if (!v.marca.trim() || !v.modelo.trim()) return "Informe marca e modelo.";
      const ano = Number(v.anoModelo);
      if (!ano || ano < 1950 || ano > new Date().getFullYear() + 2) return "Informe um ano de modelo válido.";
      const fab = Number(v.anoFabricacao);
      if (fab && (fab > ano || fab < ano - 1)) return "O ano de fabricação deve ser o mesmo do modelo ou um ano antes (ex.: 2022/2023).";
    }
    if (p === 2) {
      if (!v.preco) return "Informe o preço anunciado.";
      if (v.origem !== "consignacao" && !v.custo) return "Informe quanto o carro custou (ou marque consignação).";
    }
    return null;
  };

  const avancar = () => {
    const e = validarPasso(passo);
    setErroLocal(e);
    if (!e) setPasso((p) => Math.min(passos.length - 1, p + 1));
  };

  const adicionarFotos = (lista: FileList | null) => {
    if (!lista) return;
    const novas = [...lista].filter((f) => f.type.startsWith("image/")).map((f) => ({ id: crypto.randomUUID(), arquivo: f, url: URL.createObjectURL(f) }));
    setFotos((a) => [...a, ...novas]);
  };
  const mover = (i: number, d: -1 | 1) =>
    setFotos((a) => {
      const b = [...a];
      const j = i + d;
      if (j < 0 || j >= b.length) return a;
      [b[i], b[j]] = [b[j], b[i]];
      return b;
    });

  const enviar = () => {
    for (let p = 0; p < passos.length; p++) {
      const e = validarPasso(p);
      if (e) {
        setPasso(p);
        setErroLocal(e);
        return;
      }
    }
    const tamanhoTotal = fotosLocais.reduce((s, f) => s + f.arquivo.size, 0) + docs.reduce((s, d) => s + d.arquivo.size, 0);
    if (tamanhoTotal > 24 * 1024 * 1024) {
      setErroLocal("As fotos e documentos passam de 24 MB juntos. Envie menos agora e complete depois na central do veículo.");
      return;
    }
    const fd = new FormData();
    for (const [k, valor] of Object.entries(v)) {
      if (Array.isArray(valor)) valor.forEach((x) => fd.append(k, x));
      else if (k === "custo" || k === "preco" || k === "precoFipe") fd.append(k, valor || k === "custo" ? (Number(valor) / 100).toFixed(2).replace(".", ",") : "");
      else fd.append(k, String(valor));
    }
    if (!edicao) {
      fotosLocais.forEach((f) => fd.append("fotos", f.arquivo));
      docs.forEach((d, i) => {
        fd.append("documentos", d.arquivo);
        fd.append(`tipoDocumento_${i}`, d.tipo);
      });
      if (publicar) fd.append("publicado", "on");
      if (compra.lancar) fd.append("lancarCompra", "on");
      if (compra.paga) fd.append("compraPaga", "on");
      fd.append("contaCompra", compra.conta);
      fd.append("vencimentoCompra", v.dataEntrada);
      try {
        localStorage.removeItem(CHAVE_RASCUNHO);
      } catch {}
    }
    setErroLocal(null);
    startTransition(() => despachar(fd));
  };

  const campoTexto = (k: keyof ValoresVeiculo, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <input className={classeCampo} value={String(v[k] ?? "")} onChange={(e) => set(k, e.target.value as never)} {...props} />
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[220px_1fr]">
      {/* Passos */}
      <ol className="flex gap-2 overflow-x-auto xl:flex-col xl:gap-1">
        {passos.map((p, i) => (
          <li key={p}>
            <button
              type="button"
              onClick={() => (i <= passo || edicao ? setPasso(i) : avancar())}
              className={cn(
                "flex w-full items-center gap-3 whitespace-nowrap rounded-xl px-3 py-2.5 text-left text-sm transition",
                i === passo ? "bg-laranja font-semibold text-asfalto" : i < passo ? "text-giz hover:bg-chumbo" : "text-nevoa hover:bg-chumbo",
              )}
            >
              <span className={cn("grid size-6 place-items-center rounded-full border text-xs", i === passo ? "border-asfalto/40" : i < passo ? "border-laranja bg-laranja/15 text-laranja" : "border-linha")}>
                {i < passo ? <Check size={13} /> : i + 1}
              </span>
              {p}
            </button>
          </li>
        ))}
      </ol>

      <div className="min-w-0 rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5 md:p-6">
        {rascunhoRestaurado && passo === 0 && (
          <p className="mb-4 flex flex-wrap items-center gap-2 rounded-xl bg-chumbo/70 px-3 py-2 text-xs text-nevoa">
            Continuamos do rascunho que você deixou.
            <button
              type="button"
              className="text-laranja hover:underline"
              onClick={() => {
                setV({ ...VALORES_VAZIOS, dataEntrada: hojeISO() });
                setRascunhoRestaurado(false);
                try {
                  localStorage.removeItem(CHAVE_RASCUNHO);
                } catch {}
              }}
            >
              Começar do zero
            </button>
          </p>
        )}

        {passo === 0 && (
          <div className="space-y-5">
            <BuscaFipe
              aoEscolher={(d) =>
                setV((a) => {
                  const fab = Number(a.anoFabricacao);
                  const anoFabricacao = fab && fab <= Number(d.ano) && fab >= Number(d.ano) - 1 ? a.anoFabricacao : d.ano;
                  return { ...a, marca: d.marca, modelo: d.modelo, versao: d.versao, anoModelo: d.ano, anoFabricacao, combustivel: d.combustivel, cambio: d.cambio ?? a.cambio, precoFipe: d.precoFipe, codigoFipe: d.codigoFipe };
                })
              }
            />
            <div className="grid gap-4 md:grid-cols-3">
              <Campo rotulo="Marca" obrigatorio>
                {campoTexto("marca", { placeholder: "Hyundai" })}
              </Campo>
              <Campo rotulo="Modelo" obrigatorio>
                {campoTexto("modelo", { placeholder: "HB20" })}
              </Campo>
              <Campo rotulo="Versão">{campoTexto("versao", { placeholder: "Comfort 1.0" })}</Campo>
              <Campo rotulo="Ano do modelo" obrigatorio>
                {campoTexto("anoModelo", { inputMode: "numeric", placeholder: "2022", maxLength: 4 })}
              </Campo>
              <Campo rotulo="Ano de fabricação">{campoTexto("anoFabricacao", { inputMode: "numeric", placeholder: "2021", maxLength: 4 })}</Campo>
              <Campo rotulo="Quilometragem">{campoTexto("km", { inputMode: "numeric", placeholder: "52000" })}</Campo>
              <Campo rotulo="Cor">
                <input className={classeCampo} list="cores" value={v.cor} onChange={(e) => set("cor", e.target.value)} placeholder="Prata" />
                <datalist id="cores">
                  {CORES.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
              </Campo>
            </div>
            <details className="rounded-2xl border border-linha/70 p-4" open={Boolean(v.placa || v.chassi || v.renavam)}>
              <summary className="cursor-pointer text-sm font-medium">
                Dados para contrato <span className="font-normal text-nevoa">(opcionais: o contrato pede o que faltar)</span>
              </summary>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <Campo rotulo="Placa">{campoTexto("placa", { placeholder: "ABC1D23", maxLength: 8 })}</Campo>
                <Campo rotulo="Chassi">{campoTexto("chassi", { placeholder: "9BW…", maxLength: 17 })}</Campo>
                <Campo rotulo="RENAVAM">{campoTexto("renavam", { inputMode: "numeric", maxLength: 11 })}</Campo>
              </div>
            </details>
          </div>
        )}

        {passo === 1 && (
          <div className="space-y-6">
            <Campo rotulo="Categoria">
              <Chips simples opcoes={CATEGORIAS} marcados={[v.categoria]} alternar={(o) => set("categoria", o)} />
            </Campo>
            <div className="grid gap-4 md:grid-cols-3">
              <Campo rotulo="Câmbio">
                <select className={classeCampo} value={v.cambio} onChange={(e) => set("cambio", e.target.value)}>
                  {CAMBIOS.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </Campo>
              <Campo rotulo="Combustível">
                <select className={classeCampo} value={v.combustivel} onChange={(e) => set("combustivel", e.target.value)}>
                  {COMBUSTIVEIS.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </Campo>
              <Campo rotulo="Portas">
                <select className={classeCampo} value={v.portas} onChange={(e) => set("portas", e.target.value)}>
                  {["2", "3", "4", "5"].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </Campo>
            </div>
            <Campo rotulo="Equipamentos" dica="Marque o que o carro tem; aparece na página do carro na vitrine">
              <Chips opcoes={[...new Set([...OPCIONAIS, ...v.opcionais])]} marcados={v.opcionais} alternar={(o) => alternar("opcionais", o)} />
              <div className="mt-3 flex max-w-sm gap-2">
                <input className={classeCampo} placeholder="Outro equipamento" value={novoOpcional} onChange={(e) => setNovoOpcional(e.target.value)} onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    if (novoOpcional.trim()) alternar("opcionais", novoOpcional.trim());
                    setNovoOpcional("");
                  }
                }} />
                <button
                  type="button"
                  className={classeBotao("secundario")}
                  onClick={() => {
                    if (novoOpcional.trim()) alternar("opcionais", novoOpcional.trim());
                    setNovoOpcional("");
                  }}
                >
                  <Plus size={15} /> Incluir
                </button>
              </div>
            </Campo>
            <Campo rotulo="Destaques na vitrine" dica="Aparecem como etiquetas no card do site">
              <Chips opcoes={DESTAQUES} marcados={v.destaques} alternar={(o) => alternar("destaques", o)} />
            </Campo>
            <Campo rotulo="Descrição do anúncio">
              <textarea className={cn(classeCampo, "h-28 py-2")} value={v.descricao} onChange={(e) => set("descricao", e.target.value)} placeholder="Revisões em dia, pneus novos, único dono…" />
            </Campo>
          </div>
        )}

        {passo === 2 && (
          <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
            <div className="space-y-5">
              <Campo rotulo="Como o carro entrou">
                <Chips simples opcoes={Object.values(ORIGEM_VEICULO)} marcados={[ORIGEM_VEICULO[v.origem as keyof typeof ORIGEM_VEICULO]]} alternar={(o) => set("origem", Object.entries(ORIGEM_VEICULO).find(([, n]) => n === o)![0])} />
              </Campo>
              <div className="grid gap-4 md:grid-cols-2">
                <Campo rotulo={v.origem === "consignacao" ? "Dono do carro / fornecedor" : "Fornecedor"}>{campoTexto("fornecedor", { placeholder: "Particular, revenda, leilão…" })}</Campo>
                <Campo rotulo="Data de entrada">
                  <input type="date" className={cn(classeCampo, "num")} value={v.dataEntrada} onChange={(e) => set("dataEntrada", e.target.value)} />
                </Campo>
                <Campo rotulo={v.origem === "consignacao" ? "Valor a repassar ao dono" : "Custo (quanto pagou)"} obrigatorio={v.origem !== "consignacao"}>
                  <CampoDinheiro name="_custo" defaultValue={v.custo} onValor={(c) => set("custo", c)} />
                </Campo>
                <Campo rotulo="Preço anunciado" obrigatorio>
                  <CampoDinheiro name="_preco" defaultValue={v.preco} onValor={(c) => set("preco", c)} />
                </Campo>
                <Campo rotulo="Desconto máximo na negociação (%)">
                  <input inputMode="decimal" className={cn(classeCampo, "num")} value={v.descontoMaximoPct} onChange={(e) => set("descontoMaximoPct", e.target.value)} />
                </Campo>
                <Campo rotulo="Preço FIPE de referência">
                  <CampoDinheiro key={v.codigoFipe} name="_fipe" defaultValue={v.precoFipe} onValor={(c) => set("precoFipe", c)} />
                </Campo>
              </div>
              {!edicao && (v.origem === "compra" || v.origem === "leilao") && (
                <div className="rounded-2xl border border-linha/70 p-4 text-sm">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="accent-[#ff7a1a]" checked={compra.lancar} onChange={(e) => setCompra((c) => ({ ...c, lancar: e.target.checked }))} />
                    Lançar a compra no fluxo de caixa
                  </label>
                  {compra.lancar && (
                    <div className="mt-3 flex flex-wrap items-center gap-4 pl-6">
                      <label className="flex items-center gap-2 text-nevoa">
                        <input type="checkbox" className="accent-[#ff7a1a]" checked={compra.paga} onChange={(e) => setCompra((c) => ({ ...c, paga: e.target.checked }))} />
                        Já foi pago
                      </label>
                      {contas.length > 0 && (
                        <select className={cn(classeCampo, "h-9 w-auto")} value={compra.conta} onChange={(e) => setCompra((c) => ({ ...c, conta: e.target.value }))}>
                          {contas.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.nome}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="h-fit rounded-2xl bg-chumbo/60 p-4 text-sm">
              <p className="text-xs uppercase tracking-[0.12em] text-nevoa">Resultado previsto</p>
              <dl className="mt-3 space-y-2.5">
                <div className="flex justify-between"><dt className="text-nevoa">Lucro no anunciado</dt><dd className={cn("num font-semibold", calc.lucro >= 0 ? "text-sucesso" : "text-perigo")}>{reais(calc.lucro)}</dd></div>
                <div className="flex justify-between"><dt className="text-nevoa">Margem</dt><dd className="num">{calc.margem.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</dd></div>
                <div className="flex justify-between"><dt className="text-nevoa">Preço mínimo</dt><dd className="num text-laranja">{reais(calc.minimo)}</dd></div>
                <div className="flex justify-between"><dt className="text-nevoa">Lucro no mínimo</dt><dd className={cn("num", calc.lucroMinimo >= 0 ? "text-sucesso" : "text-perigo")}>{reais(calc.lucroMinimo)}</dd></div>
                {calc.vsFipe !== null && (
                  <div className="flex justify-between"><dt className="text-nevoa">Em relação à FIPE</dt><dd className="num">{calc.vsFipe >= 0 ? "+" : ""}{calc.vsFipe.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</dd></div>
                )}
              </dl>
              {calc.lucroMinimo < 0 && v.preco > 0 && <p className="mt-3 text-xs text-perigo">Com o desconto máximo, a venda fica abaixo do custo.</p>}
              <p className="mt-3 text-[11px] text-nevoa-2">Gastos de preparação lançados depois entram no cálculo da central do veículo.</p>
            </div>
          </div>
        )}

        {passo === 3 && !edicao && (
          <div className="space-y-6">
            <div>
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-sm font-medium">
                  Fotos <span className="font-normal text-nevoa">({fotosLocais.length}) · a primeira é a capa</span>
                </p>
                <button type="button" className={classeBotao("secundario", "sm")} onClick={() => inputFotos.current?.click()}>
                  <ImagePlus size={14} /> Adicionar fotos
                </button>
              </div>
              <input ref={inputFotos} type="file" accept="image/*" multiple hidden onChange={(e) => { adicionarFotos(e.target.files); e.target.value = ""; }} />
              {fotosLocais.length === 0 ? (
                <button
                  type="button"
                  onClick={() => inputFotos.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); adicionarFotos(e.dataTransfer.files); }}
                  className="grid w-full place-items-center rounded-2xl border border-dashed border-linha py-12 text-sm text-nevoa hover:border-laranja/50"
                >
                  <ImagePlus size={26} className="mb-2" />
                  Arraste as fotos aqui ou clique para escolher
                  <span className="mt-1 text-xs text-nevoa-2">Sem foto o carro fica como rascunho e não vai para a vitrine</span>
                </button>
              ) : (
                <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {fotosLocais.map((f, i) => (
                    <li key={f.id} className={cn("group relative aspect-[4/3] overflow-hidden rounded-xl", i === 0 && "ring-2 ring-laranja")}>
                      <Image src={f.url} alt="" fill unoptimized className="object-cover" />
                      {i === 0 && <span className="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-laranja px-2 py-0.5 text-[10px] font-semibold text-asfalto"><Star size={10} /> Capa</span>}
                      <div className="absolute inset-x-0 bottom-0 flex justify-between bg-gradient-to-t from-black/80 to-transparent p-2">
                        <span className="flex gap-1">
                          <button type="button" onClick={() => mover(i, -1)} disabled={i === 0} className="rounded-md bg-black/60 p-1 disabled:opacity-30" aria-label="Mover para a esquerda"><ChevronLeft size={14} /></button>
                          <button type="button" onClick={() => mover(i, 1)} disabled={i === fotosLocais.length - 1} className="rounded-md bg-black/60 p-1 disabled:opacity-30" aria-label="Mover para a direita"><ChevronRight size={14} /></button>
                        </span>
                        <button type="button" onClick={() => setFotos((a) => a.filter((x) => x.id !== f.id))} className="rounded-md bg-black/60 p-1 text-perigo" aria-label="Remover foto"><Trash2 size={14} /></button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <p className="mb-3 text-sm font-medium">
                Documentos <span className="font-normal text-nevoa">(opcional: dá para enviar depois na central do veículo)</span>
              </p>
              <ul className="space-y-2">
                {docs.map((d) => (
                  <li key={d.id} className="flex flex-wrap items-center gap-3 rounded-xl border border-linha/70 p-2.5 text-sm">
                    <FileText size={16} className="text-nevoa" />
                    <span className="min-w-0 flex-1 truncate">{d.arquivo.name}</span>
                    <select className={cn(classeCampo, "h-9 w-56")} value={d.tipo} onChange={(e) => setDocs((a) => a.map((x) => (x.id === d.id ? { ...x, tipo: e.target.value } : x)))}>
                      {[...TIPOS_DOCUMENTO, "Outro"].map((t) => (
                        <option key={t}>{t}</option>
                      ))}
                    </select>
                    <button type="button" onClick={() => setDocs((a) => a.filter((x) => x.id !== d.id))} className="text-nevoa hover:text-perigo" aria-label="Remover documento"><X size={16} /></button>
                  </li>
                ))}
              </ul>
              <label className={cn(classeBotao("secundario", "sm"), "mt-3 cursor-pointer")}>
                <Plus size={14} /> Anexar documento
                <input
                  type="file"
                  accept="application/pdf,image/*"
                  multiple
                  hidden
                  onChange={(e) => {
                    const lista = [...(e.target.files ?? [])].map((f, i) => ({ id: crypto.randomUUID(), arquivo: f, tipo: TIPOS_DOCUMENTO[(docs.length + i) % TIPOS_DOCUMENTO.length] }));
                    setDocs((a) => [...a, ...lista]);
                    e.target.value = "";
                  }}
                />
              </label>
            </div>
          </div>
        )}

        {passo === 4 && !edicao && (
          <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-chumbo">
              {fotosLocais[0] ? <Image src={fotosLocais[0].url} alt="" fill unoptimized className="object-cover" /> : <p className="grid h-full place-items-center text-sm text-nevoa">Sem foto</p>}
            </div>
            <div>
              <h3 className="display text-2xl font-bold">
                {v.marca} {v.modelo} <span className="text-nevoa">{v.versao}</span>
              </h3>
              <p className="text-nevoa">
                {[v.anoModelo, v.cor, v.km && `${Number(v.km).toLocaleString("pt-BR")} km`, v.categoria, v.cambio].filter(Boolean).join(" · ")}
              </p>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Anunciado</dt><dd className="num font-semibold">{reais(v.preco)}</dd></div>
                <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">{v.origem === "consignacao" ? "Repasse" : "Custo"}</dt><dd className="num font-semibold">{reais(v.custo)}</dd></div>
                <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Lucro previsto</dt><dd className="num font-semibold text-sucesso">{reais(calc.lucro)}</dd></div>
                <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Fotos · docs</dt><dd className="num font-semibold">{fotosLocais.length} · {docs.length}</dd></div>
              </dl>
              <label className="mt-5 flex items-center gap-2 text-sm">
                <input type="checkbox" className="accent-[#ff7a1a]" checked={publicar} onChange={(e) => setPublicar(e.target.checked)} disabled={!fotosLocais.length} />
                Publicar na vitrine agora
                {!fotosLocais.length && <span className="text-xs text-nevoa">(precisa de ao menos uma foto)</span>}
              </label>
              {!fotosLocais.length && <p className="mt-2 text-xs text-alerta">Sem fotos o carro será salvo como rascunho.</p>}
            </div>
          </div>
        )}

        {(erroLocal || estado) && (
          <div className="mt-5">
            {erroLocal ? <p className="rounded-xl border border-perigo/30 bg-perigo/10 px-3 py-2 text-sm text-perigo">{erroLocal}</p> : <Retorno estado={estado} />}
          </div>
        )}

        <div className="mt-6 flex items-center justify-between gap-3 border-t border-linha/60 pt-5">
          <button type="button" onClick={() => setPasso((p) => Math.max(0, p - 1))} disabled={passo === 0} className={classeBotao("fantasma")}>
            <ArrowLeft size={16} /> Voltar
          </button>
          {passo < passos.length - 1 ? (
            <div className="flex gap-2">
              {edicao && (
                <button type="button" onClick={enviar} disabled={enviando} className={classeBotao("secundario")}>
                  {enviando ? "Salvando…" : "Salvar alterações"}
                </button>
              )}
              <button type="button" onClick={avancar} className={classeBotao("primario")}>
                Continuar <ArrowRight size={16} />
              </button>
            </div>
          ) : (
            <button type="button" onClick={enviar} disabled={enviando} className={classeBotao("primario")}>
              {enviando ? <><Loader2 size={16} className="animate-spin" /> Salvando…</> : edicao ? "Salvar alterações" : "Cadastrar veículo"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
