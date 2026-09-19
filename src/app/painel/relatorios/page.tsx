import Link from "next/link";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { GraficoArea, GraficoBarras } from "@/components/painel/graficos";
import { Cartao, LinkBotao, MiniIndicador, Tabela, td, th } from "@/components/ui";
import { dre, fechada, indicadores } from "@/lib/consultas/indicadores";
import { nomeVeiculo } from "@/lib/consultas/veiculos";
import { COR } from "@/lib/cores";
import { dataBR, hojeISO, mesCurto, mesLongo, reais, reaisInteiros, somarMeses } from "@/lib/dominio";
import { cn } from "@/lib/cn";

export const metadata = { title: "Relatórios" };

function Linha({ rotulo, valor, sinal, forte, sub }: { rotulo: string; valor: number; sinal?: "+" | "−"; forte?: boolean; sub?: boolean }) {
  return (
    <div className={cn("flex justify-between py-2 text-sm", forte && "border-t border-linha font-semibold", sub && "pl-4 text-nevoa")}>
      <span className={forte ? "" : "text-nevoa"}>{rotulo}</span>
      <span className={cn("num", forte && (valor >= 0 ? "text-sucesso" : "text-perigo"))}>
        {sinal}
        {reais(Math.abs(valor))}
      </span>
    </div>
  );
}

