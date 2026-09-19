// Roda antes de "next start" em produção:
// 1) aplica as migrações do banco novo (feito pela conexão);
// 2) se MIGRAR_ANTIGO_URL estiver definida, importa o sistema antigo uma única vez.
import { banco } from "@/db";
import { jaMigrado, migrarSistemaAntigo } from "@/lib/migracao/antigo";

async function main() {
  await banco();
  console.log("[iniciar] banco pronto");
  const url = process.env.MIGRAR_ANTIGO_URL;
  if (!url) return;
  if (await jaMigrado()) {
    console.log("[iniciar] dados do sistema antigo já importados");
    return;
  }
  const { Pool } = await import("pg");
  const antigo = new Pool({ connectionString: url, max: 2 });
  try {
    console.log("[iniciar] importando o sistema antigo…");
    await migrarSistemaAntigo(async (q) => (await antigo.query(q)).rows, (m) => console.log("[migração]", m));
  } finally {
    await antigo.end();
  }
}

main()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error("[iniciar] falhou:", e);
    process.exit(1);
  });
