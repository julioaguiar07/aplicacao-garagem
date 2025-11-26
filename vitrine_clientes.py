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
    page_title="Garagem Multimarcas - Veículos Premium",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================
# CSS COMPLETO E PROFISSIONAL
# =============================================

st.markdown('''
<style>
    .stApp {
        background: #0f0f0f;
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: 100%;
    }
    
    /* Header */
    .header-container {
        background: #1a1a1a;
        padding: 15px 0;
        border-bottom: 3px solid #e88e1b;
    }
    
    .contact-bar {
        background: #e88e1b;
        color: white;
        padding: 8px 0;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 50px 0;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Container principal */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 20px;
    }
    
    /* Grid de 4 colunas FIXO */
    .vehicles-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 25px;
        margin: 30px 0;
    }
    
    /* Card do veículo - DESIGN PREMIUM */
    .vehicle-card {
        background: #1e1e1e;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #333;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .vehicle-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #e88e1b, #f4c220);
    }
    
    .vehicle-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(232, 142, 27, 0.15);
        border-color: #e88e1b;
    }
    
    .vehicle-image {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 15px;
        background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
    }
    
    .vehicle-badges {
        position: absolute;
        top: 25px;
        left: 25px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
    
    .vehicle-title {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        margin: 10px 0 5px 0;
        line-height: 1.3;
    }
    
    .vehicle-info {
        color: #b0b0b0;
        font-size: 13px;
        margin-bottom: 12px;
        line-height: 1.4;
    }
    
    .vehicle-price {
        font-size: 22px;
        font-weight: 800;
        color: #e88e1b;
        margin: 15px 0 5px 0;
    }
    
    .vehicle-financing {
        color: #888;
        font-size: 12px;
        margin-bottom: 15px;
    }
    
    .btn-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 15px;
    }
    
    .btn-details {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        text-decoration: none;
        display: block;
    }
    
    .btn-details:hover {
        background: linear-gradient(135deg, #d87e0b, #e4b210);
        transform: translateY(-2px);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        text-decoration: none;
        display: block;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .btn-whatsapp:hover {
        background: linear-gradient(135deg, #20bd5c, #0f7a61);
        transform: translateY(-2px);
    }
    
    /* Filtros modernos */
    .filters-section {
        background: #1a1a1a;
        padding: 25px;
        border-radius: 12px;
        margin: 30px 0;
        border: 1px solid #333;
    }
    
    .filter-title {
        font-size: 20px;
        font-weight: 700;
        color: #e88e1b;
        margin-bottom: 20px;
    }
    
    /* Footer */
    .footer {
        background: #1a1a1a;
        padding: 40px 0;
        margin-top: 50px;
        border-top: 1px solid #333;
    }
    
    /* Responsividade */
    @media (max-width: 1200px) {
        .vehicles-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    @media (max-width: 900px) {
        .vehicles-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 600px) {
        .vehicles-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Esconde elementos Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
''', unsafe_allow_html=True)

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
# COMPONENTES PREMIUM
# =============================================

