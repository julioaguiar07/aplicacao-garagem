import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowUpRight, CarFront, Phone } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { FotoCarro } from "@/components/foto-carro";
import { BaixaLancamento, CancelarVenda, DocumentosVenda, EtapasVenda } from "@/components/painel/venda";
import { FormAcao } from "@/components/interativos";
import { Cartao, Campo, SeloLancamento, Tabela, classeCampo, td, th } from "@/components/ui";
import { listarContas } from "@/lib/consultas/caixa";
import { vendaCompleta } from "@/lib/consultas/vendas";
import { nomeVeiculo } from "@/lib/consultas/veiculos";
import { salvarObservacoes } from "@/lib/acoes/vendas";
import { FORMAS_PAGAMENTO, TIPOS_CUSTO_VENDA, type FormaPagamento, dataBR, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export async function generateMetadata({ params }: PageProps<"/painel/vendas/[id]">) {
  const v = await vendaCompleta(Number((await params).id));
  return { title: v ? `Venda: ${v.veiculo.modelo} ${v.veiculo.anoModelo}` : "Venda" };
}

function resumoDetalhes(forma: string, d: Record<string, string | number | boolean | null>) {
  const n = (k: string) => Number(d[k] ?? 0);
  switch (forma) {
    case "cartao":
      return `${n("parcelas")}x · taxa ${n("taxaPct").toLocaleString("pt-BR")}%${d.antecipado ? " · antecipado" : ""}`;
    case "financiamento_bancario":
      return `${d.banco || "Banco"} · ${n("parcelas")}x a ${n("taxaMensal").toLocaleString("pt-BR")}% a.m.${n("retorno") ? ` · retorno ${reais(n("retorno"))}` : ""}`;
    case "financiamento_proprio":
      return `${n("parcelas")} parcelas · juros ${n("jurosMensalPct").toLocaleString("pt-BR")}% a.m.`;
    case "leasing":
      return String(d.instituicao || "");
    case "consorcio":
      return String(d.administradora || "");
    case "cheque":
      return `${d.banco || ""} nº ${d.numero || "—"} · bom para ${dataBR(String(d.bomPara || ""))}`;
    case "troca":
      return `${d.marca} ${d.modelo} ${d.ano ?? ""}`;
    default:
      return d.recebido ? "Recebido" : "A receber";
  }
}

export default async function DetalheVenda({ params }: PageProps<"/painel/vendas/[id]">) {
  const v = await vendaCompleta(Number((await params).id));
  if (!v) notFound();
  const contas = (await listarContas()).map((c) => ({ id: c.id, nome: c.nome }));
  const faltando = [
    !v.veiculo.placa && { campo: "placa", rotulo: "Placa" },
    !v.veiculo.chassi && { campo: "chassi", rotulo: "Chassi" },
    !v.veiculo.renavam && { campo: "renavam", rotulo: "RENAVAM" },
    !v.veiculo.cor && { campo: "cor", rotulo: "Cor" },
    !v.cliente.cpf && { campo: "cpf", rotulo: "CPF ou CNPJ do comprador" },
    !v.cliente.endereco && { campo: "endereco", rotulo: "Endereço do comprador" },
    !v.cliente.cidade && { campo: "cidade", rotulo: "Cidade do comprador" },
  ].filter(Boolean) as { campo: string; rotulo: string }[];
  const recebido = v.lancamentos.filter((l) => l.tipo === "entrada" && l.pagoEm).reduce((s, l) => s + l.valor, 0);
  const aReceber = v.lancamentos.filter((l) => l.tipo === "entrada" && !l.pagoEm).reduce((s, l) => s + l.valor, 0);
  const cancelada = v.venda.etapa === "cancelada";

  return (
    <>
      <BarraSuperior
        titulo={`Venda: ${nomeVeiculo(v.veiculo)} ${v.veiculo.anoModelo}`}
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Vendas", href: "/painel/vendas" }, { rotulo: `#${v.venda.id}` }]}
      />

      <section className="grid overflow-hidden rounded-[var(--radius-card)] border border-linha/60 bg-grafite md:grid-cols-[280px_1fr]">
        <FotoCarro src={v.capa?.urlCard} alt="" className="aspect-[4/3] md:aspect-auto" sizes="280px" />
        <div className="space-y-5 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs text-nevoa">Comprador</p>
              <Link href={`/painel/clientes/${v.cliente.id}`} className="display text-xl font-bold hover:text-laranja">
                {v.cliente.nome}
              </Link>
              {v.cliente.telefone && (
                <p className="flex items-center gap-1.5 text-sm text-nevoa">
                  <Phone size={13} /> {v.cliente.telefone}
                </p>
              )}
            </div>
            <div className="text-right">
              <p className="text-xs text-nevoa">Preço final · {dataBR(v.venda.dataVenda)}</p>
              <p className="display num text-3xl font-bold">{reais(v.venda.precoFinal)}</p>
              <p className={cn("num text-sm", v.lucro >= 0 ? "text-sucesso" : "text-perigo")}>Lucro {reais(v.lucro)}</p>
            </div>
          </div>
          <EtapasVenda vendaId={v.venda.id} etapa={v.venda.etapa} />
          <div className="flex flex-wrap gap-2 text-sm">
            <Link href={`/painel/estoque/${v.veiculo.id}`} className="flex items-center gap-1.5 rounded-full border border-linha px-3 py-1.5 text-nevoa hover:text-giz">
              <CarFront size={14} /> Central do veículo <ArrowUpRight size={13} />
            </Link>
            {v.trocas.map((t) => (
              <Link key={t.id} href={`/painel/estoque/${t.id}`} className="flex items-center gap-1.5 rounded-full border border-laranja/40 px-3 py-1.5 text-laranja hover:bg-laranja/10">
                Troca: {t.marca} {t.modelo} {t.anoModelo} <ArrowUpRight size={13} />
              </Link>
            ))}
          </div>
        </div>
      </section>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="min-w-0 space-y-5">
          <Cartao titulo="Como o cliente pagou">
            <ul className="divide-y divide-linha/50">
              {v.pagamentos.map((p) => (
                <li key={p.id} className="flex flex-wrap items-center gap-3 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{FORMAS_PAGAMENTO[p.forma as FormaPagamento]}</p>
                    <p className="text-xs text-nevoa">{resumoDetalhes(p.forma, p.detalhes)}</p>
                  </div>
                  <span className="num font-semibold">{reais(p.valor)}</span>
                </li>
              ))}
            </ul>
          </Cartao>

          <Cartao titulo="Valores desta venda no caixa" className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5">
            {v.lancamentos.length === 0 ? (
              <p className="px-5 pb-5 text-sm text-nevoa">Nada no caixa.</p>
            ) : (
              <Tabela minimo={620}>
                <thead>
                  <tr className="border-y border-linha/60">
                    <th className={th}>Vencimento</th>
                    <th className={th}>Descrição</th>
                    <th className={th}>Situação</th>
                    <th className={cn(th, "text-right")}>Valor</th>
                    <th className={th} />
                  </tr>
                </thead>
                <tbody>
                  {v.lancamentos.map((l) => (
                    <tr key={l.id} className="border-b border-linha/40 last:border-0">
                      <td className={cn(td, "num text-nevoa")}>{dataBR(l.vencimento)}</td>
                      <td className={td}>{l.descricao}</td>
                      <td className={td}>
                        <SeloLancamento status={l.status} tipo={l.tipo} />
                      </td>
                      <td className={cn(td, "num text-right", l.tipo === "entrada" ? "text-sucesso" : "")}>
                        {l.tipo === "entrada" ? "+" : "−"}
                        {reais(l.valor)}
                      </td>
                      <td className={cn(td, "text-right")}>{!cancelada && <BaixaLancamento id={l.id} valor={l.valor} tipo={l.tipo} pago={Boolean(l.pagoEm)} contas={contas} />}</td>
                    </tr>
                  ))}
                </tbody>
              </Tabela>
            )}
            <div className="flex flex-wrap gap-6 border-t border-linha/60 px-5 py-3 text-sm">
              <span className="text-nevoa">Recebido <span className="num ml-1 text-sucesso">{reais(recebido)}</span></span>
              <span className="text-nevoa">A receber <span className="num ml-1 text-giz">{reais(aReceber)}</span></span>
            </div>
          </Cartao>

          <Cartao titulo="Documentos da venda">
            <DocumentosVenda vendaId={v.venda.id} faltando={faltando} />
          </Cartao>
        </div>

        <div className="space-y-5">
          <Cartao titulo="Resultado">
            <dl className="space-y-2.5 text-sm">
              <div className="flex justify-between"><dt className="text-nevoa">Preço anunciado</dt><dd className="num">{reais(v.veiculo.preco)}</dd></div>
              <div className="flex justify-between"><dt className="text-nevoa">Desconto concedido</dt><dd className="num">{reais(Math.max(0, v.veiculo.preco - v.venda.precoFinal))}</dd></div>
              <div className="flex justify-between"><dt className="text-nevoa">{v.veiculo.origem === "consignacao" ? "Repasse ao dono" : "Custo do carro"}</dt><dd className="num">−{reais(v.veiculo.custo)}</dd></div>
              <div className="flex justify-between"><dt className="text-nevoa">Gastos de preparação</dt><dd className="num">−{reais(v.totalGastos)}</dd></div>
              {v.custos.map((c) => (
                <div key={c.id} className="flex justify-between"><dt className="text-nevoa">{TIPOS_CUSTO_VENDA[c.tipo as keyof typeof TIPOS_CUSTO_VENDA]}</dt><dd className="num">−{reais(c.valor)}</dd></div>
              ))}
              {v.taxas > 0 && <div className="flex justify-between"><dt className="text-nevoa">Taxas de cartão</dt><dd className="num">−{reais(v.taxas)}</dd></div>}
              {v.retorno > 0 && <div className="flex justify-between"><dt className="text-nevoa">Retorno do banco</dt><dd className="num text-sucesso">+{reais(v.retorno)}</dd></div>}
              <div className="flex justify-between border-t border-linha pt-2.5 font-semibold"><dt>Lucro</dt><dd className={cn("num", v.lucro >= 0 ? "text-sucesso" : "text-perigo")}>{reais(v.lucro)}</dd></div>
              <div className="flex justify-between text-xs"><dt className="text-nevoa">Margem</dt><dd className="num">{((v.lucro / v.venda.precoFinal) * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</dd></div>
            </dl>
          </Cartao>

          <Cartao titulo="Anotações">
            <FormAcao acao={salvarObservacoes.bind(null, v.venda.id)} rotulo="Salvar" variante="secundario" limparAoConcluir={false}>
              <Campo rotulo="Data da venda">
                <input type="date" name="dataVenda" defaultValue={v.venda.dataVenda} className={cn(classeCampo, "num")} />
              </Campo>
              <Campo rotulo="Observações">
                <textarea name="observacoes" defaultValue={v.venda.observacoes ?? ""} className={cn(classeCampo, "h-24 py-2")} />
              </Campo>
            </FormAcao>
          </Cartao>

          <Cartao titulo="Histórico">
            <ol className="relative space-y-4 border-l border-linha pl-5">
              {v.eventos.map((e) => (
                <li key={e.id} className="relative text-sm">
                  <span className="absolute -left-[25px] top-1 size-2.5 rounded-full border-2 border-grafite bg-laranja" />
                  <p>{e.titulo}</p>
                  {e.detalhe && <p className="text-xs text-nevoa">{e.detalhe}</p>}
                  <p className="num text-[11px] text-nevoa-2">{e.criadoEm.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Fortaleza" })}</p>
                </li>
              ))}
            </ol>
          </Cartao>

          {!cancelada && (
            <div className="rounded-[var(--radius-card)] border border-perigo/30 p-5">
              <p className="mb-3 text-sm text-nevoa">Desistência ou erro no cadastro? Cancelar apaga os valores em aberto e devolve o carro ao estoque.</p>
              <CancelarVenda vendaId={v.venda.id} />
            </div>
          )}
        </div>
      </div>
    </>
  );
}
