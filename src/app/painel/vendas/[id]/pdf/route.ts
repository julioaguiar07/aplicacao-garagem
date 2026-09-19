import { exigirLogin } from "@/lib/auth";
import { vendaCompleta } from "@/lib/consultas/vendas";
import { dadosLoja } from "@/lib/consultas/configuracoes";
import { gerarChecklistEntrega, gerarContrato, gerarGarantia, gerarRecibo } from "@/lib/pdf";
import { slugify } from "@/lib/dominio";

const GERADORES = { contrato: gerarContrato, recibo: gerarRecibo, garantia: gerarGarantia, entrega: gerarChecklistEntrega };

export async function GET(req: Request, { params }: RouteContext<"/painel/vendas/[id]/pdf">) {
  await exigirLogin();
  const tipo = new URL(req.url).searchParams.get("tipo") as keyof typeof GERADORES;
  const gerar = GERADORES[tipo];
  if (!gerar) return new Response("Documento inválido", { status: 400 });
  const venda = await vendaCompleta(Number((await params).id));
  if (!venda) return new Response("Venda não encontrada", { status: 404 });
  const pdf = await gerar(venda, await dadosLoja());
  const nome = `${tipo}-${slugify(`${venda.veiculo.modelo}-${venda.cliente.nome}`)}.pdf`;
  return new Response(new Uint8Array(pdf), {
    headers: { "Content-Type": "application/pdf", "Content-Disposition": `inline; filename="${nome}"` },
  });
}
