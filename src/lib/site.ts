// Endereço público da vitrine. No endereço do painel (adm-...) a raiz abre o painel,
// então o link "Ver vitrine" precisa apontar para o domínio da loja.
export const URL_VITRINE = process.env.NODE_ENV === "production" ? "https://www.carmelomultimarcas.com.br" : "/";
