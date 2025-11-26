import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
import os
import base64
from PIL import Image
import io
import math
import random

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Veículos Premium em Mossoró",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================
# CSS PROFISSIONAL - ESTILO APP.PY
# =============================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem;
        padding-right: 2rem;
        background: transparent;
    }
    
    .header-premium {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0 2rem 0;
        position: relative;
    }
    
    .header-premium::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #e88e1b, #f4c220, #ffca02);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .vehicle-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        border-color: rgba(232, 142, 27, 0.3);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
    }
    
    .vehicle-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
    }
    
    .vehicle-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }
    
    .vehicle-subtitle {
        color: #a0a0a0;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        line-height: 1.4;
    }
    
    .vehicle-features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-tag {
        background: rgba(255, 255, 255, 0.08);
        color: #e0e0e0;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 500;
    }
    
    .price-section {
        margin-top: auto;
        padding-top: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .vehicle-price {
        font-size: 1.6rem;
        font-weight: 800;
        color: #e88e1b;
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    
    .price-label {
        font-size: 0.75rem;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .financing-info {
        font-size: 0.8rem;
        color: #a0a0a0;
        margin-top: 0.5rem;
    }
    
    .badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        margin-right: 0.5rem;
    }
    
    .badge-new {
        background: linear-gradient(135deg, #27ae60, #219a52);
        color: white;
    }
    
    .badge-lowkm {
        background: linear-gradient(135deg, #e88e1b, #d87e0b);
        color: white;
    }
    
    .badge-promo {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        color: white;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 0.5rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(232, 142, 27, 0.4);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
        text-align: center;
        width: 100%;
        margin-top: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .btn-whatsapp:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
    }
    
    .filter-section {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .filter-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #ffffff;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 4rem 0;
        text-align: center;
        margin-bottom: 3rem;
        border-radius: 0 0 20px 20px;
    }
    
    .contact-info {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    
    .contact-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #e88e1b;
        font-weight: 500;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Animações */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS
# =============================================

class WebsiteDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        if self.database_url:
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            return psycopg2.connect(self.database_url, sslmode='require')
        return None
    
    def get_veiculos_estoque(self):
        """Busca veículos em estoque"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, modelo, ano, marca, cor, preco_venda, 
                       km, placa, combustivel, cambio, portas, observacoes,
                       data_cadastro, preco_entrada
                FROM veiculos 
                WHERE status = 'Em estoque'
                ORDER BY data_cadastro DESC
            ''')
            
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            veiculos = []
            for row in resultados:
                veiculo = dict(zip(colunas, row))
                veiculo['idade'] = datetime.now().year - veiculo['ano']
                if veiculo['preco_entrada']:
                    margem = ((veiculo['preco_venda'] - veiculo['preco_entrada']) / veiculo['preco_entrada']) * 100
                    veiculo['margem'] = margem
                else:
                    veiculo['margem'] = 0
                    
                veiculos.append(veiculo)
            
            return veiculos
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar veículos: {e}")
            return []
        finally:
            if conn:
                conn.close()

# =============================================
# COMPONENTES DA VITRINE
# =============================================

def generate_vehicle_image(veiculo):
    """Gera imagem do veículo"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '1a1a1a', 'Branco': 'ffffff',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513',
        'Bege': 'f5deb3', 'Dourado': 'd4af37', 'Vinho': '722f37'
    }
    
    color_hex = color_map.get(veiculo['cor'], '3498db')
    texto = f"{veiculo['marca']}+{veiculo['modelo']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={texto}"

def render_vehicle_card(veiculo, index):
    """Renderiza card do veículo"""
    image_url = generate_vehicle_image(veiculo)
    
    # Determinar badges
    badges = []
    if veiculo['idade'] <= 1:
        badges.append(('🆕 NOVO', 'badge-new'))
    elif veiculo['km'] < 30000:
        badges.append(('🛣️ BAIXA KM', 'badge-lowkm'))
    
    if veiculo.get('margem', 0) > 25:
        badges.append(('💎 PROMOÇÃO', 'badge-promo'))
    
    # Calcular parcelas
    entrada = veiculo['preco_venda'] * 0.2
    parcelas = (veiculo['preco_venda'] - entrada) / 48
    
    # Usar container do Streamlit em vez de HTML para evitar nesting
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f'<img src="{image_url}" class="vehicle-image" alt="{veiculo["marca"]} {veiculo["modelo"]}">', unsafe_allow_html=True)
        
        with col2:
            for text, badge_class in badges:
                st.markdown(f'<div class="badge {badge_class}">{text}</div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="vehicle-title">{veiculo["marca"]} {veiculo["modelo"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vehicle-subtitle">📅 {veiculo["ano"]} • 🛣️ {veiculo["km"]:,} km • 🎨 {veiculo["cor"]}</div>', unsafe_allow_html=True)
            
            # Features
            col_feat1, col_feat2, col_feat3 = st.columns(3)
            with col_feat1:
                st.markdown(f'<div class="feature-tag">⚙️ {veiculo["cambio"]}</div>', unsafe_allow_html=True)
            with col_feat2:
                st.markdown(f'<div class="feature-tag">⛽ {veiculo["combustivel"]}</div>', unsafe_allow_html=True)
            with col_feat3:
                st.markdown(f'<div class="feature-tag">🚪 {veiculo["portas"]}</div>', unsafe_allow_html=True)
    
    # Preço e botões
    st.markdown(f'''
    <div class="price-section">
        <div class="price-label">PREÇO À VISTA</div>
        <div class="vehicle-price">R$ {veiculo["preco_venda"]:,.2f}</div>
        <div class="financing-info">Ou R$ {entrada:,.2f} + 48x de R$ {parcelas:,.2f}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botões - usando columns do Streamlit corretamente
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("🔍 Ver Detalhes", key=f"details_{veiculo['id']}_{index}", use_container_width=True):
            st.session_state[f"modal_{veiculo['id']}"] = True
    
    with btn_col2:
        whatsapp_msg = f"Olá! Gostaria de mais informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}"
        whatsapp_url = f"https://wa.me/5584981885353?text={whatsapp_msg.replace(' ', '%20')}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="btn-whatsapp">💬 WhatsApp</a>', unsafe_allow_html=True)

def render_filters(veiculos):
    """Renderiza filtros na sidebar"""
    with st.sidebar:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">🔍 Filtros</div>', unsafe_allow_html=True)
        
        # Busca
        busca = st.text_input("Buscar veículo", placeholder="Marca, modelo...")
        
        # Filtros principais
        marcas = ["Todas"] + sorted(list(set([v['marca'] for v in veiculos])))
        marca = st.selectbox("Marca", marcas)
        
        if veiculos:
            anos = ["Todos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano = st.selectbox("Ano", anos)
            
            preco_min = min(v['preco_venda'] for v in veiculos)
            preco_max = max(v['preco_venda'] for v in veiculos)
            preco_range = st.slider("Faixa de Preço", int(preco_min), int(preco_max), 
                                  (int(preco_min), int(preco_max)))
        
        combustiveis = list(set([v['combustivel'] for v in veiculos]))
        combustivel = st.multiselect("Combustível", combustiveis, default=combustiveis)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return {
            'busca': busca,
            'marca': marca,
            'ano': ano,
            'preco_range': preco_range if veiculos else (0, 100000),
            'combustivel': combustivel
        }

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header com logo
    col_logo, col_title, col_contact = st.columns([1, 2, 1])
    
    with col_logo:
        try:
            # Tenta carregar a logo
            logo = Image.open("logoca.png")
            st.image(logo, width=120)
        except:
            st.markdown("""
            <div style="font-size: 3rem; text-align: center;">
                🚗
            </div>
            """, unsafe_allow_html=True)
    
    with col_title:
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="margin:0; font-size: 2.2rem; background: linear-gradient(135deg, #ffffff, #e0e0e0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800;">
                Garagem Multimarcas
            </h1>
            <p style="margin:0; color: #a0a0a0; font-size: 1rem;">Veículos Premium em Mossoró</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_contact:
        st.markdown("""
        <div style="text-align: right;">
            <p style="margin:0; font-weight: 600; color: #e88e1b;">(84) 98188-5353</p>
            <p style="margin:0; color: #a0a0a0; font-size: 0.8rem;">Mossoró/RN</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 style="color: white; font-size: 3rem; margin-bottom: 1rem;">Encontre Seu Carro dos Sonhos</h1>
        <p style="color: #ccc; font-size: 1.2rem; max-width: 600px; margin: 0 auto;">
            Os melhores veículos novos e seminovos com condições especiais de pagamento
        </p>
        <div class="contact-info">
            <div class="contact-item">📞 (84) 98188-5353</div>
            <div class="contact-item">📍 Mossoró/RN</div>
            <div class="contact-item">⏰ Seg-Sex: 8h-18h</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar dados
    db = WebsiteDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Layout principal
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        if veiculos:
            filtros = render_filters(veiculos)
        else:
            filtros = {}
    
    with col_main:
        st.markdown("""
        <div class="glass-card">
            <h2>🚗 Veículos Disponíveis</h2>
            <p style="color: #a0a0a0;">Confira nosso estoque selecionado</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Aplicar filtros
        if veiculos and filtros:
            veiculos_filtrados = veiculos.copy()
            
            if filtros['busca']:
                busca_lower = filtros['busca'].lower()
                veiculos_filtrados = [v for v in veiculos_filtrados 
                                    if busca_lower in v['marca'].lower() 
                                    or busca_lower in v['modelo'].lower()]
            
            if filtros['marca'] != "Todas":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == filtros['marca']]
            
            if filtros['ano'] != "Todos":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == filtros['ano']]
            
            if 'preco_range' in filtros:
                veiculos_filtrados = [v for v in veiculos_filtrados 
                                    if filtros['preco_range'][0] <= v['preco_venda'] <= filtros['preco_range'][1]]
            
            if filtros['combustivel']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v['combustivel'] in filtros['combustivel']]
        else:
            veiculos_filtrados = veiculos
        
        # Ordenação
        if veiculos_filtrados:
            ordenacao = st.selectbox("Ordenar por", 
                                   ["Mais recentes", "Menor preço", "Maior preço", "Mais novo", "Menor KM"])
            
            if ordenacao == "Menor preço":
                veiculos_filtrados.sort(key=lambda x: x['preco_venda'])
            elif ordenacao == "Maior preço":
                veiculos_filtrados.sort(key=lambda x: x['preco_venda'], reverse=True)
            elif ordenacao == "Mais novo":
                veiculos_filtrados.sort(key=lambda x: x['ano'], reverse=True)
            elif ordenacao == "Menor KM":
                veiculos_filtrados.sort(key=lambda x: x['km'])
            else:
                veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
        
        # Exibir veículos
        if not veiculos_filtrados:
            st.info("""
            ## 🔍 Nenhum veículo encontrado
            *Tente ajustar os filtros para encontrar o veículo ideal!*
            
            **📞 Entre em contato:** (84) 98188-5353
            """)
        else:
            st.markdown(f'<div style="color: #a0a0a0; margin-bottom: 2rem;">Encontramos {len(veiculos_filtrados)} veículo(s)</div>', unsafe_allow_html=True)
            
            # Grid de veículos
            for i, veiculo in enumerate(veiculos_filtrados):
                with st.container():
                    st.markdown('<div class="vehicle-card fade-in">', unsafe_allow_html=True)
                    render_vehicle_card(veiculo, i)
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #a0a0a0; padding: 2rem;">
        <p style="margin: 0; font-size: 0.9rem; font-weight: 600; color: #e88e1b;">Garagem Multimarcas</p>
        <p style="margin: 0; font-size: 0.8rem;">Seu parceiro automotivo em Mossoró</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.7rem; color: #666;">
            © 2024 Garagem Multimarcas - Todos os direitos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
