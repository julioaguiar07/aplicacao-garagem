CREATE TABLE "clientes" (
	"id" serial PRIMARY KEY NOT NULL,
	"nome" text NOT NULL,
	"telefone" text,
	"email" text,
	"cpf" text,
	"endereco" text,
	"cidade" text,
	"origem" text,
	"interesse" text,
	"observacoes" text,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "configuracoes" (
	"chave" text PRIMARY KEY NOT NULL,
	"valor" jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "contas" (
	"id" serial PRIMARY KEY NOT NULL,
	"nome" text NOT NULL,
	"tipo" text DEFAULT 'banco' NOT NULL,
	"saldo_inicial" integer DEFAULT 0 NOT NULL,
	"ativa" boolean DEFAULT true NOT NULL
);
--> statement-breakpoint
CREATE TABLE "custos_venda" (
	"id" serial PRIMARY KEY NOT NULL,
	"venda_id" integer NOT NULL,
	"tipo" text NOT NULL,
	"descricao" text,
	"valor" integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE "documentos" (
	"id" serial PRIMARY KEY NOT NULL,
	"veiculo_id" integer,
	"venda_id" integer,
	"tipo" text NOT NULL,
	"nome_arquivo" text NOT NULL,
	"chave" text NOT NULL,
	"mime" text NOT NULL,
	"tamanho" integer NOT NULL,
	"validade" date,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "eventos" (
	"id" serial PRIMARY KEY NOT NULL,
	"veiculo_id" integer,
	"venda_id" integer,
	"cliente_id" integer,
	"titulo" text NOT NULL,
	"detalhe" text,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "fotos" (
	"id" serial PRIMARY KEY NOT NULL,
	"veiculo_id" integer NOT NULL,
	"chave_original" text NOT NULL,
	"chave_card" text NOT NULL,
	"foco_y" double precision DEFAULT 0.57 NOT NULL,
	"ordem" integer DEFAULT 0 NOT NULL,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "gastos" (
	"id" serial PRIMARY KEY NOT NULL,
	"veiculo_id" integer NOT NULL,
	"data" date NOT NULL,
	"categoria" text NOT NULL,
	"descricao" text NOT NULL,
	"valor" integer NOT NULL,
	"nota_chave" text,
	"lancamento_id" integer,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "lancamentos" (
	"id" serial PRIMARY KEY NOT NULL,
	"tipo" text NOT NULL,
	"descricao" text NOT NULL,
	"categoria" text NOT NULL,
	"valor" integer NOT NULL,
	"vencimento" date NOT NULL,
	"pago_em" date,
	"conta_id" integer,
	"veiculo_id" integer,
	"venda_id" integer,
	"pagamento_id" integer,
	"cliente_id" integer,
	"parcela" integer,
	"total_parcelas" integer,
	"grupo_recorrencia" text,
	"comprovante_chave" text,
	"observacoes" text,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "pagamentos" (
	"id" serial PRIMARY KEY NOT NULL,
	"venda_id" integer NOT NULL,
	"forma" text NOT NULL,
	"valor" integer NOT NULL,
	"detalhes" jsonb DEFAULT '{}'::jsonb NOT NULL,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "veiculos" (
	"id" serial PRIMARY KEY NOT NULL,
	"slug" text NOT NULL,
	"marca" text NOT NULL,
	"modelo" text NOT NULL,
	"versao" text,
	"ano_modelo" integer NOT NULL,
	"ano_fabricacao" integer,
	"cor" text,
	"km" integer,
	"categoria" text DEFAULT 'Hatch' NOT NULL,
	"cambio" text DEFAULT 'Manual' NOT NULL,
	"combustivel" text DEFAULT 'Flex' NOT NULL,
	"portas" integer,
	"placa" text,
	"chassi" text,
	"renavam" text,
	"opcionais" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"destaques" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"descricao" text,
	"status" text DEFAULT 'disponivel' NOT NULL,
	"publicado" boolean DEFAULT false NOT NULL,
	"origem" text DEFAULT 'compra' NOT NULL,
	"fornecedor" text,
	"cliente_origem_id" integer,
	"data_entrada" date NOT NULL,
	"custo" integer NOT NULL,
	"preco" integer NOT NULL,
	"desconto_maximo_pct" double precision DEFAULT 5 NOT NULL,
	"preco_fipe" integer,
	"codigo_fipe" text,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL,
	"atualizado_em" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "veiculos_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "vendas" (
	"id" serial PRIMARY KEY NOT NULL,
	"veiculo_id" integer NOT NULL,
	"cliente_id" integer NOT NULL,
	"etapa" text DEFAULT 'negociacao' NOT NULL,
	"preco_final" integer NOT NULL,
	"data_venda" date NOT NULL,
	"observacoes" text,
	"criado_em" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "custos_venda" ADD CONSTRAINT "custos_venda_venda_id_vendas_id_fk" FOREIGN KEY ("venda_id") REFERENCES "public"."vendas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documentos" ADD CONSTRAINT "documentos_veiculo_id_veiculos_id_fk" FOREIGN KEY ("veiculo_id") REFERENCES "public"."veiculos"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documentos" ADD CONSTRAINT "documentos_venda_id_vendas_id_fk" FOREIGN KEY ("venda_id") REFERENCES "public"."vendas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "eventos" ADD CONSTRAINT "eventos_veiculo_id_veiculos_id_fk" FOREIGN KEY ("veiculo_id") REFERENCES "public"."veiculos"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "eventos" ADD CONSTRAINT "eventos_venda_id_vendas_id_fk" FOREIGN KEY ("venda_id") REFERENCES "public"."vendas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "eventos" ADD CONSTRAINT "eventos_cliente_id_clientes_id_fk" FOREIGN KEY ("cliente_id") REFERENCES "public"."clientes"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "fotos" ADD CONSTRAINT "fotos_veiculo_id_veiculos_id_fk" FOREIGN KEY ("veiculo_id") REFERENCES "public"."veiculos"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "gastos" ADD CONSTRAINT "gastos_veiculo_id_veiculos_id_fk" FOREIGN KEY ("veiculo_id") REFERENCES "public"."veiculos"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "gastos" ADD CONSTRAINT "gastos_lancamento_id_lancamentos_id_fk" FOREIGN KEY ("lancamento_id") REFERENCES "public"."lancamentos"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "lancamentos" ADD CONSTRAINT "lancamentos_conta_id_contas_id_fk" FOREIGN KEY ("conta_id") REFERENCES "public"."contas"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "lancamentos" ADD CONSTRAINT "lancamentos_veiculo_id_veiculos_id_fk" FOREIGN KEY ("veiculo_id") REFERENCES "public"."veiculos"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "lancamentos" ADD CONSTRAINT "lancamentos_venda_id_vendas_id_fk" FOREIGN KEY ("venda_id") REFERENCES "public"."vendas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "lancamentos" ADD CONSTRAINT "lancamentos_pagamento_id_pagamentos_id_fk" FOREIGN KEY ("pagamento_id") REFERENCES "public"."pagamentos"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "lancamentos" ADD CONSTRAINT "lancamentos_cliente_id_clientes_id_fk" FOREIGN KEY ("cliente_id") REFERENCES "public"."clientes"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "pagamentos" ADD CONSTRAINT "pagamentos_venda_id_vendas_id_fk" FOREIGN KEY ("venda_id") REFERENCES "public"."vendas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "veiculos" ADD CONSTRAINT "veiculos_cliente_origem_id_clientes_id_fk" FOREIGN KEY ("cliente_origem_id") REFERENCES "public"."clientes"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "vendas" ADD CONSTRAINT "vendas_veiculo_id_veiculos_id_fk" FOREIGN KEY ("veiculo_id") REFERENCES "public"."veiculos"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "vendas" ADD CONSTRAINT "vendas_cliente_id_clientes_id_fk" FOREIGN KEY ("cliente_id") REFERENCES "public"."clientes"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "clientes_nome_idx" ON "clientes" USING btree ("nome");--> statement-breakpoint
CREATE INDEX "eventos_criado_idx" ON "eventos" USING btree ("criado_em");--> statement-breakpoint
CREATE INDEX "lancamentos_vencimento_idx" ON "lancamentos" USING btree ("vencimento");--> statement-breakpoint
CREATE INDEX "veiculos_status_idx" ON "veiculos" USING btree ("status");