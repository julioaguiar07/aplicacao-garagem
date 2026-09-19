import "server-only";
import fs from "node:fs";
import path from "node:path";
import { drizzle as drizzlePg } from "drizzle-orm/node-postgres";
import { drizzle as drizzlePglite } from "drizzle-orm/pglite";
import { migrate as migratePg } from "drizzle-orm/node-postgres/migrator";
import { migrate as migratePglite } from "drizzle-orm/pglite/migrator";
import * as schema from "./schema";

// Com DATABASE_URL (Railway) usa Postgres; sem ela, um Postgres embutido (PGlite) em .dados/,
// com o mesmo SQL e as mesmas migrações.

type Banco = ReturnType<typeof drizzlePglite<typeof schema>>;

const PASTA_MIGRACOES = path.join(process.cwd(), "drizzle");

async function conectar(): Promise<Banco> {
  const url = process.env.DATABASE_URL;
  if (url) {
    const { Pool } = await import("pg");
    const pool = new Pool({ connectionString: url, max: 10 });
    const banco = drizzlePg(pool, { schema });
    await migratePg(banco, { migrationsFolder: PASTA_MIGRACOES });
    return banco as unknown as Banco;
  }
  if (process.env.NODE_ENV === "production" && process.env.RAILWAY_ENVIRONMENT) throw new Error("DATABASE_URL não definida no Railway");
  const { PGlite } = await import("@electric-sql/pglite");
  const pasta = path.resolve(process.env.BANCO_LOCAL_DIR ?? path.join(process.cwd(), ".dados", "pglite"));
  fs.mkdirSync(path.dirname(pasta), { recursive: true });
  const cliente = new PGlite(pasta);
  const banco = drizzlePglite(cliente, { schema });
  await migratePglite(banco, { migrationsFolder: PASTA_MIGRACOES });
  return banco;
}

// Uma única conexão por processo (sobrevive ao recarregamento do `next dev`)
const global_ = globalThis as unknown as { __banco?: Promise<Banco> };

export function banco(): Promise<Banco> {
  global_.__banco ??= conectar();
  return global_.__banco;
}

export { schema };
