import "server-only";
import fs from "node:fs/promises";
import path from "node:path";
import { PDFDocument, type PDFFont, type PDFPage, StandardFonts, rgb } from "pdf-lib";
import type { VendaCompleta } from "@/lib/consultas/vendas";
import type { DadosLoja } from "@/lib/consultas/configuracoes";
import { FORMAS_PAGAMENTO, type FormaPagamento, dataBR, hojeISO, reais } from "@/lib/dominio";
import { MARCA } from "@/lib/marca";

// Documentos da venda em PDF (A4), com o logo da loja e rodapé com os dados da loja.

const A4 = { w: 595.28, h: 841.89 };
const MARGEM = 56;
const LARANJA = rgb(1, 0.478, 0.102);
const CINZA = rgb(0.35, 0.37, 0.4);

type Ctx = { doc: PDFDocument; pagina: PDFPage; y: number; normal: PDFFont; negrito: PDFFont; loja: DadosLoja; logo: Awaited<ReturnType<PDFDocument["embedPng"]>> };

async function iniciar(loja: DadosLoja): Promise<Ctx> {
  const doc = await PDFDocument.create();
  const [normal, negrito, logo] = await Promise.all([
    doc.embedFont(StandardFonts.Helvetica),
    doc.embedFont(StandardFonts.HelveticaBold),
    doc.embedPng(await fs.readFile(path.join(process.cwd(), "public", MARCA.pasta, "logo-preta.png"))),
  ]);
  const ctx = { doc, pagina: null as unknown as PDFPage, y: 0, normal, negrito, loja, logo };
  novaPagina(ctx);
  return ctx;
}

function novaPagina(ctx: Ctx) {
  const p = ctx.doc.addPage([A4.w, A4.h]);
  const alturaLogo = 42;
  const larguraLogo = (ctx.logo.width / ctx.logo.height) * alturaLogo;
  p.drawImage(ctx.logo, { x: MARGEM, y: A4.h - 40 - alturaLogo, width: larguraLogo, height: alturaLogo });
  p.drawRectangle({ x: 0, y: A4.h - 100, width: A4.w, height: 3, color: LARANJA });
  const rodape = [ctx.loja.razaoSocial, ctx.loja.cnpj && `CNPJ ${ctx.loja.cnpj}`, `${ctx.loja.endereco} · ${ctx.loja.cidade}${ctx.loja.cep ? ` · CEP ${ctx.loja.cep}` : ""}`, ctx.loja.telefone]
    .filter(Boolean)
    .join("  ·  ");
  p.drawRectangle({ x: 0, y: 44, width: A4.w, height: 1, color: LARANJA });
  p.drawText(limpar(rodape), { x: MARGEM, y: 28, size: 8, font: ctx.normal, color: CINZA });
  ctx.pagina = p;
  ctx.y = A4.h - 130;
}

/** Remove caracteres fora do WinAnsi (fonte padrão do PDF) */
function limpar(t: string) {
  return t.replace(/[“”]/g, '"').replace(/[‘’]/g, "'").replace(/[→]/g, "->").replace(/[^\x20-\x7E\xA0-\xFF•–—]/g, "");
}

function quebrar(texto: string, fonte: PDFFont, tamanho: number, largura: number) {
  const linhas: string[] = [];
  for (const paragrafo of texto.split("\n").map(limpar)) {
    let atual = "";
    for (const palavra of paragrafo.split(" ")) {
      const teste = atual ? `${atual} ${palavra}` : palavra;
      if (fonte.widthOfTextAtSize(teste, tamanho) > largura && atual) {
        linhas.push(atual);
        atual = palavra;
      } else atual = teste;
    }
    linhas.push(atual);
  }
  return linhas;
}

function texto(ctx: Ctx, t: string, o: { tamanho?: number; negrito?: boolean; cor?: ReturnType<typeof rgb>; espaco?: number; centro?: boolean } = {}) {
  const tamanho = o.tamanho ?? 10;
  const fonte = o.negrito ? ctx.negrito : ctx.normal;
  const largura = A4.w - MARGEM * 2;
  for (const linha of quebrar(t, fonte, tamanho, largura)) {
    if (ctx.y < 80) novaPagina(ctx);
    const x = o.centro ? (A4.w - fonte.widthOfTextAtSize(linha, tamanho)) / 2 : MARGEM;
    ctx.pagina.drawText(linha, { x, y: ctx.y, size: tamanho, font: fonte, color: o.cor ?? rgb(0.08, 0.09, 0.1) });
    ctx.y -= tamanho * 1.45;
  }
  ctx.y -= o.espaco ?? 6;
}

