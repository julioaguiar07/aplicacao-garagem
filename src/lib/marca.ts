// Marca da instalação. O padrão é a Carmelo; outra instalação (ex.: a demonstração)
// troca tudo por variáveis NEXT_PUBLIC_* definidas no serviço antes do build.
const env = (v: string | undefined) => (v && v.trim() ? v.trim() : undefined);

export const DEMO = process.env.NEXT_PUBLIC_DEMO === "1";

export const MARCA = {
  nome: env(process.env.NEXT_PUBLIC_MARCA_NOME) ?? "Carmelo Multimarcas",
  curto: env(process.env.NEXT_PUBLIC_MARCA_CURTO) ?? "Carmelo",
  /** Pasta em /public com logo-branca.png, logo-preta.png, logo-icone.png, logo-circulo.png, compartilhar.png e os ícones */
  pasta: env(process.env.NEXT_PUBLIC_MARCA_PASTA) ?? "/marca",
  /** Domínio público da vitrine; vazio na demonstração (usa o próprio endereço) */
  site: DEMO ? "" : (env(process.env.NEXT_PUBLIC_SITE_URL) ?? "https://www.carmelomultimarcas.com.br"),
  slogan: env(process.env.NEXT_PUBLIC_MARCA_SLOGAN) ?? "Seminovos com procedência em Mossoró/RN",
  descricao:
    env(process.env.NEXT_PUBLIC_MARCA_DESCRICAO) ??
    "Seminovos revisados e com procedência na Carmelo Multimarcas, em Mossoró/RN. Veja o estoque, simule o financiamento e fale com a gente pelo WhatsApp.",
  /** Senha exibida na tela de entrada da demonstração */
  senhaDemo: DEMO ? (env(process.env.NEXT_PUBLIC_DEMO_SENHA) ?? "demo") : null,
};

export const logo = (arquivo: string) => `${MARCA.pasta}/${arquivo}`;

// "Ver vitrine" no painel: no endereço adm-… a raiz abre o painel, então aponta para o domínio da loja
export const URL_VITRINE = process.env.NODE_ENV === "production" && MARCA.site ? MARCA.site : "/";
