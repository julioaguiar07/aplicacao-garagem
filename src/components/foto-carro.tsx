import Image from "next/image";
import type { FotoVeiculo } from "@/lib/tipos";
import { cn } from "@/lib/cn";

interface Props {
  foto?: FotoVeiculo;
  alt: string;
  prioridade?: boolean;
  sizes?: string;
  className?: string;
}

/** Foto completa do carro preenchendo o formato do card */
export function FotoCarro({ foto, alt, prioridade, sizes, className }: Props) {
  return (
    <div className={cn("relative overflow-hidden bg-chumbo", className)}>
      {foto ? (
        <Image
          src={foto.card}
          alt={alt}
          fill
          priority={prioridade}
          sizes={sizes ?? "(min-width: 1280px) 30vw, (min-width: 768px) 45vw, 90vw"}
          className="object-cover transition duration-500 group-hover:scale-[1.03]"
        />
      ) : (
        <div className="absolute inset-0 grid place-items-center text-sm text-nevoa">Sem foto</div>
      )}
    </div>
  );
}
