import { notFound } from "next/navigation";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { FormVeiculo, type ValoresVeiculo } from "@/components/painel/form-veiculo";
import { editarVeiculo } from "@/lib/acoes/veiculos";
import { nomeVeiculo, veiculoCompleto } from "@/lib/consultas/veiculos";

export const metadata = { title: "Editar veículo" };

export default async function EditarVeiculo({ params }: PageProps<"/painel/estoque/[id]/editar">) {
  const id = Number((await params).id);
  const dados = await veiculoCompleto(id);
  if (!dados) notFound();
  const v = dados.veiculo;
  const inicial: ValoresVeiculo = {
    marca: v.marca,
    modelo: v.modelo,
    versao: v.versao ?? "",
    anoModelo: String(v.anoModelo),
    anoFabricacao: v.anoFabricacao ? String(v.anoFabricacao) : "",
    cor: v.cor ?? "",
    km: v.km !== null ? String(v.km) : "",
    placa: v.placa ?? "",
    chassi: v.chassi ?? "",
    renavam: v.renavam ?? "",
    categoria: v.categoria,
    cambio: v.cambio,
    combustivel: v.combustivel,
    portas: v.portas ? String(v.portas) : "4",
    opcionais: v.opcionais,
    destaques: v.destaques,
    descricao: v.descricao ?? "",
    origem: v.origem,
    fornecedor: v.fornecedor ?? "",
    dataEntrada: v.dataEntrada,
    custo: v.custo,
    preco: v.preco,
    descontoMaximoPct: String(v.descontoMaximoPct).replace(".", ","),
    precoFipe: v.precoFipe ?? 0,
    codigoFipe: v.codigoFipe ?? "",
  };
  const acao = editarVeiculo.bind(null, id) as unknown as Parameters<typeof FormVeiculo>[0]["acao"];
  return (
    <>
      <BarraSuperior
        titulo={`Editar ${nomeVeiculo(v)} ${v.anoModelo}`}
        trilha={[{ rotulo: "Estoque", href: "/painel/estoque" }, { rotulo: `${v.modelo} ${v.anoModelo}`, href: `/painel/estoque/${id}` }, { rotulo: "Editar" }]}
        acoes={<span />}
      />
      <FormVeiculo acao={acao} inicial={inicial} edicao />
    </>
  );
}
