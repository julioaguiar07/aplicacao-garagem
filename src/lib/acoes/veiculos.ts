"use server";

import { and, asc, eq, isNull } from "drizzle-orm";
import { redirect } from "next/navigation";
import { banco, schema } from "@/db";
import { exigirLogin } from "@/lib/auth";
import { apagarArquivo, salvarArquivo } from "@/lib/armazenamento";
import { processarFoto, reenquadrar } from "@/lib/fotos";
import { CATEGORIAS_GASTO, ORIGEM_VEICULO, STATUS_VEICULO, hojeISO, paraCentavos, reais, slugify } from "@/lib/dominio";
import { type Resultado, arquivos, atualizarTelas, inteiro, paraBuffer, registrarEvento, texto } from "./comum";

const { veiculos, fotos, documentos, gastos, lancamentos, vendas } = schema;

const TIPOS_ARQUIVO_DOC = ["application/pdf", "image/jpeg", "image/png", "image/webp"];
const MAX_DOC = 15 * 1024 * 1024;

function lerDadosVeiculo(form: FormData) {
  const marca = texto(form, "marca");
  const modelo = texto(form, "modelo");
  const anoModelo = inteiro(form, "anoModelo");
  const custo = paraCentavos(texto(form, "custo"));
  const preco = paraCentavos(texto(form, "preco"));
  const erros: string[] = [];
  if (!marca) erros.push("marca");
  if (!modelo) erros.push("modelo");
  if (!anoModelo || anoModelo < 1950 || anoModelo > new Date().getFullYear() + 2) erros.push("ano");
  if (custo === null) erros.push("custo");
  if (!preco) erros.push("preço anunciado");
  const origem = (texto(form, "origem") ?? "compra") as keyof typeof ORIGEM_VEICULO;
  return {
    erros,
    dados: {
      marca: marca!,
      modelo: modelo!,
      versao: texto(form, "versao"),
      anoModelo: anoModelo!,
      anoFabricacao: inteiro(form, "anoFabricacao"),
      cor: texto(form, "cor"),
      km: inteiro(form, "km"),
      categoria: texto(form, "categoria") ?? "Hatch",
      cambio: texto(form, "cambio") ?? "Manual",
      combustivel: texto(form, "combustivel") ?? "Flex",
      portas: inteiro(form, "portas"),
      placa: texto(form, "placa")?.toUpperCase().replace(/[^A-Z0-9]/g, "") ?? null,
      chassi: texto(form, "chassi")?.toUpperCase() ?? null,
      renavam: texto(form, "renavam"),
      opcionais: form.getAll("opcionais").map(String),
      destaques: form.getAll("destaques").map(String),
      descricao: texto(form, "descricao"),
      origem: origem in ORIGEM_VEICULO ? origem : "compra",
      fornecedor: texto(form, "fornecedor"),
      dataEntrada: texto(form, "dataEntrada") ?? hojeISO(),
      custo: custo ?? 0,
      preco: preco ?? 0,
      descontoMaximoPct: Number(texto(form, "descontoMaximoPct")?.replace(",", ".") ?? 5) || 0,
      precoFipe: paraCentavos(texto(form, "precoFipe")),
      codigoFipe: texto(form, "codigoFipe"),
    },
  };
}

async function slugUnico(base: string, id?: number) {
  const db = await banco();
  let slug = base;
  for (let i = 2; ; i++) {
    const [existe] = await db.select({ id: veiculos.id }).from(veiculos).where(eq(veiculos.slug, slug));
    if (!existe || existe.id === id) return slug;
    slug = `${base}-${i}`;
  }
}

