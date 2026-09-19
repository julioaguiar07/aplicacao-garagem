import { and, eq, ne } from "drizzle-orm";
import { z } from "zod";
import { banco, schema } from "@/db";
import { registrarEvento } from "./eventos";
import { ETAPAS_VENDA, ETAPAS_VENDIDO, FORMAS_PAGAMENTO, TIPOS_CUSTO_VENDA, type EtapaVenda, parcelaPrice, reais, slugify, somarDias, somarMeses } from "@/lib/dominio";

// Núcleo da venda: grava venda, pagamentos, custos, contas a receber/pagar, troca e status do carro.
// Usado pela tela de nova venda e pela carga de demonstração.

const { vendas, veiculos, clientes, pagamentos, custosVenda, lancamentos } = schema;

const data = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const centavos = z.number().int().nonnegative();

export const esquemaVenda = z.object({
  veiculoId: z.number().int(),
  cliente: z.union([
    z.object({ id: z.number().int() }),
    z.object({ novo: z.object({ nome: z.string().trim().min(2), telefone: z.string().trim().optional(), cpf: z.string().trim().optional(), origem: z.string().optional() }) }),
  ]),
  precoFinal: centavos.min(1),
  dataVenda: data,
  etapa: z.enum(Object.keys(ETAPAS_VENDA) as [EtapaVenda, ...EtapaVenda[]]),
  observacoes: z.string().optional(),
  pagamentos: z
    .array(
      z.object({
        forma: z.enum(Object.keys(FORMAS_PAGAMENTO) as [keyof typeof FORMAS_PAGAMENTO, ...(keyof typeof FORMAS_PAGAMENTO)[]]),
        valor: centavos.min(1),
        detalhes: z.record(z.string(), z.union([z.string(), z.number(), z.boolean(), z.null()])),
      }),
    )
    .min(1, "Adicione ao menos uma forma de pagamento."),
  custos: z.array(z.object({ tipo: z.enum(Object.keys(TIPOS_CUSTO_VENDA) as [string, ...string[]]), descricao: z.string().optional(), valor: centavos.min(1) })),
});
export type NovaVenda = z.infer<typeof esquemaVenda>;

type Det = Record<string, string | number | boolean | null>;
const num = (d: Det, k: string, padrao = 0) => (d[k] === null || d[k] === undefined || d[k] === "" ? padrao : Number(d[k]));
const str = (d: Det, k: string, padrao: string) => (typeof d[k] === "string" && d[k] ? String(d[k]) : padrao);


