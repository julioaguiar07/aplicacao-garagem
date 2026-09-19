# Carmelo Multimarcas v2

Sistema de gestão e vitrine da Carmelo Multimarcas (Mossoró/RN), em reconstrução.
O sistema anterior (Streamlit + Flask) está em [`legacy/`](legacy/) e continua em produção pela branch `main` até a virada.

## Stack

- Next.js 16 (App Router, Server Actions) + React 19 + TypeScript
- Tailwind CSS 4, Recharts, lucide-react
- Postgres com Drizzle ORM: em produção o Postgres do Railway (`DATABASE_URL`); localmente um Postgres embutido (PGlite) em `.dados/`
- Arquivos (fotos, documentos, comprovantes) fora do banco: `.dados/arquivos/` local; bucket do Railway na virada
- Login de um único administrador (bcrypt + cookie assinado), PDFs com pdf-lib, fotos com sharp

## Rodando localmente

```bash
npm install
npm run semear   # cria o banco local com dados de demonstração (apaga o que houver)
npm run dev      # http://localhost:3000
```

- Vitrine: `/` · Painel: `/painel` (senha local: `carmelo`)
- `npm run semear` precisa do servidor parado (o PGlite aceita um processo por vez).

## Variáveis de ambiente (produção)

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | Postgres do Railway (as migrações rodam sozinhas ao iniciar) |
| `SESSAO_SEGREDO` | Assinatura do cookie de login (texto longo e aleatório) |
| `ADMIN_SENHA_INICIAL` | Senha do primeiro acesso; depois troque em Configurações |

## Estrutura

- `src/db/` schema e conexão · `drizzle/` migrações (`npm run db:gerar` após mudar o schema)
- `src/lib/consultas/` leituras · `src/lib/acoes/` gravações (server actions) · `src/lib/negocio/` regras compartilhadas (venda)
- `src/app/painel/` painel · `src/app/page.tsx` e `src/app/carros/` vitrine
- `scripts/semear.ts` carga de demonstração (fotos reais da vitrine atual em `public/demo/`, demais dados fictícios)
