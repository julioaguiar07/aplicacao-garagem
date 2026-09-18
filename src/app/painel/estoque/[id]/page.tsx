import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import {
  Check,
  CircleAlert,
  Clock,
  Eye,
  FileText,
  Handshake,
  ImagePlus,
  Pencil,
  Plus,
  Receipt,
  Sparkles,
  Upload,
} from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { FotoCarro } from "@/components/foto-carro";
import { SeloMarca, StatusVeiculoSelo } from "@/components/status-veiculo";
import { VEICULOS, lucroPrevisto, nomeCompleto, pendencias, precoMinimo, totalGastos, veiculoPorId } from "@/lib/demo/veiculos";
import type { StatusDocumento, Veiculo } from "@/lib/tipos";
import { data, diasDesde, km, pct, reais } from "@/lib/formato";
import { cn } from "@/lib/cn";

const ABAS = [
  { id: "geral", rotulo: "Visão geral" },
  { id: "documentos", rotulo: "Documentos" },
  { id: "gastos", rotulo: "Gastos" },
  { id: "rentabilidade", rotulo: "Rentabilidade" },
  { id: "fotos", rotulo: "Fotos" },
  { id: "historico", rotulo: "Histórico" },
] as const;
type Aba = (typeof ABAS)[number]["id"];

export function generateStaticParams() {
  return VEICULOS.map((v) => ({ id: String(v.id) }));
}

export async function generateMetadata({ params }: PageProps<"/painel/estoque/[id]">) {
  const v = veiculoPorId(Number((await params).id));
  return { title: v ? `${nomeCompleto(v)} ${v.anoModelo}` : "Veículo" };
}

function Cartao({ titulo, acao, className, children }: { titulo?: string; acao?: React.ReactNode; className?: string; children: React.ReactNode }) {
  return (
    <section className={cn("rounded-[var(--radius-card)] border border-linha/60 bg-grafite p-5", className)}>
      {titulo && (
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="display text-[17px] font-semibold">{titulo}</h2>
          {acao}
        </div>
      )}
      {children}
    </section>
  );
}

function BotaoSecundario({ icone: Icone, children }: { icone: typeof Plus; children: React.ReactNode }) {
  return (
    <button className="flex items-center gap-1.5 rounded-full border border-linha px-3 py-1.5 text-xs text-nevoa transition hover:border-laranja/50 hover:text-giz">
      <Icone size={14} />
      {children}
    </button>
  );
}

const COR_DOC: Record<StatusDocumento, string> = {
  ok: "bg-sucesso/15 text-sucesso",
  pendente: "bg-chumbo-2 text-nevoa",
  vencido: "bg-perigo/15 text-perigo",
};
const NOME_DOC: Record<StatusDocumento, string> = { ok: "Enviado", pendente: "Pendente", vencido: "Vencido" };

function Campo({ rotulo, valor, faltando }: { rotulo: string; valor?: React.ReactNode; faltando?: boolean }) {
  return (
    <div className="border-b border-linha/50 py-2.5 last:border-0">
      <dt className="text-xs text-nevoa">{rotulo}</dt>
      <dd className={cn("num mt-0.5 text-sm", faltando && "text-nevoa-2")}>
        {faltando ? (
          <span className="inline-flex items-center gap-1.5">
            Não informado
            <span className="rounded-full border border-dashed border-laranja/50 px-2 py-px text-[11px] text-laranja">completar</span>
          </span>
        ) : (
          valor
        )}
      </dd>
    </div>
  );
}