export async function cadastrarVeiculo(_: Resultado<number> | null, form: FormData): Promise<Resultado<number>> {
  await exigirLogin();
  const { erros, dados } = lerDadosVeiculo(form);
  if (erros.length) return { ok: false, erro: `Preencha: ${erros.join(", ")}.` };
  const fotosEnviadas = arquivos(form, "fotos");
  const publicar = form.get("publicado") === "on";
  const db = await banco();

  const status = fotosEnviadas.length === 0 ? "rascunho" : dados.origem === "consignacao" ? "consignado" : (texto(form, "status") ?? "disponivel");
  const [novo] = await db
    .insert(veiculos)
    .values({ ...dados, slug: "tmp-" + Date.now(), status, publicado: publicar && fotosEnviadas.length > 0 })
    .returning({ id: veiculos.id });
  const slug = await slugUnico(slugify(`${dados.marca} ${dados.modelo} ${dados.versao ?? ""} ${dados.anoModelo}`), novo.id);
  await db.update(veiculos).set({ slug }).where(eq(veiculos.id, novo.id));

  // Se alguma foto não puder ser lida, desfaz o cadastro para não sobrar carro pela metade
  const salvas: { chaveOriginal: string; chaveCard: string }[] = [];
  try {
    for (const [ordem, f] of fotosEnviadas.entries()) {
      const p = await processarFoto(novo.id, await paraBuffer(f));
      salvas.push(p);
      await db.insert(fotos).values({ veiculoId: novo.id, ...p, ordem });
    }
  } catch {
    await db.delete(veiculos).where(eq(veiculos.id, novo.id));
    for (const s of salvas) await Promise.all([apagarArquivo(s.chaveOriginal), apagarArquivo(s.chaveCard)]);
    return { ok: false, erro: "Não consegui ler uma das fotos. Envie em JPG, PNG ou WebP e tente de novo." };
  }

  // Documentos enviados no cadastro (campo doc_<índice> + tipo_<índice>)
  for (const [i, f] of arquivos(form, "documentos").entries()) {
    const tipo = texto(form, `tipoDocumento_${i}`) ?? "Outro";
    if (!TIPOS_ARQUIVO_DOC.includes(f.type) || f.size > MAX_DOC) continue;
    const chave = await salvarArquivo(`privado/veiculos/${novo.id}`, f.name, await paraBuffer(f));
    await db.insert(documentos).values({ veiculoId: novo.id, tipo, nomeArquivo: f.name, chave, mime: f.type, tamanho: f.size });
  }

  // Compra no caixa (não se aplica a consignação nem troca)
  if (form.get("lancarCompra") === "on" && dados.custo > 0 && (dados.origem === "compra" || dados.origem === "leilao")) {
    const pago = form.get("compraPaga") === "on";
    await db.insert(lancamentos).values({
      tipo: "saida",
      descricao: `Compra: ${dados.marca} ${dados.modelo} ${dados.anoModelo}`,
      categoria: "Compra de veículo",
      valor: dados.custo,
      vencimento: texto(form, "vencimentoCompra") ?? dados.dataEntrada,
      pagoEm: pago ? (texto(form, "vencimentoCompra") ?? dados.dataEntrada) : null,
      contaId: inteiro(form, "contaCompra"),
      veiculoId: novo.id,
    });
  }

  await registrarEvento({ veiculoId: novo.id, titulo: "Veículo cadastrado", detalhe: ORIGEM_VEICULO[dados.origem] });
  atualizarTelas();
  redirect(`/painel/estoque/${novo.id}`);
}

export async function editarVeiculo(id: number, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const { erros, dados } = lerDadosVeiculo(form);
  if (erros.length) return { ok: false, erro: `Preencha: ${erros.join(", ")}.` };
  const db = await banco();
  const [antes] = await db.select().from(veiculos).where(eq(veiculos.id, id));
  if (!antes) return { ok: false, erro: "Veículo não encontrado." };
  const slug = await slugUnico(slugify(`${dados.marca} ${dados.modelo} ${dados.versao ?? ""} ${dados.anoModelo}`), id);
  await db.update(veiculos).set({ ...dados, slug, atualizadoEm: new Date() }).where(eq(veiculos.id, id));
  const mudancas: string[] = [];
  if (antes.preco !== dados.preco) mudancas.push(`preço ${reais(antes.preco)} → ${reais(dados.preco)}`);
  if (antes.km !== dados.km) mudancas.push("quilometragem");
  await registrarEvento({ veiculoId: id, titulo: antes.preco !== dados.preco ? "Preço alterado" : "Dados atualizados", detalhe: mudancas.join(" · ") || undefined });
  atualizarTelas();
  redirect(`/painel/estoque/${id}`);
}

/** Status que o usuário pode definir à mão (reservado/vendido vêm das vendas) */
export async function alterarStatus(id: number, status: string): Promise<Resultado> {
  await exigirLogin();
  if (!["disponivel", "em_preparacao", "consignado", "rascunho"].includes(status)) return { ok: false, erro: "Esse status é definido pela venda." };
  const db = await banco();
  const [v] = await db.select().from(veiculos).where(eq(veiculos.id, id));
  if (!v) return { ok: false, erro: "Veículo não encontrado." };
  if (v.status === "vendido" || v.status === "reservado") return { ok: false, erro: "Este carro está numa venda. Mude pela venda." };
  await db.update(veiculos).set({ status, publicado: status === "rascunho" ? false : v.publicado }).where(eq(veiculos.id, id));
  await registrarEvento({ veiculoId: id, titulo: `Status: ${STATUS_VEICULO[status as keyof typeof STATUS_VEICULO]}` });
  atualizarTelas();
  return { ok: true };
}

