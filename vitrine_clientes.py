import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2
import os
from PIL import Image
import base64
import io

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Catálogo Premium",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================
# CSS PREMIUM - DESIGN DE CATÁLOGO LUXUOSO
# =============================================

st.markdown('''
<style>
    /* Reset e configurações base */
    .stApp {
        background: #0a0a0a;
        color: #ffffff;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        line-height: 1.6;
    }
    
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: 100%;
    }
    
    /* Header Luxuoso */
    .luxury-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d1a0f 50%, #1a1a1a 100%);
        padding: 20px 0;
        border-bottom: 3px solid #d4af37;
        position: relative;
        overflow: hidden;
    }
    
    .luxury-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="0.5" fill="%23ffffff" opacity="0.02"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .contact-bar {
        background: linear-gradient(90deg, #d4af37, #f4c220);
        color: #1a1a1a;
        padding: 12px 0;
        text-align: center;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 0.5px;
    }
    
    /* Hero Section Impactante */
    .hero-section {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2d1a0f 100%);
        padding: 80px 0 60px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.1) 0%, transparent 70%);
    }
    
    /* Container principal */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 20px;
    }
    
    /* Grid de veículos - Design de galeria */
    .vehicles-gallery {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 30px;
        margin: 40px 0;
    }
    
    /* Card premium com efeitos sofisticados */
    .luxury-card {
        background: linear-gradient(145deg, #1a1a1a, #0f0f0f);
        border-radius: 20px;
        padding: 0;
        border: 1px solid #333;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .luxury-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
        transition: left 0.6s ease;
    }
    
    .luxury-card:hover {
        transform: translateY(-12px) scale(1.02);
        border-color: #d4af37;
        box-shadow: 0 25px 50px rgba(212, 175, 55, 0.2);
    }
    
    .luxury-card:hover::before {
        left: 100%;
    }
    
    .card-header {
        position: relative;
        overflow: hidden;
        border-radius: 20px 20px 0 0;
    }
    
    .vehicle-image {
        width: 100%;
        height: 220px;
        object-fit: cover;
        transition: transform 0.6s ease;
    }
    
    .luxury-card:hover .vehicle-image {
        transform: scale(1.1);
    }
    
    .card-badges {
        position: absolute;
        top: 15px;
        left: 15px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        z-index: 2;
    }
    
    .luxury-badge {
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .badge-new {
        background: linear-gradient(135deg, #27ae60, #219a52);
        color: white;
    }
    
    .badge-lowkm {
        background: linear-gradient(135deg, #d4af37, #b8941f);
        color: #1a1a1a;
    }
    
    .badge-promo {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
    }
    
    .card-content {
        padding: 25px;
    }
    
    .vehicle-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 12px 0;
        line-height: 1.3;
        background: linear-gradient(135deg, #ffffff, #d4af37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .vehicle-specs {
        color: #b0b0b0;
        font-size: 14px;
        margin-bottom: 15px;
        line-height: 1.5;
    }
    
    .spec-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
    }
    
    .price-section {
        border-top: 1px solid #333;
        padding-top: 20px;
        margin-top: 15px;
    }
    
    .vehicle-price {
        font-size: 28px;
        font-weight: 800;
        color: #d4af37;
        margin: 0 0 8px 0;
        text-shadow: 0 2px 4px rgba(212, 175, 55, 0.3);
    }
    
    .vehicle-financing {
        color: #888;
        font-size: 13px;
        margin-bottom: 20px;
        line-height: 1.4;
    }
    
    .btn-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 20px;
    }
    
    .btn-details {
        background: linear-gradient(135deg, #333, #555);
        color: white;
        border: none;
        padding: 14px;
        border-radius: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        text-decoration: none;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-size: 14px;
    }
    
    .btn-details:hover {
        background: linear-gradient(135deg, #444, #666);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 255, 255, 0.1);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        border: none;
        padding: 14px;
        border-radius: 12px;
        font-weight: 600;
        text-decoration: none;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.3s ease;
        font-size: 14px;
    }
    
    .btn-whatsapp:hover {
        background: linear-gradient(135deg, #20bd5c, #0f7a61);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 211, 102, 0.3);
    }
    
    /* Filtros premium */
    .filters-section {
        background: linear-gradient(135deg, #1a1a1a, #0f0f0f);
        padding: 30px;
        border-radius: 20px;
        margin: 40px 0;
        border: 1px solid #333;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    
    .filter-title {
        font-size: 24px;
        font-weight: 700;
        color: #d4af37;
        margin-bottom: 25px;
        text-align: center;
    }
    
    /* Footer luxuoso */
    .luxury-footer {
        background: linear-gradient(135deg, #1a1a1a, #0f0f0f);
        padding: 50px 0 30px;
        margin-top: 60px;
        border-top: 1px solid #333;
        position: relative;
    }
    
    .luxury-footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #d4af37, #f4c220, #d4af37);
    }
    
    /* Contador de veículos */
    .vehicle-counter {
        background: linear-gradient(135deg, #d4af37, #f4c220);
        color: #1a1a1a;
        padding: 8px 20px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 14px;
        display: inline-block;
        margin-bottom: 20px;
    }
    
    /* Loading animado */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(212, 175, 55, 0.3);
        border-radius: 50%;
        border-top-color: #d4af37;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Responsividade aprimorada */
    @media (max-width: 1200px) {
        .vehicles-gallery {
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }
    }
    
    @media (max-width: 768px) {
        .vehicles-gallery {
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        
        .btn-container {
            grid-template-columns: 1fr;
        }
        
        .hero-section {
            padding: 60px 0 40px;
        }
    }
    
    /* Esconde elementos Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Melhorias nos selects do Streamlit */
    .stSelectbox > div > div {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        color: white;
    }
    
    .stSlider > div > div > div {
        color: #d4af37;
    }
</style>
''', unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS - CONEXÃO COM POSTGRES
# =============================================

class LuxuryDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        """Conecta ao PostgreSQL do Railway"""
        if self.database_url:
            # Corrigir URL se necessário
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            try:
                return psycopg2.connect(self.database_url, sslmode='require')
            except Exception as e:
                st.error(f"Erro na conexão: {e}")
                return None
        return None
    
    def get_veiculos_estoque(self):
        """Busca veículos em estoque com fotos"""
        conn = self.get_connection()
        if not conn:
            st.error("❌ Não foi possível conectar ao banco de dados")
            return []
        
        try:
            cursor = conn.cursor()
            
            # Verificar se a coluna foto existe
            cursor.execute('''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'veiculos' AND column_name = 'foto'
            ''')
            tem_foto = cursor.fetchone() is not None
            
            query = '''
                SELECT id, modelo, ano, marca, cor, preco_venda, 
                       km, placa, combustivel, cambio, portas, observacoes,
                       data_cadastro, preco_entrada
            '''
            
            if tem_foto:
                query += ', foto'
            
            query += '''
                FROM veiculos 
                WHERE status = 'Em estoque'
                ORDER BY data_cadastro DESC
            '''
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            veiculos = []
            for row in resultados:
                veiculo = dict(zip(colunas, row))
                
                # Processar foto se existir
                if tem_foto and veiculo.get('foto'):
                    try:
                        # Converter bytes para base64
                        if isinstance(veiculo['foto'], bytes):
                            veiculo['foto_base64'] = base64.b64encode(veiculo['foto']).decode()
                        else:
                            veiculo['foto_base64'] = None
                    except:
                        veiculo['foto_base64'] = None
                else:
                    veiculo['foto_base64'] = None
                
                veiculos.append(veiculo)
            
            return veiculos
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar veículos: {e}")
            return []
        finally:
            if conn:
                conn.close()

# =============================================
# COMPONENTES PREMIUM
# =============================================

def generate_placeholder_image(veiculo):
    """Gera imagem placeholder baseada nas características do veículo"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '1a1a1a', 'Branco': 'ffffff',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513',
        'Bege': 'f5deb3', 'Dourado': 'd4af37', 'Vinho': '722f37',
        'Amarelo': 'f1c40f', 'Roxo': '9b59b6'
    }
    
    color_hex = color_map.get(veiculo['cor'], '3498db')
    texto = f"{veiculo['marca']}+{veiculo['modelo']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/600x400/{color_hex}/ffffff?text={texto}"

def create_luxury_card(veiculo):
    """Cria card premium para o veículo"""
    
    # Usar foto real se disponível, senão placeholder
    if veiculo.get('foto_base64'):
        image_src = f"data:image/jpeg;base64,{veiculo['foto_base64']}"
    else:
        image_src = generate_placeholder_image(veiculo)
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges_html = ""
    if idade <= 1:
        badges_html += '<div class="luxury-badge badge-new">🆕 NOVO</div>'
    if veiculo['km'] < 20000:
        badges_html += '<div class="luxury-badge badge-lowkm">⭐ BAIXA KM</div>'
    elif veiculo['km'] < 50000:
        badges_html += '<div class="luxury-badge badge-lowkm">🛣️ POUCA KM</div>'
    
    # Cálculo de financiamento
    entrada = veiculo['preco_venda'] * 0.2
    parcela = (veiculo['preco_venda'] - entrada) / 48
    
    # Formatar dados
    preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    entrada_formatada = f"R$ {entrada:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    parcela_formatada = f"R$ {parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    km_formatado = f"{veiculo['km']:,}".replace(',', '.')
    
    # Criar HTML do card
    card_html = f'''
    <div class="luxury-card">
        <div class="card-header">
            <img src="{image_src}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}" 
                 onerror="this.src='{generate_placeholder_image(veiculo)}'">
            <div class="card-badges">
                {badges_html}
            </div>
        </div>
        
        <div class="card-content">
            <div class="vehicle-title">{veiculo['marca']} {veiculo['modelo']}</div>
            
            <div class="vehicle-specs">
                <div class="spec-item">📅 <strong>Ano:</strong> {veiculo['ano']}</div>
                <div class="spec-item">🛣️ <strong>KM:</strong> {km_formatado}</div>
                <div class="spec-item">🎨 <strong>Cor:</strong> {veiculo['cor']}</div>
                <div class="spec-item">⚙️ <strong>Câmbio:</strong> {veiculo['cambio']}</div>
                <div class="spec-item">⛽ <strong>Combustível:</strong> {veiculo['combustivel']}</div>
                <div class="spec-item">🚪 <strong>Portas:</strong> {veiculo['portas']}</div>
            </div>
            
            <div class="price-section">
                <div class="vehicle-price">{preco_formatado}</div>
                <div class="vehicle-financing">
                    💰 <strong>Entrada:</strong> {entrada_formatada}<br>
                    📅 <strong>48x de:</strong> {parcela_formatada}
                </div>
            </div>
            
            <div class="btn-container">
                <button class="btn-details" onclick="showVehicleDetails({veiculo['id']})">
                    🔍 Detalhes Completos
                </button>
                <a href="https://wa.me/5584981885353?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - {preco_formatado}" 
                   target="_blank" class="btn-whatsapp">
                    💬 Falar no WhatsApp
                </a>
            </div>
        </div>
    </div>
    '''
    return card_html

def render_vehicle_gallery(veiculos):
    """Renderiza galeria completa de veículos"""
    if not veiculos:
        return '''
        <div style="text-align: center; padding: 80px 20px; color: #888;">
            <div style="font-size: 48px; margin-bottom: 20px;">🚫</div>
            <h3 style="color: #d4af37; margin-bottom: 10px;">Nenhum veículo encontrado</h3>
            <p style="color: #666; font-size: 16px;">Tente ajustar os filtros para encontrar mais opções!</p>
        </div>
        '''
    
    gallery_html = '<div class="vehicles-gallery">'
    for veiculo in veiculos:
        gallery_html += create_luxury_card(veiculo)
    gallery_html += '</div>'
    
    return gallery_html

# =============================================
# PÁGINA PRINCIPAL - CATÁLOGO LUXUOSO
# =============================================

def main():
    # Header Premium
    st.markdown('''
    <div class="contact-bar">
        ⭐ CONDIÇÕES ESPECIAIS • 📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Seg-Sex: 8h-18h | Sáb: 8h-12h
    </div>
    
    <div class="luxury-header">
        <div class="main-container">
            <div style="display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 2;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #d4af37, #f4c220); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                        🚗 GARAGEM MULTIMARCAS
                    </div>
                </div>
                <div style="color: #d4af37; font-size: 18px; font-weight: 600; text-align: right;">
                    Excelência Automotiva<br><span style="color: #ccc; font-size: 14px;">Desde 2024</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="hero-section">
        <div class="main-container">
            <h1 style="margin: 0; color: white; font-size: 52px; font-weight: 800; margin-bottom: 20px; line-height: 1.1;">
                CATÁLOGO <span style="background: linear-gradient(135deg, #d4af37, #f4c220); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">PREMIUM</span>
            </h1>
            <p style="color: #ccc; font-size: 22px; margin: 0 auto 30px; max-width: 600px; line-height: 1.4;">
                Descubra nossa seleção exclusiva de veículos novos e seminovos com as melhores condições do mercado
            </p>
            <div class="vehicle-counter">
                🚗 Veículos Selecionados • ⭐ Condições Especiais
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Container principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Buscar dados do banco
    with st.spinner('🔄 Carregando veículos premium...'):
        db = LuxuryDatabase()
        veiculos = db.get_veiculos_estoque()
    
    # Seção de Filtros Premium
    st.markdown('''
    <div class="filters-section">
        <div class="filter-title">🎯 ENCONTRE SEU VEÍCULO IDEAL</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Filtros em colunas
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if veiculos:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca_filtro = st.selectbox("**🏷️ Marca**", marcas, key="marca_filter")
        else:
            marca_filtro = "Todas as marcas"
    
    with col2:
        if veiculos:
            anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("**📅 Ano**", anos, key="ano_filter")
        else:
            ano_filtro = "Todos os anos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos)) if veiculos else 0
            preco_max = int(max(v['preco_venda'] for v in veiculos)) if veiculos else 200000
            preco_filtro = st.slider("**💰 Preço Máximo**", preco_min, preco_max, preco_max, 1000, key="preco_filter")
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("**🔃 Ordenar**", 
                               ["Mais recentes", "Menor preço", "Maior preço", "Mais novo", "Menor KM"],
                               key="ordenacao_filter")
    
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
        else:  # Mais recentes
            veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
    
    # Exibir contador e resultados
    st.markdown(f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 30px 0 20px 0;">
        <h2 style="color: white; margin: 0;">🚗 VEÍCULOS DISPONÍVEIS</h2>
        <div style="background: linear-gradient(135deg, #d4af37, #f4c220); color: #1a1a1a; padding: 8px 20px; border-radius: 20px; font-weight: 700;">
            {len(veiculos_filtrados)} ENCONTRADOS
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Renderizar galeria de veículos
    gallery_html = render_vehicle_gallery(veiculos_filtrados)
    
    # Usar components.html para renderizar HTML corretamente
    try:
        from streamlit.components.v1 import html
        html(gallery_html, height=800, scrolling=True)
    except:
        # Fallback se components não estiver disponível
        st.markdown(gallery_html, unsafe_allow_html=True)
    
    # Footer Luxuoso
    st.markdown('''
    <div class="luxury-footer">
        <div class="main-container">
            <div style="text-align: center;">
                <div style="font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #d4af37, #f4c220); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px;">
                    GARAGEM MULTIMARCAS
                </div>
                <div style="color: #ccc; margin-bottom: 20px; font-size: 16px;">
                    ⭐ Sua jornada automotiva premium começa aqui ⭐
                </div>
                <div style="color: #888; margin-bottom: 30px;">
                    📞 (84) 98188-5353 • 📍 Mossoró/RN • ✉️ contato@garagemmultimarcas.com
                </div>
                <div style="color: #666; font-size: 14px; border-top: 1px solid #333; padding-top: 20px;">
                    © 2024 Garagem Multimarcas - Todos os direitos reservados<br>
                    <small>Catálogo premium desenvolvido com excelência</small>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha main-container
    
    # JavaScript para interações avançadas
    st.markdown('''
    <script>
    function showVehicleDetails(vehicleId) {
        // Aqui você pode implementar um modal com detalhes completos
        const message = `🔍 Detalhes completos do veículo ID: ${vehicleId}\\n\\nEm breve: Modal com fotos ampliadas, histórico completo e mais informações!`;
        alert(message);
    }
    
    // Efeitos de hover melhorados
    document.addEventListener('DOMContentLoaded', function() {
        const cards = document.querySelectorAll('.luxury-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-12px) scale(1.02)';
            });
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    });
    
    // Smooth scroll para filtros
    function scrollToFilters() {
        document.querySelector('.filters-section').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }
    </script>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
