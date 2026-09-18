import Image from "next/image";
import Link from "next/link";
import { MapPin, MessageCircle } from "lucide-react";
import { LOJA, linkWhatsapp } from "@/lib/vitrine";

export function Cabecalho() {
  return (
    <header className="border-b border-linha/70 bg-[#101114]">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-6 px-4 md:px-6">
        <Link href="/" aria-label="Carmelo Multimarcas, início" className="shrink-0">
          <Image src="/marca/logo-branca.png" alt="Carmelo Multimarcas" width={124} height={43} priority />
        </Link>
        <nav className="ml-auto hidden items-center gap-7 text-sm text-giz/80 md:flex">
          <Link href="/#estoque" className="hover:text-giz">
            Estoque
          </Link>
          <Link href="/#financiamento" className="hover:text-giz">
            Financiamento
          </Link>
          <a href={linkWhatsapp("Olá! Quero avaliar meu carro na troca.")} target="_blank" rel="noopener" className="hover:text-giz">
            Avaliar meu carro
          </a>
          <Link href="/#contato" className="flex items-center gap-1.5 hover:text-giz">
            <MapPin size={15} /> Mossoró/RN
          </Link>
        </nav>
        <a
          href={linkWhatsapp("Olá! Vim pelo site da Carmelo.")}
          target="_blank"
          rel="noopener"
          className="ml-auto flex h-9 items-center gap-2 rounded-full bg-laranja px-4 text-sm font-semibold text-asfalto transition hover:bg-ambar md:ml-0"
        >
          <MessageCircle size={16} /> <span className="hidden sm:inline">WhatsApp</span> <span className="num sm:hidden">{LOJA.telefone}</span>
        </a>
      </div>
    </header>
  );
}

/** Faixa de informações abaixo do cabeçalho (no lugar das etapas de reserva da referência) */
export function FaixaInfo({ disponiveis }: { disponiveis: number }) {
  const celulas = [
    { rotulo: "Estoque", valor: `${disponiveis} carros disponíveis`, href: "/#estoque" },
    { rotulo: "Onde estamos", valor: `${LOJA.endereco}, ${LOJA.cidade}`, href: "/#contato" },
    { rotulo: "Financiamento", valor: "Simule a parcela", href: "/#financiamento" },
    { rotulo: "Seu usado", valor: "Aceitamos na troca", href: linkWhatsapp("Olá! Quero avaliar meu carro na troca."), externo: true },
    { rotulo: "Fale com a gente", valor: LOJA.telefone, href: linkWhatsapp("Olá! Vim pelo site da Carmelo."), externo: true },
  ];
  return (
    <div className="border-b border-linha/70 bg-[#101114]">
      <ul className="mx-auto grid max-w-[1440px] grid-cols-2 md:grid-cols-5">
        {celulas.map((c, i) => (
          <li key={c.rotulo} className={i === 0 ? "col-span-2 md:col-span-1" : undefined}>
            <a
              href={c.href}
              target={c.externo ? "_blank" : undefined}
              rel={c.externo ? "noopener" : undefined}
              className="group block h-full border-b border-r border-linha/70 px-4 py-3 transition hover:bg-grafite md:border-b-0 md:px-6"
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-nevoa">{c.rotulo}</p>
              <p className="num mt-0.5 truncate text-sm text-giz group-hover:text-laranja md:text-[15px]">{c.valor}</p>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Rodape() {
  return (
    <footer id="contato" className="border-t border-linha/70 bg-[#101114]">
      <div className="mx-auto grid max-w-[1440px] gap-8 px-4 py-12 md:grid-cols-[1.2fr_1fr_1fr] md:px-6">
        <div>
          <Image src="/marca/logo-branca.png" alt="Carmelo Multimarcas" width={150} height={52} />
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-nevoa">
            Seminovos com procedência, laudo e documentação em dia. Financiamento com os principais bancos e avaliação do seu usado na troca.
          </p>
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-nevoa">Endereço</p>
          <p className="mt-2 text-sm leading-relaxed">
            {LOJA.endereco}
            <br />
            {LOJA.cep} · {LOJA.cidade}
          </p>
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-nevoa">Contato</p>
          <a href={linkWhatsapp("Olá! Vim pelo site da Carmelo.")} target="_blank" rel="noopener" className="num mt-2 block text-sm hover:text-laranja">
            WhatsApp {LOJA.telefone}
          </a>
        </div>
      </div>
      <p className="border-t border-linha/50 py-4 text-center text-xs text-nevoa-2">
        © {new Date().getFullYear()} {LOJA.nome}. Preços e condições sujeitos a alteração sem aviso.
      </p>
    </footer>
  );
}
