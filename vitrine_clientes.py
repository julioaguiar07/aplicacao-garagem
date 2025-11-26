import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2
import os
from PIL import Image

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Veículos em Mossoró",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================
# CSS - FUNDO ESCURO COM GRID 4 COLUNAS
# =============================================

st.markdown("""
<style>
    .stApp {
        background: #0f0f0f;
        color: #ffffff;
        font-family: 'Arial', sans-serif;
    }
    
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: 100%;
    }
    
    /* Header */
    .header {
        background: #1a1a1a;
        padding: 1rem 0;
        border-bottom: 2px solid #e88e1b;
    }
    
    .contact-bar {
        background: #e88e1b;
        color: white;
        padding: 0.5rem 0;
        text-align: center;
        font-weight: bold;
    }
    
    /* Hero Section */
    .hero {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 3rem 0;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Grid de 4 colunas */
    .vehicle-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        padding: 20px 0;
    }
    
    /* Card do veículo */
    .vehicle-card {
        background: #1a1a1a;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #333;
        transition: transform 0.3s ease;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        border-color: #e88e1b;
    }
    
    .vehicle-image {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 10px;
        background: #2d2d2d;
    }
    
    .vehicle-title {
        font-size: 16px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 5px;
    }
    
    .vehicle-info {
        color: #cccccc;
        font-size: 12px;
        margin-bottom: 10px;
    }
    
    .vehicle-price {
        font-size: 20px;
        font-weight: bold;
        color: #e88e1b;
        margin-bottom: 5px;
    }
    
    .vehicle-financing {
        color: #888;
        font-size: 11px;
        margin-bottom: 10px;
    }
    
    .btn-whatsapp {
        background: #25D366;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
        cursor: pointer;
        text-decoration: none;
        display: block;
        text-align: center;
        margin-top: 5px;
    }
    
    .btn-details {
        background: #e88e1b;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
        cursor: pointer;
        margin-top: 5px;
    }
    
    /* Filtros */
    .filter-section {
        background: #1a1a1a;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: bold;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    
    .badge-new {
        background: #27ae60;
        color: white;
    }
    
    .badge-lowkm {
        background: #e88e1b;
        color: white;
    }
    
    /* Esconde elementos Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
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
            return []
        finally:
            if conn:
                conn.close()

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def generate_vehicle_image(veiculo):
    """Gera imagem do veículo"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '000000', 'Branco': 'ffffff',
        'Vermelho': 'ff0000', 'Azul': '0000ff', 'Cinza': '808080',
        'Verde': '008000', 'Laranja': 'ffa500', 'Marrom': '8b4513'
    }
    
    color_hex = color_map.get(veiculo['cor'], '666666')
    texto = f"{veiculo['marca']} {veiculo['modelo']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/300x150/{color_hex}/ffffff?text={texto}"

