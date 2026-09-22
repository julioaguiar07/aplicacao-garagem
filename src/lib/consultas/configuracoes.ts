import "server-only";
import { eq } from "drizzle-orm";
import { banco, schema } from "@/db";

export interface DadosLoja {
  whatsapp: string;
  telefone: string;
  endereco: string;
  cidade: string;
  cep: string;
  cnpj: string;
  razaoSocial: string;
  simulacao: { entradaPct: number; taxaMensalPct: number; meses: number };
}

export const LOJA_PADRAO: DadosLoja = {
  whatsapp: "5584986913666",
  telefone: "(84) 98691-3666",
  endereco: "Rua José Damião, 61",
  cidade: "Mossoró/RN",
  cep: "59619-140",
  cnpj: "",
  razaoSocial: "Carmelo Multimarcas",
  simulacao: { entradaPct: 30, taxaMensalPct: 1.99, meses: 48 },
};

export async function dadosLoja(): Promise<DadosLoja> {
  const db = await banco();
  const [linha] = await db.select().from(schema.configuracoes).where(eq(schema.configuracoes.chave, "loja"));
  return { ...LOJA_PADRAO, ...((linha?.valor as Partial<DadosLoja>) ?? {}) };
}
