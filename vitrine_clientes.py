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
# CSS PROFISSIONAL - ESTILO WEBMOTORS
# =============================================

st.markdown("""
<style>
    /* Reset e configurações gerais */
    .stApp {
        background: #ffffff;
        color: #333333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
    }
    
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: 100%;
    }
    
    /* Esconde elementos do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Header profissional */
    .main-header {
        background: #1a1a1a;
        color: white;
        padding: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .contact-bar {
        background: #e88e1b;
        color: white;
        padding: 0.5rem 0;
        font-weight: 600;
        text-align: center;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: white;
        padding: 3rem 0;
        text-align: center;
    }
    
    /* Sistema de grid profissional */
    .vehicle-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Card de veículo - estilo WebMotors */
    .vehicle-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        overflow: hidden;
        transition: all 0.3s ease;
        border: 1px solid #e8e8e8;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .vehicle-image-container {
        position: relative;
        width: 100%;
        height: 200px;
        overflow: hidden;
    }
    
    .vehicle-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .vehicle-badges {
        position: absolute;
        top: 10px;
        left: 10px;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .badge-new {
        background: #e74c3c;
        color: white;
    }
    
    .badge-lowkm {
        background: #27ae60;
        color: white;
    }
    
    .badge-promo {
        background: #e88e1b;
        color: white;
    }
    
    .vehicle-content {
        padding: 1rem;
    }
    
    .vehicle-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }
    
    .vehicle-subtitle {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    .vehicle-features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-tag {
        background: #f8f9fa;
        color: #555;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        border: 1px solid #e8e8e8;
    }
    
    .price-section {
        border-top: 1px solid #e8e8e8;
        padding-top: 1rem;
    }
    
    .vehicle-price {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e88e1b;
        margin-bottom: 0.25rem;
    }
    
    .price-label {
        font-size: 0.75rem;
        color: #666;
        text-transform: uppercase;
    }
    
    .financing-info {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    /* Botões profissionais */
    .btn-primary {
        background: #e88e1b;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        text-align: center;
        width: 100%;
        margin-top: 0.5rem;
        transition: background 0.3s ease;
    }
    
    .btn-primary:hover {
        background: #d87e0b;
        color: white;
        text-decoration: none;
    }
    
    .btn-whatsapp {
        background: #25D366;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        text-align: center;
        width: 100%;
        margin-top: 0.5rem;
        transition: background 0.3s ease;
    }
    
    .btn-whatsapp:hover {
        background: #20bd5c;
        color: white;
        text-decoration: none;
    }
    
    /* Filtros sidebar */
    .filter-section {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e8e8e8;
    }
    
    .filter-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1a1a1a;
    }
    
    /* Modal de detalhes */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 2rem;
    }
    
    .modal-content {
        background: white;
        border-radius: 12px;
        max-width: 1000px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .vehicle-grid {
            grid-template-columns: 1fr;
        }
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
                veiculos.append(veiculo)
            
            return veiculos
            
        except Exception as e:
            return []
        finally:
            if conn:
                conn.close()

# =============================================
# COMPONENTES PROFISSIONAIS
# =============================================

def generate_vehicle_image(veiculo):
    """Gera imagem realista do veículo"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '1a1a1a', 'Branco': 'ffffff',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513'
    }
    
    color_hex = color_map.get(veiculo['cor'], '3498db')
    texto = f"{veiculo['marca']}+{veiculo['modelo']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={texto}"

def render_vehicle_card(veiculo, index):
    """Renderiza card profissional do veículo"""
    image_url = generate_vehicle_image(veiculo)
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges = []
    if idade <= 1:
        badges.append(('🆕 NOVO', 'badge-new'))
    if veiculo['km'] < 30000:
        badges.append(('🛣️ BAIXA KM', 'badge-lowkm'))
    
    # Calcular parcelas
    entrada = veiculo['preco_venda'] * 0.2
    parcelas = (veiculo['preco_venda'] - entrada) / 48
    
    # Gerar HTML do card
    html = f'''
    <div class="vehicle-card">
        <div class="vehicle-image-container">
            <img src="{image_url}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
            <div class="vehicle-badges">
                {''.join([f'<div class="badge {badge_class}">{text}</div>' for text, badge_class in badges])}
            </div>
        </div>
        
        <div class="vehicle-content">
            <div class="vehicle-title">{veiculo['marca']} {veiculo['modelo']}</div>
            <div class="vehicle-subtitle">
                📅 {veiculo['ano']} • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}
            </div>
            
            <div class="vehicle-features">
                <span class="feature-tag">⚙️ {veiculo['cambio']}</span>
                <span class="feature-tag">⛽ {veiculo['combustivel']}</span>
                <span class="feature-tag">🚪 {veiculo['portas']} portas</span>
            </div>
            
            <div class="price-section">
                <div class="price-label">PREÇO À VISTA</div>
                <div class="vehicle-price">R$ {veiculo['preco_venda']:,.2f}</div>
                <div class="financing-info">
                    Ou R$ {entrada:,.2f} + 48x de R$ {parcelas:,.2f}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 1rem;">
                <button onclick="window.showVehicleDetails({index})" class="btn-primary">
                    🔍 Ver Detalhes
                </button>
                <a href="https://wa.me/5584981885353?text=Olá! Gostaria de mais informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}" 
                   target="_blank" class="btn-whatsapp">
                    💬 WhatsApp
                </a>
            </div>
        </div>
    </div>
    '''
    
    # Usar st.markdown para renderizar o HTML
    st.markdown(html, unsafe_allow_html=True)