def render_vehicle_card(veiculo):
    """Renderiza card do veículo"""
    image_url = generate_vehicle_image(veiculo)
    
    # Badges
    idade = datetime.now().year - veiculo['ano']
    badges_html = ""
    if idade <= 1:
        badges_html += '<span class="badge badge-new">NOVO</span>'
    if veiculo['km'] < 30000:
        badges_html += '<span class="badge badge-lowkm">BAIXA KM</span>'
    
    # Cálculo de parcelas
    entrada = veiculo['preco_venda'] * 0.2
    parcela = (veiculo['preco_venda'] - entrada) / 48
    
    html = f'''
    <div class="vehicle-card">
        <img src="{image_url}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
        {badges_html}
        <div class="vehicle-title">{veiculo['marca']} {veiculo['modelo']}</div>
        <div class="vehicle-info">
            {veiculo['ano']} • {veiculo['km']:,} km • {veiculo['combustivel']}
        </div>
        <div class="vehicle-price">R$ {veiculo['preco_venda']:,.2f}</div>
        <div class="vehicle-financing">
            Ou 48x de R$ {parcela:,.2f}
        </div>
        <button class="btn-details" onclick="alert('Detalhes do {veiculo['marca']} {veiculo['modelo']}')">
            🔍 Ver Detalhes
        </button>
        <a href="https://wa.me/5584981885353?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}" 
           target="_blank" class="btn-whatsapp">
            💬 WhatsApp
        </a>
    </div>
    '''
    return html

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header
    st.markdown("""
    <div class="contact-bar">
        📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Seg-Sex: 8h-18h
    </div>
    
    <div class="header">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; gap: 20px;">
            <div style="font-size: 24px; font-weight: bold; color: #e88e1b;">
                🚗 GARAGEM MULTIMARCAS
            </div>
            <div style="color: #ccc; font-size: 14px;">
                Seu carro dos sonhos está aqui!
            </div>
        </div>
    </div>
    
    <div class="hero">
        <div style="max-width: 800px; margin: 0 auto;">
            <h1 style="margin: 0; color: white; font-size: 36px;">ENCONTRE SEU CARRO IDEAL</h1>
            <p style="color: #ccc; font-size: 18px; margin: 10px 0 0 0;">
                Os melhores veículos com condições especiais de pagamento
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar dados
    db = WebsiteDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Filtros simples
    st.markdown("""
    <div class="filter-section">
        <h3 style="margin: 0; color: white;">🔍 Filtros</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        marcas = ["Todas"] + sorted(list(set([v['marca'] for v in veiculos]))) if veiculos else ["Todas"]
        marca_filtro = st.selectbox("Marca", marcas)
    
    with col2:
        if veiculos:
            anos = ["Todos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("Ano", anos)
        else:
            ano_filtro = "Todos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos))
            preco_max = int(max(v['preco_venda'] for v in veiculos))
            preco_filtro = st.slider("Preço Máximo", preco_min, preco_max, preco_max)
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("Ordenar por", ["Mais Novos", "Menor Preço", "Maior Preço"])
    
    # Aplicar filtros
    if veiculos:
        veiculos_filtrados = veiculos.copy()
        
        if marca_filtro != "Todas":
            veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == marca_filtro]
        
        if ano_filtro != "Todos":
            veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == ano_filtro]
        
        veiculos_filtrados = [v for v in veiculos_filtrados if v['preco_venda'] <= preco_filtro]
        
        if ordenacao == "Menor Preço":
            veiculos_filtrados.sort(key=lambda x: x['preco_venda'])
        elif ordenacao == "Maior Preço":
            veiculos_filtrados.sort(key=lambda x: x['preco_venda'], reverse=True)
        else:
            veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
    else:
        veiculos_filtrados = []
    
    # Grid de veículos
    st.markdown(f"<h3 style='color: white; margin: 20px 0;'>{len(veiculos_filtrados)} veículos encontrados</h3>", unsafe_allow_html=True)
    
    if veiculos_filtrados:
        # Criar grid de 4 colunas
        html_grid = '<div class="vehicle-grid">'
        for veiculo in veiculos_filtrados:
            html_grid += render_vehicle_card(veiculo)
        html_grid += '</div>'
        
        st.markdown(html_grid, unsafe_allow_html=True)
    else:
        st.markdown('''
        <div style="text-align: center; padding: 40px; color: #888;">
            <h3>🚫 Nenhum veículo encontrado</h3>
            <p>Tente ajustar os filtros ou entre em contato conosco!</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Footer
    st.markdown('''
    <div style="text-align: center; padding: 40px 20px; color: #666; border-top: 1px solid #333; margin-top: 40px;">
        <p style="margin: 0; font-size: 14px; color: #e88e1b; font-weight: bold;">GARAGEM MULTIMARCAS</p>
        <p style="margin: 5px 0; font-size: 12px;">Seu parceiro automotivo em Mossoró</p>
        <p style="margin: 10px 0 0 0; font-size: 11px;">© 2024 - Todos os direitos reservados</p>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
