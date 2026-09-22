// Roda antes de "next start" em produção:
// 1) aplica as migrações do banco novo (feito pela conexão);
// 2) se MIGRAR_ANTIGO_URL estiver definida, importa o sistema antigo uma única vez;
// 3) na instalação de demonstração (DEMO_SEMEAR=1), preenche o banco vazio com dados fictícios.
import { sql } from "drizzle-orm";
import { banco, schema } from "@/db";
import { jaMigrado, migrarSistemaAntigo } from "@/lib/migracao/antigo";

async function main() {
  const db = await banco();
  console.log("[iniciar] banco pronto");

  if (process.env.DEMO_SEMEAR === "1") {
    // Proteções: nunca junto com a migração do sistema antigo, e só com o banco vazio
    if (process.env.MIGRAR_ANTIGO_URL) throw new Error("DEMO_SEMEAR não pode ser usado junto com MIGRAR_ANTIGO_URL");
    const [{ n }] = await db.select({ n: sql<number>`count(*)::int` }).from(schema.veiculos);
    if (n > 0) {
      console.log("[iniciar] demonstração já tem dados");
      return;
    }
    console.log("[iniciar] preenchendo a demonstração com dados fictícios…");
    const { semear } = await import("./semear");
    await semear();
    return;
  }

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
