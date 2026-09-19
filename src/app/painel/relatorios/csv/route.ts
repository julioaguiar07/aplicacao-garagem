import { exigirLogin } from "@/lib/auth";
import { listarVendas } from "@/lib/consultas/vendas";
import { listarVeiculos, nomeVeiculo } from "@/lib/consultas/veiculos";
import { todosLancamentos } from "@/lib/consultas/caixa";
import { ETAPAS_VENDA, FORMAS_PAGAMENTO, STATUS_VEICULO, dataBR, hojeISO } from "@/lib/dominio";

// Exportações em CSV (separador ";" e vírgula decimal, abrem direto no Excel em português)

const dinheiro = (c: number) => (c / 100).toFixed(2).replace(".", ",");
const celula = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;

function csv(cabecalho: string[], linhas: unknown[][]) {
  return "﻿" + [cabecalho, ...linhas].map((l) => l.map(celula).join(";")).join("\r\n");
}

export async function GET(req: Request) {
  await exigirLogin();
  const tipo = new URL(req.url).searchParams.get("tipo");
  let conteudo: string;
  if (tipo === "vendas") {
    const vendas = await listarVendas({ incluirCanceladas: true });
    conteudo = csv(
      ["Data", "Veículo", "Cliente", "Etapa", "Forma principal", "Preço anunciado", "Preço final", "Custo total", "Lucro", "Dias no pátio"],
      vendas.map((v) => [
        dataBR(v.venda.dataVenda),
        v.nomeVeiculo,
        v.cliente.nome,
        ETAPAS_VENDA[v.venda.etapa as keyof typeof ETAPAS_VENDA],
        v.formaPrincipal ? FORMAS_PAGAMENTO[v.formaPrincipal as keyof typeof FORMAS_PAGAMENTO] : "",
        dinheiro(v.veiculo.preco),
        dinheiro(v.venda.precoFinal),
        dinheiro(v.custoTotal),
        dinheiro(v.lucro),
        v.diasAteVender,
      ]),
    );
  } else if (tipo === "estoque") {
    const lista = await listarVeiculos({ incluirVendidos: true });
    conteudo = csv(
      ["Veículo", "Ano", "Placa", "Status", "Entrada", "Dias", "Km", "Custo", "Gastos", "Preço anunciado"],
      lista.map((v) => [nomeVeiculo(v), v.anoModelo, v.placa ?? "", STATUS_VEICULO[v.status as keyof typeof STATUS_VEICULO], dataBR(v.dataEntrada), v.dias, v.km ?? "", dinheiro(v.custo), dinheiro(v.totalGastos), dinheiro(v.preco)]),
    );
  } else if (tipo === "lancamentos") {
    const lista = await todosLancamentos();
    conteudo = csv(
      ["Vencimento", "Pago em", "Tipo", "Categoria", "Descrição", "Valor", "Situação"],
      lista
        .sort((a, b) => a.vencimento.localeCompare(b.vencimento))
        .map((l) => [dataBR(l.vencimento), l.pagoEm ? dataBR(l.pagoEm) : "", l.tipo === "entrada" ? "Entrada" : "Saída", l.categoria, l.descricao, dinheiro(l.valor), l.status]),
    );
  } else return new Response("Tipo inválido", { status: 400 });
  return new Response(conteudo, {
    headers: { "Content-Type": "text/csv; charset=utf-8", "Content-Disposition": `attachment; filename="carmelo-${tipo}-${hojeISO()}.csv"` },
  });
}
