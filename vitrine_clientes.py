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
# CSS ESTILO OLX
# =============================================

st.markdown('''
<style>
    /* Reset e configurações base */
    .stApp {
        background: #f5f5f5;
        color: #333333;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: 100%;
    }
    
    /* Header */
    .header-container {
        background: #ffffff;
        padding: 15px 0;
        border-bottom: 3px solid #e88e1b;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .contact-bar {
        background: #e88e1b;
        color: #ffffff;
        padding: 12px 0;
        text-align: center;
        font-weight: 700;
        font-size: 14px;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 40px 0 30px;
        text-align: center;
        color: white;
    }
    
    /* Grid de Cards - Estilo OLX */
    .vehicles-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px;
        margin: 30px 0;
        padding: 0 10px;
    }
    
    /* Card estilo OLX */
    .vehicle-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 0;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .vehicle-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        border-color: #e88e1b;
    }
    
    /* Container da imagem */
    .image-container {
        position: relative;
        width: 100%;
        height: 200px;
        overflow: hidden;
        background: #f8f8f8;
    }
    
    .vehicle-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    }
    
    .vehicle-card:hover .vehicle-image {
        transform: scale(1.05);
    }
    
    /* Badges */
    .card-badge {
        position: absolute;
        top: 10px;
        left: 10px;
        background: #e88e1b;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        z-index: 2;
    }
    
    .badge-new {
        background: #27ae60;
    }
    
    .badge-lowkm {
        background: #e88e1b;
    }
    
    /* Conteúdo do card */
    .card-content {
        padding: 15px;
    }
    
    .vehicle-price {
        font-size: 20px;
        font-weight: 800;
        color: #2c3e50;
        margin: 0 0 8px 0;
    }
    
    .vehicle-name {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 8px 0;
        line-height: 1.3;
    }
    
    .vehicle-details {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 13px;
        color: #7f8c8d;
    }
    
    .vehicle-year {
        font-weight: 600;
        color: #e88e1b;
    }
    
    .vehicle-km {
        font-weight: 500;
    }
    
    .vehicle-specs {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        font-size: 12px;
        color: #7f8c8d;
    }
    
    .spec-item {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* Botões */
    .btn-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    
    .stButton>button {
        width: 100%;
        border: none;
        border-radius: 6px;
        padding: 8px;
        font-weight: 600;
        font-size: 11px;
        transition: all 0.3s ease;
    }
    
    .btn-details {
        background: #3498db;
        color: white;
    }
    
    .btn-details:hover {
        background: #2980b9;
    }
    
    .btn-whatsapp {
        background: #25D366;
        color: white;
    }
    
    .btn-whatsapp:hover {
        background: #20bd5c;
    }
    
    /* Filtros */
    .filters-section {
        background: #ffffff;
        padding: 25px;
        border-radius: 12px;
        margin: 30px 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .filter-title {
        font-size: 18px;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Footer */
    .footer {
        background: #2c3e50;
        padding: 40px 0 20px;
        margin-top: 50px;
        color: white;
    }
    
    .vehicle-counter {
        background: #e88e1b;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
        display: inline-block;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(232, 142, 27, 0.3);
    }
    
    /* Loading */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px;
    }
    
    /* Detalhes do veículo */
    .details-modal {
        background: #ffffff;
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        border: 2px solid #e88e1b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Esconde elementos Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Melhorias nos selects */
    .stSelectbox > div > div {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    
    .stSlider > div > div > div {
        color: #e88e1b;
    }
</style>
''', unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS
# =============================================

class LuxuryDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        """Conecta ao PostgreSQL do Railway"""
        if self.database_url:
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            try:
                return psycopg2.connect(self.database_url, sslmode='require')
            except Exception as e:
                return None
        return None
    
    def get_veiculos_estoque(self):
        """Busca veículos em estoque com fotos"""
        conn = self.get_connection()
        if not conn:
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
            return []
        finally:
            if conn:
                conn.close()

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def generate_placeholder_image(veiculo):
    """Gera imagem placeholder estilo OLX"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '2c3e50', 'Branco': 'ecf0f1',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513',
        'Bege': 'f5deb3', 'Dourado': 'd4af37', 'Vinho': '722f37'
    }
    
    color_hex = color_map.get(veiculo['cor'], '3498db')
    texto = f"{veiculo['marca']}+{veiculo['modelo']}".replace(' ', '+')
    
    return f"https://via.placeholder.com/400x300/{color_hex}/ffffff?text={texto}"

def load_logo():
    """Carrega a logo do repositório"""
    try:
        logo = Image.open("logoca.png")
        return logo
    except:
        return None

def create_vehicle_card(veiculo):
    """Cria um card de veículo estilo OLX"""
    
    # Usar foto real se disponível, senão placeholder
    if veiculo.get('foto_base64'):
        image_src = f"data:image/jpeg;base64,{veiculo['foto_base64']}"
    else:
        image_src = generate_placeholder_image(veiculo)
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges = []
    if idade <= 1:
        badges.append(("🆕 NOVO", "badge-new"))
    if veiculo['km'] < 20000:
        badges.append(("⭐ BAIXA KM", "badge-lowkm"))
    
    # Formatar dados
    preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    km_formatado = f"{veiculo['km']:,} km".replace(',', '.')
    
    # Criar HTML do card
    card_html = f'''
    <div class="vehicle-card">
        <div class="image-container">
            <img src="{image_src}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
            {''.join([f'<div class="card-badge {badge_class}">{badge_text}</div>' for badge_text, badge_class in badges])}
        </div>
        
        <div class="card-content">
            <div class="vehicle-price">{preco_formatado}</div>
            <div class="vehicle-name">{veiculo['marca']} {veiculo['modelo']}</div>
            
            <div class="vehicle-details">
                <span class="vehicle-year">{veiculo['ano']}</span>
                <span class="vehicle-km">{km_formatado}</span>
            </div>
            
            <div class="vehicle-specs">
                <div class="spec-item">⚙️ {veiculo['cambio']}</div>
                <div class="spec-item">⛽ {veiculo['combustivel']}</div>
            </div>
            
            <div class="btn-container">
                <button class="btn-details" onclick="showVehicleDetails({veiculo['id']})">
                    🔍 Ver Detalhes
                </button>
                <a href="https://wa.me/5584981885353?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - {preco_formatado}" 
                   target="_blank" class="btn-whatsapp">
                    💬 WhatsApp
                </a>
            </div>
        </div>
    </div>
    '''
    return card_html

def render_vehicle_grid(veiculos):
    """Renderiza grid de veículos"""
    if not veiculos:
        return '''
        <div style="text-align: center; padding: 60px 20px; color: #7f8c8d;">
            <div style="font-size: 64px; margin-bottom: 20px;">🚗</div>
            <h3 style="color: #e88e1b; margin-bottom: 10px;">Nenhum veículo encontrado</h3>
            <p style="color: #95a5a6;">Tente ajustar os filtros para encontrar mais opções!</p>
        </div>
        '''
    
    grid_html = '<div class="vehicles-grid">'
    for veiculo in veiculos:
        grid_html += create_vehicle_card(veiculo)
    grid_html += '</div>'
    
    return grid_html

def show_vehicle_details(veiculo):
    """Mostra detalhes completos do veículo"""
    with st.expander(f"🚗 Detalhes Completos - {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}", expanded=True):
        # Imagem principal
        if veiculo.get('foto_base64'):
            image_src = f"data:image/jpeg;base64,{veiculo['foto_base64']}"
            st.image(image_src, use_column_width=True)
        else:
            st.image(generate_placeholder_image(veiculo), use_column_width=True)
        
        # Informações em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Informações do Veículo")
            st.write(f"**Marca:** {veiculo['marca']}")
            st.write(f"**Modelo:** {veiculo['modelo']}")
            st.write(f"**Ano:** {veiculo['ano']}")
            st.write(f"**Cor:** {veiculo['cor']}")
            st.write(f"**KM:** {veiculo['km']:,}")
        
        with col2:
            st.subheader("⚙️ Especificações Técnicas")
            st.write(f"**Câmbio:** {veiculo['cambio']}")
            st.write(f"**Combustível:** {veiculo['combustivel']}")
            st.write(f"**Portas:** {veiculo['portas']}")
            st.write(f"**Placa:** {veiculo['placa'] or 'Não informada'}")
        
        # Preço
        st.subheader("💰 Valores")
        preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        entrada = veiculo['preco_venda'] * 0.2
        parcela = (veiculo['preco_venda'] - entrada) / 48
        entrada_formatada = f"R$ {entrada:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        parcela_formatada = f"R$ {parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        col_preco1, col_preco2, col_preco3 = st.columns(3)
        with col_preco1:
            st.metric("Preço à Vista", preco_formatado)
        with col_preco2:
            st.metric("Entrada", entrada_formatada)
        with col_preco3:
            st.metric("Parcela (48x)", parcela_formatada)
        
        if veiculo.get('observacoes'):
            st.subheader("📝 Observações")
            st.info(veiculo['observacoes'])

# =============================================
# PÁGINA PRINCIPAL - ESTILO OLX
# =============================================

def main():
    # Header
    logo = load_logo()
    
    st.markdown('<div class="contact-bar">⭐ CONDIÇÕES ESPECIAIS • 📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Seg-Sex: 8h-18h</div>', unsafe_allow_html=True)
    
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        if logo:
            st.image(logo, width=80)
        else:
            st.markdown('<div style="font-size: 40px; text-align: center;">🚗</div>', unsafe_allow_html=True)
    
    with col_title:
        st.markdown('<div style="font-size: 32px; font-weight: 800; color: #e88e1b; margin-top: 10px; text-align: center;">GARAGEM MULTIMARCAS</div>', unsafe_allow_html=True)
    
    # Hero Section
    st.markdown('''
    <div class="hero-section">
        <h1 style="font-size: 36px; font-weight: 800; margin-bottom: 10px;">
            CATÁLOGO DE VEÍCULOS
        </h1>
        <p style="font-size: 18px; opacity: 0.9;">
            Encontre o carro dos seus sonhos com as melhores condições
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Buscar dados do banco
    with st.spinner('🔄 Carregando veículos...'):
        db = LuxuryDatabase()
        veiculos = db.get_veiculos_estoque()
    
    # Filtros
    st.markdown('<div class="filters-section">', unsafe_allow_html=True)
    st.markdown('<div class="filter-title">🔍 FILTRAR VEÍCULOS</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if veiculos:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca_filtro = st.selectbox("Marca", marcas)
        else:
            marca_filtro = "Todas as marcas"
    
    with col2:
        if veiculos:
            anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("Ano", anos)
        else:
            ano_filtro = "Todos os anos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos)) if veiculos else 0
            preco_max = int(max(v['preco_venda'] for v in veiculos)) if veiculos else 200000
            preco_filtro = st.slider("Preço Máximo (R$)", preco_min, preco_max, preco_max, 1000)
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("Ordenar", ["Mais recentes", "Menor preço", "Maior preço", "Menor KM"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
        elif ordenacao == "Menor KM":
            veiculos_filtrados.sort(key=lambda x: x['km'])
        else:
            veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
    
    # Exibir resultados
    st.markdown(f'<div class="vehicle-counter">🚗 {len(veiculos_filtrados)} VEÍCULOS ENCONTRADOS</div>', unsafe_allow_html=True)
    
    # Renderizar grid
    grid_html = render_vehicle_grid(veiculos_filtrados)
    st.markdown(grid_html, unsafe_allow_html=True)
    
    # Footer
    st.markdown('''
    <div class="footer">
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: 800; color: #e88e1b; margin-bottom: 10px;">
                GARAGEM MULTIMARCAS
            </div>
            <div style="color: #bdc3c7; margin-bottom: 15px;">
                ⭐ Sua escolha certa em veículos ⭐
            </div>
            <div style="color: #95a5a6; margin-bottom: 20px;">
                📞 (84) 98188-5353 • 📍 Mossoró/RN
            </div>
            <div style="color: #7f8c8d; font-size: 12px;">
                © 2024 Garagem Multimarcas - Todos os direitos reservados
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # JavaScript para interações
    st.markdown('''
    <script>
    function showVehicleDetails(vehicleId) {
        // Em uma implementação real, isso abriria um modal ou expandiria os detalhes
        alert("Detalhes do veículo ID: " + vehicleId + "\\n\\nFuncionalidade em desenvolvimento!");
    }
    
    // Efeito hover melhorado
    document.addEventListener('DOMContentLoaded', function() {
        const cards = document.querySelectorAll('.vehicle-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
            });
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    });
    </script>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
