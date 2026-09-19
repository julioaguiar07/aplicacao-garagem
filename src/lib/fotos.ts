import "server-only";
import sharp from "sharp";
import { lerArquivo, salvarArquivo } from "@/lib/armazenamento";

/** Foco vertical padrão: nas fotos do showroom o carro fica um pouco abaixo do meio */
export const FOCO_PADRAO = 0.57;

/** Maior recorte 4:3 que cabe na foto, posicionado no foco vertical (0 = topo, 1 = base) */
async function card(original: Buffer, focoY: number) {
  const { width: W = 0, height: H = 0 } = await sharp(original).metadata();
  let cw = W;
  let ch = Math.round((cw * 3) / 4);
  if (ch > H) {
    ch = H;
    cw = Math.round((ch * 4) / 3);
  }
  const left = Math.round((W - cw) / 2);
  const top = Math.round(Math.min(Math.max(0, H * focoY - ch / 2), H - ch));
  return sharp(original).extract({ left, top, width: cw, height: ch }).resize(1200, 900).webp({ quality: 82 }).toBuffer();
}

/** Trata a foto enviada: corrige orientação, remove EXIF/GPS e gera a versão do card */
export async function processarFoto(veiculoId: number, entrada: Buffer, focoY = FOCO_PADRAO) {
  const original = await sharp(entrada).rotate().resize(1600, 1600, { fit: "inside", withoutEnlargement: true }).webp({ quality: 82 }).toBuffer();
  const pasta = `publico/veiculos/${veiculoId}`;
  const chaveOriginal = await salvarArquivo(pasta, "original.webp", original);
  const chaveCard = await salvarArquivo(pasta, "card.webp", await card(original, focoY));
  return { chaveOriginal, chaveCard, focoY };
}

/** Refaz o recorte do card a partir da original com um novo foco */
export async function reenquadrar(veiculoId: number, chaveOriginal: string, focoY: number) {
  const original = await lerArquivo(chaveOriginal);
  return salvarArquivo(`publico/veiculos/${veiculoId}`, "card.webp", await card(original, focoY));
}