export async function alternarPublicado(id: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [v] = await db.select().from(veiculos).where(eq(veiculos.id, id));
  if (!v) return { ok: false, erro: "Veículo não encontrado." };
  if (!v.publicado) {
    const [capa] = await db.select({ id: fotos.id }).from(fotos).where(eq(fotos.veiculoId, id));
    if (!capa) return { ok: false, erro: "Envie ao menos uma foto antes de publicar." };
    if (v.status === "vendido" || v.status === "rascunho") return { ok: false, erro: "Carro vendido ou em rascunho não vai para a vitrine." };
  }
  await db.update(veiculos).set({ publicado: !v.publicado }).where(eq(veiculos.id, id));
  await registrarEvento({ veiculoId: id, titulo: v.publicado ? "Retirado da vitrine" : "Publicado na vitrine" });
  atualizarTelas();
  return { ok: true };
}

export async function excluirVeiculo(id: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [venda] = await db.select({ id: vendas.id }).from(vendas).where(eq(vendas.veiculoId, id));
  if (venda) return { ok: false, erro: "Este carro tem venda registrada. Cancele a venda antes de excluir." };
  const arquivosFotos = await db.select().from(fotos).where(eq(fotos.veiculoId, id));
  const arquivosDocs = await db.select().from(documentos).where(eq(documentos.veiculoId, id));
  // Lançamentos do carro que ainda não foram pagos saem junto; os pagos ficam no caixa sem vínculo
  await db.delete(lancamentos).where(and(eq(lancamentos.veiculoId, id), isNull(lancamentos.pagoEm)));
  await db.delete(veiculos).where(eq(veiculos.id, id));
  for (const f of arquivosFotos) await Promise.all([apagarArquivo(f.chaveCard), apagarArquivo(f.chaveOriginal)]);
  for (const d of arquivosDocs) await apagarArquivo(d.chave);
  atualizarTelas();
  redirect("/painel/estoque");
}

// ---------- fotos ----------

export async function adicionarFotos(id: number, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const lista = arquivos(form, "fotos");
  if (!lista.length) return { ok: false, erro: "Escolha ao menos uma foto." };
  const db = await banco();
  const existentes = await db.select({ ordem: fotos.ordem }).from(fotos).where(eq(fotos.veiculoId, id));
  let ordem = existentes.reduce((m, f) => Math.max(m, f.ordem + 1), 0);
  for (const f of lista) {
    if (!f.type.startsWith("image/")) continue;
    const p = await processarFoto(id, await paraBuffer(f));
    await db.insert(fotos).values({ veiculoId: id, ...p, ordem: ordem++ });
  }
  const [v] = await db.select().from(veiculos).where(eq(veiculos.id, id));
  if (v?.status === "rascunho") await db.update(veiculos).set({ status: v.origem === "consignacao" ? "consignado" : "disponivel" }).where(eq(veiculos.id, id));
  await registrarEvento({ veiculoId: id, titulo: `${lista.length} foto${lista.length > 1 ? "s" : ""} adicionada${lista.length > 1 ? "s" : ""}` });
  atualizarTelas();
  return { ok: true };
}

export async function removerFoto(fotoId: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [f] = await db.delete(fotos).where(eq(fotos.id, fotoId)).returning();
  if (!f) return { ok: false, erro: "Foto não encontrada." };
  await Promise.all([apagarArquivo(f.chaveCard), apagarArquivo(f.chaveOriginal)]);
  const restantes = await db.select({ id: fotos.id }).from(fotos).where(eq(fotos.veiculoId, f.veiculoId));
  if (!restantes.length) await db.update(veiculos).set({ publicado: false }).where(eq(veiculos.id, f.veiculoId));
  atualizarTelas();
  return { ok: true };
}

export async function definirCapa(fotoId: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [f] = await db.select().from(fotos).where(eq(fotos.id, fotoId));
  if (!f) return { ok: false, erro: "Foto não encontrada." };
  const todas = await db.select().from(fotos).where(eq(fotos.veiculoId, f.veiculoId)).orderBy(asc(fotos.ordem), asc(fotos.id));
  const ordenadas = [f, ...todas.filter((x) => x.id !== f.id)];
  for (const [ordem, x] of ordenadas.entries()) await db.update(fotos).set({ ordem }).where(eq(fotos.id, x.id));
  atualizarTelas();
  return { ok: true };
}

