import type { DocumentoVeiculo, FotoVeiculo, GastoVeiculo, Veiculo } from "@/lib/tipos";

/*
 * Dados do protótipo (Fase 0).
 * Marca, modelo, ano, cor, km, câmbio, combustível, portas, preço, data de cadastro e foto
 * são os que a vitrine atual já publica. Custo, gastos, documentos e histórico são FICTÍCIOS,
 * apenas para demonstrar as telas; os dados reais entram pela migração (Fase 2).
 */

function fotos(id: number): FotoVeiculo[] {
  const base = `/demo/veiculos/${id}`;
  return [
    { original: `${base}/original.webp`, card: `${base}/card.webp`, capa: true },
  ];
}

const TIPOS_DOC = ["CRLV", "Recibo de compra (ATPV-e)", "Laudo cautelar", "Consulta de débitos", "Contrato de entrada"];

function documentos(ok: number, vencido?: string): DocumentoVeiculo[] {
  return TIPOS_DOC.map((tipo, i) => {
    if (tipo === vencido) return { tipo, status: "vencido", validade: "2026-09-05", arquivo: "demo.pdf" };
    return i < ok
      ? { tipo, status: "ok", arquivo: "demo.pdf", enviadoEm: "2026-09-10" }
      : { tipo, status: "pendente" };
  });
}

let gid = 1;
function gasto(data: string, categoria: GastoVeiculo["categoria"], descricao: string, valor: number, comNota = true): GastoVeiculo {
  return { id: `g${gid++}`, data, categoria, descricao, valor, comNota };
}

