import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Calendar, Check, DoorOpen, Fuel, Gauge, MessageCircle, Palette, Settings2 } from "lucide-react";
import { Cabecalho, Rodape } from "@/components/vitrine/cabecalho";
import { FotoCarro } from "@/components/foto-carro";
import { Simulador } from "@/components/vitrine/simulador";
import { linkWhatsapp, veiculosPublicados } from "@/lib/vitrine";
import { km, precoPartido } from "@/lib/formato";

export function generateStaticParams() {
  return veiculosPublicados().map((v) => ({ slug: v.slug }));
}

function buscar(slug: string) {
  return veiculosPublicados().find((v) => v.slug === slug);
}

export async function generateMetadata({ params }: PageProps<"/carros/[slug]">) {
  const v = buscar((await params).slug);
  if (!v) return {};
  const titulo = `${v.marca} ${v.modelo} ${v.versao ?? ""} ${v.ano}`.replace(/\s+/g, " ");
  return {
    title: titulo,
    description: `${titulo}, ${km(v.km)}, ${v.cambio}. Veja fotos, ficha e simule a parcela na Carmelo Multimarcas.`,
    openGraph: { title: titulo, images: v.foto ? [v.foto.card] : [] },
  };
}

export default async function PaginaVeiculo({ params }: PageProps<"/carros/[slug]">) {
  const v = buscar((await params).slug);
  if (!v) notFound();
  const nome = `${v.marca} ${v.modelo}`;
  const { inteiros, centavos } = precoPartido(v.preco);
  const ficha = [
    { icone: Calendar, rotulo: "Ano", valor: v.ano },
    { icone: Gauge, rotulo: "Quilometragem", valor: km(v.km) },
    { icone: Settings2, rotulo: "Câmbio", valor: v.cambio },
    { icone: Fuel, rotulo: "Combustível", valor: v.combustivel },
    { icone: Palette, rotulo: "Cor", valor: v.cor },
    { icone: DoorOpen, rotulo: "Portas", valor: v.portas },
  ];

  return (
    <div className="min-h-dvh bg-[#0d0e10]">
      <Cabecalho />
      <main className="mx-auto max-w-[1440px] px-4 pb-16 pt-6 md:px-6">
        <Link href="/#estoque" className="inline-flex items-center gap-1.5 text-sm text-nevoa hover:text-giz">
          <ArrowLeft size={16} /> Voltar ao estoque
        </Link>

        <div className="mt-5 grid gap-8 lg:grid-cols-[minmax(0,1.5fr)_minmax(340px,1fr)]">
          <div className="min-w-0">
            <FotoCarro foto={v.foto} alt={`${nome} ${v.ano}`} prioridade className="aspect-[4/3] rounded-md" sizes="(min-width: 1024px) 60vw, 100vw" />
            {v.fotos.length > 0 && (
              <div className="mt-3 grid grid-cols-4 gap-3 sm:grid-cols-6">
                {v.fotos.map((f) => (
                  <div key={f.original} className="relative aspect-[4/3] overflow-hidden rounded-md ring-2 ring-laranja">
                    <Image src={f.card} alt="" fill sizes="160px" className="object-cover" />
                  </div>
                ))}
              </div>
            )}

            <section className="mt-10">
              <h2 className="display text-xl font-bold">Ficha</h2>
              <dl className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded-md bg-linha/60 sm:grid-cols-3">
                {ficha.map(({ icone: Icone, rotulo, valor }) => (
                  <div key={rotulo} className="bg-[#141518] p-4">
                    <dt className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.1em] text-nevoa">
                      <Icone size={13} /> {rotulo}
                    </dt>
                    <dd className="num mt-1.5 font-semibold">{valor}</dd>
                  </div>
                ))}
              </dl>
            </section>

            {v.opcionais.length > 0 && (
              <section className="mt-10">
                <h2 className="display text-xl font-bold">Opcionais</h2>
                <ul className="mt-4 grid gap-x-6 gap-y-2.5 sm:grid-cols-2">
                  {v.opcionais.map((o) => (
                    <li key={o} className="flex items-center gap-2.5 text-sm text-giz/85">
                      <Check size={15} className="text-laranja" /> {o}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {v.descricao && (
              <section className="mt-10">
                <h2 className="display text-xl font-bold">Sobre este carro</h2>
                <p className="mt-3 max-w-prose leading-relaxed text-giz/80">{v.descricao}</p>
              </section>
            )}
          </div>

          <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
            <div>
              <div className="flex flex-wrap gap-1.5">
                <span className="rounded-full border border-linha px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em] text-giz/75">{v.categoria}</span>
                {v.destaques.map((d) => (
                  <span key={d} className="rounded-full border border-laranja/50 px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em] text-laranja">
                    {d}
                  </span>
                ))}
              </div>
              <h1 className="display mt-3 text-4xl font-bold leading-tight md:text-5xl">{nome}</h1>
              <p className="mt-1 text-lg text-nevoa">
                {[v.versao, v.ano].filter(Boolean).join(" · ")}
              </p>
              <p className="num mt-5 leading-none">
                <span className="mr-1 text-base font-semibold text-nevoa">R$</span>
                <span className="display text-5xl font-bold">{inteiros.replace(/R\$\s?/, "")}</span>
                <span className="text-2xl font-semibold">{centavos}</span>
              </p>
              <p className="mt-2 text-[11px] font-medium uppercase tracking-[0.1em] text-nevoa">à vista · aceitamos seu usado na troca</p>
            </div>

            <a
              href={linkWhatsapp(`Olá! Tenho interesse no ${nome} ${v.ano} que vi no site.`)}
              target="_blank"
              rel="noopener"
              className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-laranja font-semibold text-asfalto transition hover:bg-ambar"
            >
              <MessageCircle size={18} /> Quero este carro
            </a>
            <a
              href={linkWhatsapp(`Olá! Quero avaliar meu carro na troca pelo ${nome} ${v.ano}.`)}
              target="_blank"
              rel="noopener"
              className="flex h-12 w-full items-center justify-center rounded-md border border-linha text-sm font-medium text-giz/85 transition hover:border-laranja/60 hover:text-giz"
            >
              Avaliar meu carro na troca
            </a>

            <Simulador preco={v.preco} />
          </aside>
        </div>
      </main>
      <Rodape />
    </div>
  );
}