function AbaGeral({ v }: { v: Veiculo }) {
  const p = pendencias(v);
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <Cartao titulo="Ficha do veículo" acao={<BotaoSecundario icone={Pencil}>Editar dados</BotaoSecundario>}>
          <dl className="grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
            <Campo rotulo="Marca e modelo" valor={`${v.marca} ${v.modelo}`} />
            <Campo rotulo="Versão" valor={v.versao} faltando={!v.versao} />
            <Campo rotulo="Ano modelo / fabricação" valor={`${v.anoModelo} / ${v.anoFabricacao ?? v.anoModelo}`} />
            <Campo rotulo="Quilometragem" valor={km(v.km)} />
            <Campo rotulo="Cor" valor={v.cor} />
            <Campo rotulo="Categoria" valor={v.categoria} />
            <Campo rotulo="Câmbio" valor={v.cambio} />
            <Campo rotulo="Combustível" valor={v.combustivel} />
            <Campo rotulo="Portas" valor={v.portas} />
            <Campo rotulo="Placa" valor={v.placa} faltando={!v.placa} />
            <Campo rotulo="Chassi" valor={v.chassi} faltando={!v.chassi} />
            <Campo rotulo="RENAVAM" valor={v.renavam} faltando={!v.renavam} />
          </dl>
          <p className="mt-4 rounded-xl bg-chumbo/60 px-3 py-2 text-xs text-nevoa">
            Placa, chassi e RENAVAM são opcionais. Se faltarem quando você gerar o contrato, o sistema pede só esses campos e salva aqui.
          </p>
        </Cartao>

        <Cartao titulo="Opcionais">
          {v.opcionais.length ? (
            <ul className="flex flex-wrap gap-2">
              {v.opcionais.map((o) => (
                <li key={o} className="flex items-center gap-1.5 rounded-full border border-linha bg-chumbo/50 px-3 py-1.5 text-sm">
                  <Check size={14} className="text-laranja" />
                  {o}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-nevoa">Nenhum opcional marcado.</p>
          )}
        </Cartao>

        {v.descricao && (
          <Cartao titulo="Descrição do anúncio">
            <p className="max-w-prose text-sm leading-relaxed text-giz/85">{v.descricao}</p>
          </Cartao>
        )}
      </div>

      <div className="space-y-5">
        <Cartao titulo="Pendências">
          {p.total === 0 ? (
            <p className="flex items-center gap-2 text-sm text-sucesso">
              <Check size={16} /> Tudo em dia com este carro.
            </p>
          ) : (
            <ul className="space-y-2.5 text-sm">
              {v.documentos
                .filter((d) => d.status !== "ok")
                .map((d) => (
                  <li key={d.tipo} className="flex items-center gap-3">
                    <CircleAlert size={16} className={d.status === "vencido" ? "text-perigo" : "text-laranja"} />
                    <span className="flex-1">{d.tipo}</span>
                    <span className={cn("rounded-full px-2 py-0.5 text-[11px]", COR_DOC[d.status])}>{NOME_DOC[d.status]}</span>
                  </li>
                ))}
              {p.dados > 0 && (
                <li className="flex items-center gap-3">
                  <CircleAlert size={16} className="text-nevoa" />
                  <span className="flex-1">Dados para contrato ({p.dados} campos)</span>
                  <span className="rounded-full bg-chumbo-2 px-2 py-0.5 text-[11px] text-nevoa">Opcional</span>
                </li>
              )}
            </ul>
          )}
        </Cartao>

        <Cartao titulo="Entrada no estoque">
          <dl>
            <Campo rotulo="Origem" valor={{ compra: "Compra", troca: "Troca em venda", consignacao: "Consignação", leilao: "Leilão" }[v.origem]} />
            <Campo rotulo="Fornecedor" valor={v.fornecedor} faltando={!v.fornecedor} />
            <Campo rotulo="Data de entrada" valor={data(v.cadastradoEm)} />
          </dl>
        </Cartao>
      </div>
    </div>
  );
}

function AbaDocumentos({ v }: { v: Veiculo }) {
  return (
    <Cartao titulo="Documentos do veículo" acao={<BotaoSecundario icone={Plus}>Adicionar outro tipo</BotaoSecundario>}>
      <ul className="divide-y divide-linha/50">
        {v.documentos.map((d) => (
          <li key={d.tipo} className="flex flex-wrap items-center gap-4 py-3.5">
            <span className={cn("grid size-10 place-items-center rounded-xl", d.status === "ok" ? "bg-sucesso/10 text-sucesso" : d.status === "vencido" ? "bg-perigo/10 text-perigo" : "bg-chumbo text-nevoa")}>
              <FileText size={18} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-medium">{d.tipo}</p>
              <p className="text-xs text-nevoa">
                {d.status === "ok" && d.enviadoEm && `Enviado em ${data(d.enviadoEm + "T12:00:00-03:00")}`}
                {d.status === "vencido" && d.validade && `Venceu em ${data(d.validade + "T12:00:00-03:00")}. Envie a versão atualizada.`}
                {d.status === "pendente" && "Ainda não enviado"}
              </p>
            </div>
            <span className={cn("rounded-full px-2.5 py-1 text-xs", COR_DOC[d.status])}>{NOME_DOC[d.status]}</span>
            {d.status === "ok" ? (
              <BotaoSecundario icone={Eye}>Ver arquivo</BotaoSecundario>
            ) : (
              <button className="flex items-center gap-1.5 rounded-full bg-laranja px-3 py-1.5 text-xs font-semibold text-asfalto hover:bg-ambar">
                <Upload size={14} /> Enviar
              </button>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-nevoa">PDF, JPG ou PNG. Os arquivos ficam no armazenamento do Railway, nunca no banco de dados.</p>
    </Cartao>
  );
}

function AbaGastos({ v }: { v: Veiculo }) {
  const total = totalGastos(v);
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_340px]">
      <Cartao titulo="Gastos com este carro" className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5">
        {v.gastos.length === 0 ? (
          <p className="px-5 pb-6 text-sm text-nevoa">Nenhum gasto lançado. Use o formulário ao lado para registrar o primeiro.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-y border-linha/60 text-left text-xs text-nevoa">
                  <th className="px-5 py-2.5 font-medium">Data</th>
                  <th className="px-3 py-2.5 font-medium">Descrição</th>
                  <th className="px-3 py-2.5 font-medium">Categoria</th>
                  <th className="px-3 py-2.5 font-medium">Nota</th>
                  <th className="px-5 py-2.5 text-right font-medium">Valor</th>
                </tr>
              </thead>
              <tbody>
                {v.gastos.map((g) => (
                  <tr key={g.id} className="border-b border-linha/40">
                    <td className="num px-5 py-3 text-nevoa">{data(g.data + "T12:00:00-03:00")}</td>
                    <td className="px-3 py-3">{g.descricao}</td>
                    <td className="px-3 py-3 text-nevoa">{g.categoria}</td>
                    <td className="px-3 py-3">{g.comNota ? <Receipt size={16} className="text-sucesso" aria-label="Com nota" /> : <span className="text-nevoa-2">—</span>}</td>
                    <td className="num px-5 py-3 text-right">{reais(g.valor)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={4} className="px-5 py-3 text-right text-nevoa">Total</td>
                  <td className="num px-5 py-3 text-right font-semibold">{reais(total)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </Cartao>

      <Cartao titulo="Lançar gasto">
        <form className="space-y-3">
          <label className="block">
            <span className="text-xs text-nevoa">Descrição</span>
            <input className="mt-1 h-10 w-full rounded-xl border border-linha bg-asfalto px-3 text-sm focus:border-laranja/60 focus:outline-none" placeholder="Ex.: polimento completo" />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs text-nevoa">Valor</span>
              <input inputMode="decimal" className="num mt-1 h-10 w-full rounded-xl border border-linha bg-asfalto px-3 text-sm focus:border-laranja/60 focus:outline-none" placeholder="R$ 0,00" />
            </label>
            <label className="block">
              <span className="text-xs text-nevoa">Data</span>
              <input type="date" defaultValue="2026-09-18" className="num mt-1 h-10 w-full rounded-xl border border-linha bg-asfalto px-3 text-sm focus:border-laranja/60 focus:outline-none" />
            </label>
          </div>
          <label className="block">
            <span className="text-xs text-nevoa">Categoria</span>
            <select className="mt-1 h-10 w-full rounded-xl border border-linha bg-asfalto px-3 text-sm focus:border-laranja/60 focus:outline-none">
              {["Preparação", "Mecânica", "Funilaria e pintura", "Estética", "Pneus", "Documentação", "Outros"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <button type="button" className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-linha py-3 text-xs text-nevoa hover:border-laranja/50">
            <Upload size={14} /> Anexar nota fiscal (opcional)
          </button>
          <button type="button" className="h-10 w-full rounded-xl bg-laranja text-sm font-semibold text-asfalto hover:bg-ambar">
            Lançar gasto
          </button>
          <p className="text-xs text-nevoa">O gasto também entra no fluxo de caixa como saída.</p>
        </form>
      </Cartao>
    </div>
  );
}

function AbaRentabilidade({ v }: { v: Veiculo }) {
  const gastos = totalGastos(v);
  const custoVendaPrevisto = 780; // despachante/transferência, média da loja (demonstração)
  const custoTotal = v.custo + gastos + custoVendaPrevisto;
  const minimo = precoMinimo(v);
  const linhas = [
    { rotulo: "Custo de aquisição", valor: v.custo },
    { rotulo: "Gastos de preparação", valor: gastos },
    { rotulo: "Custos de venda previstos", valor: custoVendaPrevisto },
  ];
  const escala = Math.max(v.preco, v.precoFipe ?? 0) * 1.04;

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Cartao titulo="Quanto este carro custou">
        <ul className="space-y-3">
          {linhas.map((l) => (
            <li key={l.rotulo} className="flex items-center justify-between text-sm">
              <span className="text-nevoa">{l.rotulo}</span>
              <span className="num">{reais(l.valor)}</span>
            </li>
          ))}
          <li className="flex items-center justify-between border-t border-linha pt-3 text-sm font-semibold">
            <span>Custo total</span>
            <span className="num">{reais(custoTotal)}</span>
          </li>
        </ul>
      </Cartao>

      <Cartao titulo="Faixa de negociação">
        <div className="relative mt-2 h-3 rounded-full bg-chumbo">
          <div className="absolute inset-y-0 left-0 rounded-full bg-perigo/60" style={{ width: `${(custoTotal / escala) * 100}%` }} />
          <div
            className="absolute inset-y-0 rounded-full bg-gradient-to-r from-brasa to-laranja"
            style={{ left: `${(minimo / escala) * 100}%`, width: `${((v.preco - minimo) / escala) * 100}%` }}
          />
          {v.precoFipe && (
            <span className="absolute -top-1.5 h-6 w-0.5 bg-giz" style={{ left: `${(v.precoFipe / escala) * 100}%` }} title="FIPE" />
          )}
        </div>
        <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-chumbo/60 p-3">
            <dt className="text-xs text-nevoa">Preço anunciado</dt>
            <dd className="num mt-1 font-semibold">{reais(v.preco)}</dd>
          </div>
          <div className="rounded-xl bg-chumbo/60 p-3">
            <dt className="text-xs text-nevoa">Mínimo aceitável (−{pct(v.descontoMaximoPct, 0)})</dt>
            <dd className="num mt-1 font-semibold text-laranja">{reais(minimo)}</dd>
          </div>
          <div className="rounded-xl bg-chumbo/60 p-3">
            <dt className="text-xs text-nevoa">Lucro no preço anunciado</dt>
            <dd className="num mt-1 font-semibold text-sucesso">{reais(v.preco - custoTotal)}</dd>
          </div>
          <div className="rounded-xl bg-chumbo/60 p-3">
            <dt className="text-xs text-nevoa">Lucro no preço mínimo</dt>
            <dd className={cn("num mt-1 font-semibold", minimo - custoTotal >= 0 ? "text-sucesso" : "text-perigo")}>{reais(minimo - custoTotal)}</dd>
          </div>
        </dl>
        {v.precoFipe && (
          <p className="mt-4 text-xs text-nevoa">
            FIPE de referência: <span className="num text-giz">{reais(v.precoFipe)}</span> · o anúncio está{" "}
            {pct(Math.abs(((v.preco - v.precoFipe) / v.precoFipe) * 100))} {v.preco >= v.precoFipe ? "acima" : "abaixo"} da tabela.
          </p>
        )}
      </Cartao>
    </div>
  );
}

function AbaFotos({ v }: { v: Veiculo }) {
  const f = v.fotos[0];
  return (
    <div className="space-y-5">
      <Cartao titulo="Foto de capa" acao={<BotaoSecundario icone={ImagePlus}>Adicionar fotos</BotaoSecundario>}>
        <div className="grid gap-4 md:grid-cols-2">
          <figure>
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-chumbo">
              <Image src={f.original} alt="Foto original" fill sizes="(min-width: 768px) 40vw, 90vw" className="object-contain" />
            </div>
            <figcaption className="mt-2 text-xs text-nevoa">Foto enviada (sem dados de GPS)</figcaption>
          </figure>
          <figure>
            <FotoCarro foto={f} alt="Como aparece nos cards" className="aspect-[4/3] rounded-2xl" />
            <figcaption className="mt-2 flex items-center gap-2 text-xs text-nevoa">
              Como aparece nos cards e na vitrine
              <button className="ml-auto rounded-full border border-linha px-2.5 py-1 hover:text-giz">Ajustar enquadramento</button>
            </figcaption>
          </figure>
        </div>
      </Cartao>
      <Cartao titulo="Galeria">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
          <div className="relative aspect-square overflow-hidden rounded-xl ring-2 ring-laranja">
            <Image src={f.card} alt="Capa" fill sizes="160px" className="object-cover" />
            <span className="absolute left-1.5 top-1.5 rounded-full bg-laranja px-2 py-0.5 text-[10px] font-semibold text-asfalto">Capa</span>
          </div>
          {Array.from({ length: 5 }).map((_, i) => (
            <button key={i} className="grid aspect-square place-items-center rounded-xl border border-dashed border-linha text-nevoa-2 hover:border-laranja/50 hover:text-nevoa">
              <ImagePlus size={20} />
            </button>
          ))}
        </div>
        <p className="mt-3 text-xs text-nevoa">
          Dica: fotografe o carro inteiro, de frente em 3/4, com o carro no centro da foto. A primeira foto vira a capa.
        </p>
      </Cartao>
    </div>
  );
}

function AbaHistorico({ v }: { v: Veiculo }) {
  return (
    <Cartao titulo="Tudo o que aconteceu com este carro">
      <ol className="relative space-y-5 border-l border-linha pl-6">
        {[...v.historico].reverse().map((e) => (
          <li key={e.data + e.titulo} className="relative">
            <span className="absolute -left-[31px] top-1 size-3 rounded-full border-2 border-grafite bg-laranja" />
            <p className="font-medium">{e.titulo}</p>
            {e.detalhe && <p className="text-sm text-nevoa">{e.detalhe}</p>}
            <p className="num mt-0.5 text-xs text-nevoa-2">
              {new Date(e.data).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Fortaleza" })}
            </p>
          </li>
        ))}
      </ol>
    </Cartao>
  );
}

export default async function CentralVeiculo({ params, searchParams }: PageProps<"/painel/estoque/[id]">) {
  const v = veiculoPorId(Number((await params).id));
  if (!v) notFound();
  const abaParam = (await searchParams).aba;
  const aba: Aba = ABAS.some((a) => a.id === abaParam) ? (abaParam as Aba) : "geral";

  const gastos = totalGastos(v);
  const dias = diasDesde(v.cadastradoEm);
  const p = pendencias(v);
  const indicadores = [
    { rotulo: "Custo + gastos", valor: reais(v.custo + gastos) },
    { rotulo: "Preço mínimo", valor: reais(precoMinimo(v)) },
    { rotulo: "Lucro previsto", valor: reais(lucroPrevisto(v)), destaque: true },
    { rotulo: "No pátio", valor: dias === 0 ? "Chegou hoje" : `${dias} ${dias === 1 ? "dia" : "dias"}`, alerta: dias >= 45 },
  ];

  return (
    <>
      <BarraSuperior
        titulo={`${nomeCompleto(v)} ${v.anoModelo}`}
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Estoque", href: "/painel/estoque" }, { rotulo: `${v.modelo} ${v.anoModelo}` }]}
      />

      {/* Cabeçalho da central */}
      <section className="grid overflow-hidden rounded-[var(--radius-card)] border border-linha/60 bg-grafite lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <FotoCarro foto={v.fotos[0]} alt={`${nomeCompleto(v)} ${v.anoModelo}`} prioridade className="aspect-[16/10] lg:aspect-auto lg:min-h-[340px]" sizes="(min-width: 1024px) 50vw, 100vw" />
        <div className="flex flex-col p-6">
          <div className="flex items-start gap-3">
            <SeloMarca marca={v.marca} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-nevoa">
                {v.categoria} · {v.cor} · {km(v.km)}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <StatusVeiculoSelo status={v.status} />
                {v.publicado && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-chumbo px-2.5 py-1 text-xs text-nevoa">
                    <Eye size={13} /> Na vitrine
                  </span>
                )}
                {v.destaques.map((d) => (
                  <span key={d} className="rounded-full border border-laranja/40 px-2.5 py-0.5 text-xs text-laranja">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <p className="mt-5 text-xs text-nevoa">Preço anunciado</p>
          <p className="display num text-4xl font-bold">{reais(v.preco)}</p>

          <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2 2xl:grid-cols-4">
            {indicadores.map((i) => (
              <div key={i.rotulo} className="rounded-2xl bg-chumbo/60 p-3">
                <dt className="text-[11px] text-nevoa">{i.rotulo}</dt>
                <dd className={cn("num mt-1 text-sm font-semibold", i.destaque && "text-sucesso", i.alerta && "text-laranja")}>{i.valor}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-auto flex flex-wrap gap-2 pt-6">
            <Link
              href="/painel/vendas"
              className="flex h-10 items-center gap-2 rounded-full bg-laranja px-4 text-sm font-semibold text-asfalto hover:bg-ambar"
            >
              <Handshake size={16} /> Iniciar venda
            </Link>
            <Link href={`/carros/${v.slug}`} target="_blank" className="flex h-10 items-center gap-2 rounded-full border border-linha px-4 text-sm text-nevoa hover:text-giz">
              <Eye size={16} /> Ver na vitrine
            </Link>
            <button className="flex h-10 items-center gap-2 rounded-full border border-linha px-4 text-sm text-nevoa hover:text-giz">
              <Sparkles size={16} /> Gerar story
            </button>
          </div>
        </div>
      </section>

      {/* Abas */}
      <nav className="sticky top-0 z-20 -mx-4 mt-6 mb-5 overflow-x-auto bg-asfalto/90 px-4 py-2 backdrop-blur md:-mx-8 md:px-8" aria-label="Seções do veículo">
        <ul className="flex gap-1.5">
          {ABAS.map((a) => {
            const on = a.id === aba;
            const contagem = a.id === "documentos" ? p.docs : a.id === "gastos" ? v.gastos.length : 0;
            return (
              <li key={a.id}>
                <Link
                  href={a.id === "geral" ? `/painel/estoque/${v.id}` : `/painel/estoque/${v.id}?aba=${a.id}`}
                  scroll={false}
                  aria-current={on ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-2 whitespace-nowrap rounded-full px-4 py-2 text-sm transition",
                    on ? "bg-giz font-semibold text-asfalto" : "text-nevoa hover:bg-chumbo hover:text-giz",
                  )}
                >
                  {a.rotulo}
                  {contagem > 0 && (
                    <span className={cn("num rounded-full px-1.5 text-[11px]", on ? "bg-asfalto/15" : "bg-chumbo-2", a.id === "documentos" && !on && "text-laranja")}>
                      {contagem}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {aba === "geral" && <AbaGeral v={v} />}
      {aba === "documentos" && <AbaDocumentos v={v} />}
      {aba === "gastos" && <AbaGastos v={v} />}
      {aba === "rentabilidade" && <AbaRentabilidade v={v} />}
      {aba === "fotos" && <AbaFotos v={v} />}
      {aba === "historico" && <AbaHistorico v={v} />}

      <p className="mt-6 flex items-center gap-2 text-xs text-nevoa-2">
        <Clock size={13} /> Cadastrado em {data(v.cadastradoEm)}
      </p>
    </>
  );
}
