import type { FotoVeiculo, Veiculo } from "@/lib/tipos";
import { VEICULOS } from "@/lib/demo/veiculos";
import { parcelaPrice } from "@/lib/formato";

/**
 * Dados que podem ir para o navegador na vitrine pública.
 * Custo, preço mínimo, placa, chassi, RENAVAM, fornecedor e documentos nunca saem do servidor.
 */
export interface VeiculoPublico {
  slug: string;
  marca: string;
  modelo: string;
  versao?: string;
  ano: number;
  km: number;
  cor: string;
  categoria: string;
  cambio: string;
  combustivel: string;
  portas: number;
  preco: number;
  parcela: number;
  destaques: string[];
  opcionais: string[];
  descricao?: string;
  foto?: FotoVeiculo;
  fotos: FotoVeiculo[];
  cadastradoEm: string;
}

export const LOJA = {
  nome: "Carmelo Multimarcas",
  whatsapp: "558430622434",
  telefone: "(84) 3062-2434",
  endereco: "Rua José Damião, 61",
  cidade: "Mossoró/RN",
  cep: "59619-140",
};

/** Premissas da simulação exibida na vitrine (ajustáveis nas Configurações) */
export const SIMULACAO = { entradaPct: 30, taxaMensalPct: 1.99, meses: 48 };

export function paraPublico(v: Veiculo): VeiculoPublico {
  const financiado = v.preco * (1 - SIMULACAO.entradaPct / 100);
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
    parcela: parcelaPrice(financiado, SIMULACAO.taxaMensalPct, SIMULACAO.meses),
    destaques: v.destaques,
    opcionais: v.opcionais,
    descricao: v.descricao,
    foto: v.fotos.find((f) => f.capa) ?? v.fotos[0],
    fotos: v.fotos,
    cadastradoEm: v.cadastradoEm,
  };
}

export function veiculosPublicados(): VeiculoPublico[] {
  return VEICULOS.filter((v) => v.publicado && (v.status === "disponivel" || v.status === "reservado")).map(paraPublico);
}

export function linkWhatsapp(texto: string) {
  return `https://wa.me/${LOJA.whatsapp}?text=${encodeURIComponent(texto)}`;
}
