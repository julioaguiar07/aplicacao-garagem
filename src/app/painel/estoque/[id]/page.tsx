import Link from "next/link";
import { notFound } from "next/navigation";
import { Check, CircleAlert, Clock, ExternalLink, Eye, FileText, Handshake, Pencil, Receipt, Trash2 } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { FotoCarro } from "@/components/foto-carro";
import { SeloMarca, StatusVeiculoSelo } from "@/components/status-veiculo";
import { ControlesVeiculo, FormDocumento, FormGasto, GaleriaFotos } from "@/components/painel/central";
import { BotaoAcao } from "@/components/interativos";
import { Cartao, LinkBotao, Tabela, td, th } from "@/components/ui";
import { nomeVeiculo, precoMinimo, veiculoCompleto } from "@/lib/consultas/veiculos";
import { listarContas } from "@/lib/consultas/caixa";
import { vendaCompleta } from "@/lib/consultas/vendas";
import { removerDocumento, removerGasto } from "@/lib/acoes/veiculos";
import { urlArquivo } from "@/lib/armazenamento";
import { ETAPAS_VENDA, ORIGEM_VEICULO, dataBR, reais } from "@/lib/dominio";
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

type Dados = NonNullable<Awaited<ReturnType<typeof veiculoCompleto>>>;

export async function generateMetadata({ params }: PageProps<"/painel/estoque/[id]">) {
  const d = await veiculoCompleto(Number((await params).id));
  return { title: d ? `${nomeVeiculo(d.veiculo)} ${d.veiculo.anoModelo}` : "Veículo" };
}

function Campo({ rotulo, valor, faltando }: { rotulo: string; valor?: React.ReactNode; faltando?: boolean }) {
  return (
    <div className="border-b border-linha/50 py-2.5 last:border-0">
      <dt className="text-xs text-nevoa">{rotulo}</dt>
      <dd className={cn("num mt-0.5 text-sm", faltando && "text-nevoa-2")}>
        {faltando ? (
          <span className="inline-flex items-center gap-1.5">
            Não informado
            <span className="rounded-full border border-dashed border-laranja/50 px-2 py-px text-[11px] text-laranja">opcional</span>
          </span>
        ) : (
          valor
        )}
      </dd>
    </div>
  );
}

const COR_DOC = { ok: "bg-sucesso/15 text-sucesso", pendente: "bg-chumbo-2 text-nevoa", vencido: "bg-perigo/15 text-perigo" };
const NOME_DOC = { ok: "Enviado", pendente: "Pendente", vencido: "Vencido" };

