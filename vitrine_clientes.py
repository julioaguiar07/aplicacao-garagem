import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import psycopg2
import os
import base64
from PIL import Image
import io
import math

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Veículos Novos e Seminovos em Mossoró",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CSS PROFISSIONAL - ESTILO WEBSITE REAL
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
    
    /* Header profissional */
    .main-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: white;
        padding: 2rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .contact-info {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    
    .contact-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #e88e1b;
        font-weight: 500;
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
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        overflow: hidden;
        transition: all 0.3s ease;
        border: 1px solid #e1e1e1;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    .vehicle-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        background: #f8f9fa;
    }
    
    .vehicle-content {
        padding: 1.5rem;
    }
    
    .vehicle-title {
        font-size: 1.2rem;
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
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid #e1e1e1;
    }
    
    .price-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e1e1e1;
    }
    
    .vehicle-price {
        font-size: 1.5rem;
        font-weight: 700;
        color: #e88e1b;
    }
    
    .price-label {
        font-size: 0.8rem;
        color: #666;
    }
    
    /* Botões profissionais */
    .btn-primary {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    
    .btn-primary:hover {
        background: linear-gradient(135deg, #d87e0b, #e4b210);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(232, 142, 27, 0.3);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    
    .btn-whatsapp:hover {
        background: linear-gradient(135deg, #20bd5c, #0f7a61);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
    }
    
    /* Filtros sidebar */
    .filter-section {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e1e1e1;
    }
    
    .filter-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1a1a1a;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Destaques e badges */
    .badge-new {
        background: #e74c3c;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: 600;
        position: absolute;
        top: 1rem;
        left: 1rem;
    }
    
    .badge-lowkm {
        background: #27ae60;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: 600;
        position: absolute;
        top: 1rem;
        left: 1rem;
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
        border-radius: 15px;
        max-width: 1000px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .vehicle-grid {
            grid-template-columns: 1fr;
        }
        
        .contact-info {
            flex-direction: column;
            align-items: center;
            gap: 1rem;
        }
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
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
        """Busca veículos em estoque - CORRIGIDO sem coluna foto"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            # ✅ QUERY CORRIGIDA - sem a coluna 'foto' que não existe ainda
            cursor.execute('''
                SELECT id, modelo, ano, marca, cor, preco_venda, 
                       km, placa, combustivel, cambio, portas, observacoes,
                       data_cadastro
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
            st.error(f"❌ Erro ao buscar veículos: {e}")
            return []
        finally:
            conn.close()

# =============================================
# COMPONENTES PROFISSIONAIS
# =============================================

def generate_vehicle_image(veiculo):
    """Gera imagem realista do veículo"""
    # Cores realistas para diferentes marcas/cores
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '000000', 'Branco': 'ffffff',
        'Vermelho': 'ff0000', 'Azul': '0066cc', 'Cinza': '666666',
        'Verde': '008000', 'Laranja': 'ff6600', 'Marrom': '8b4513'
    }
    
    color_hex = color_map.get(veiculo['cor'], '2d2d2d')
    
    # Imagem placeholder profissional
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={veiculo['marca']}+{veiculo['modelo']}"

def render_vehicle_card(veiculo, index):
    """Renderiza card profissional do veículo"""
    image_url = generate_vehicle_image(veiculo)
    idade = datetime.now().year - veiculo['ano']
    
    # Determinar badges
    badges = []
    if idade <= 2:
        badges.append(('🆕 SEMI-NOVO', 'badge-new'))
    if veiculo['km'] < 50000:
        badges.append(('🛣️ BAIXA KM', 'badge-lowkm'))
    
    st.markdown(f'''
    <div class="vehicle-card fade-in">
        <div style="position: relative;">
            <img src="{image_url}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
            {''.join([f'<div class="{badge_class}" style="top: {1 + i*2}rem;">{text}</div>' for i, (text, badge_class) in enumerate(badges)])}
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
            
            <div class="price-container">
                <div>
                    <div class="price-label">PREÇO À VISTA</div>
                    <div class="vehicle-price">R$ {veiculo['preco_venda']:,.2f}</div>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Ver Detalhes", key=f"details_{veiculo['id']}_{index}", use_container_width=True):
            st.session_state[f"modal_{veiculo['id']}"] = True
    
    with col2:
        whatsapp_msg = f"Olá! Gostaria de mais informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}"
        whatsapp_url = f"https://wa.me/5584981885353?text={whatsapp_msg.replace(' ', '%20')}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="btn-whatsapp">💬 WhatsApp</a>', unsafe_allow_html=True)

def render_vehicle_modal(veiculo):
    """Modal profissional de detalhes do veículo"""
    image_url = generate_vehicle_image(veiculo)
    
    st.markdown(f'''
    <div class="modal-overlay">
        <div class="modal-content">
            <div style="padding: 2rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: start;">
                    {/* Lado esquerdo - Imagem e preço */}
                    <div>
                        <img src="{image_url}" style="width: 100%; border-radius: 10px; margin-bottom: 1.5rem;">
                        
                        <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 1.5rem; border-radius: 10px; text-align: center;">
                            <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">PREÇO À VISTA</div>
                            <div style="font-size: 2rem; font-weight: 700; color: #e88e1b;">R$ {veiculo['preco_venda']:,.2f}</div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem;">
                            <a href="https://wa.me/5584981885353?text=Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}" 
                               target="_blank" class="btn-whatsapp" style="text-align: center;">
                                💬 Falar no WhatsApp
                            </a>
                            <button onclick="window.closeModal()" class="btn-primary" style="background: #6c757d;">
                                📞 Ligar Agora
                            </button>
                        </div>
                    </div>
                    
                    {/* Lado direito - Detalhes */}
                    <div>
                        <h1 style="margin: 0 0 0.5rem 0; color: #1a1a1a; font-size: 2rem;">{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}</h1>
                        <div style="color: #666; margin-bottom: 2rem; font-size: 1.1rem;">
                            📅 {datetime.now().year - veiculo['ano']} ano(s) • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}
                        </div>
                        
                        {/* Especificações */}
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1a1a1a; margin-bottom: 1rem;">📊 Especificações Técnicas</h3>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                    <div style="font-weight: 600; color: #333;">Combustível</div>
                                    <div style="color: #666;">{veiculo['combustivel']}</div>
                                </div>
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                    <div style="font-weight: 600; color: #333;">Câmbio</div>
                                    <div style="color: #666;">{veiculo['cambio']}</div>
                                </div>
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                    <div style="font-weight: 600; color: #333;">Portas</div>
                                    <div style="color: #666;">{veiculo['portas']}</div>
                                </div>
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                    <div style="font-weight: 600; color: #333;">Placa</div>
                                    <div style="color: #666;">{veiculo['placa'] or 'Não informada'}</div>
                                </div>
                            </div>
                        </div>
                        
                        {/* Descrição */}
                        {veiculo['observacoes'] and f'''
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1a1a1a; margin-bottom: 1rem;">📝 Descrição do Veículo</h3>
                            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; line-height: 1.6; color: #555;">
                                {veiculo['observacoes']}
                            </div>
                        </div>
                        ''' or ''}
                        
                        {/* Simulador de financiamento */}
                        <div>
                            <h3 style="color: #1a1a1a; margin-bottom: 1rem;">💰 Simular Financiamento</h3>
                            <div style="background: linear-gradient(135deg, #e3f2fd, #bbdefb); padding: 1.5rem; border-radius: 8px;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                                    <div>
                                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Entrada</div>
                                        <div style="font-size: 1.2rem; color: #e88e1b;">R$ {(veiculo['preco_venda'] * 0.2):,.2f}</div>
                                    </div>
                                    <div>
                                        <div style="font-weight: 600; margin-bottom: 0.5rem;">48x de</div>
                                        <div style="font-size: 1.2rem; color: #e88e1b;">R$ {(veiculo['preco_venda'] * 0.8 / 48):,.2f}</div>
                                    </div>
                                </div>
                                <div style="color: #666; font-size: 0.9rem;">
                                    *Consulte condições especiais na loja
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# =============================================
# PÁGINA PRINCIPAL - WEBSITE PROFISSIONAL
# =============================================

def main():
    # Header profissional
    st.markdown("""
    <div class="main-header">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem;">
            <div class="logo-container">
                <h1 style="margin: 0; font-size: 2.5rem; font-weight: 800; color: #e88e1b;">
                    GARAGEM MULTIMARCAS
                </h1>
            </div>
            <p style="text-align: center; margin: 0; color: #ccc; font-size: 1.2rem;">
                Veículos Novos e Seminovos em Mossoró
            </p>
            <div class="contact-info">
                <div class="contact-item">
                    📞 (84) 98188-5353
                </div>
                <div class="contact-item">
                    📍 Mossoró/RN
                </div>
                <div class="contact-item">
                    ⏰ Segunda a Sexta: 8h-18h
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Conteúdo principal
    st.markdown("""
    <div style="max-width: 1200px; margin: 0 auto; padding: 2rem;">
    """, unsafe_allow_html=True)
    
    # Buscar dados
    db = WebsiteDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Sidebar de filtros profissionais
    with st.sidebar:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">🔍 Filtros Avançados</div>', unsafe_allow_html=True)
        
        # Filtros
        marcas = list(set([v['marca'] for v in veiculos]))
        marca_selecionada = st.selectbox("Marca", ["Todas as marcas"] + sorted(marcas))
        
        if veiculos:
            preco_max = max(v['preco_venda'] for v in veiculos)
            preco_range = st.slider("Faixa de Preço (R$)", 0, int(preco_max * 1.1), 
                                  (0, int(preco_max)), 5000)
        
        anos = sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
        ano_selecionado = st.selectbox("Ano", ["Todos os anos"] + anos)
        
        combustiveis = list(set([v['combustivel'] for v in veiculos]))
        combustivel_selecionado = st.multiselect("Combustível", combustiveis, default=combustiveis)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Filtro de quilometragem
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">🛣️ Quilometragem</div>', unsafe_allow_html=True)
        km_options = ["Qualquer KM", "Até 50.000 km", "50.000 - 100.000 km", "Acima de 100.000 km"]
        km_selecionado = st.selectbox("Faixa de KM", km_options)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    veiculos_filtrados = veiculos.copy()
    
    if marca_selecionada != "Todas as marcas":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == marca_selecionada]
    
    if veiculos:
        veiculos_filtrados = [v for v in veiculos_filtrados if preco_range[0] <= v['preco_venda'] <= preco_range[1]]
    
    if ano_selecionado != "Todos os anos":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == ano_selecionado]
    
    if combustivel_selecionado:
        veiculos_filtrados = [v for v in veiculos_filtrados if v['combustivel'] in combustivel_selecionado]
    
    # Filtro de KM
    if km_selecionado == "Até 50.000 km":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['km'] <= 50000]
    elif km_selecionado == "50.000 - 100.000 km":
        veiculos_filtrados = [v for v in veiculos_filtrados if 50000 < v['km'] <= 100000]
    elif km_selecionado == "Acima de 100.000 km":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['km'] > 100000]
    
    # Header do catálogo
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"## 🚗 Veículos Disponíveis ({len(veiculos_filtrados)})")
    
    with col2:
        ordenacao = st.selectbox("Ordenar por", 
                               ["Mais recentes", "Menor preço", "Maior preço", "Mais novo", "Menor KM"])
    
    # Aplicar ordenação
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
    
    # Grid de veículos
    if not veiculos_filtrados:
        st.info("""
        ## 🔍 Nenhum veículo encontrado
        *Tente ajustar os filtros para encontrar o veículo ideal para você!*
        
        **📞 Entre em contato conosco:** (84) 98188-5353
        """)
    else:
        # Renderizar grid profissional
        st.markdown('<div class="vehicle-grid">', unsafe_allow_html=True)
        
        cols = st.columns(3)
        for i, veiculo in enumerate(veiculos_filtrados):
            with cols[i % 3]:
                render_vehicle_card(veiculo, i)
                
                # Modal de detalhes
                if st.session_state.get(f"modal_{veiculo['id']}"):
                    render_vehicle_modal(veiculo)
                    if st.button("✕ Fechar", key=f"close_{veiculo['id']}", use_container_width=True):
                        st.session_state[f"modal_{veiculo['id']}"] = False
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer profissional
    st.markdown("""
    </div>
    
    <div style="background: #1a1a1a; color: white; padding: 3rem 0; margin-top: 4rem;">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem; text-align: center;">
            <h3 style="color: #e88e1b; margin-bottom: 1.5rem;">Garagem Multimarcas</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-bottom: 2rem;">
                <div>
                    <h4 style="color: #ccc; margin-bottom: 1rem;">📞 Contato</h4>
                    <p>(84) 98188-5353</p>
                    <p>Mossoró - RN</p>
                </div>
                <div>
                    <h4 style="color: #ccc; margin-bottom: 1rem;">⏰ Horário</h4>
                    <p>Segunda a Sexta: 8h-18h</p>
                    <p>Sábado: 8h-12h</p>
                </div>
                <div>
                    <h4 style="color: #ccc; margin-bottom: 1rem;">💎 Serviços</h4>
                    <p>Venda de Veículos</p>
                    <p>Financiamento</p>
                    <p>Consórcio</p>
                </div>
            </div>
            <p style="color: #666; font-size: 0.9rem; border-top: 1px solid #333; padding-top: 2rem;">
                © 2024 Garagem Multimarcas - Todos os direitos reservados
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