export default async function Relatorios({ searchParams }: PageProps<"/painel/relatorios">) {
  const sp = await searchParams;
  const hoje = hojeISO();
  const mes = typeof sp.mes === "string" && /^\d{4}-\d{2}$/.test(sp.mes) ? sp.mes : hoje.slice(0, 7);
  const meses = Array.from({ length: 6 }, (_, i) => somarMeses(`${mes}-01`, i - 5).slice(0, 7));
  const [atual, historico, k] = await Promise.all([dre(mes), Promise.all(meses.map((m) => dre(m))), indicadores()]);

  // Rentabilidade por veículo vendido (6 meses até o mês escolhido)
  const vendidos = k.vendas
    .filter((v) => fechada(v) && v.venda.dataVenda.slice(0, 7) >= meses[0] && v.venda.dataVenda.slice(0, 7) <= mes)
    .map((v) => ({ ...v, porDia: v.lucro / Math.max(1, v.diasAteVender), margem: (v.lucro / v.venda.precoFinal) * 100 }))
    .sort((a, b) => b.porDia - a.porDia);

  // Categorias e marcas: quantidade, giro e lucro médio
  function agrupar(chave: (v: (typeof vendidos)[number]) => string) {
    const mapa = new Map<string, { qtd: number; lucro: number; dias: number }>();
    for (const v of vendidos) {
      const g = mapa.get(chave(v)) ?? { qtd: 0, lucro: 0, dias: 0 };
      mapa.set(chave(v), { qtd: g.qtd + 1, lucro: g.lucro + v.lucro, dias: g.dias + v.diasAteVender });
    }
    return [...mapa.entries()].map(([nome, g]) => ({ nome, qtd: g.qtd, lucroMedio: g.lucro / g.qtd, giro: g.dias / g.qtd })).sort((a, b) => b.lucroMedio - a.lucroMedio);
  }
  const categorias = agrupar((v) => v.veiculo.categoria);
  const marcas = agrupar((v) => v.veiculo.marca);
  const melhorGiro = [...categorias].sort((a, b) => a.giro - b.giro)[0];

  return (
    <>
      <BarraSuperior
        titulo="Relatórios"
        trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Relatórios" }]}
        acoes={
          <div className="flex items-center gap-1 rounded-full border border-linha bg-grafite p-1">
            <Link href={`/painel/relatorios?mes=${somarMeses(`${mes}-01`, -1).slice(0, 7)}`} className="rounded-full p-1.5 text-nevoa hover:bg-chumbo hover:text-giz" aria-label="Mês anterior">
              <ChevronLeft size={16} />
            </Link>
            <span className="w-36 text-center text-sm">{mesLongo(mes)}</span>
            <Link href={`/painel/relatorios?mes=${somarMeses(`${mes}-01`, 1).slice(0, 7)}`} className="rounded-full p-1.5 text-nevoa hover:bg-chumbo hover:text-giz" aria-label="Próximo mês">
              <ChevronRight size={16} />
            </Link>
          </div>
        }
      />

      <div className="space-y-5">
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[380px_1fr]">
          <Cartao titulo={`Resultado de ${mesCurto(mes)}`}>
            <Linha rotulo={`Vendas (${atual.vendas.length} carros)`} valor={atual.receita} />
            <Linha rotulo="Custo dos carros vendidos" valor={atual.custoVeiculos} sinal="−" sub />
            <Linha rotulo="Preparação e custos de venda" valor={atual.preparacao} sinal="−" sub />
            {atual.taxas > 0 && <Linha rotulo="Taxas de cartão" valor={atual.taxas} sinal="−" sub />}
            {atual.retorno > 0 && <Linha rotulo="Retorno de financiamentos" valor={atual.retorno} sinal="+" sub />}
            <Linha rotulo="Lucro bruto" valor={atual.lucroBruto} forte />
            {atual.despesas.map((d) => (
              <Linha key={d.categoria} rotulo={d.categoria} valor={d.valor} sinal="−" sub />
            ))}
            {atual.outrasReceitas > 0 && <Linha rotulo="Outras receitas" valor={atual.outrasReceitas} sinal="+" sub />}
            <Linha rotulo="Resultado do mês" valor={atual.resultado} forte />
            <p className="mt-3 text-[11px] text-nevoa-2">Vendas contam a partir do contrato assinado. Despesas pelo mês de vencimento.</p>
          </Cartao>
          <Cartao titulo="Receita, lucro bruto e resultado (6 meses)">
            <GraficoArea
              eixoX="mes"
              dados={historico.map((d) => ({ mes: mesCurto(d.mes), receita: d.receita / 100, lucro: d.lucroBruto / 100, resultado: d.resultado / 100 }))}
              series={[
                { chave: "receita", nome: "Receita", cor: COR.laranja },
                { chave: "lucro", nome: "Lucro bruto", cor: COR.ambar },
                { chave: "resultado", nome: "Resultado", cor: COR.verde },
              ]}
              altura={330}
            />
          </Cartao>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MiniIndicador rotulo="Resultado acumulado (6 meses)" valor={reaisInteiros(historico.reduce((s, d) => s + d.resultado, 0))} tom={historico.reduce((s, d) => s + d.resultado, 0) >= 0 ? "bom" : "ruim"} />
          <MiniIndicador rotulo="Despesas fixas por mês" valor={reaisInteiros(k.despesasFixasMes)} dica={`Pede ${k.pontoEquilibrio?.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) ?? "—"} carros/mês para empatar`} />
          <MiniIndicador rotulo="Categoria que gira mais rápido" valor={melhorGiro ? melhorGiro.nome : "—"} dica={melhorGiro ? `${Math.round(melhorGiro.giro)} dias em média` : undefined} />
          <MiniIndicador rotulo="Melhor lucro por dia" valor={vendidos[0] ? reaisInteiros(vendidos[0].porDia) : "—"} dica={vendidos[0] ? `${vendidos[0].nomeVeiculo}` : undefined} />
        </div>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <Cartao titulo="Lucro médio e giro por categoria">
            <GraficoBarras
              eixoX="nome"
              dados={categorias.map((c) => ({ nome: c.nome, lucroMedio: Math.round(c.lucroMedio / 100) }))}
              series={[{ chave: "lucroMedio", nome: "Lucro médio", cor: COR.laranja }]}
              altura={220}
            />
            <Tabela minimo={380}>
              <thead>
                <tr className="border-b border-linha/60">
                  <th className={cn(th, "pl-0 first:pl-0")}>Categoria</th>
                  <th className={cn(th, "text-right")}>Vendidos</th>
                  <th className={cn(th, "text-right")}>Giro</th>
                  <th className={cn(th, "text-right last:pr-0")}>Lucro médio</th>
                </tr>
              </thead>
              <tbody>
                {categorias.map((c) => (
                  <tr key={c.nome} className="border-b border-linha/40 last:border-0">
                    <td className={cn(td, "pl-0 first:pl-0")}>{c.nome}</td>
                    <td className={cn(td, "num text-right")}>{c.qtd}</td>
                    <td className={cn(td, "num text-right")}>{Math.round(c.giro)} dias</td>
                    <td className={cn(td, "num text-right text-sucesso last:pr-0")}>{reaisInteiros(c.lucroMedio)}</td>
                  </tr>
                ))}
              </tbody>
            </Tabela>
          </Cartao>
          <Cartao titulo="Marcas que mais dão lucro">
            <GraficoBarras
              eixoX="nome"
              dados={marcas.slice(0, 8).map((c) => ({ nome: c.nome, lucroMedio: Math.round(c.lucroMedio / 100), qtd: c.qtd }))}
              series={[{ chave: "lucroMedio", nome: "Lucro médio", cor: COR.ambar }]}
              altura={220}
            />
            <ul className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
              {marcas.map((m) => (
                <li key={m.nome} className="flex justify-between">
                  <span className="text-nevoa">
                    {m.nome} <span className="num text-xs">({m.qtd})</span>
                  </span>
                  <span className="num">{Math.round(m.giro)} d</span>
                </li>
              ))}
            </ul>
          </Cartao>
        </div>

        <Cartao
          titulo="Rentabilidade por carro vendido (6 meses)"
          className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5"
          acao={
            <LinkBotao href="/painel/relatorios/csv?tipo=vendas" tamanho="sm">
              <Download size={14} /> Exportar vendas (CSV)
            </LinkBotao>
          }
        >
          <Tabela minimo={860}>
            <thead>
              <tr className="border-y border-linha/60">
                <th className={th}>Veículo</th>
                <th className={th}>Venda</th>
                <th className={cn(th, "text-right")}>No pátio</th>
                <th className={cn(th, "text-right")}>Custo total</th>
                <th className={cn(th, "text-right")}>Preço final</th>
                <th className={cn(th, "text-right")}>Lucro</th>
                <th className={cn(th, "text-right")}>Margem</th>
                <th className={cn(th, "text-right")}>Lucro/dia</th>
              </tr>
            </thead>
            <tbody>
              {vendidos.map((v) => (
                <tr key={v.venda.id} className="border-b border-linha/40 last:border-0 hover:bg-chumbo/30">
                  <td className={cn(td, "font-medium")}>
                    <Link href={`/painel/vendas/${v.venda.id}`} className="hover:text-laranja">
                      {v.nomeVeiculo}
                    </Link>
                  </td>
                  <td className={cn(td, "num text-nevoa")}>{dataBR(v.venda.dataVenda)}</td>
                  <td className={cn(td, "num text-right")}>{v.diasAteVender} d</td>
                  <td className={cn(td, "num text-right text-nevoa")}>{reais(v.custoTotal)}</td>
                  <td className={cn(td, "num text-right")}>{reais(v.venda.precoFinal)}</td>
                  <td className={cn(td, "num text-right", v.lucro >= 0 ? "text-sucesso" : "text-perigo")}>{reais(v.lucro)}</td>
                  <td className={cn(td, "num text-right")}>{v.margem.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</td>
                  <td className={cn(td, "num text-right font-medium")}>{reaisInteiros(v.porDia)}</td>
                </tr>
              ))}
            </tbody>
          </Tabela>
          {vendidos.length === 0 && <p className="p-6 text-center text-sm text-nevoa">Nenhuma venda fechada no período.</p>}
        </Cartao>

        <Cartao
          titulo="Estoque atual: capital parado"
          className="p-0 [&>div:first-child]:px-5 [&>div:first-child]:pt-5"
          acao={
            <div className="flex gap-2">
              <LinkBotao href="/painel/relatorios/csv?tipo=estoque" tamanho="sm">
                <Download size={14} /> Estoque (CSV)
              </LinkBotao>
              <LinkBotao href="/painel/relatorios/csv?tipo=lancamentos" tamanho="sm">
                <Download size={14} /> Caixa (CSV)
              </LinkBotao>
            </div>
          }
        >
          <Tabela minimo={760}>
            <thead>
              <tr className="border-y border-linha/60">
                <th className={th}>Veículo</th>
                <th className={cn(th, "text-right")}>Dias</th>
                <th className={cn(th, "text-right")}>Investido</th>
                <th className={cn(th, "text-right")}>Anunciado</th>
                <th className={cn(th, "text-right")}>Lucro previsto</th>
                <th className={cn(th, "text-right")}>Custo do tempo parado</th>
              </tr>
            </thead>
            <tbody>
              {[...k.estoque]
                .sort((a, b) => b.dias - a.dias)
                .map((v) => {
                  const investido = v.custo + v.totalGastos;
                  return (
                    <tr key={v.id} className="border-b border-linha/40 last:border-0 hover:bg-chumbo/30">
                      <td className={cn(td, "font-medium")}>
                        <Link href={`/painel/estoque/${v.id}`} className="hover:text-laranja">
                          {nomeVeiculo(v)} {v.anoModelo}
                        </Link>
                      </td>
                      <td className={cn(td, "num text-right", v.dias >= 45 && "text-laranja")}>{v.dias}</td>
                      <td className={cn(td, "num text-right")}>{reais(investido)}</td>
                      <td className={cn(td, "num text-right")}>{reais(v.preco)}</td>
                      <td className={cn(td, "num text-right text-sucesso")}>{reais(v.preco - investido)}</td>
                      <td className={cn(td, "num text-right text-nevoa")}>{reais(Math.round((investido * 0.01 * v.dias) / 30))}</td>
                    </tr>
                  );
                })}
            </tbody>
            <tfoot>
              <tr>
                <td className={cn(td, "text-nevoa")}>{k.estoque.length} carros</td>
                <td />
                <td className={cn(td, "num text-right font-semibold")}>{reais(k.capitalInvestido)}</td>
                <td className={cn(td, "num text-right font-semibold")}>{reais(k.valorEstoque)}</td>
                <td className={cn(td, "num text-right font-semibold text-sucesso")}>{reais(k.lucroPotencial)}</td>
                <td />
              </tr>
            </tfoot>
          </Tabela>
          <p className="px-5 pb-4 text-[11px] text-nevoa-2">Custo do tempo parado: 1% ao mês sobre o valor investido, o que o dinheiro renderia se não estivesse no carro.</p>
        </Cartao>
      </div>
    </>
  );
}
