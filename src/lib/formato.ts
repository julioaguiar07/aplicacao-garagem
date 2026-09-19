// Formatação para a vitrine (valores em REAIS, não centavos)
const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const inteiro = new Intl.NumberFormat("pt-BR");

export const reais = (v: number) => brl.format(v);
export const km = (v: number) => `${inteiro.format(v)} km`;

/** Separa "R$ 78.000" e ",00" para o preço com centavos menores da vitrine */
export function precoPartido(v: number) {
  const [inteiros, centavos] = brl.format(v).split(",");
  return { inteiros, centavos: `,${centavos}` };
}
