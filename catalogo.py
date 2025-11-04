import streamlit as st
import pandas as pd
import psycopg2
import os
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_card import card

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Catálogo Oficial",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================
# CSS PREMIUM - MESMO ESTILO DO APP PRINCIPAL
# =============================================

st.markdown("""
<style>
    /* Fundo escuro elegante igual ao admin */
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header premium */
    .header-premium {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem 3rem;
        margin: 2rem 0;
        position: relative;
        text-align: center;
    }
    
    .header-premium::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #e88e1b, #f4c220, #ffca02);
        border-radius: 20px 20px 0 0;
    }
    
    /* Cards de veículos premium */
    .vehicle-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 0;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        border-color: rgba(232, 142, 27, 0.3);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
    }
    
    .vehicle-image {
        width: 100%;
        height: 220px;
        object-fit: cover;
        border-radius: 16px 16px 0 0;
    }
    
    .vehicle-badge {
        position: absolute;
        top: 15px;
        right: 15px;
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        z-index: 2;
    }
    
    .vehicle-content {
        padding: 1.5rem;
    }
    
    .vehicle-price {
        color: #e88e1b;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 1rem 0;
        text-align: center;
    }
    
    .vehicle-specs {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .spec-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        color: #a0a0a0;
    }
    
    /* Filtros premium */
    .filter-section {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .stats-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stats-card:hover {
        border-color: rgba(232, 142, 27, 0.3);
        transform: translateY(-2px);
    }
    
    /* Botões premium */
    .stButton>button {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        color: white;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(232, 142, 27, 0.4);
    }
    
    /* Contato flutuante */
    .floating-contact {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 50px;
        box-shadow: 0 8px 30px rgba(232, 142, 27, 0.4);
        z-index: 1000;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Loading personalizado */
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
    }
    
    /* Footer premium */
    .footer-premium {
        background: rgba(255, 255, 255, 0.03);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 3rem 0;
        margin-top: 4rem;
        text-align: center;
    }
    
    /* Esconde elementos do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS - MESMA CONEXÃO DO APP PRINCIPAL
# =============================================

class CatalogoPublico:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        """Conecta ao mesmo banco do app principal"""
        return psycopg2.connect(self.database_url, sslmode='require')
    
    def get_veiculos_estoque(self):
        """Busca apenas veículos em estoque"""
        conn = self.get_connection()
        try:
            query = '''
                SELECT 
                    id, modelo, marca, ano, cor, preco_venda, km, 
                    combustivel, cambio, portas, observacoes, data_cadastro,
                    chassi, renavam, ano_fabricacao, ano_modelo
                FROM veiculos 
                WHERE status = 'Em estoque'
                ORDER BY data_cadastro DESC
            '''
            df = pd.read_sql(query, conn)
            return df.to_dict('records')
        except Exception as e:
            st.error(f"❌ Erro ao carregar veículos: {e}")
            return []
        finally:
            conn.close()
    
    def get_foto_veiculo(self, veiculo_id):
        """Busca foto do veículo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT foto FROM veiculos WHERE id = %s', (veiculo_id,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado and resultado[0] else None
        except:
            return None
        finally:
            conn.close()
    
    def get_estatisticas(self):
        """Busca estatísticas para o dashboard"""
        conn = self.get_connection()
        try:
            # Total de veículos
            query_total = "SELECT COUNT(*) FROM veiculos WHERE status = 'Em estoque'"
            total_veiculos = pd.read_sql(query_total, conn).iloc[0,0]
            
            # Valor total do estoque
            query_valor = "SELECT SUM(preco_venda) FROM veiculos WHERE status = 'Em estoque'"
            valor_estoque = pd.read_sql(query_valor, conn).iloc[0,0] or 0
            
            # Marcas disponíveis
            query_marcas = "SELECT COUNT(DISTINCT marca) FROM veiculos WHERE status = 'Em estoque'"
            total_marcas = pd.read_sql(query_marcas, conn).iloc[0,0]
            
            # Veículo mais novo
            query_novo = "SELECT MAX(ano) FROM veiculos WHERE status = 'Em estoque'"
            ano_mais_novo = pd.read_sql(query_novo, conn).iloc[0,0] or datetime.datetime.now().year
            
            return {
                'total_veiculos': total_veiculos,
                'valor_estoque': valor_estoque,
                'total_marcas': total_marcas,
                'ano_mais_novo': ano_mais_novo
            }
        except Exception as e:
            return {'total_veiculos': 0, 'valor_estoque': 0, 'total_marcas': 0, 'ano_mais_novo': datetime.datetime.now().year}
        finally:
            conn.close()

# =============================================
# COMPONENTES PERSONALIZADOS
# =============================================

def criar_placeholder_image(marca, modelo, ano, width=400, height=250):
    """Cria imagem placeholder personalizada"""
    img = Image.new('RGB', (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Texto centralizado
    texto_principal = f"{marca} {modelo}"
    texto_secundario = f"{ano} • Aguardando fotos"
    
    # Centralizar texto
    bbox_principal = draw.textbbox((0, 0), texto_principal, font=font_large)
    bbox_secundario = draw.textbbox((0, 0), texto_secundario, font=font_small)
    
    x_principal = (width - (bbox_principal[2] - bbox_principal[0])) // 2
    x_secundario = (width - (bbox_secundario[2] - bbox_secundario[0])) // 2
    
    draw.text((x_principal, height//2 - 20), texto_principal, fill=(232, 142, 27), font=font_large)
    draw.text((x_secundario, height//2 + 20), texto_secundario, fill=(160, 160, 160), font=font_small)
    
    # Converter para bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

def criar_card_veiculo(veiculo, catalogo):
    """Cria card premium para cada veículo"""
    foto_bytes = catalogo.get_foto_veiculo(veiculo['id'])
    
    if not foto_bytes:
        foto_bytes = criar_placeholder_image(
            veiculo['marca'], 
            veiculo['modelo'], 
            veiculo['ano']
        )
    
    # Badge de destaque
    badge_text = "⭐ NOVO" if veiculo['ano'] >= datetime.datetime.now().year - 1 else "🚗 SEMINOVO"
    
    # Especificações formatadas
    specs_html = f"""
    <div class="vehicle-specs">
        <div class="spec-item">📅 <span>{veiculo['ano']}</span></div>
        <div class="spec-item">🎨 <span>{veiculo['cor']}</span></div>
        <div class="spec-item">🛣️ <span>{veiculo['km']:,} km</span></div>
        <div class="spec-item">⛽ <span>{veiculo['combustivel']}</span></div>
        <div class="spec-item">⚙️ <span>{veiculo['cambio']}</span></div>
        <div class="spec-item">🚪 <span>{veiculo['portas']} portas</span></div>
    </div>
    """
    
    st.markdown(f"""
    <div class="vehicle-card">
        <div class="vehicle-badge">{badge_text}</div>
        <img src="data:image/png;base64,{foto_bytes.hex()}" class="vehicle-image" onerror="this.style.display='none'">
        <div class="vehicle-content">
            <h3>{veiculo['marca']} {veiculo['modelo']}</h3>
            {specs_html}
            <div class="vehicle-price">R$ {veiculo['preco_venda']:,.2f}</div>
            {f'<p style="color: #a0a0a0; font-size: 0.9rem; margin-top: 1rem;">{veiculo["observacoes"]}</p>' if veiculo["observacoes"] else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão de interesse
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("💬 Tenho interesse", key=f"btn_{veiculo['id']}", use_container_width=True):
            st.session_state[f"veiculo_interesse_{veiculo['id']}"] = True

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header Premium
    col_logo, col_title = st.columns([1, 3])
    
    with col_logo:
        try:
            logo = Image.open("logoca.png")
            st.image(logo, width=120)
        except:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 3rem;">🚗</div>
                <div style="color: #e88e1b; font-weight: bold;">GARAGEM MULTIMARCAS</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_title:
        st.markdown("""
        <div class="header-premium">
            <h1 style="margin:0; font-size: 3rem; background: linear-gradient(135deg, #ffffff, #e0e0e0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800;">
                Catálogo Premium
            </h1>
            <p style="margin:0; color: #a0a0a0; font-size: 1.2rem; margin-top: 0.5rem;">
                Os melhores veículos seminovos com procedência garantida
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Inicializar catálogo
    catalogo = CatalogoPublico()
    
    # Dashboard de Estatísticas
    st.markdown("### 📊 Nosso Estoque em Números")
    estatisticas = catalogo.get_estatisticas()
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    with col_stats1:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 2rem;">🚗</div>
            <h3>{estatisticas['total_veiculos']}</h3>
            <p style="color: #a0a0a0; margin: 0;">Veículos Disponíveis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stats2:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 2rem;">💰</div>
            <h3>R$ {estatisticas['valor_estoque']:,.0f}</h3>
            <p style="color: #a0a0a0; margin: 0;">Valor em Estoque</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stats3:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 2rem;">🏷️</div>
            <h3>{estatisticas['total_marcas']}</h3>
            <p style="color: #a0a0a0; margin: 0;">Marcas Diferentes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stats4:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 2rem;">⭐</div>
            <h3>{estatisticas['ano_mais_novo']}</h3>
            <p style="color: #a0a0a0; margin: 0;">Ano Mais Recente</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de Filtros
    st.markdown("### 🔍 Encontre Seu Veículo Ideal")
    
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
        
        with col_filtro1:
            filtro_marca = st.selectbox("**Marca**", ["Todas as Marcas"])
        
        with col_filtro2:
            filtro_ano_min = st.slider("**Ano Mínimo**", 1970, 2030, 2015, 
                                     help="Selecione o ano mínimo do veículo")
        
        with col_filtro3:
            filtro_preco_max = st.slider("**Preço Máximo**", 0, 500000, 150000, 10000,
                                       format="R$ %d",
                                       help="Defina seu orçamento máximo")
        
        with col_filtro4:
            filtro_combustivel = st.selectbox("**Combustível**", 
                                            ["Todos", "Gasolina", "Álcool", "Flex", "Diesel", "Elétrico"])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Carregar veículos
    with st.spinner('🚗 Carregando nosso estoque premium...'):
        veiculos = catalogo.get_veiculos_estoque()
    
    # Atualizar opções de marca
    if veiculos:
        marcas_disponiveis = sorted(list(set([v['marca'] for v in veiculos])))
        # Aqui precisaríamos de um workaround para atualizar o selectbox dinamicamente
    
    # Aplicar filtros
    veiculos_filtrados = []
    for veiculo in veiculos:
        if filtro_marca != "Todas as Marcas" and veiculo['marca'] != filtro_marca:
            continue
        if veiculo['ano'] < filtro_ano_min:
            continue
        if veiculo['preco_venda'] > filtro_preco_max:
            continue
        if filtro_combustivel != "Todos" and veiculo['combustivel'] != filtro_combustivel:
            continue
        veiculos_filtrados.append(veiculo)
    
    # Exibir resultados
    if veiculos_filtrados:
        st.markdown(f"### 🎯 {len(veiculos_filtrados)} Veículos Encontrados")
        st.markdown(f"<p style='color: #a0a0a0;'>Filtros aplicados: {filtro_marca} • A partir de {filtro_ano_min} • Até R$ {filtro_preco_max:,.0f}</p>", 
                   unsafe_allow_html=True)
        
        # Grid de veículos
        cols = st.columns(3)
        for i, veiculo in enumerate(veiculos_filtrados):
            with cols[i % 3]:
                criar_card_veiculo(veiculo, catalogo)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 4rem; background: rgba(255,255,255,0.03); border-radius: 16px;">
            <div style="font-size: 4rem;">🔍</div>
            <h3>Nenhum veículo encontrado</h3>
            <p style="color: #a0a0a0;">Tente ajustar os filtros para encontrar mais opções</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de Contato
    st.markdown("---")
    st.markdown("### 📞 Pronto para Agendar uma Visita?")
    
    col_contato1, col_contato2, col_contato3 = st.columns(3)
    
    with col_contato1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem;">📞</div>
            <h4>Telefone</h4>
            <p style="color: #e88e1b; font-size: 1.2rem; font-weight: bold;">(84) 99999-9999</p>
            <p style="color: #a0a0a0;">Atendimento personalizado</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_contato2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem;">📍</div>
            <h4>Endereço</h4>
            <p style="color: #e88e1b; font-size: 1.1rem; font-weight: bold;">Av. Principal, 123</p>
            <p style="color: #a0a0a0;">Mossoró/RN - Centro</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_contato3:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem;">🕒</div>
            <h4>Horário</h4>
            <p style="color: #e88e1b; font-size: 1.1rem; font-weight: bold;">Segunda a Sexta</p>
            <p style="color: #a0a0a0;">8h às 18h • Sábado 8h às 12h</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer Premium
    st.markdown("""
    <div class="footer-premium">
        <p style="margin: 0; color: #a0a0a0; font-size: 0.9rem;">
            © 2024 Garagem Multimarcas - Todos os direitos reservados
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.8rem;">
            Veículos seminovos com procedência garantida • Financiamento facilitado • Troca bem avaliada
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão flutuante de WhatsApp
    st.markdown("""
    <div class="floating-contact">
        <span>💬</span>
        Fale pelo WhatsApp
    </div>
    """, unsafe_allow_html=True)

# =============================================
# EXECUÇÃO
# =============================================

if __name__ == "__main__":
    main()
