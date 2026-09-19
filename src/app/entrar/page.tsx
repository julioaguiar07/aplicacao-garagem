import Image from "next/image";
import { FormEntrar } from "./form-entrar";

export const metadata = { title: "Entrar", robots: { index: false } };

export default async function Entrar({ searchParams }: PageProps<"/entrar">) {
  const voltar = (await searchParams).voltar;
  return (
    <main className="grid min-h-dvh place-items-center bg-asfalto px-4">
      <div className="brilho-laranja w-full max-w-sm rounded-[var(--radius-card)] border border-linha/60 p-8">
        <Image src="/marca/logo-branca.png" alt="Carmelo Multimarcas" width={150} height={52} priority />
        <h1 className="display mt-8 text-2xl font-bold">Painel da loja</h1>
        <p className="mt-1 text-sm text-nevoa">Entre com a senha do administrador.</p>
        <FormEntrar voltar={typeof voltar === "string" ? voltar : "/painel"} />
      </div>
    </main>
  );
}