def generate_vehicle_image(veiculo):
    """Gera imagem realista do veículo"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '1a1a1a', 'Branco': 'ffffff',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513',
        'Bege': 'f5deb3', 'Dourado': 'd4af37', 'Vinho': '722f37'
    }
    
    color_hex = color_map.get(veiculo['cor'], '3498db')
    texto = f"{veiculo['marca']}+{veiculo['modelo']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={texto}"

def create_vehicle_card(veiculo):
    """Cria HTML completo do card do veículo"""
    image_url = generate_vehicle_image(veiculo)
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges_html = ""
    if idade <= 1:
        badges_html += '<div class="badge badge-new">🆕 NOVO</div>'
    if veiculo['km'] < 30000:
        badges_html += '<div class="badge badge-lowkm">🛣️ BAIXA KM</div>'
    
    # Cálculo de parcelas
    entrada = veiculo['preco_venda'] * 0.2
    parcela = (veiculo['preco_venda'] - entrada) / 48
    
    # Criar HTML do card
    card_html = f'''
    <div class="vehicle-card">
        <img src="{image_url}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
        <div class="vehicle-badges">
            {badges_html}
        </div>
        <div class="vehicle-title">{veiculo['marca']} {veiculo['modelo']}</div>
        <div class="vehicle-info">
            📅 {veiculo['ano']} • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}
        </div>
        <div class="vehicle-info">
            ⚙️ {veiculo['cambio']} • ⛽ {veiculo['combustivel']} • 🚪 {veiculo['portas']} portas
        </div>
        <div class="vehicle-price">R$ {veiculo['preco_venda']:,.2f}</div>
        <div class="vehicle-financing">
            📊 Ou R$ {entrada:,.2f} + 48x de R$ {parcela:,.2f}
        </div>
        <div class="btn-container">
            <button class="btn-details" onclick="showVehicleDetails('{veiculo['marca']}', '{veiculo['modelo']}', {veiculo['ano']}, {veiculo['preco_venda']})">
                🔍 Ver Detalhes
            </button>
            <a href="https://wa.me/5584981885353?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}" 
               target="_blank" class="btn-whatsapp">
                💬 WhatsApp
            </a>
        </div>
    </div>
    '''
    return card_html

def render_vehicle_grid(veiculos):
    """Renderiza grid completo de veículos"""
    if not veiculos:
        return '<div style="text-align: center; padding: 60px; color: #888;"><h3>🚫 Nenhum veículo encontrado</h3><p>Tente ajustar os filtros!</p></div>'
    
    grid_html = '<div class="vehicles-grid">'
    for veiculo in veiculos:
        grid_html += create_vehicle_card(veiculo)
    grid_html += '</div>'
    
    return grid_html

# =============================================
# PÁGINA PRINCIPAL - COMPLETA
# =============================================

def main():
    # Header Premium
    st.markdown('''
    <div class="contact-bar">
        📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Segunda a Sexta: 8h-18h • Sábado: 8h-12h
    </div>
    
    <div class="header-container">
        <div class="main-container">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 28px; font-weight: 800; color: #e88e1b;">
                        🚗 GARAGEM MULTIMARCAS
                    </div>
                </div>
                <div style="color: #ccc; font-size: 16px; font-weight: 500;">
                    Seu carro dos sonhos está aqui!
                </div>
            </div>
        </div>
    </div>
    
    <div class="hero-section">
        <div class="main-container">
            <h1 style="margin: 0; color: white; font-size: 42px; font-weight: 800; margin-bottom: 15px;">
                ENCONTRE SEU CARRO DOS SONHOS
            </h1>
            <p style="color: #ccc; font-size: 20px; margin: 0; max-width: 600px; margin: 0 auto;">
                Os melhores veículos novos e seminovos com condições especiais de pagamento
            </p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Container principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Buscar dados
    db = WebsiteDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Seção de Filtros
    st.markdown('''
    <div class="filters-section">
        <div class="filter-title">🔍 FILTRAR VEÍCULOS</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Filtros em colunas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos]))) if veiculos else ["Todas as marcas"]
        marca_filtro = st.selectbox("**Marca**", marcas)
    
    with col2:
        if veiculos:
            anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("**Ano**", anos)
        else:
            ano_filtro = "Todos os anos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos))
            preco_max = int(max(v['preco_venda'] for v in veiculos))
            preco_filtro = st.slider("**Preço Máximo (R$)**", preco_min, preco_max, preco_max, 1000)
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("**Ordenar por**", ["Mais recentes", "Menor preço", "Maior preço", "Mais novo", "Menor KM"])
    
    # Aplicar filtros
    veiculos_filtrados = []
    if veiculos:
        veiculos_filtrados = veiculos.copy()
        
        if marca_filtro != "Todas as marcas":
            veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == marca_filtro]
        
        if ano_filtro != "Todos os anos":
            veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == ano_filtro]
        
        veiculos_filtrados = [v for v in veiculos_filtrados if v['preco_venda'] <= preco_filtro]
        
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
    
    # Exibir resultados
    st.markdown(f'<h2 style="color: white; margin: 30px 0 20px 0;">🚗 VEÍCULOS DISPONÍVEIS ({len(veiculos_filtrados)})</h2>', unsafe_allow_html=True)
    
    # Renderizar grid de veículos
    grid_html = render_vehicle_grid(veiculos_filtrados)
    st.markdown(grid_html, unsafe_allow_html=True)
    
    # Footer
    st.markdown('''
    <div class="footer">
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: 800; color: #e88e1b; margin-bottom: 10px;">
                GARAGEM MULTIMARCAS
            </div>
            <div style="color: #ccc; margin-bottom: 20px;">
                Seu parceiro automotivo em Mossoró • 📞 (84) 98188-5353
            </div>
            <div style="color: #666; font-size: 14px;">
                © 2024 Garagem Multimarcas - Todos os direitos reservados
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha main-container
    
    # JavaScript para interações
    st.markdown('''
    <script>
    function showVehicleDetails(marca, modelo, ano, preco) {
        const message = `Detalhes do veículo:\\n\\n${marca} ${modelo} ${ano}\\nPreço: R$ ${preco.toLocaleString('pt-BR', {minimumFractionDigits: 2})}\\n\\nEntre em contato para mais informações!`;
        alert(message);
    }
    </script>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
