import Image from "next/image";
import { CarFront } from "lucide-react";
import { cn } from "@/lib/cn";

interface Props {
  src?: string | null;
  alt: string;
  prioridade?: boolean;
  sizes?: string;
  className?: string;
}

/** Foto completa do carro preenchendo o formato do card */
export function FotoCarro({ src, alt, prioridade, sizes, className }: Props) {
  return (
    <div className={cn("relative overflow-hidden bg-chumbo", className)}>
      {src ? (
        <Image
          src={src}
          alt={alt}
          fill
          priority={prioridade}
          sizes={sizes ?? "(min-width: 1280px) 30vw, (min-width: 768px) 45vw, 90vw"}
          className="object-cover transition duration-500 group-hover:scale-[1.03]"
        />
      ) : (
        <div className="absolute inset-0 grid place-items-center text-nevoa-2">
          <CarFront size={28} strokeWidth={1.4} />
        </div>
      )}
    </div>
  );
}
