import { BarraSuperior } from "@/components/painel/barra-superior";
import { FormAcao } from "@/components/interativos";
import { Campo, Cartao, classeCampo } from "@/components/ui";
import { alterarSenha, salvarLoja } from "@/lib/acoes/configuracoes";
import { dadosLoja } from "@/lib/consultas/configuracoes";
import { cn } from "@/lib/cn";

export const metadata = { title: "Configurações" };

export default async function Configuracoes() {
  const loja = await dadosLoja();
  return (
    <>
      <BarraSuperior titulo="Configurações" trilha={[{ rotulo: "Painel", href: "/painel" }, { rotulo: "Configurações" }]} />
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
        <Cartao titulo="Dados da loja">
          <p className="-mt-2 mb-4 text-sm text-nevoa">Aparecem na vitrine, no botão de WhatsApp e nos contratos, recibos e termos.</p>
          <FormAcao acao={salvarLoja} rotulo="Salvar dados da loja" limparAoConcluir={false}>
            <div className="grid gap-3 md:grid-cols-2">
              <Campo rotulo="Razão social / nome no contrato">
                <input name="razaoSocial" defaultValue={loja.razaoSocial} className={classeCampo} />
              </Campo>
              <Campo rotulo="CNPJ">
                <input name="cnpj" defaultValue={loja.cnpj} className={classeCampo} placeholder="00.000.000/0001-00" />
              </Campo>
              <Campo rotulo="WhatsApp (com 55 e DDD)" dica="Usado nos botões da vitrine">
                <input name="whatsapp" defaultValue={loja.whatsapp} className={cn(classeCampo, "num")} />
              </Campo>
              <Campo rotulo="Telefone exibido">
                <input name="telefone" defaultValue={loja.telefone} className={classeCampo} />
              </Campo>
              <Campo rotulo="Endereço">
                <input name="endereco" defaultValue={loja.endereco} className={classeCampo} />
              </Campo>
              <Campo rotulo="Cidade/UF">
                <input name="cidade" defaultValue={loja.cidade} className={classeCampo} />
              </Campo>
              <Campo rotulo="CEP">
                <input name="cep" defaultValue={loja.cep} className={cn(classeCampo, "num")} />
              </Campo>
            </div>
            <h3 className="display pt-3 text-base font-semibold">Simulação de parcela na vitrine</h3>
            <div className="grid gap-3 md:grid-cols-3">
              <Campo rotulo="Entrada (%)">
                <input name="entradaPct" defaultValue={loja.simulacao.entradaPct} inputMode="decimal" className={cn(classeCampo, "num")} />
              </Campo>
              <Campo rotulo="Taxa ao mês (%)">
                <input name="taxaMensalPct" defaultValue={String(loja.simulacao.taxaMensalPct).replace(".", ",")} inputMode="decimal" className={cn(classeCampo, "num")} />
              </Campo>
              <Campo rotulo="Parcelas">
                <input name="meses" defaultValue={loja.simulacao.meses} inputMode="numeric" className={cn(classeCampo, "num")} />
              </Campo>
            </div>
          </FormAcao>
        </Cartao>

        <div className="space-y-5">
          <Cartao titulo="Trocar senha">
            <FormAcao acao={alterarSenha} rotulo="Trocar senha" variante="secundario">
              <Campo rotulo="Senha atual">
                <input name="atual" type="password" autoComplete="current-password" required className={classeCampo} />
              </Campo>
              <Campo rotulo="Nova senha" dica="Pelo menos 8 caracteres">
                <input name="nova" type="password" autoComplete="new-password" minLength={8} required className={classeCampo} />
              </Campo>
              <Campo rotulo="Confirmar nova senha">
                <input name="confirmar" type="password" autoComplete="new-password" minLength={8} required className={classeCampo} />
              </Campo>
            </FormAcao>
          </Cartao>
          <Cartao titulo="Sobre os dados">
            <ul className="space-y-2 text-sm text-nevoa">
              <li>Fotos e documentos ficam fora do banco de dados, e as fotos perdem a localização (GPS) ao serem enviadas.</li>
              <li>A vitrine nunca mostra custo, preço mínimo, placa, chassi ou RENAVAM.</li>
              <li>Contas bancárias e saldos iniciais são ajustados no Fluxo de caixa.</li>
            </ul>
          </Cartao>
        </div>
      </div>
    </>
  );
}
