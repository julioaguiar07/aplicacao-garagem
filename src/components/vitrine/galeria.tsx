"use client";

import Image from "next/image";
import { useState } from "react";
import { ChevronLeft, ChevronRight, Expand } from "lucide-react";
import { cn } from "@/lib/cn";

/** Galeria da página do carro: foto grande, miniaturas e tela cheia com a foto original */
export function Galeria({ fotos, alt }: { fotos: { card: string; original: string }[]; alt: string }) {
  const [i, setI] = useState(0);
  const [cheia, setCheia] = useState(false);
  const ir = (d: number) => setI((a) => (a + d + fotos.length) % fotos.length);
  if (!fotos.length) return null;
  return (
    <div>
      <div className="group relative aspect-[4/3] overflow-hidden rounded-md bg-chumbo">
        <Image src={fotos[i].card} alt={`${alt}, foto ${i + 1}`} fill priority sizes="(min-width: 1024px) 60vw, 100vw" className="object-cover" />
        {fotos.length > 1 && (
          <>
            <button onClick={() => ir(-1)} className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-black/55 p-2 text-giz hover:bg-black/75" aria-label="Foto anterior">
              <ChevronLeft size={20} />
            </button>
            <button onClick={() => ir(1)} className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-black/55 p-2 text-giz hover:bg-black/75" aria-label="Próxima foto">
              <ChevronRight size={20} />
            </button>
          </>
        )}
        <button onClick={() => setCheia(true)} className="absolute bottom-3 right-3 flex items-center gap-1.5 rounded-full bg-black/60 px-3 py-1.5 text-xs text-giz hover:bg-black/80">
          <Expand size={13} /> Ver foto inteira {fotos.length > 1 && `· ${i + 1}/${fotos.length}`}
        </button>
      </div>
      {fotos.length > 1 && (
        <div className="mt-3 grid grid-cols-4 gap-3 sm:grid-cols-6">
          {fotos.map((f, j) => (
            <button key={f.card} onClick={() => setI(j)} className={cn("relative aspect-[4/3] overflow-hidden rounded-md", j === i ? "ring-2 ring-laranja" : "opacity-70 hover:opacity-100")} aria-label={`Foto ${j + 1}`}>
              <Image src={f.card} alt="" fill sizes="160px" className="object-cover" />
            </button>
          ))}
        </div>
      )}
      {cheia && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/90 p-4" onClick={() => setCheia(false)} role="dialog" aria-label="Foto em tela cheia">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={fotos[i].original} alt={alt} className="max-h-full max-w-full rounded-md object-contain" />
          <button className="absolute right-4 top-4 rounded-full bg-white/10 px-3 py-1.5 text-sm text-giz" onClick={() => setCheia(false)}>
            Fechar
          </button>
        </div>
      )}
    </div>
  );
}
