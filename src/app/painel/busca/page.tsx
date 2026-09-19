import Link from "next/link";
import { BarraSuperior } from "@/components/painel/barra-superior";
import { FotoCarro } from "@/components/foto-carro";
import { StatusVeiculoSelo } from "@/components/status-veiculo";
import { Cartao, Vazio } from "@/components/ui";
import { listarVeiculos, nomeVeiculo } from "@/lib/consultas/veiculos";
import { listarClientes } from "@/lib/consultas/clientes";
import { listarVendas } from "@/lib/consultas/vendas";
import { ETAPAS_VENDA, dataBR, reais } from "@/lib/dominio";

export const metadata = { title: "Busca" };

const normal = (t: string) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export default async function Busca({ searchParams }: PageProps<"/painel/busca">) {
  const q = String((await searchParams).q ?? "").trim();
  const termo = normal(q);
  const termoPlaca = q.toUpperCase().replace(/[^A-Z0-9]/g, "");
  const [veiculos, clientes, vendas] = q ? await Promise.all([listarVeiculos({ incluirVendidos: true }), listarClientes(), listarVendas({ incluirCanceladas: true })]) : [[], [], []];
  const achouVeiculos = veiculos.filter(
    (v) => normal(`${v.marca} ${v.modelo} ${v.versao ?? ""} ${v.anoModelo} ${v.cor ?? ""}`).includes(termo) || (termoPlaca.length >= 3 && (v.placa ?? "").includes(termoPlaca)) || (v.chassi ?? "").toUpperCase().includes(q.toUpperCase()),
  );
  const achouClientes = clientes.filter((c) => normal(`${c.nome} ${c.telefone ?? ""} ${c.cpf ?? ""} ${c.email ?? ""}`).includes(termo));
  const achouVendas = vendas.filter((v) => normal(`${v.nomeVeiculo} ${v.cliente.nome}`).includes(termo));
  const total = achouVeiculos.length + achouClientes.length + achouVendas.length;

  return (
    <>
      <BarraSuperior titulo={q ? `Busca: “${q}”` : "Busca"} trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Busca" }]} />
      {!q ? (
        <Vazio>Digite na busca acima um modelo, placa, nome ou telefone.</Vazio>
      ) : total === 0 ? (
        <Vazio>Nada encontrado para “{q}”. Tente só o modelo (ex.: HB20) ou parte do nome.</Vazio>
      ) : (
        <div className="space-y-5">
          {achouVeiculos.length > 0 && (
            <Cartao titulo={`Veículos (${achouVeiculos.length})`}>
              <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {achouVeiculos.map((v) => (
                  <li key={v.id}>
                    <Link href={`/painel/estoque/${v.id}`} className="flex items-center gap-3 rounded-xl border border-linha/60 p-2 hover:border-laranja/50">
                      <FotoCarro src={v.capa?.urlCard} alt="" className="h-14 w-20 shrink-0 rounded-lg" sizes="80px" />
                      <div className="min-w-0">
                        <p className="truncate font-medium">
                          {nomeVeiculo(v)} {v.anoModelo}
                        </p>
                        <div className="mt-1 flex items-center gap-2">
                          <StatusVeiculoSelo status={v.status} />
                          <span className="num text-xs text-nevoa">{reais(v.preco)}</span>
                        </div>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
          {achouClientes.length > 0 && (
            <Cartao titulo={`Clientes (${achouClientes.length})`}>
              <ul className="divide-y divide-linha/50">
                {achouClientes.map((c) => (
                  <li key={c.id}>
                    <Link href={`/painel/clientes/${c.id}`} className="flex items-center justify-between gap-3 py-2.5 hover:text-laranja">
                      <span className="font-medium">{c.nome}</span>
                      <span className="num text-sm text-nevoa">{c.telefone ?? ""} · {c.compras} compra(s)</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
          {achouVendas.length > 0 && (
            <Cartao titulo={`Vendas (${achouVendas.length})`}>
              <ul className="divide-y divide-linha/50">
                {achouVendas.map((v) => (
                  <li key={v.venda.id}>
                    <Link href={`/painel/vendas/${v.venda.id}`} className="flex flex-wrap items-center justify-between gap-3 py-2.5 hover:text-laranja">
                      <span className="font-medium">
                        {v.nomeVeiculo} · {v.cliente.nome}
                      </span>
                      <span className="num text-sm text-nevoa">
                        {dataBR(v.venda.dataVenda)} · {ETAPAS_VENDA[v.venda.etapa as keyof typeof ETAPAS_VENDA]} · {reais(v.venda.precoFinal)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
        </div>
      )}
    </>
  );
}
