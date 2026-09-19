import Link from "next/link";
import { notFound } from "next/navigation";
import { MessageCircle, Trash2 } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { EditarCliente } from "@/components/painel/clientes";
import { BaixaLancamento } from "@/components/painel/venda";
import { BotaoAcao } from "@/components/interativos";
import { Cartao, LinkBotao, MiniIndicador, SeloLancamento, Tabela, td, th } from "@/components/ui";
import { clienteCompleto } from "@/lib/consultas/clientes";
import { listarContas } from "@/lib/consultas/caixa";
import { excluirCliente } from "@/lib/acoes/clientes";
import { ETAPAS_VENDA, ORIGEM_VEICULO, dataBR, reais } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export async function generateMetadata({ params }: PageProps<"/painel/clientes/[id]">) {
  const c = await clienteCompleto(Number((await params).id));
  return { title: c?.cliente.nome ?? "Cliente" };
}

export default async function Cliente({ params }: PageProps<"/painel/clientes/[id]">) {
  const d = await clienteCompleto(Number((await params).id));
  if (!d) notFound();
  const c = d.cliente;
  const contas = (await listarContas()).map((x) => ({ id: x.id, nome: x.nome }));
  const ativas = d.vendas.filter((v) => v.venda.etapa !== "cancelada");
  const emAberto = d.parcelas.filter((p) => !p.pagoEm);
  const atrasado = emAberto.filter((p) => p.status === "atrasado").reduce((s, p) => s + p.valor, 0);
  const pagoEmDia = d.parcelas.filter((p) => p.pagoEm && p.pagoEm <= p.vencimento).length;
  const pagas = d.parcelas.filter((p) => p.pagoEm).length;

  return (
    <>
      <BarraSuperior
        titulo={c.nome}
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Clientes", href: "/painel/clientes" }, { rotulo: c.nome }]}
        acoes={
          <div className="flex gap-2">
            {c.telefone && (
              <LinkBotao href={`https://wa.me/55${c.telefone.replace(/\D/g, "")}`} target="_blank">
                <MessageCircle size={16} /> WhatsApp
              </LinkBotao>
            )}
            <LinkBotao href={`/painel/vendas/nova?cliente=${c.id}`} variante="primario">
              Nova venda
            </LinkBotao>
          </div>
        }
      />
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
        <div className="min-w-0 space-y-5">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <MiniIndicador rotulo="Compras" valor={ativas.length} />
            <MiniIndicador rotulo="Total comprado" valor={reais(ativas.reduce((s, v) => s + v.venda.precoFinal, 0))} />
            <MiniIndicador rotulo="Ainda deve" valor={reais(emAberto.reduce((s, p) => s + p.valor, 0))} tom={atrasado ? "ruim" : undefined} dica={atrasado ? `${reais(atrasado)} atrasado` : undefined} />
            <MiniIndicador rotulo="Pontualidade" valor={pagas ? `${Math.round((pagoEmDia / pagas) * 100)}%` : "—"} dica="Parcelas pagas até o vencimento" />
          </div>

          <Cartao titulo="Compras" className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5">
            {d.vendas.length === 0 ? (
              <p className="px-5 pb-5 text-sm text-nevoa">Nenhuma compra ainda.{c.interesse ? ` Interesse: ${c.interesse}.` : ""}</p>
            ) : (
              <Tabela minimo={560}>
                <thead>
                  <tr className="border-y border-linha/60">
                    <th className={th}>Veículo</th>
                    <th className={th}>Data</th>
                    <th className={th}>Etapa</th>
                    <th className={cn(th, "text-right")}>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {d.vendas.map((v) => (
                    <tr key={v.venda.id} className="border-b border-linha/40 last:border-0">
                      <td className={td}>
                        <Link href={`/painel/vendas/${v.venda.id}`} className="font-medium hover:text-laranja">
                          {v.nomeVeiculo}
                        </Link>
                      </td>
                      <td className={cn(td, "num text-nevoa")}>{dataBR(v.venda.dataVenda)}</td>
                      <td className={cn(td, "text-nevoa")}>{ETAPAS_VENDA[v.venda.etapa as keyof typeof ETAPAS_VENDA]}</td>
                      <td className={cn(td, "num text-right")}>{reais(v.venda.precoFinal)}</td>
                    </tr>
                  ))}
                </tbody>
              </Tabela>
            )}
          </Cartao>

          {d.parcelas.length > 0 && (
            <Cartao titulo="Pagamentos do cliente" className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5">
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
                  {d.parcelas.map((p) => (
                    <tr key={p.id} className="border-b border-linha/40 last:border-0">
                      <td className={cn(td, "num text-nevoa")}>{dataBR(p.vencimento)}</td>
                      <td className={td}>{p.descricao}</td>
                      <td className={td}>
                        <SeloLancamento status={p.status} tipo={p.tipo} />
                      </td>
                      <td className={cn(td, "num text-right")}>{reais(p.valor)}</td>
                      <td className={cn(td, "text-right")}>
                        <BaixaLancamento id={p.id} valor={p.valor} tipo={p.tipo} pago={Boolean(p.pagoEm)} contas={contas} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Tabela>
            </Cartao>
          )}

          {d.veiculosDoCliente.length > 0 && (
            <Cartao titulo="Carros que vieram deste cliente">
              <ul className="space-y-2 text-sm">
                {d.veiculosDoCliente.map((v) => (
                  <li key={v.id}>
                    <Link href={`/painel/estoque/${v.id}`} className="hover:text-laranja">
                      {v.marca} {v.modelo} {v.anoModelo}
                    </Link>{" "}
                    <span className="text-nevoa">· {ORIGEM_VEICULO[v.origem as keyof typeof ORIGEM_VEICULO]} · {reais(v.custo)}</span>
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
        </div>

        <div className="space-y-5">
          <Cartao titulo="Dados do cliente">
            <EditarCliente id={c.id} c={c} />
          </Cartao>
          <Cartao titulo="Histórico">
            {d.eventos.length === 0 ? (
              <p className="text-sm text-nevoa">Cadastrado em {c.criadoEm.toLocaleDateString("pt-BR")}.</p>
            ) : (
              <ol className="relative space-y-4 border-l border-linha pl-5">
                {d.eventos.map((e) => (
                  <li key={e.id} className="relative text-sm">
                    <span className="absolute -left-[25px] top-1 size-2.5 rounded-full border-2 border-grafite bg-laranja" />
                    <p>{e.titulo}</p>
                    {e.detalhe && <p className="text-xs text-nevoa">{e.detalhe}</p>}
                    <p className="num text-[11px] text-nevoa-2">{e.criadoEm.toLocaleDateString("pt-BR")}</p>
                  </li>
                ))}
              </ol>
            )}
          </Cartao>
          {d.vendas.length === 0 && (
            <BotaoAcao acao={excluirCliente.bind(null, c.id)} confirmar="Excluir este cliente?" variante="fantasma" tamanho="md">
              <Trash2 size={15} /> Excluir cliente
            </BotaoAcao>
          )}
        </div>
      </div>
    </>
  );
}
