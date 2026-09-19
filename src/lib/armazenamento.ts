import "server-only";
import { randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

// Arquivos (fotos, documentos, notas, comprovantes) ficam fora do banco.
// Local: pasta .dados/arquivos. Em produção: volume do Railway (ARQUIVOS_DIR).
// Chaves começando com "publico/" podem ser servidas sem login (fotos da vitrine).

// Em produção, ARQUIVOS_DIR aponta para o volume persistente do Railway
const RAIZ = path.resolve(process.env.ARQUIVOS_DIR ?? path.join(process.cwd(), ".dados", "arquivos"));

function caminho(chave: string) {
  const alvo = path.normalize(path.join(RAIZ, chave));
  if (!alvo.startsWith(RAIZ)) throw new Error("Chave de arquivo inválida");
  return alvo;
}

export async function salvarArquivo(pasta: string, nome: string, dados: Buffer) {
  const ext = path.extname(nome).toLowerCase().replace(/[^.a-z0-9]/g, "") || ".bin";
  const chave = `${pasta}/${randomUUID()}${ext}`;
  const alvo = caminho(chave);
  await fs.mkdir(path.dirname(alvo), { recursive: true });
  await fs.writeFile(alvo, dados);
  return chave;
}

export async function lerArquivo(chave: string) {
  return fs.readFile(caminho(chave));
}

export async function apagarArquivo(chave: string | null | undefined) {
  if (!chave) return;
  await fs.rm(caminho(chave), { force: true });
}

export function urlArquivo(chave: string) {
  return `/arquivos/${chave}`;
}

export const MIME: Record<string, string> = {
  ".webp": "image/webp",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".pdf": "application/pdf",
};