export async function reenquadrarFoto(fotoId: number, focoY: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [f] = await db.select().from(fotos).where(eq(fotos.id, fotoId));
  if (!f) return { ok: false, erro: "Foto não encontrada." };
  const foco = Math.min(1, Math.max(0, focoY));
  const chaveCard = await reenquadrar(f.veiculoId, f.chaveOriginal, foco);
  await db.update(fotos).set({ chaveCard, focoY: foco }).where(eq(fotos.id, fotoId));
  await apagarArquivo(f.chaveCard);
  atualizarTelas();
  return { ok: true };
}

// ---------- documentos ----------

export async function enviarDocumento(veiculoId: number, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const [arquivo] = arquivos(form, "arquivo");
  const tipo = texto(form, "tipo") === "__outro" ? texto(form, "tipoOutro") : texto(form, "tipo");
  if (!arquivo) return { ok: false, erro: "Escolha o arquivo." };
  if (!tipo) return { ok: false, erro: "Informe o tipo do documento." };
  if (!TIPOS_ARQUIVO_DOC.includes(arquivo.type)) return { ok: false, erro: "Envie PDF, JPG, PNG ou WebP." };
  if (arquivo.size > MAX_DOC) return { ok: false, erro: "Arquivo acima de 15 MB." };
  const db = await banco();
  const chave = await salvarArquivo(`privado/veiculos/${veiculoId}`, arquivo.name, await paraBuffer(arquivo));
  await db.insert(documentos).values({ veiculoId, tipo, nomeArquivo: arquivo.name, chave, mime: arquivo.type, tamanho: arquivo.size, validade: texto(form, "validade") });
  await registrarEvento({ veiculoId, titulo: `${tipo} anexado` });
  atualizarTelas();
  return { ok: true, mensagem: `${tipo} enviado.` };
}

export async function removerDocumento(id: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [d] = await db.delete(documentos).where(eq(documentos.id, id)).returning();
  if (d) await apagarArquivo(d.chave);
  atualizarTelas();
  return { ok: true };
}

// ---------- gastos ----------

export async function lancarGasto(veiculoId: number, _: Resultado | null, form: FormData): Promise<Resultado> {
  await exigirLogin();
  const descricao = texto(form, "descricao");
  const valor = paraCentavos(texto(form, "valor"));
  const data = texto(form, "data") ?? hojeISO();
  const categoria = texto(form, "categoria") ?? "Outros";
  if (!descricao) return { ok: false, erro: "Descreva o gasto." };
  if (!valor) return { ok: false, erro: "Informe o valor." };
  if (!(CATEGORIAS_GASTO as readonly string[]).includes(categoria)) return { ok: false, erro: "Categoria inválida." };
  const db = await banco();
  const [v] = await db.select().from(veiculos).where(eq(veiculos.id, veiculoId));
  if (!v) return { ok: false, erro: "Veículo não encontrado." };
  const [nota] = arquivos(form, "nota");
  const notaChave = nota ? await salvarArquivo(`privado/veiculos/${veiculoId}/notas`, nota.name, await paraBuffer(nota)) : null;
  const pago = form.get("pago") === "on";
  const [lanc] = await db
    .insert(lancamentos)
    .values({
      tipo: "saida",
      descricao: `${descricao} (${v.modelo} ${v.anoModelo})`,
      categoria: "Preparação de veículo",
      valor,
      vencimento: data,
      pagoEm: pago ? data : null,
      contaId: inteiro(form, "contaId"),
      veiculoId,
      comprovanteChave: notaChave,
    })
    .returning({ id: lancamentos.id });
  await db.insert(gastos).values({ veiculoId, data, categoria, descricao, valor, notaChave, lancamentoId: lanc.id });
  await registrarEvento({ veiculoId, titulo: "Gasto lançado", detalhe: `${descricao} · ${reais(valor)}` });
  atualizarTelas();
  return { ok: true, mensagem: "Gasto lançado e enviado ao caixa." };
}

export async function removerGasto(id: number): Promise<Resultado> {
  await exigirLogin();
  const db = await banco();
  const [g] = await db.delete(gastos).where(eq(gastos.id, id)).returning();
  if (!g) return { ok: false, erro: "Gasto não encontrado." };
  if (g.lancamentoId) await db.delete(lancamentos).where(eq(lancamentos.id, g.lancamentoId));
  await apagarArquivo(g.notaChave);
  await registrarEvento({ veiculoId: g.veiculoId, titulo: "Gasto removido", detalhe: `${g.descricao} · ${reais(g.valor)}` });
  atualizarTelas();
  return { ok: true };
}