def render_vehicle_modal(veiculo):
    """Modal de detalhes do veículo"""
    image_url = generate_vehicle_image(veiculo)
    
    # Cálculos financeiros
    entrada = veiculo['preco_venda'] * 0.2
    parcelas_48 = (veiculo['preco_venda'] - entrada) / 48
    parcelas_36 = (veiculo['preco_venda'] - entrada) / 36
    parcelas_24 = (veiculo['preco_venda'] - entrada) / 24
    
    html = f'''
    <div class="modal-overlay" id="modal-{veiculo['id']}">
        <div class="modal-content">
            <div style="padding: 2rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3rem;">
                    <!-- Galeria de imagens -->
                    <div>
                        <img src="{image_url}" style="width: 100%; border-radius: 8px; margin-bottom: 1rem;">
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;">
                            <img src="{image_url}" style="width: 100%; height: 80px; object-fit: cover; border-radius: 4px;">
                            <div style="background: #f8f9fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #666;">
                                + Fotos
                            </div>
                            <div style="background: #f8f9fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #666;">
                                + Fotos
                            </div>
                        </div>
                    </div>
                    
                    <!-- Informações do veículo -->
                    <div>
                        <h1 style="margin: 0 0 0.5rem 0; color: #1a1a1a;">{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}</h1>
                        <div style="color: #666; margin-bottom: 2rem;">
                            📅 {datetime.now().year - veiculo['ano']} ano(s) • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}
                        </div>
                        
                        <!-- Preço -->
                        <div style="background: #fff9e6; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
                            <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">PREÇO À VISTA</div>
                            <div style="font-size: 2rem; font-weight: 700; color: #e88e1b;">R$ {veiculo['preco_venda']:,.2f}</div>
                        </div>
                        
                        <!-- Especificações -->
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1a1a1a; margin-bottom: 1rem;">📊 Especificações Técnicas</h3>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                <div>
                                    <strong>Combustível</strong><br>
                                    <span style="color: #666;">{veiculo['combustivel']}</span>
                                </div>
                                <div>
                                    <strong>Câmbio</strong><br>
                                    <span style="color: #666;">{veiculo['cambio']}</span>
                                </div>
                                <div>
                                    <strong>Portas</strong><br>
                                    <span style="color: #666;">{veiculo['portas']}</span>
                                </div>
                                <div>
                                    <strong>Placa</strong><br>
                                    <span style="color: #666;">{veiculo['placa'] or 'Não informada'}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Financiamento -->
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1a1a1a; margin-bottom: 1rem;">💳 Simular Financiamento</h3>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                                    <div style="font-weight: 600; color: #e88e1b;">24x</div>
                                    <div style="font-size: 1.1rem; font-weight: 700;">R$ {parcelas_24:,.2f}</div>
                                </div>
                                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                                    <div style="font-weight: 600; color: #e88e1b;">36x</div>
                                    <div style="font-size: 1.1rem; font-weight: 700;">R$ {parcelas_36:,.2f}</div>
                                </div>
                                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                                    <div style="font-weight: 600; color: #e88e1b;">48x</div>
                                    <div style="font-size: 1.1rem; font-weight: 700;">R$ {parcelas_48:,.2f}</div>
                                </div>
                            </div>
                            <div style="color: #666; font-size: 0.9rem;">
                                *Entrada de R$ {entrada:,.2f} (20%). Condições sujeitas à análise.
                            </div>
                        </div>
                        
                        <!-- Botões de ação -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <a href="https://wa.me/5584981885353?text=Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}" 
                               target="_blank" class="btn-whatsapp">
                                💬 Falar no WhatsApp
                            </a>
                            <button onclick="window.closeModal()" class="btn-primary">
                                📞 Ligar Agora
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return html

def render_filters(veiculos):
    """Renderiza filtros avançados"""
    with st.sidebar:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">🔍 Filtros Avançados</div>', unsafe_allow_html=True)
        
        # Busca
        busca = st.text_input("Buscar veículo", placeholder="Digite marca, modelo...")
        
        # Filtros principais
        col1, col2 = st.columns(2)
        with col1:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca = st.selectbox("Marca", marcas)
        
        with col2:
            if veiculos:
                anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
                ano = st.selectbox("Ano", anos)
        
        # Faixa de preço
        if veiculos:
            preco_min = min(v['preco_venda'] for v in veiculos)
            preco_max = max(v['preco_venda'] for v in veiculos)
            preco_range = st.slider("Faixa de Preço (R$)", int(preco_min), int(preco_max), 
                                  (int(preco_min), int(preco_max)), 1000)
        
        # Filtros avançados
        with st.expander("➕ Mais Filtros"):
            combustiveis = list(set([v['combustivel'] for v in veiculos]))
            combustivel = st.multiselect("Combustível", combustiveis, default=combustiveis)
            
            cambios = list(set([v['cambio'] for v in veiculos]))
            cambio = st.multiselect("Câmbio", cambios, default=cambios)
            
            km_options = ["Qualquer KM", "Até 30.000 km", "30.000 - 60.000 km", "Acima de 60.000 km"]
            km = st.selectbox("Quilometragem", km_options)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return {
            'busca': busca,
            'marca': marca,
            'ano': ano,
            'preco_range': preco_range if veiculos else (0, 100000),
            'combustivel': combustivel,
            'cambio': cambio,
            'km': km
        }

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header profissional
    st.markdown("""
    <div class="contact-bar">
        📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Segunda a Sexta: 8h-18h
    </div>
    
    <div class="main-header">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center;">
            <div class="logo-container">
                <h1 style="margin: 0; color: #e88e1b; font-size: 1.8rem;">GARAGEM MULTIMARCAS</h1>
            </div>
            <div style="color: white; font-weight: 600;">Seu carro dos sonhos está aqui!</div>
        </div>
    </div>
    
    <div class="hero-section">
        <div style="max-width: 800px; margin: 0 auto;">
            <h1 style="margin: 0 0 1rem 0; font-size: 2.5rem;">Encontre o carro perfeito</h1>
            <p style="font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9;">
                Os melhores veículos novos e seminovos com condições especiais
            </p>
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
        st.markdown("## 🚗 Veículos Disponíveis")
        
        # Aplicar filtros
        if veiculos and filtros:
            veiculos_filtrados = veiculos.copy()
            
            # Filtro de busca
            if filtros['busca']:
                busca_lower = filtros['busca'].lower()
                veiculos_filtrados = [v for v in veiculos_filtrados 
                                    if busca_lower in v['marca'].lower() 
                                    or busca_lower in v['modelo'].lower()]
            
            # Filtro de marca
            if filtros['marca'] != "Todas as marcas":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == filtros['marca']]
            
            # Filtro de ano
            if filtros['ano'] != "Todos os anos":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == filtros['ano']]
            
            # Filtro de preço
            veiculos_filtrados = [v for v in veiculos_filtrados 
                                if filtros['preco_range'][0] <= v['preco_venda'] <= filtros['preco_range'][1]]
            
            # Filtro de combustível
            if filtros['combustivel']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v['combustivel'] in filtros['combustivel']]
            
            # Filtro de câmbio
            if filtros['cambio']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v['cambio'] in filtros['cambio']]
            
            # Filtro de KM
            if filtros['km'] == "Até 30.000 km":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['km'] <= 30000]
            elif filtros['km'] == "30.000 - 60.000 km":
                veiculos_filtrados = [v for v in veiculos_filtrados if 30000 < v['km'] <= 60000]
            elif filtros['km'] == "Acima de 60.000 km":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['km'] > 60000]
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
            *Tente ajustar os filtros para encontrar o veículo ideal para você!*
            
            **📞 Entre em contato conosco:** (84) 98188-5353
            """)
        else:
            st.markdown(f"**Encontramos {len(veiculos_filtrados)} veículo(s)**")
            
            # Grid de veículos usando HTML/CSS
            html_grid = '<div class="vehicle-grid">'
            for i, veiculo in enumerate(veiculos_filtrados):
                # Criar um container para cada card
                with st.container():
                    render_vehicle_card(veiculo, i)
            html_grid += '</div>'
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p style="margin: 0; font-weight: 600; color: #e88e1b;">Garagem Multimarcas</p>
        <p style="margin: 0; font-size: 0.9rem;">Seu parceiro automotivo em Mossoró</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem;">
            © 2024 - Todos os direitos reservados
        </p>
    </div>
    
    <script>
    function showVehicleDetails(index) {
        // Implementar modal de detalhes
        alert('Detalhes do veículo ' + index);
    }
    
    function closeModal() {
        // Fechar modal
        document.querySelector('.modal-overlay').style.display = 'none';
    }
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
