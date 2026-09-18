# Carmelo Multimarcas v2

Sistema de gestão e vitrine da Carmelo Multimarcas (Mossoró/RN), em reconstrução.
O sistema anterior (Streamlit + Flask) está em [`legacy/`](legacy/) e continua em produção pela branch `main` até a virada.

## Stack

- Next.js 16 (App Router) + React 19 + TypeScript
- Tailwind CSS 4, Recharts, lucide-react
- Próximas fases: Postgres com Prisma, autenticação de um único administrador, armazenamento de fotos e documentos no Railway

## Rodando localmente

```bash
npm install
npm run dev      # http://localhost:3000
```

- Vitrine: `/`
- Painel: `/painel`

## Estado atual: Fase 0 (protótipo)

As telas usam dados de demonstração em `src/lib/demo/`. Marca, modelo, ano, km, preço e fotos são os que a vitrine atual já publica;
custos, gastos, documentos e vendas são fictícios. Nada aqui lê ou grava no banco de produção.

As fotos em `public/demo/veiculos/` foram geradas com `scripts/prototipo-fotos.mjs` (sem EXIF/GPS, recorte 4:3 para os cards).
