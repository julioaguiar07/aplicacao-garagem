const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const brlSemCentavos = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});
const inteiro = new Intl.NumberFormat("pt-BR");
const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });

export const reais = (v: number) => brl.format(v);
export const reaisInteiros = (v: number) => brlSemCentavos.format(v);
export const numeroCompacto = (v: number) => compacto.format(v);
export const reaisCompacto = (v: number) => `R$ ${compacto.format(v)}`;
export const km = (v: number) => `${inteiro.format(v)} km`;
export const numero = (v: number) => inteiro.format(v);
export const pct = (v: number, casas = 1) =>
  `${v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas })}%`;

/** Separa "R$ 78.000" e ",00" para o preço com centavos menores da vitrine */
export function precoPartido(v: number) {
  const [inteiros, centavos] = brl.format(v).split(",");
  return { inteiros, centavos: `,${centavos}` };
}

export function data(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", { timeZone: "America/Fortaleza" });
}

export function dataCurta(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    timeZone: "America/Fortaleza",
  });
}

/** Data de referência do protótipo (hoje) */
export const HOJE = new Date("2026-09-18T12:00:00-03:00");

export function diasDesde(iso: string, hoje = HOJE) {
  return Math.max(0, Math.floor((hoje.getTime() - new Date(iso).getTime()) / 86_400_000));
}

/** Parcela pela Tabela Price */
export function parcelaPrice(valor: number, taxaMensalPct: number, meses: number) {
  const i = taxaMensalPct / 100;
  if (i === 0) return valor / meses;
  return (valor * i) / (1 - Math.pow(1 + i, -meses));
}