function AbaGeral({ d }: { d: Dados }) {
  const v = d.veiculo;
  const pend = d.checklist.filter((c) => c.status !== "ok");
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <Cartao titulo="Ficha do veículo" acao={<LinkBotao href={`/painel/estoque/${v.id}/editar`} tamanho="sm"><Pencil size={14} /> Editar dados</LinkBotao>}>
          <dl className="grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
            <Campo rotulo="Marca e modelo" valor={`${v.marca} ${v.modelo}`} />
            <Campo rotulo="Versão" valor={v.versao} faltando={!v.versao} />
            <Campo rotulo="Ano modelo / fabricação" valor={`${v.anoModelo} / ${v.anoFabricacao ?? v.anoModelo}`} />
            <Campo rotulo="Quilometragem" valor={v.km !== null ? `${v.km.toLocaleString("pt-BR")} km` : undefined} faltando={v.km === null} />
            <Campo rotulo="Cor" valor={v.cor} faltando={!v.cor} />
            <Campo rotulo="Categoria" valor={v.categoria} />
            <Campo rotulo="Câmbio" valor={v.cambio} />
            <Campo rotulo="Combustível" valor={v.combustivel} />
            <Campo rotulo="Portas" valor={v.portas} faltando={!v.portas} />
            <Campo rotulo="Placa" valor={v.placa} faltando={!v.placa} />
            <Campo rotulo="Chassi" valor={v.chassi} faltando={!v.chassi} />
            <Campo rotulo="RENAVAM" valor={v.renavam} faltando={!v.renavam} />
          </dl>
        </Cartao>
        <Cartao titulo="Equipamentos">
          {v.opcionais.length ? (
            <ul className="flex flex-wrap gap-2">
              {v.opcionais.map((o) => (
                <li key={o} className="flex items-center gap-1.5 rounded-full border border-linha bg-chumbo/50 px-3 py-1.5 text-sm">
                  <Check size={14} className="text-laranja" /> {o}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-nevoa">Nenhum equipamento marcado. Use “Editar dados” para dizer o que o carro tem.</p>
          )}
        </Cartao>
        {v.descricao && (
          <Cartao titulo="Descrição do anúncio">
            <p className="max-w-prose whitespace-pre-line text-sm leading-relaxed text-giz/85">{v.descricao}</p>
          </Cartao>
        )}
      </div>
      <div className="space-y-5">
        <Cartao titulo="Documentos pendentes">
          {pend.length === 0 ? (
            <p className="flex items-center gap-2 text-sm text-sucesso">
              <Check size={16} /> Documentação completa.
            </p>
          ) : (
            <ul className="space-y-2.5 text-sm">
              {pend.map((c) => (
                <li key={c.tipo}>
                  <Link href={`/painel/estoque/${v.id}?aba=documentos`} className="flex items-center gap-3 hover:text-laranja">
                    <CircleAlert size={16} className={c.status === "vencido" ? "text-perigo" : "text-laranja"} />
                    <span className="flex-1">{c.tipo}</span>
                    <span className={cn("rounded-full px-2 py-0.5 text-[11px]", COR_DOC[c.status])}>{NOME_DOC[c.status]}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Cartao>
        <Cartao titulo="Entrada no estoque">
          <dl>
            <Campo rotulo="Origem" valor={ORIGEM_VEICULO[v.origem as keyof typeof ORIGEM_VEICULO]} />
            {d.clienteOrigem && (
              <Campo
                rotulo={v.origem === "consignacao" ? "Dono (consignante)" : "Veio de"}
                valor={
                  <Link href={`/painel/clientes/${d.clienteOrigem.id}`} className="text-laranja hover:underline">
                    {d.clienteOrigem.nome}
                  </Link>
                }
              />
            )}
            <Campo rotulo="Fornecedor" valor={v.fornecedor} faltando={!v.fornecedor} />
            <Campo rotulo="Data de entrada" valor={dataBR(v.dataEntrada)} />
          </dl>
        </Cartao>
      </div>
    </div>
  );
}

function AbaDocumentos({ d }: { d: Dados }) {
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_340px]">
      <Cartao titulo="Checklist de documentos">
        <ul className="divide-y divide-linha/50">
          {d.checklist.map((c) => (
            <li key={c.tipo} className="py-3.5">
              <div className="flex flex-wrap items-center gap-4">
                <span className={cn("grid size-10 place-items-center rounded-xl", c.status === "ok" ? "bg-sucesso/10 text-sucesso" : c.status === "vencido" ? "bg-perigo/10 text-perigo" : "bg-chumbo text-nevoa")}>
                  <FileText size={18} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{c.tipo}</p>
                  <p className="text-xs text-nevoa">
                    {c.atual
                      ? `${c.atual.nomeArquivo} · enviado em ${c.atual.criadoEm.toLocaleDateString("pt-BR")}${c.atual.validade ? ` · validade ${dataBR(c.atual.validade)}` : ""}`
                      : "Ainda não enviado"}
                  </p>
                </div>
                <span className={cn("rounded-full px-2.5 py-1 text-xs", COR_DOC[c.status])}>{NOME_DOC[c.status]}</span>
                {c.atual && (
                  <span className="flex items-center gap-1">
                    <a href={urlArquivo(c.atual.chave)} target="_blank" rel="noopener" className="flex h-8 items-center gap-1.5 rounded-full border border-linha px-3 text-xs text-nevoa hover:text-giz">
                      <ExternalLink size={13} /> Abrir
                    </a>
                    <BotaoAcao acao={removerDocumento.bind(null, c.atual.id)} confirmar="Remover arquivo?" variante="fantasma">
                      <Trash2 size={13} />
                    </BotaoAcao>
                  </span>
                )}
              </div>
              {c.historico.length > 0 && <p className="ml-14 mt-1 text-[11px] text-nevoa-2">+ {c.historico.length} versão(ões) anterior(es) guardada(s)</p>}
            </li>
          ))}
        </ul>
      </Cartao>
      <Cartao titulo="Enviar documento">
        <FormDocumento veiculoId={d.veiculo.id} tipoInicial={d.checklist.find((c) => c.status !== "ok")?.tipo} />
      </Cartao>
    </div>
  );
}

async function AbaGastos({ d }: { d: Dados }) {
  const contas = await listarContas();
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_340px]">
      <Cartao titulo="Gastos com este carro" className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5">
        {d.gastos.length === 0 ? (
          <p className="px-5 pb-6 text-sm text-nevoa">Nenhum gasto lançado. Use o formulário ao lado para registrar o primeiro.</p>
        ) : (
          <Tabela minimo={560}>
            <thead>
              <tr className="border-y border-linha/60">
                <th className={th}>Data</th>
                <th className={th}>Descrição</th>
                <th className={th}>Categoria</th>
                <th className={th}>Nota</th>
                <th className={cn(th, "text-right")}>Valor</th>
                <th className={th} />
              </tr>
            </thead>
            <tbody>
              {d.gastos.map((g) => (
                <tr key={g.id} className="border-b border-linha/40">
                  <td className={cn(td, "num text-nevoa")}>{dataBR(g.data)}</td>
                  <td className={td}>{g.descricao}</td>
                  <td className={cn(td, "text-nevoa")}>{g.categoria}</td>
                  <td className={td}>
                    {g.notaChave ? (
                      <a href={urlArquivo(g.notaChave)} target="_blank" rel="noopener" className="text-sucesso" aria-label="Abrir nota fiscal">
                        <Receipt size={16} />
                      </a>
                    ) : (
                      <span className="text-nevoa-2">—</span>
                    )}
                  </td>
                  <td className={cn(td, "num text-right")}>{reais(g.valor)}</td>
                  <td className={cn(td, "w-10 text-right")}>
                    <BotaoAcao acao={removerGasto.bind(null, g.id)} confirmar="Remover gasto?" variante="fantasma">
                      <Trash2 size={13} />
                    </BotaoAcao>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={4} className={cn(td, "text-right text-nevoa")}>Total</td>
                <td className={cn(td, "num text-right font-semibold")}>{reais(d.totalGastos)}</td>
                <td />
              </tr>
            </tfoot>
          </Tabela>
        )}
      </Cartao>
      <Cartao titulo="Lançar gasto">
        <FormGasto veiculoId={d.veiculo.id} contas={contas.map((c) => ({ id: c.id, nome: c.nome }))} />
      </Cartao>
    </div>
  );
}

async function AbaRentabilidade({ d }: { d: Dados }) {
  const v = d.veiculo;
  const venda = d.vendaAtiva ? await vendaCompleta(d.vendaAtiva.venda.id) : null;
  const custoBase = v.custo + d.totalGastos;
  const minimo = precoMinimo(v);
  const escala = Math.max(v.preco, v.precoFipe ?? 0, custoBase) * 1.04;
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <Cartao titulo={venda ? "Resultado da venda" : "Quanto este carro custou"}>
        <ul className="space-y-3 text-sm">
          <li className="flex justify-between"><span className="text-nevoa">{v.origem === "consignacao" ? "Repasse ao dono" : "Custo de aquisição"}</span><span className="num">{reais(v.custo)}</span></li>
          <li className="flex justify-between"><span className="text-nevoa">Gastos de preparação</span><span className="num">{reais(d.totalGastos)}</span></li>
          {venda && (
            <>
              <li className="flex justify-between"><span className="text-nevoa">Custos da venda</span><span className="num">{reais(venda.totalCustos)}</span></li>
              {venda.taxas > 0 && <li className="flex justify-between"><span className="text-nevoa">Taxas de cartão</span><span className="num">{reais(venda.taxas)}</span></li>}
              {venda.retorno > 0 && <li className="flex justify-between"><span className="text-nevoa">Retorno do banco</span><span className="num text-sucesso">+{reais(venda.retorno)}</span></li>}
              <li className="flex justify-between"><span className="text-nevoa">Preço final</span><span className="num">{reais(venda.venda.precoFinal)}</span></li>
            </>
          )}
          <li className="flex justify-between border-t border-linha pt-3 font-semibold">
            <span>{venda ? "Lucro da venda" : "Lucro no preço anunciado"}</span>
            <span className={cn("num", (venda ? venda.lucro : v.preco - custoBase) >= 0 ? "text-sucesso" : "text-perigo")}>{reais(venda ? venda.lucro : v.preco - custoBase)}</span>
          </li>
        </ul>
        {venda && (
          <LinkBotao href={`/painel/vendas/${venda.venda.id}`} tamanho="sm" className="mt-4">
            Ver venda
          </LinkBotao>
        )}
      </Cartao>
      <Cartao titulo="Faixa de negociação">
        <div className="relative mt-2 h-3 rounded-full bg-chumbo">
          <div className="absolute inset-y-0 left-0 rounded-full bg-perigo/60" style={{ width: `${(custoBase / escala) * 100}%` }} />
          <div className="absolute inset-y-0 rounded-full bg-gradient-to-r from-brasa to-laranja" style={{ left: `${(minimo / escala) * 100}%`, width: `${Math.max(1, ((v.preco - minimo) / escala) * 100)}%` }} />
          {v.precoFipe && <span className="absolute -top-1.5 h-6 w-0.5 bg-giz" style={{ left: `${(v.precoFipe / escala) * 100}%` }} title="FIPE" />}
        </div>
        <p className="mt-2 text-[11px] text-nevoa-2">Vermelho: custo com gastos · laranja: faixa de negociação · traço branco: FIPE</p>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Preço anunciado</dt><dd className="num mt-1 font-semibold">{reais(v.preco)}</dd></div>
          <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Mínimo (−{v.descontoMaximoPct.toLocaleString("pt-BR")}%)</dt><dd className="num mt-1 font-semibold text-laranja">{reais(minimo)}</dd></div>
          <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Lucro no mínimo</dt><dd className={cn("num mt-1 font-semibold", minimo - custoBase >= 0 ? "text-sucesso" : "text-perigo")}>{reais(minimo - custoBase)}</dd></div>
          <div className="rounded-xl bg-chumbo/60 p-3"><dt className="text-xs text-nevoa">Custo por dia no pátio</dt><dd className="num mt-1 font-semibold">{d.dias > 0 ? reais(Math.round(custoBase * 0.01 / 30)) : "—"}</dd></div>
        </dl>
        <p className="mt-3 text-[11px] text-nevoa-2">Custo por dia: 1% ao mês sobre o capital parado no carro (custo de oportunidade).</p>
        {v.precoFipe ? (
          <p className="mt-3 text-xs text-nevoa">
            FIPE de referência: <span className="num text-giz">{reais(v.precoFipe)}</span> · anúncio {Math.abs(((v.preco - v.precoFipe) / v.precoFipe) * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%{" "}
            {v.preco >= v.precoFipe ? "acima" : "abaixo"} da tabela.
          </p>
        ) : null}
      </Cartao>
    </div>
  );
}

function AbaHistorico({ d }: { d: Dados }) {
  return (
    <Cartao titulo="Tudo o que aconteceu com este carro">
      {d.eventos.length === 0 ? (
        <p className="text-sm text-nevoa">Sem registros.</p>
      ) : (
        <ol className="relative space-y-5 border-l border-linha pl-6">
          {d.eventos.map((e) => (
            <li key={e.id} className="relative">
              <span className="absolute -left-[31px] top-1 size-3 rounded-full border-2 border-grafite bg-laranja" />
              <p className="font-medium">{e.titulo}</p>
              {e.detalhe && <p className="text-sm text-nevoa">{e.detalhe}</p>}
              <p className="num mt-0.5 text-xs text-nevoa-2">{e.criadoEm.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Fortaleza" })}</p>
            </li>
          ))}
        </ol>
      )}
    </Cartao>
  );
}

export default async function CentralVeiculo({ params, searchParams }: PageProps<"/painel/estoque/[id]">) {
  const d = await veiculoCompleto(Number((await params).id));
  if (!d) notFound();
  const v = d.veiculo;
  const abaParam = (await searchParams).aba;
  const aba: Aba = ABAS.some((a) => a.id === abaParam) ? (abaParam as Aba) : "geral";
  const pendDocs = d.checklist.filter((c) => c.status !== "ok").length;
  const indicadores = [
    { rotulo: v.origem === "consignacao" ? "Repasse + gastos" : "Custo + gastos", valor: reais(v.custo + d.totalGastos) },
    { rotulo: "Preço mínimo", valor: reais(precoMinimo(v)) },
    { rotulo: "Lucro previsto", valor: reais(v.preco - v.custo - d.totalGastos), destaque: true },
    { rotulo: v.status === "vendido" ? "Ficou no pátio" : "No pátio", valor: d.dias === 0 ? "Chegou hoje" : `${d.dias} ${d.dias === 1 ? "dia" : "dias"}`, alerta: d.dias >= 45 && v.status !== "vendido" },
  ];

  return (
    <>
      <BarraSuperior
        titulo={`${nomeVeiculo(v)} ${v.anoModelo}`}
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Estoque", href: "/painel/estoque" }, { rotulo: `${v.modelo} ${v.anoModelo}` }]}
      />

      <section className="grid overflow-hidden rounded-[var(--radius-card)] border border-linha/60 bg-grafite lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <FotoCarro src={d.fotos[0]?.urlCard} alt={`${nomeVeiculo(v)} ${v.anoModelo}`} prioridade className="aspect-[4/3] lg:aspect-auto lg:min-h-[360px]" sizes="(min-width: 1024px) 50vw, 100vw" />
        <div className="flex flex-col p-6">
          <div className="flex items-start gap-3">
            <SeloMarca marca={v.marca} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-nevoa">{[v.categoria, v.cor, v.km !== null && `${v.km.toLocaleString("pt-BR")} km`].filter(Boolean).join(" · ")}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <StatusVeiculoSelo status={v.status} />
                {v.publicado && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-chumbo px-2.5 py-1 text-xs text-nevoa">
                    <Eye size={13} /> Na vitrine
                  </span>
                )}
                {v.destaques.map((x) => (
                  <span key={x} className="rounded-full border border-laranja/40 px-2.5 py-0.5 text-xs text-laranja">
                    {x}
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

          <div className="mt-auto space-y-3 pt-6">
            <div className="flex flex-wrap gap-2">
              {d.vendaAtiva ? (
                <LinkBotao href={`/painel/vendas/${d.vendaAtiva.venda.id}`} variante="primario">
                  <Handshake size={16} /> Venda: {ETAPAS_VENDA[d.vendaAtiva.venda.etapa as keyof typeof ETAPAS_VENDA]}
                </LinkBotao>
              ) : v.status !== "rascunho" ? (
                <LinkBotao href={`/painel/vendas/nova?veiculo=${v.id}`} variante="primario">
                  <Handshake size={16} /> Iniciar venda
                </LinkBotao>
              ) : null}
              {v.publicado && (
                <LinkBotao href={`/carros/${v.slug}`} target="_blank">
                  <ExternalLink size={16} /> Ver na vitrine
                </LinkBotao>
              )}
            </div>
            <ControlesVeiculo id={v.id} status={v.status} publicado={v.publicado} temVenda={Boolean(d.vendaAtiva)} />
          </div>
        </div>
      </section>

      <nav className="sticky top-0 z-20 -mx-4 mb-5 mt-6 overflow-x-auto bg-asfalto/90 px-4 py-2 backdrop-blur md:-mx-8 md:px-8" aria-label="Seções do veículo">
        <ul className="flex gap-1.5">
          {ABAS.map((a) => {
            const on = a.id === aba;
            const contagem = a.id === "documentos" ? pendDocs : a.id === "gastos" ? d.gastos.length : a.id === "fotos" ? d.fotos.length : 0;
            return (
              <li key={a.id}>
                <Link
                  href={a.id === "geral" ? `/painel/estoque/${v.id}` : `/painel/estoque/${v.id}?aba=${a.id}`}
                  scroll={false}
                  aria-current={on ? "page" : undefined}
                  className={cn("flex items-center gap-2 whitespace-nowrap rounded-full px-4 py-2 text-sm transition", on ? "bg-giz font-semibold text-asfalto" : "text-nevoa hover:bg-chumbo hover:text-giz")}
                >
                  {a.rotulo}
                  {contagem > 0 && <span className={cn("num rounded-full px-1.5 text-[11px]", on ? "bg-asfalto/15" : "bg-chumbo-2", a.id === "documentos" && !on && "text-laranja")}>{contagem}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {aba === "geral" && <AbaGeral d={d} />}
      {aba === "documentos" && <AbaDocumentos d={d} />}
      {aba === "gastos" && <AbaGastos d={d} />}
      {aba === "rentabilidade" && <AbaRentabilidade d={d} />}
      {aba === "fotos" && (
        <Cartao titulo="Fotos">
          <GaleriaFotos veiculoId={v.id} fotos={d.fotos.map((f) => ({ id: f.id, urlCard: f.urlCard, urlOriginal: f.urlOriginal, focoY: f.focoY }))} />
          <p className="mt-4 text-xs text-nevoa">Dica: fotografe o carro inteiro, de frente em 3/4, com ele no centro. As fotos perdem os dados de localização ao serem enviadas.</p>
        </Cartao>
      )}
      {aba === "historico" && <AbaHistorico d={d} />}

      <p className="mt-6 flex items-center gap-2 text-xs text-nevoa-2">
        <Clock size={13} /> Entrou em {dataBR(v.dataEntrada)}
      </p>
    </>
  );
}
