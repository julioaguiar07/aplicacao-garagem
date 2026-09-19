import "server-only";
import { and, asc, eq, inArray } from "drizzle-orm";
import { banco, schema } from "@/db";
import { urlArquivo } from "@/lib/armazenamento";
import { dadosLoja, type DadosLoja } from "@/lib/consultas/configuracoes";
import { parcelaPrice } from "@/lib/dominio";

/**
 * Dados que podem ir para o navegador na vitrine pública.
 * Custo, preço mínimo, placa, chassi, RENAVAM, fornecedor e documentos nunca saem do servidor.
 */
export interface VeiculoPublico {
  slug: string;
  marca: string;
  modelo: string;
  versao: string | null;
  ano: number;
  km: number | null;
  cor: string | null;
  categoria: string;
  cambio: string;
  combustivel: string;
  portas: number | null;
  preco: number; // centavos
  parcela: number; // centavos
  reservado: boolean;
  destaques: string[];
  opcionais: string[];
  descricao: string | null;
  capa: string | null;
  fotos: { card: string; original: string }[];
  entrada: string;
}

export async function vitrine(): Promise<{ veiculos: VeiculoPublico[]; loja: DadosLoja }> {
  const db = await banco();
  const [loja, lista] = await Promise.all([
    dadosLoja(),
    db
      .select()
      .from(schema.veiculos)
      .where(and(eq(schema.veiculos.publicado, true), inArray(schema.veiculos.status, ["disponivel", "consignado", "reservado"]))),
  ]);
  const ids = lista.map((v) => v.id);
  const fotos = ids.length ? await db.select().from(schema.fotos).where(inArray(schema.fotos.veiculoId, ids)).orderBy(asc(schema.fotos.ordem), asc(schema.fotos.id)) : [];
  const { entradaPct, taxaMensalPct, meses } = loja.simulacao;
  const veiculos = lista
    .map((v) => {
      const doCarro = fotos.filter((f) => f.veiculoId === v.id).map((f) => ({ card: urlArquivo(f.chaveCard), original: urlArquivo(f.chaveOriginal) }));
      return {
        slug: v.slug,
        marca: v.marca,
        modelo: v.modelo,
        versao: v.versao,
        ano: v.anoModelo,
        km: v.km,
        cor: v.cor,
        categoria: v.categoria,
        cambio: v.cambio,
        combustivel: v.combustivel,
        portas: v.portas,
        preco: v.preco,
        parcela: parcelaPrice(Math.round(v.preco * (1 - entradaPct / 100)), taxaMensalPct, meses),
        reservado: v.status === "reservado",
        destaques: v.destaques,
        opcionais: v.opcionais,
        descricao: v.descricao,
        capa: doCarro[0]?.card ?? null,
        fotos: doCarro,
        entrada: v.dataEntrada,
      };
    })
    .filter((v) => v.capa)
    .sort((a, b) => Number(a.reservado) - Number(b.reservado) || b.entrada.localeCompare(a.entrada));
  return { veiculos, loja };
}

export function linkWhatsapp(numero: string, texto: string) {
  return `https://wa.me/${numero}?text=${encodeURIComponent(texto)}`;
}