/** Grava a venda completa; devolve o id ou uma mensagem de erro para o usuário */
export async function registrarVenda(entrada: NovaVenda): Promise<{ ok: true; id: number } | { ok: false; erro: string }> {
  const soma = entrada.pagamentos.reduce((s, p) => s + p.valor, 0);
  if (soma !== entrada.precoFinal) {
    const dif = entrada.precoFinal - soma;
    return { ok: false, erro: dif > 0 ? `Faltam ${reais(dif)} nas formas de pagamento.` : `As formas de pagamento passam ${reais(-dif)} do preço final.` };
  }
  const db = await banco();
  const [veiculo] = await db.select().from(veiculos).where(eq(veiculos.id, entrada.veiculoId));
  if (!veiculo) return { ok: false as const, erro: "Veículo não encontrado." };
  const [ativa] = await db.select({ id: vendas.id }).from(vendas).where(and(eq(vendas.veiculoId, veiculo.id), ne(vendas.etapa, "cancelada")));
  if (ativa) return { ok: false as const, erro: "Este carro já está numa venda em andamento." };

  // Cliente
  let clienteId: number;
  if ("id" in entrada.cliente) clienteId = entrada.cliente.id;
  else {
    const n = entrada.cliente.novo;
    const [c] = await db.insert(clientes).values({ nome: n.nome, telefone: n.telefone || null, cpf: n.cpf || null, origem: n.origem || null }).returning({ id: clientes.id });
    clienteId = c.id;
    await registrarEvento({ clienteId, titulo: "Cliente cadastrado na venda" });
  }

  const [venda] = await db
    .insert(vendas)
    .values({ veiculoId: veiculo.id, clienteId, etapa: entrada.etapa, precoFinal: entrada.precoFinal, dataVenda: entrada.dataVenda, observacoes: entrada.observacoes || null })
    .returning();
  const nome = `${veiculo.modelo} ${veiculo.anoModelo}`;
  const d0 = entrada.dataVenda;

  for (const p of entrada.pagamentos) {
    const det = { ...p.detalhes } as Det;
    const receber = async (valor: number, vencimento: string, categoria: string, desc: string, extra: Partial<typeof lancamentos.$inferInsert> = {}) => {
      await db.insert(lancamentos).values({ tipo: "entrada", descricao: desc, categoria, valor, vencimento, vendaId: venda.id, clienteId, veiculoId: veiculo.id, ...extra });
    };

    // Troca: o carro do cliente entra no estoque com o valor de avaliação como custo
    if (p.forma === "troca") {
      const marca = str(det, "marca", "Veículo");
      const modelo = str(det, "modelo", "na troca");
      const ano = num(det, "ano", new Date().getFullYear());
      const [novoCarro] = await db
        .insert(veiculos)
        .values({
          slug: `troca-${venda.id}-${Date.now()}`,
          marca,
          modelo,
          versao: typeof det.versao === "string" ? det.versao : null,
          anoModelo: ano,
          km: det.km ? num(det, "km") : null,
          cor: typeof det.cor === "string" ? det.cor : null,
          placa: typeof det.placa === "string" ? det.placa.toUpperCase() : null,
          status: "em_preparacao",
          origem: "troca",
          clienteOrigemId: clienteId,
          dataEntrada: d0,
          custo: p.valor,
          preco: Math.round(p.valor * 1.15),
        })
        .returning({ id: veiculos.id });
      await db.update(veiculos).set({ slug: `${slugify(`${marca} ${modelo} ${ano}`)}-${novoCarro.id}` }).where(eq(veiculos.id, novoCarro.id));
      det.veiculoTrocaId = novoCarro.id;
      await registrarEvento({ veiculoId: novoCarro.id, titulo: "Entrou como troca", detalhe: `Na venda do ${nome}` });
    }

    const [pag] = await db.insert(pagamentos).values({ vendaId: venda.id, forma: p.forma, valor: p.valor, detalhes: det }).returning({ id: pagamentos.id });
    const vinc = { pagamentoId: pag.id };

    switch (p.forma) {
      case "sinal":
      case "pix_dinheiro": {
        const quando = str(det, "data", d0);
        await receber(p.valor, quando, p.forma === "sinal" ? "Sinal" : "Venda de veículo", `${p.forma === "sinal" ? "Sinal" : "Pagamento à vista"}: ${nome}`, {
          ...vinc,
          pagoEm: det.recebido ? quando : null,
          contaId: det.contaId ? num(det, "contaId") : null,
        });
        break;
      }
      case "cartao": {
        const n = Math.max(1, num(det, "parcelas", 1));
        const liquido = Math.round(p.valor * (1 - num(det, "taxaPct") / 100));
        const primeiro = str(det, "primeiroRecebimento", somarDias(d0, 30));
        if (det.antecipado || n === 1) await receber(liquido, primeiro, "Venda de veículo", `Cartão (${n}x, líquido): ${nome}`, vinc);
        else
          for (let i = 0; i < n; i++)
            await receber(Math.round(liquido / n), somarMeses(primeiro, i), "Venda de veículo", `Cartão ${i + 1}/${n}: ${nome}`, { ...vinc, parcela: i + 1, totalParcelas: n });
        break;
      }
      case "financiamento_bancario": {
        const banco_ = str(det, "banco", "banco");
        const liberacao = str(det, "previsaoLiberacao", somarDias(d0, 5));
        await receber(p.valor, liberacao, "Venda de veículo", `Liberação ${banco_}: ${nome}`, vinc);
        if (num(det, "retorno") > 0) await receber(num(det, "retorno"), somarDias(liberacao, 30), "Retorno de financiamento", `Retorno ${banco_}: ${nome}`, vinc);
        break;
      }
      case "leasing":
      case "consorcio": {
        const inst = str(det, p.forma === "leasing" ? "instituicao" : "administradora", p.forma === "leasing" ? "instituição" : "administradora");
        await receber(p.valor, str(det, "previsaoLiberacao", somarDias(d0, 10)), "Venda de veículo", `${p.forma === "leasing" ? "Leasing" : "Consórcio"} ${inst}: ${nome}`, vinc);
        break;
      }
      case "financiamento_proprio": {
        const n = Math.max(1, num(det, "parcelas", 1));
        const valorParcela = parcelaPrice(p.valor, num(det, "jurosMensalPct"), n);
        const primeiro = str(det, "primeiroVencimento", somarMeses(d0, 1));
        for (let i = 0; i < n; i++)
          await receber(valorParcela, somarMeses(primeiro, i), "Financiamento próprio", `Parcela ${i + 1}/${n}: ${nome}`, { ...vinc, parcela: i + 1, totalParcelas: n });
        break;
      }
      case "cheque":
        await receber(p.valor, str(det, "bomPara", d0), "Venda de veículo", `Cheque ${str(det, "banco", "")} ${str(det, "numero", "")}: ${nome}`.replace(/\s+/g, " "), vinc);
        break;
      case "troca":
        break; // não movimenta dinheiro
    }
  }

  for (const c of entrada.custos) {
    await db.insert(custosVenda).values({ vendaId: venda.id, tipo: c.tipo, descricao: c.descricao || null, valor: c.valor });
    await db.insert(lancamentos).values({
      tipo: "saida",
      descricao: `${TIPOS_CUSTO_VENDA[c.tipo as keyof typeof TIPOS_CUSTO_VENDA]}${c.descricao ? ` (${c.descricao})` : ""}: ${nome}`,
      categoria: c.tipo === "comissao" ? "Comissão" : "Custo de venda",
      valor: c.valor,
      vencimento: d0,
      vendaId: venda.id,
      veiculoId: veiculo.id,
    });
  }

  if (veiculo.origem === "consignacao") {
    await db.insert(lancamentos).values({
      tipo: "saida",
      descricao: `Repasse ao dono (consignação): ${nome}`,
      categoria: "Repasse de consignação",
      valor: veiculo.custo,
      vencimento: somarDias(d0, 5),
      vendaId: venda.id,
      veiculoId: veiculo.id,
      clienteId: veiculo.clienteOrigemId,
    });
  }

  const vendido = ETAPAS_VENDIDO.includes(entrada.etapa);
  await db.update(veiculos).set({ status: vendido ? "vendido" : "reservado", publicado: vendido ? false : veiculo.publicado }).where(eq(veiculos.id, veiculo.id));
  await registrarEvento({ veiculoId: veiculo.id, vendaId: venda.id, clienteId, titulo: "Venda registrada", detalhe: `${reais(entrada.precoFinal)} · ${ETAPAS_VENDA[entrada.etapa]}` });
  return { ok: true, id: venda.id };
}
