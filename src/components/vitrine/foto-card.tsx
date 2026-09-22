"use client";

import Image from "next/image";
import { useState } from "react";
import { CarFront, Images } from "lucide-react";
import { cn } from "@/lib/cn";

interface Props {
  fotos: { card: string }[];
  alt: string;
  prioridade?: boolean;
  sizes?: string;
  className?: string;
}

/**
 * Foto do card na vitrine: mostra quantas fotos o carro tem e deixa passar por elas
 * com o mouse (no computador), sem sair da lista. No celular fica só o contador.
 */
export function FotoCard({ fotos, alt, prioridade, sizes, className }: Props) {
  const [i, setI] = useState(0);
  // Só carrega a foto depois que ela é vista uma vez; as já vistas ficam montadas para trocar sem piscar
  const [carregadas, setCarregadas] = useState<number[]>([0]);
  const n = fotos.length;

  if (!n)
    return (
      <div className={cn("relative overflow-hidden bg-chumbo", className)}>
        <div className="absolute inset-0 grid place-items-center text-nevoa-2">
          <CarFront size={28} strokeWidth={1.4} />
        </div>
      </div>
    );

  const irPara = (alvo: number) => {
    setI(alvo);
    setCarregadas((a) => (a.includes(alvo) ? a : [...a, alvo]));
  };

  const aoMover = (e: React.MouseEvent<HTMLDivElement>) => {
    if (n < 2) return;
    const { left, width } = e.currentTarget.getBoundingClientRect();
    const faixa = Math.floor(((e.clientX - left) / width) * n);
    const alvo = Math.min(n - 1, Math.max(0, faixa));
    if (alvo !== i) irPara(alvo);
  };

  return (
    <div className={cn("relative overflow-hidden bg-chumbo", className)} onMouseMove={aoMover} onMouseLeave={() => setI(0)}>
      {fotos.map((f, j) =>
        carregadas.includes(j) ? (
          <Image
            key={f.card}
            src={f.card}
            alt={j === 0 ? alt : ""}
            fill
            priority={prioridade && j === 0}
            sizes={sizes ?? "(min-width: 1280px) 30vw, (min-width: 768px) 45vw, 90vw"}
            className={cn("object-cover transition-opacity duration-200", j === i ? "opacity-100" : "opacity-0")}
          />
        ) : null,
      )}

      {/* Barrinhas de posição, como nos apps de anúncio: aparecem ao passar o mouse */}
      {n > 1 && (
        <div className="pointer-events-none absolute inset-x-3 top-3 hidden gap-1 opacity-0 transition-opacity duration-200 group-hover:opacity-100 sm:flex">
          {fotos.map((f, j) => (
            <span key={f.card} className={cn("h-[3px] flex-1 rounded-full transition-colors", j === i ? "bg-giz" : "bg-giz/30")} />
          ))}
        </div>
      )}

      {/* Contador sempre visível: mostra que existem outras fotos */}
      <span className="num pointer-events-none absolute bottom-3 right-3 flex items-center gap-1.5 rounded-full bg-black/65 px-2.5 py-1 text-[11px] font-semibold text-giz backdrop-blur-sm">
        <Images size={13} />
        {n > 1 ? `${i + 1}/${n}` : "1 foto"}
      </span>
    </div>
  );
}
