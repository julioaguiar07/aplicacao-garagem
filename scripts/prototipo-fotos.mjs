// Gera as imagens do protótipo a partir das fotos da vitrine atual.
// Uso: node scripts/prototipo-fotos.mjs <pasta-fotos>
//
// Para cada veículo gera em public/demo/veiculos/<id>/:
//   original.webp  foto tratada (orientação corrigida, sem EXIF/GPS, até 1600px)
//   card.webp      foto completa no formato do card (4:3), 1200x900
//
// Enquadramento: centralizado na horizontal e com foco em 57% da altura, onde o carro
// costuma estar nas fotos verticais do showroom. No sistema, o foco poderá ser ajustado por foto.
import sharp from "sharp";
import fs from "node:fs";
import path from "node:path";

const [pastaFotos] = process.argv.slice(2);
const destino = "public/demo/veiculos";
const FOCO_Y = 0.57;

for (const arquivo of fs.readdirSync(pastaFotos)) {
  const id = path.parse(arquivo).name;
  const saida = path.join(destino, id);
  fs.rmSync(saida, { recursive: true, force: true });
  fs.mkdirSync(saida, { recursive: true });

  const base = await sharp(path.join(pastaFotos, arquivo)).rotate().resize(1600, 1600, { fit: "inside" }).toBuffer();
  const { width: W, height: H } = await sharp(base).metadata();
  await sharp(base).webp({ quality: 82 }).toFile(path.join(saida, "original.webp"));

  // Maior recorte 4:3 que cabe na foto, posicionado no foco
  let cw = W;
  let ch = Math.round((cw * 3) / 4);
  if (ch > H) {
    ch = H;
    cw = Math.round((ch * 4) / 3);
  }
  const left = Math.round((W - cw) / 2);
  const top = Math.round(Math.min(Math.max(0, H * FOCO_Y - ch / 2), H - ch));
  await sharp(base)
    .extract({ left, top, width: cw, height: ch })
    .resize(1200, 900)
    .webp({ quality: 82 })
    .toFile(path.join(saida, "card.webp"));

  console.log(id, `${W}x${H} → recorte 4:3 em y=${top}`);
}
