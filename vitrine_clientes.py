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
# CSS AVANÇADO - DESIGN SYSTEM PROFISSIONAL
# =============================================

st.markdown("""
<style>
    /* Reset completo */
    .stApp {
        background: #ffffff;
        color: #1a1a1a;
        font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
        line-height: 1.6;
        scroll-behavior: smooth;
    }
    
    /* Remove todos os elementos padrão do Streamlit */
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: 100%;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Variáveis CSS */
    :root {
        --primary: #e88e1b;
        --primary-dark: #d87e0b;
        --secondary: #2d2d2d;
        --accent: #ff6b35;
        --text: #1a1a1a;
        --text-light: #666666;
        --background: #ffffff;
        --surface: #f8f9fa;
        --border: #e8e8e8;
        --success: #27ae60;
        --warning: #f39c12;
        --error: #e74c3c;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 20px rgba(0,0,0,0.12);
        --shadow-lg: 0 8px 40px rgba(0,0,0,0.15);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
    }
    
    /* Header Hero com gradiente animado */
    .hero-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #3d3d3d 100%);
        color: white;
        padding: 4rem 0 3rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 200%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(232, 142, 27, 0.1) 50%, 
            transparent 100%);
        animation: shimmer 8s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .hero-content {
        position: relative;
        z-index: 2;
    }
    
    /* Navigation Bar */
    .navbar {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border);
        padding: 1rem 0;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: var(--shadow-sm);
    }
    
    /* Cards de veículo - Design moderno */
    .vehicle-card {
        background: var(--background);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid var(--border);
        position: relative;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .vehicle-card:hover {
        transform: translateY(-8px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary);
    }
    
    .vehicle-image-container {
        position: relative;
        width: 100%;
        height: 220px;
        overflow: hidden;
        background: linear-gradient(135deg, #f5f5f5, #e8e8e8);
    }
    
    .vehicle-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s ease;
    }
    
    .vehicle-card:hover .vehicle-image {
        transform: scale(1.05);
    }
    
    .vehicle-badges {
        position: absolute;
        top: 12px;
        left: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        z-index: 2;
    }
    
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: var(--shadow-sm);
    }
    
    .badge-new {
        background: linear-gradient(135deg, var(--success), #219a52);
        color: white;
    }
    
    .badge-lowkm {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
    }
    
    .badge-promo {
        background: linear-gradient(135deg, var(--error), #c0392b);
        color: white;
    }
    
    .vehicle-content {
        padding: 1.5rem;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    
    .vehicle-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }
    
    .vehicle-subtitle {
        color: var(--text-light);
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
        background: var(--surface);
        color: var(--text-light);
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid var(--border);
        font-weight: 500;
    }
    
    .price-section {
        margin-top: auto;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
    }
    
    .vehicle-price {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--primary);
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    
    .price-label {
        font-size: 0.75rem;
        color: var(--text-light);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .financing-info {
        font-size: 0.8rem;
        color: var(--text-light);
        margin-top: 0.5rem;
    }
    
    /* Botões modernos */
    .btn-primary {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: var(--radius-md);
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        width: 100%;
        margin-top: 1rem;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(232, 142, 27, 0.4);
        background: linear-gradient(135deg, var(--primary-dark), #c86e0a);
        color: white;
        text-decoration: none;
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: var(--radius-md);
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        width: 100%;
        margin-top: 0.5rem;
    }
    
    .btn-whatsapp:hover {
        background: linear-gradient(135deg, #20bd5c, #0f7a61);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4);
        color: white;
        text-decoration: none;
    }
    
    /* Filtros avançados */
    .filter-sidebar {
        background: var(--background);
        border-radius: var(--radius-lg);
        padding: 2rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    
    .filter-header {
        display: flex;
        justify-content: between;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    
    .filter-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .filter-group {
        margin-bottom: 1.5rem;
    }
    
    .filter-label {
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.5rem;
        display: block;
    }
    
    /* Loading skeletons */
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: var(--radius-md);
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
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
        backdrop-filter: blur(10px);
    }
    
    .modal-content {
        background: var(--background);
        border-radius: var(--radius-lg);
        max-width: 1000px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: var(--shadow-lg);
        position: relative;
    }
    
    .modal-close {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: rgba(0,0,0,0.5);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 10;
        font-size: 1.2rem;
    }
    
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
    
    /* Grid responsivo */
    .vehicle-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .vehicle-grid {
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
        
        .hero-header {
            padding: 3rem 0 2rem 0;
        }
        
        .filter-sidebar {
            padding: 1.5rem;
        }
    }
    
    /* Customização dos componentes Streamlit */
    .stSelectbox > div > div {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
    }
    
    .stSlider > div > div > div {
        color: var(--primary);
    }
    
    .stMultiselect > div > div {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
    }
    
    /* Estados vazios */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--text-light);
    }
    
    .empty-state h3 {
        color: var(--text);
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    /* Footer */
    .footer {
        background: var(--secondary);
        color: white;
        padding: 3rem 0 2rem 0;
        margin-top: 4rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS OTIMIZADO
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
        """Busca veículos em estoque com cache"""
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
                # Calcular idade do veículo
                veiculo['idade'] = datetime.now().year - veiculo['ano']
                # Calcular margem (para badges promocionais)
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
# COMPONENTES AVANÇADOS DE UI
# =============================================

def generate_vehicle_image(veiculo, size="large"):
    """Gera imagem realista do veículo com múltiplos ângulos"""
    # Cores premium
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '1a1a1a', 'Branco': 'ffffff',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513',
        'Bege': 'f5deb3', 'Dourado': 'd4af37', 'Vinho': '722f37',
        'Azul Marinho': '2c3e50', 'Verde Musgo': '556b2f'
    }
    
    color_hex = color_map.get(veiculo['cor'], '3498db')
    
    # Diferentes tamanhos para diferentes usos
    sizes = {
        "small": "300x200",
        "medium": "400x250", 
        "large": "600x400",
        "xlarge": "800x500"
    }
    
    size_str = sizes.get(size, "400x250")
    
    # Texto otimizado
    texto = f"{veiculo['marca']}+{veiculo['modelo']}+{veiculo['ano']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/{size_str}/{color_hex}/ffffff?text={texto}"

def render_vehicle_skeleton(count=6):
    """Renderiza skeletons de loading"""
    cols = st.columns(3)
    for i in range(count):
        with cols[i % 3]:
            st.markdown("""
            <div class="vehicle-card">
                <div class="vehicle-image-container skeleton" style="height: 220px;"></div>
                <div class="vehicle-content">
                    <div class="skeleton" style="height: 24px; width: 80%; margin-bottom: 8px;"></div>
                    <div class="skeleton" style="height: 16px; width: 60%; margin-bottom: 16px;"></div>
                    <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                        <div class="skeleton" style="height: 28px; width: 70px; border-radius: 20px;"></div>
                        <div class="skeleton" style="height: 28px; width: 70px; border-radius: 20px;"></div>
                    </div>
                    <div class="skeleton" style="height: 32px; width: 70%; margin-top: auto;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_vehicle_card(veiculo, index):
    """Renderiza card premium do veículo"""
    image_url = generate_vehicle_image(veiculo, "medium")
    
    # Determinar badges dinamicamente
    badges = []
    if veiculo['idade'] <= 1:
        badges.append(('🌟 NOVO', 'badge-new'))
    elif veiculo['km'] < 30000:
        badges.append(('🛣️ BAIXA KM', 'badge-lowkm'))
    
    # Badge promocional para margens altas
    if veiculo.get('margem', 0) > 25:
        badges.append(('💎 PROMOÇÃO', 'badge-promo'))
    
    # Calcular parcelas
    entrada = veiculo['preco_venda'] * 0.2
    parcelas = (veiculo['preco_venda'] - entrada) / 48
    
    st.markdown(f'''
    <div class="vehicle-card fade-in">
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
    """Modal premium de detalhes do veículo"""
    image_url = generate_vehicle_image(veiculo, "xlarge")
    
    # Cálculos financeiros
    entrada = veiculo['preco_venda'] * 0.2
    parcelas_48 = (veiculo['preco_venda'] - entrada) / 48
    parcelas_36 = (veiculo['preco_venda'] - entrada) / 36
    parcelas_24 = (veiculo['preco_venda'] - entrada) / 24
    
    st.markdown(f'''
    <div class="modal-overlay">
        <div class="modal-content">
            <button class="modal-close" onclick="window.closeModal()">×</button>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; padding: 2rem;">
                <!-- Lado esquerdo - Galeria -->
                <div>
                    <img src="{image_url}" style="width: 100%; border-radius: 12px; margin-bottom: 1.5rem;">
                    
                    <!-- Mini galeria -->
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;">
                        <img src="{image_url}" style="width: 100%; height: 80px; object-fit: cover; border-radius: 8px; cursor: pointer;">
                        <div style="background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666; font-size: 0.8rem;">
                            + Fotos
                        </div>
                        <div style="background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666; font-size: 0.8rem;">
                            + Fotos
                        </div>
                    </div>
                    
                    <!-- Ações rápidas -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 2rem;">
                        <a href="https://wa.me/5584981885353?text=Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}" 
                           target="_blank" class="btn-whatsapp">
                            💬 Falar no WhatsApp
                        </a>
                        <button onclick="window.simularFinanciamento()" class="btn-primary">
                            💰 Simular Financiamento
                        </button>
                    </div>
                </div>
                
                <!-- Lado direito - Detalhes -->
                <div>
                    <h1 style="margin: 0 0 0.5rem 0; color: #1a1a1a; font-size: 2.2rem; font-weight: 800;">
                        {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}
                    </h1>
                    <div style="color: #666; margin-bottom: 2rem; font-size: 1.1rem; display: flex; gap: 1rem; flex-wrap: wrap;">
                        <span>📅 {datetime.now().year - veiculo['ano']} ano(s)</span>
                        <span>🛣️ {veiculo['km']:,} km</span>
                        <span>🎨 {veiculo['cor']}</span>
                        <span>🚪 {veiculo['portas']} portas</span>
                    </div>
                    
                    <!-- Preço em destaque -->
                    <div style="background: linear-gradient(135deg, #fff9e6, #ffefcc); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px;">PREÇO À VISTA</div>
                        <div style="font-size: 2.5rem; font-weight: 800; color: #e88e1b;">R$ {veiculo['preco_venda']:,.2f}</div>
                    </div>
                    
                    <!-- Especificações técnicas -->
                    <div style="margin-bottom: 2rem;">
                        <h3 style="color: #1a1a1a; margin-bottom: 1rem; font-size: 1.3rem;">📊 Especificações Técnicas</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                <div style="font-weight: 600; color: #333; margin-bottom: 0.5rem;">Combustível</div>
                                <div style="color: #666;">{veiculo['combustivel']}</div>
                            </div>
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                <div style="font-weight: 600; color: #333; margin-bottom: 0.5rem;">Câmbio</div>
                                <div style="color: #666;">{veiculo['cambio']}</div>
                            </div>
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                <div style="font-weight: 600; color: #333; margin-bottom: 0.5rem;">Portas</div>
                                <div style="color: #666;">{veiculo['portas']}</div>
                            </div>
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                                <div style="font-weight: 600; color: #333; margin-bottom: 0.5rem;">Placa</div>
                                <div style="color: #666;">{veiculo['placa'] or 'Não informada'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Opções de financiamento -->
                    <div>
                        <h3 style="color: #1a1a1a; margin-bottom: 1rem; font-size: 1.3rem;">💳 Opções de Financiamento</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                            <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-weight: 600; color: #27ae60;">24x</div>
                                <div style="font-size: 1.1rem; font-weight: 700;">R$ {parcelas_24:,.2f}</div>
                            </div>
                            <div style="background: #fff9e6; padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-weight: 600; color: #e88e1b;">36x</div>
                                <div style="font-size: 1.1rem; font-weight: 700;">R$ {parcelas_36:,.2f}</div>
                            </div>
                            <div style="background: #e8f4fd; padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-weight: 600; color: #3498db;">48x</div>
                                <div style="font-size: 1.1rem; font-weight: 700;">R$ {parcelas_48:,.2f}</div>
                            </div>
                        </div>
                        <div style="color: #666; font-size: 0.9rem; text-align: center;">
                            *Entrada de R$ {entrada:,.2f} (20%). Condições sujeitas à análise de crédito.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def render_advanced_filters(veiculos):
    """Filtros avançados com busca inteligente"""
    with st.sidebar:
        st.markdown('<div class="filter-sidebar">', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-title">🔍 Filtros Avançados</div>', unsafe_allow_html=True)
        
        # Busca por texto
        busca = st.text_input("🔎 Buscar veículo", placeholder="Digite marca, modelo...")
        
        # Filtros principais
        col1, col2 = st.columns(2)
        
        with col1:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca_selecionada = st.selectbox("Marca", marcas)
        
        with col2:
            if veiculos:
                anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
                ano_selecionado = st.selectbox("Ano", anos)
        
        # Faixa de preço com range slider
        if veiculos:
            preco_min = min(v['preco_venda'] for v in veiculos)
            preco_max = max(v['preco_venda'] for v in veiculos)
            preco_range = st.slider(
                "Faixa de Preço (R$)", 
                int(preco_min), 
                int(preco_max * 1.1), 
                (int(preco_min), int(preco_max)),
                1000
            )
        
        # Filtros avançados
        with st.expander("➕ Filtros Avançados", expanded=False):
            col3, col4 = st.columns(2)
            
            with col3:
                combustiveis = list(set([v['combustivel'] for v in veiculos]))
                combustivel_selecionado = st.multiselect("Combustível", combustiveis, default=combustiveis)
                
                cambios = list(set([v['cambio'] for v in veiculos]))
                cambio_selecionado = st.multiselect("Câmbio", cambios, default=cambios)
            
            with col4:
                km_options = ["Qualquer KM", "Até 30.000 km", "30.000 - 60.000 km", "60.000 - 100.000 km", "Acima de 100.000 km"]
                km_selecionado = st.selectbox("Quilometragem", km_options)
                
                cores = list(set([v['cor'] for v in veiculos]))
                cor_selecionada = st.multiselect("Cor", cores, default=cores)
        
        # Filtros especiais
        with st.expander("💎 Filtros Especiais", expanded=False):
            filtros_especiais = st.multiselect(
                "Destaques",
                ["⭐ Baixa KM", "🌟 Semi-novo", "💎 Promoção", "🚀 Performance"]
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return {
            'busca': busca,
            'marca': marca_selecionada,
            'ano': ano_selecionado,
            'preco_range': preco_range,
            'combustivel': combustivel_selecionado,
            'cambio': cambio_selecionado,
            'km': km_selecionado,
            'cor': cor_selecionada,
            'especiais': filtros_especiais
        }

# =============================================
# PÁGINA PRINCIPAL - WEBSITE PREMIUM
# =============================================

def main():
    # Inicialização do estado
    if 'veiculos_loaded' not in st.session_state:
        st.session_state.veiculos_loaded = False
    if 'veiculos_data' not in st.session_state:
        st.session_state.veiculos_data = []
    
    # Header Hero com navegação
    st.markdown("""
    <div class="navbar">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 2rem;">
                <div style="font-size: 1.5rem; font-weight: 800; color: #e88e1b;">GARAGEM MULTIMARCAS</div>
                <div style="display: flex; gap: 1.5rem;">
                    <a href="#veiculos" style="color: #666; text-decoration: none; font-weight: 500;">Veículos</a>
                    <a href="#financiamento" style="color: #666; text-decoration: none; font-weight: 500;">Financiamento</a>
                    <a href="#contato" style="color: #666; text-decoration: none; font-weight: 500;">Contato</a>
                </div>
            </div>
            <div style="color: #e88e1b; font-weight: 600;">📞 (84) 98188-5353</div>
        </div>
    </div>
    
    <div class="hero-header">
        <div class="hero-content" style="max-width: 1200px; margin: 0 auto; padding: 0 2rem; text-align: center;">
            <h1 style="margin: 0 0 1rem 0; font-size: 3.5rem; font-weight: 800; line-height: 1.1;">
                Encontre o <span style="color: #e88e1b;">carro dos seus sonhos</span>
            </h1>
            <p style="font-size: 1.3rem; color: #ccc; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
                Os melhores veículos novos e seminovos de Mossoró com condições especiais de pagamento
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <a href="#veiculos" class="btn-primary" style="width: auto; padding: 1rem 2rem;">
                    🚗 Ver Veículos
                </a>
                <a href="https://wa.me/5584981885353" target="_blank" class="btn-whatsapp" style="width: auto; padding: 1rem 2rem;">
                    💬 Falar com Vendedor
                </a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Conteúdo principal
    st.markdown("""
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem;">
    """, unsafe_allow_html=True)
    
    # Loading state
    if not st.session_state.veiculos_loaded:
        with st.spinner("🚗 Carregando veículos..."):
            db = WebsiteDatabase()
            st.session_state.veiculos_data = db.get_veiculos_estoque()
            st.session_state.veiculos_loaded = True
    
    veiculos = st.session_state.veiculos_data
    
    # Layout principal com sidebar
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        if veiculos:
            filtros = render_advanced_filters(veiculos)
        else:
            filtros = {}
    
    with col_main:
        st.markdown('<a id="veiculos"></a>', unsafe_allow_html=True)
        
        # Header do catálogo
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        
        with col_header1:
            if veiculos:
                st.markdown(f"## 🚗 Veículos Disponíveis ({len(veiculos)})")
            else:
                st.markdown("## 🚗 Veículos Disponíveis")
        
        with col_header2:
            ordenacao = st.selectbox("Ordenar por", 
                                   ["Mais recentes", "Menor preço", "Maior preço", "Mais novo", "Menor KM", "Maior desconto"])
        
        with col_header3:
            visualizacao = st.selectbox("Visualização", ["Grid", "Lista"])
        
        # Aplicar filtros
        if veiculos and filtros:
            veiculos_filtrados = veiculos.copy()
            
            # Filtro de busca
            if filtros['busca']:
                busca_lower = filtros['busca'].lower()
                veiculos_filtrados = [v for v in veiculos_filtrados 
                                    if busca_lower in v['marca'].lower() 
                                    or busca_lower in v['modelo'].lower()
                                    or busca_lower in v['cor'].lower()]
            
            # Filtro de marca
            if filtros['marca'] != "Todas as marcas":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == filtros['marca']]
            
            # Filtro de ano
            if filtros['ano'] != "Todos os anos":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == filtros['ano']]
            
            # Filtro de preço
            if 'preco_range' in filtros:
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
            elif filtros['km'] == "60.000 - 100.000 km":
                veiculos_filtrados = [v for v in veiculos_filtrados if 60000 < v['km'] <= 100000]
            elif filtros['km'] == "Acima de 100.000 km":
                veiculos_filtrados = [v for v in veiculos_filtrados if v['km'] > 100000]
            
            # Filtro de cor
            if filtros['cor']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v['cor'] in filtros['cor']]
            
            # Filtros especiais
            if "⭐ Baixa KM" in filtros['especiais']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v['km'] < 30000]
            if "🌟 Semi-novo" in filtros['especiais']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v['idade'] <= 2]
            if "💎 Promoção" in filtros['especiais']:
                veiculos_filtrados = [v for v in veiculos_filtrados if v.get('margem', 0) > 20]
        else:
            veiculos_filtrados = veiculos
        
        # Aplicar ordenação
        if veiculos_filtrados:
            if ordenacao == "Menor preço":
                veiculos_filtrados.sort(key=lambda x: x['preco_venda'])
            elif ordenacao == "Maior preço":
                veiculos_filtrados.sort(key=lambda x: x['preco_venda'], reverse=True)
            elif ordenacao == "Mais novo":
                veiculos_filtrados.sort(key=lambda x: x['ano'], reverse=True)
            elif ordenacao == "Menor KM":
                veiculos_filtrados.sort(key=lambda x: x['km'])
            elif ordenacao == "Maior desconto":
                veiculos_filtrados.sort(key=lambda x: x.get('margem', 0), reverse=True)
            else:
                veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
        
        # Exibir veículos
        if not veiculos_filtrados:
            st.markdown("""
            <div class="empty-state">
                <h3>🔍 Nenhum veículo encontrado</h3>
                <p>Tente ajustar os filtros para encontrar o veículo ideal para você!</p>
                <p><strong>📞 Entre em contato conosco:</strong> (84) 98188-5353</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Grid responsivo
            st.markdown(f'<div style="margin: 1rem 0; color: #666;">Encontramos {len(veiculos_filtrados)} veículo(s)</div>', unsafe_allow_html=True)
            
            # Renderizar em grid
            cols_per_row = 3
            for i in range(0, len(veiculos_filtrados), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(veiculos_filtrados):
                        with cols[j]:
                            veiculo = veiculos_filtrados[i + j]
                            render_vehicle_card(veiculo, i + j)
                            
                            # Modal de detalhes
                            if st.session_state.get(f"modal_{veiculo['id']}"):
                                render_vehicle_modal(veiculo)
                                if st.button("✕ Fechar", key=f"close_{veiculo['id']}", use_container_width=True):
                                    st.session_state[f"modal_{veiculo['id']}"] = False
                                    st.rerun()
    
    # Seção de financiamento
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 4rem 2rem; margin: 4rem -2rem; border-radius: 0;">
        <div style="max-width: 1000px; margin: 0 auto; text-align: center;">
            <a id="financiamento"></a>
            <h2 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 1rem; color: #1a1a1a;">💳 Financiamento Facilitado</h2>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 3rem; max-width: 600px; margin-left: auto; margin-right: auto;">
                Parcelamos em até 48x com as melhores taxas do mercado
            </p>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-bottom: 3rem;">
                <div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">📝</div>
                    <h3 style="color: #1a1a1a; margin-bottom: 1rem;">Documentação Simples</h3>
                    <p style="color: #666;">Apenas RG, CPF e comprovante de residência</p>
                </div>
                <div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">⚡</div>
                    <h3 style="color: #1a1a1a; margin-bottom: 1rem;">Aprovação Rápida</h3>
                    <p style="color: #666;">Resposta em até 24 horas</p>
                </div>
                <div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">🎯</div>
                    <h3 style="color: #1a1a1a; margin-bottom: 1rem;">Taxas Especiais</h3>
                    <p style="color: #666;">As melhores condições para você</p>
                </div>
            </div>
            
            <a href="https://wa.me/5584981885353?text=Olá! Gostaria de simular um financiamento" 
               target="_blank" class="btn-primary" style="width: auto; padding: 1rem 2rem; display: inline-flex;">
                💰 Simular Financiamento
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    </div>
    
    <div class="footer">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem;">
            <a id="contato"></a>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 3rem; margin-bottom: 2rem;">
                <div>
                    <h4 style="color: #e88e1b; margin-bottom: 1rem;">Garagem Multimarcas</h4>
                    <p style="color: #ccc; line-height: 1.6;">Os melhores veículos novos e seminovos de Mossoró com condições especiais de pagamento.</p>
                </div>
                <div>
                    <h4 style="color: #e88e1b; margin-bottom: 1rem;">📞 Contato</h4>
                    <p style="color: #ccc;">(84) 98188-5353</p>
                    <p style="color: #ccc;">Av. Lauro Monte, 475 - Mossoró/RN</p>
                </div>
                <div>
                    <h4 style="color: #e88e1b; margin-bottom: 1rem;">⏰ Horário</h4>
                    <p style="color: #ccc;">Segunda a Sexta: 8h-18h</p>
                    <p style="color: #ccc;">Sábado: 8h-12h</p>
                </div>
                <div>
                    <h4 style="color: #e88e1b; margin-bottom: 1rem;">💎 Serviços</h4>
                    <p style="color: #ccc;">Venda de Veículos</p>
                    <p style="color: #ccc;">Financiamento</p>
                    <p style="color: #ccc;">Consórcio</p>
                </div>
            </div>
            
            <div style="border-top: 1px solid #444; padding-top: 2rem; text-align: center;">
                <p style="color: #888; font-size: 0.9rem;">
                    © 2024 Garagem Multimarcas - Todos os direitos reservados
                </p>
            </div>
        </div>
    </div>
    
    <script>
    function closeModal() {
        // Fechar modal - implementação via Streamlit
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'close_modal'}, '*');
    }
    
    function simularFinanciamento() {
        window.open('https://wa.me/5584981885353?text=Olá! Gostaria de simular um financiamento', '_blank');
    }
    
    // Smooth scroll para âncoras
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