function titulo(ctx: Ctx, t: string) {
  texto(ctx, t.toUpperCase(), { tamanho: 13, negrito: true, centro: true, espaco: 14 });
}

function secao(ctx: Ctx, t: string) {
  ctx.y -= 4;
  texto(ctx, t, { tamanho: 10.5, negrito: true, cor: rgb(0.78, 0.29, 0.05), espaco: 2 });
}

function assinaturas(ctx: Ctx, nomes: [string, string][]) {
  if (ctx.y < 150) novaPagina(ctx);
  ctx.y -= 38;
  const larg = (A4.w - MARGEM * 2 - 40) / 2;
  nomes.forEach(([nome, papel], i) => {
    const x = MARGEM + i * (larg + 40);
    ctx.pagina.drawLine({ start: { x, y: ctx.y }, end: { x: x + larg, y: ctx.y }, thickness: 0.8, color: CINZA });
    ctx.pagina.drawText(limpar(nome), { x, y: ctx.y - 14, size: 9, font: ctx.negrito });
    ctx.pagina.drawText(limpar(papel), { x, y: ctx.y - 26, size: 8, font: ctx.normal, color: CINZA });
  });
  ctx.y -= 34;
}

function dataExtenso(iso: string) {
  return new Date(iso + "T12:00:00").toLocaleDateString("pt-BR", { day: "numeric", month: "long", year: "numeric" });
}

function descreverVeiculo(v: VendaCompleta["veiculo"]) {
  return [
    `Marca/modelo: ${v.marca} ${v.modelo}${v.versao ? ` ${v.versao}` : ""}`,
    `Ano fabricação/modelo: ${v.anoFabricacao ?? v.anoModelo}/${v.anoModelo}`,
    `Cor: ${v.cor ?? "—"}   Combustível: ${v.combustivel}`,
    `Placa: ${v.placa ?? "—"}   Chassi: ${v.chassi ?? "—"}   RENAVAM: ${v.renavam ?? "—"}`,
    `Quilometragem na entrega: ${v.km !== null ? `${v.km.toLocaleString("pt-BR")} km` : "—"}`,
  ].join("\n");
}

function comprador(c: VendaCompleta["cliente"]) {
  return `${c.nome}, inscrito(a) no CPF/CNPJ ${c.cpf ?? "—"}, residente em ${c.endereco ?? "—"}, ${c.cidade ?? "—"}${c.telefone ? `, telefone ${c.telefone}` : ""}`;
}

function linhaPagamento(p: VendaCompleta["pagamentos"][number]) {
  const d = p.detalhes;
  const n = (k: string) => Number(d[k] ?? 0);
  const extra =
    p.forma === "financiamento_bancario"
      ? ` (${d.banco || "instituição financeira"}, ${n("parcelas")} parcelas, liberado pela financeira à vendedora)`
      : p.forma === "financiamento_proprio"
        ? ` (${n("parcelas")} parcelas mensais a partir de ${dataBR(String(d.primeiroVencimento ?? ""))}, juros de ${n("jurosMensalPct").toLocaleString("pt-BR")}% ao mês)`
        : p.forma === "troca"
          ? ` (${d.marca} ${d.modelo} ${d.ano ?? ""}${d.placa ? `, placa ${d.placa}` : ""}, recebido pelo valor de avaliação)`
          : p.forma === "cartao"
            ? ` (${n("parcelas")}x no cartão)`
            : p.forma === "cheque"
              ? ` (cheque nº ${d.numero || "—"}, ${d.banco || ""}, bom para ${dataBR(String(d.bomPara ?? ""))})`
              : p.forma === "consorcio"
                ? ` (carta de crédito ${d.administradora || ""})`
                : p.forma === "leasing"
                  ? ` (${d.instituicao || "arrendadora"})`
                  : "";
  return `• ${FORMAS_PAGAMENTO[p.forma as FormaPagamento]}: ${reais(p.valor)}${extra}`;
}