export const VEICULOS: Veiculo[] = [
  {
    id: 111,
    slug: "hyundai-hb20-2022-111",
    marca: "Hyundai",
    modelo: "HB20",
    anoModelo: 2022,
    cor: "Prata",
    km: 52000,
    categoria: "Hatch",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["Ar-condicionado", "Direção elétrica", "Vidros elétricos", "Central multimídia"],
    destaques: ["Recém-chegado"],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-17T17:16:46-03:00",
    origem: "compra",
    fornecedor: "Particular",
    custo: 70000,
    preco: 78000,
    descontoMaximoPct: 5,
    precoFipe: 76900,
    fotos: fotos(111),
    documentos: documentos(2),
    gastos: [gasto("2026-09-18", "Estética", "Higienização interna", 280)],
    historico: [
      { data: "2026-09-17T17:16:00-03:00", titulo: "Veículo cadastrado", detalhe: "Compra de particular" },
      { data: "2026-09-18T09:30:00-03:00", titulo: "Gasto lançado", detalhe: "Higienização interna · R$ 280,00" },
    ],
  },
  {
    id: 109,
    slug: "fiat-titano-volcano-2025-109",
    marca: "Fiat",
    modelo: "Titano",
    versao: "Volcano",
    anoModelo: 2025,
    cor: "Branco",
    km: 47706,
    categoria: "Picape",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["4x4", "Couro", "Câmera de ré", "Controle de tração", "Multimídia 10\""],
    destaques: ["Seminovo"],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-16T18:27:24-03:00",
    origem: "troca",
    custo: 162000,
    preco: 175000,
    descontoMaximoPct: 4,
    precoFipe: 181500,
    fotos: fotos(109),
    documentos: documentos(4),
    gastos: [
      gasto("2026-09-16", "Estética", "Polimento e cristalização", 650),
      gasto("2026-09-17", "Documentação", "Vistoria e laudo cautelar", 350),
    ],
    historico: [
      { data: "2026-09-16T18:27:00-03:00", titulo: "Veículo cadastrado", detalhe: "Entrou como troca" },
      { data: "2026-09-17T11:00:00-03:00", titulo: "Laudo cautelar anexado" },
      { data: "2026-09-17T15:40:00-03:00", titulo: "Publicado na vitrine" },
    ],
  },
  {
    id: 108,
    slug: "toyota-yaris-xl-2019-108",
    marca: "Toyota",
    modelo: "Yaris",
    versao: "XL",
    anoModelo: 2019,
    cor: "Prata",
    km: 133000,
    categoria: "Hatch",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["Ar-condicionado", "Direção elétrica", "Airbags frontais"],
    destaques: [],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-16T18:16:20-03:00",
    origem: "compra",
    custo: 62000,
    preco: 70000,
    descontoMaximoPct: 6,
    precoFipe: 68200,
    fotos: fotos(108),
    documentos: documentos(3, "Consulta de débitos"),
    gastos: [
      gasto("2026-09-16", "Pneus", "2 pneus dianteiros", 1180),
      gasto("2026-09-17", "Mecânica", "Troca de óleo e filtros", 420),
    ],
    historico: [{ data: "2026-09-16T18:16:00-03:00", titulo: "Veículo cadastrado" }],
  },
  {
    id: 106,
    slug: "volkswagen-gol-2018-106",
    marca: "Volkswagen",
    modelo: "Gol",
    anoModelo: 2018,
    cor: "Branco",
    km: 155000,
    categoria: "Hatch",
    cambio: "Manual",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["Ar-condicionado", "Direção hidráulica"],
    destaques: ["Econômico"],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-16T17:57:43-03:00",
    origem: "compra",
    custo: 40000,
    preco: 46000,
    descontoMaximoPct: 6,
    precoFipe: 44800,
    fotos: fotos(106),
    documentos: documentos(5),
    gastos: [gasto("2026-09-17", "Funilaria e pintura", "Retoque para-choque", 480)],
    historico: [{ data: "2026-09-16T17:57:00-03:00", titulo: "Veículo cadastrado" }],
  },
  {
    id: 105,
    slug: "jeep-compass-longitude-2017-105",
    marca: "Jeep",
    modelo: "Compass",
    versao: "Longitude",
    anoModelo: 2017,
    cor: "Preto",
    km: 14000,
    categoria: "SUV",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["Couro", "Teto solar", "Chave presencial", "Multimídia", "Sensor de estacionamento"],
    destaques: ["Baixa km"],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-16T17:07:40-03:00",
    origem: "consignacao",
    fornecedor: "Consignado de cliente",
    custo: 77000,
    preco: 85000,
    descontoMaximoPct: 5,
    precoFipe: 88300,
    fotos: fotos(105),
    documentos: documentos(3),
    gastos: [],
    historico: [{ data: "2026-09-16T17:07:00-03:00", titulo: "Veículo cadastrado", detalhe: "Consignação" }],
  },
  {
    id: 104,
    slug: "renault-duster-2020-104",
    marca: "Renault",
    modelo: "Duster",
    anoModelo: 2020,
    cor: "Cinza",
    km: 115000,
    categoria: "SUV",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["Ar-condicionado", "Multimídia", "Rodas de liga leve"],
    destaques: [],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-15T16:51:57-03:00",
    origem: "compra",
    custo: 76000,
    preco: 85000,
    descontoMaximoPct: 5,
    precoFipe: 82700,
    fotos: fotos(104),
    documentos: documentos(4),
    gastos: [gasto("2026-09-15", "Mecânica", "Pastilhas de freio", 390)],
    historico: [{ data: "2026-09-15T16:51:00-03:00", titulo: "Veículo cadastrado" }],
  },
  {
    id: 103,
    slug: "volvo-xc40-t5-r-design-2022-103",
    marca: "Volvo",
    modelo: "XC40",
    versao: "T5 Hybrid R-Design",
    anoModelo: 2022,
    cor: "Vermelho",
    km: 500,
    categoria: "SUV",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 4,
    opcionais: ["Teto panorâmico", "Couro", "Piloto automático adaptativo", "Som premium", "Câmera 360°"],
    destaques: ["Oferta da semana"],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-09-15T16:38:30-03:00",
    origem: "compra",
    custo: 178000,
    preco: 190000,
    descontoMaximoPct: 3,
    precoFipe: 196400,
    fotos: fotos(103),
    documentos: documentos(5),
    gastos: [gasto("2026-09-15", "Estética", "Vitrificação de pintura", 1200)],
    historico: [{ data: "2026-09-15T16:38:00-03:00", titulo: "Veículo cadastrado" }],
  },
  {
    id: 100,
    slug: "hyundai-hb20s-premium-2019-100",
    marca: "Hyundai",
    modelo: "HB20S",
    versao: "Premium 1.6",
    anoModelo: 2019,
    cor: "Branco",
    km: 65000,
    categoria: "Sedan",
    cambio: "Automático",
    combustivel: "Gasolina",
    portas: 2,
    opcionais: [
      "Bancos em couro",
      "Ar digital",
      "Direção elétrica",
      "Android Auto e CarPlay",
      "Volante multifuncional",
      "Rodas de liga leve",
      "Sensor de estacionamento",
      "Câmera de ré",
    ],
    descricao:
      "Sedã que une conforto, tecnologia e bom desempenho. Motor 1.6 flex e câmbio automático de 6 marchas, condução suave e econômica, ideal para cidade e estrada. Versão Premium com acabamento refinado e pacote completo de segurança.",
    destaques: ["Único dono"],
    status: "disponivel",
    publicado: true,
    cadastradoEm: "2026-08-01T12:03:51-03:00",
    origem: "compra",
    custo: 70000,
    preco: 75000,
    descontoMaximoPct: 4,
    precoFipe: 73900,
    fotos: fotos(100),
    documentos: documentos(5),
    gastos: [
      gasto("2026-08-02", "Estética", "Higienização completa", 320),
      gasto("2026-08-05", "Mecânica", "Revisão 60 mil km", 890),
    ],
    historico: [
      { data: "2026-08-01T12:03:00-03:00", titulo: "Veículo cadastrado" },
      { data: "2026-08-05T10:00:00-03:00", titulo: "Revisão concluída" },
      { data: "2026-09-02T16:20:00-03:00", titulo: "Preço reduzido", detalhe: "R$ 78.000 → R$ 75.000" },
    ],
  },
];

export function veiculoPorId(id: number) {
  return VEICULOS.find((v) => v.id === id);
}

export function veiculoPorSlug(slug: string) {
  return VEICULOS.find((v) => v.slug === slug);
}

export function nomeCompleto(v: Pick<Veiculo, "marca" | "modelo" | "versao">) {
  return [v.marca, v.modelo, v.versao].filter(Boolean).join(" ");
}

export function totalGastos(v: Veiculo) {
  return v.gastos.reduce((s, g) => s + g.valor, 0);
}

export function precoMinimo(v: Veiculo) {
  return v.preco * (1 - v.descontoMaximoPct / 100);
}

export function lucroPrevisto(v: Veiculo) {
  return v.preco - v.custo - totalGastos(v);
}

export function pendencias(v: Veiculo) {
  const docs = v.documentos.filter((d) => d.status !== "ok").length;
  const dados = [v.placa, v.chassi, v.renavam].filter((x) => !x).length;
  return { docs, dados, total: docs + (dados > 0 ? 1 : 0) };
}