export async function gerarContrato(v: VendaCompleta, loja: DadosLoja) {
  const ctx = await iniciar(loja);
  titulo(ctx, "Contrato particular de compra e venda de veículo");
  secao(ctx, "1. Partes");
  texto(ctx, `VENDEDORA: ${loja.razaoSocial}${loja.cnpj ? `, CNPJ ${loja.cnpj}` : ""}, com sede em ${loja.endereco}, ${loja.cidade}.`);
  texto(ctx, `COMPRADOR(A): ${comprador(v.cliente)}.`);
  secao(ctx, "2. Objeto");
  texto(ctx, "A vendedora vende ao comprador o veículo abaixo, no estado em que se encontra, examinado e aprovado pelo comprador:");
  texto(ctx, descreverVeiculo(v.veiculo));
  secao(ctx, "3. Preço e forma de pagamento");
  texto(ctx, `O preço total é de ${reais(v.venda.precoFinal)}, pago da seguinte forma:`);
  texto(ctx, v.pagamentos.map(linhaPagamento).join("\n"));
  texto(ctx, "Parcelas ou valores não pagos no vencimento sofrerão multa de 2% e juros de 1% ao mês. A quitação total ocorre com a compensação de todos os valores.");
  secao(ctx, "4. Entrega, documentação e responsabilidades");
  texto(
    ctx,
    "4.1. O veículo é entregue nesta data, com a documentação necessária à transferência. 4.2. O comprador se compromete a transferir o veículo para o seu nome no prazo de 30 dias, conforme o art. 123 do Código de Trânsito Brasileiro, respondendo por multas, tributos e ocorrências a partir da entrega. 4.3. Débitos, multas e tributos anteriores à entrega são de responsabilidade da vendedora.",
  );
  secao(ctx, "5. Garantia");
  texto(ctx, "A vendedora concede garantia legal de 90 (noventa) dias para motor e câmbio, contados da entrega, nos termos do art. 26 do Código de Defesa do Consumidor, excluídos desgaste natural, mau uso e itens de manutenção.");
  secao(ctx, "6. Foro");
  texto(ctx, `As partes elegem o foro da comarca de ${loja.cidade.split("/")[0]} para resolver questões deste contrato.`);
  texto(ctx, `${loja.cidade.split("/")[0]}, ${dataExtenso(v.venda.dataVenda)}.`, { espaco: 10 });
  assinaturas(ctx, [
    [loja.razaoSocial, "Vendedora"],
    [v.cliente.nome, "Comprador(a)"],
  ]);
  assinaturas(ctx, [
    ["Testemunha 1", "Nome e CPF"],
    ["Testemunha 2", "Nome e CPF"],
  ]);
  return ctx.doc.save();
}

export async function gerarRecibo(v: VendaCompleta, loja: DadosLoja) {
  const ctx = await iniciar(loja);
  const recebidos = v.lancamentos.filter((l) => l.tipo === "entrada" && l.pagoEm);
  const troca = v.pagamentos.filter((p) => p.forma === "troca");
  const total = recebidos.reduce((s, l) => s + l.valor, 0) + troca.reduce((s, p) => s + p.valor, 0);
  titulo(ctx, "Recibo");
  texto(ctx, reais(total), { tamanho: 20, negrito: true, centro: true, espaco: 18 });
  texto(
    ctx,
    `Recebemos de ${v.cliente.nome}${v.cliente.cpf ? ` (CPF/CNPJ ${v.cliente.cpf})` : ""} a quantia de ${reais(total)}, referente à compra do veículo ${v.veiculo.marca} ${v.veiculo.modelo} ${v.veiculo.anoModelo}${v.veiculo.placa ? `, placa ${v.veiculo.placa}` : ""}, conforme discriminado abaixo:`,
    { espaco: 10 },
  );
  texto(
    ctx,
    [
      ...recebidos.map((l) => `• ${dataBR(l.pagoEm)}: ${l.descricao.split(":")[0]} - ${reais(l.valor)}`),
      ...troca.map((p) => `• Veículo recebido na troca (${p.detalhes.marca} ${p.detalhes.modelo} ${p.detalhes.ano ?? ""}) - ${reais(p.valor)}`),
    ].join("\n") || "Nenhum valor recebido até o momento.",
  );
  const falta = v.venda.precoFinal - total;
  if (falta > 0) texto(ctx, `Saldo a receber: ${reais(falta)}, conforme contrato.`, { negrito: true });
  else texto(ctx, "Valor total do veículo quitado.", { negrito: true });
  texto(ctx, `${loja.cidade.split("/")[0]}, ${dataExtenso(hojeISO())}.`, { espaco: 10 });
  assinaturas(ctx, [[loja.razaoSocial, "Recebedora"], ["", ""]].slice(0, 1) as [string, string][]);
  return ctx.doc.save();
}

export async function gerarGarantia(v: VendaCompleta, loja: DadosLoja) {
  const ctx = await iniciar(loja);
  titulo(ctx, "Termo de garantia");
  texto(ctx, `Veículo: ${v.veiculo.marca} ${v.veiculo.modelo} ${v.veiculo.versao ?? ""} ${v.veiculo.anoModelo}${v.veiculo.placa ? ` · placa ${v.veiculo.placa}` : ""}`);
  texto(ctx, `Comprador(a): ${v.cliente.nome}`);
  texto(ctx, `Data da entrega: ${dataBR(v.venda.dataVenda)}   ·   Garantia até: ${dataBR(new Date(new Date(v.venda.dataVenda + "T12:00:00").getTime() + 90 * 86_400_000).toISOString().slice(0, 10))}`, { espaco: 12 });
  secao(ctx, "Cobertura");
  texto(ctx, "Motor (bloco, cabeçote, virabrequim, bielas, pistões e bomba de óleo) e câmbio (caixa de marchas e diferencial), por 90 dias a contar da entrega.");
  secao(ctx, "Não cobre");
  texto(ctx, "Itens de desgaste natural (embreagem, freios, pneus, bateria, suspensão, velas, correias, filtros e fluidos), parte elétrica, acessórios, estética, danos por mau uso, falta de manutenção, uso em competição ou reparos feitos fora da loja sem autorização.");
  secao(ctx, "Como acionar");
  texto(ctx, `Procure a loja pelo telefone ${loja.telefone} antes de qualquer reparo. O veículo deve ser apresentado para avaliação em ${loja.endereco}, ${loja.cidade}.`);
  assinaturas(ctx, [
    [loja.razaoSocial, "Vendedora"],
    [v.cliente.nome, "Comprador(a)"],
  ]);
  return ctx.doc.save();
}

export async function gerarChecklistEntrega(v: VendaCompleta, loja: DadosLoja) {
  const ctx = await iniciar(loja);
  titulo(ctx, "Checklist de entrega do veículo");
  texto(ctx, `${v.veiculo.marca} ${v.veiculo.modelo} ${v.veiculo.anoModelo}${v.veiculo.placa ? ` · placa ${v.veiculo.placa}` : ""} · comprador(a): ${v.cliente.nome}`, { espaco: 12 });
  const itens = [
    "Documento (CRLV) e recibo/ATPV-e para transferência",
    "Manual do proprietário",
    "Chave principal e chave reserva",
    "Estepe, macaco, chave de roda e triângulo",
    "Revisão/lavagem realizada",
    "Nível de combustível conferido",
    "Pneus e calibragem conferidos",
    "Luzes, setas e buzina funcionando",
    "Ar-condicionado e vidros elétricos funcionando",
    "Quilometragem registrada na entrega: ________ km",
    "Cliente orientado sobre garantia e transferência em 30 dias",
  ];
  for (const item of itens) {
    if (ctx.y < 100) novaPagina(ctx);
    ctx.pagina.drawRectangle({ x: MARGEM, y: ctx.y - 2, width: 10, height: 10, borderColor: CINZA, borderWidth: 0.8 });
    ctx.pagina.drawText(limpar(item), { x: MARGEM + 18, y: ctx.y, size: 10, font: ctx.normal });
    ctx.y -= 22;
  }
  texto(ctx, "Observações: ____________________________________________________________________________", { espaco: 4 });
  texto(ctx, `Entregue em ___/___/______ às ___:___.`);
  assinaturas(ctx, [
    [loja.razaoSocial, "Entregou"],
    [v.cliente.nome, "Recebeu o veículo"],
  ]);
  return ctx.doc.save();
}
