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
    
    .contact-bar {
        background: linear-gradient(90deg, #d4af37, #f4c220);
        color: #1a1a1a;
        padding: 12px 0;
        text-align: center;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 0.5px;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2d1a0f 100%);
        padding: 40px 0 30px;
        text-align: center;
        position: relative;
    }
    
    /* Cards de veículos */
    .vehicle-card {
        background: linear-gradient(145deg, #1a1a1a, #0f0f0f);
        border-radius: 15px;
        padding: 0;
        border: 1px solid #333;
        transition: all 0.3s ease;
        margin-bottom: 25px;
        overflow: hidden;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
        box-shadow: 0 10px 25px rgba(212, 175, 55, 0.2);
    }
    
    .vehicle-image-container {
        position: relative;
        height: 200px;
        overflow: hidden;
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
    
    .vehicle-badges {
        position: absolute;
        top: 10px;
        left: 10px;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    
    .luxury-badge {
        padding: 6px 12px;
        border-radius: 15px;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        backdrop-filter: blur(10px);
    }
    
    .badge-new {
        background: linear-gradient(135deg, #27ae60, #219a52);
        color: white;
    }
    
    .badge-lowkm {
        background: linear-gradient(135deg, #d4af37, #b8941f);
        color: #1a1a1a;
    }
    
    .card-content {
        padding: 20px;
    }
    
    .vehicle-title {
        font-size: 18px;
        font-weight: 700;
        color: #d4af37;
        margin: 0 0 10px 0;
        line-height: 1.3;
    }
    
    .vehicle-specs {
        color: #b0b0b0;
        font-size: 13px;
        margin-bottom: 15px;
        line-height: 1.5;
    }
    
    .spec-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    
    .price-section {
        border-top: 1px solid #333;
        padding-top: 15px;
        margin-top: 10px;
    }
    
    .vehicle-price {
        font-size: 22px;
        font-weight: 800;
        color: #d4af37;
        margin: 0 0 5px 0;
    }
    
    .vehicle-financing {
        color: #888;
        font-size: 12px;
        margin-bottom: 15px;
        line-height: 1.4;
    }
    
    .btn-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
    
    .stButton>button {
        width: 100%;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-weight: 600;
        font-size: 12px;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
    }
    
    .btn-details {
        background: linear-gradient(135deg, #333, #555);
        color: white;
    }
    
    .btn-details:hover {
        background: linear-gradient(135deg, #444, #666);
        transform: translateY(-2px);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
    }
    
    .btn-whatsapp:hover {
        background: linear-gradient(135deg, #20bd5c, #0f7a61);
        transform: translateY(-2px);
    }
    
    /* Filtros */
    .filters-section {
        background: linear-gradient(135deg, #1a1a1a, #0f0f0f);
        padding: 25px;
        border-radius: 15px;
        margin: 30px 0;
        border: 1px solid #333;
    }
    
    /* Footer */
    .luxury-footer {
        background: linear-gradient(135deg, #1a1a1a, #0f0f0f);
        padding: 40px 0 20px;
        margin-top: 50px;
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
    
    .vehicle-counter {
        background: linear-gradient(135deg, #d4af37, #f4c220);
        color: #1a1a1a;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    /* Grid responsivo */
    .vehicles-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    /* Melhorias nos componentes Streamlit */
    .stSelectbox > div > div {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        color: white;
    }
    
    .stSlider > div > div > div {
        color: #d4af37;
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
# FUNÇÕES AUXILIARES
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
    
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={texto}"

def load_logo():
    """Carrega a logo do repositório"""
    try:
        logo = Image.open("logoca.png")
        return logo
    except:
        return None

def create_vehicle_card(veiculo):
    """Cria um card de veículo usando componentes Streamlit"""
    
    # Usar foto real se disponível, senão placeholder
    if veiculo.get('foto_base64'):
        image_data = base64.b64decode(veiculo['foto_base64'])
        image = Image.open(io.BytesIO(image_data))
    else:
        # Para placeholder, vamos usar uma imagem genérica
        image = None
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges = []
    if idade <= 1:
        badges.append(("🆕 NOVO", "badge-new"))
    if veiculo['km'] < 20000:
        badges.append(("⭐ BAIXA KM", "badge-lowkm"))
    elif veiculo['km'] < 50000:
        badges.append(("🛣️ POUCA KM", "badge-lowkm"))
    
    # Cálculo de financiamento
    entrada = veiculo['preco_venda'] * 0.2
    parcela = (veiculo['preco_venda'] - entrada) / 48
    
    # Formatar dados
    preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    entrada_formatada = f"R$ {entrada:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    parcela_formatada = f"R$ {parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    km_formatado = f"{veiculo['km']:,}".replace(',', '.')
    
    # Criar card usando columns
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Imagem do veículo
            if image:
                st.image(image, use_column_width=True)
            else:
                st.image(generate_placeholder_image(veiculo), use_column_width=True)
            
            # Badges
            if badges:
                badge_cols = st.columns(len(badges))
                for i, (badge_text, badge_class) in enumerate(badges):
                    with badge_cols[i]:
                        st.markdown(f'<div class="luxury-badge {badge_class}">{badge_text}</div>', unsafe_allow_html=True)
        
        with col2:
            # Informações do veículo
            st.markdown(f'<div class="vehicle-title">{veiculo["marca"]} {veiculo["modelo"]}</div>', unsafe_allow_html=True)
            
            # Especificações
            st.markdown(f'''
            <div class="vehicle-specs">
                <div class="spec-item">📅 <strong>Ano:</strong> {veiculo['ano']}</div>
                <div class="spec-item">🛣️ <strong>KM:</strong> {km_formatado}</div>
                <div class="spec-item">🎨 <strong>Cor:</strong> {veiculo['cor']}</div>
                <div class="spec-item">⚙️ <strong>Câmbio:</strong> {veiculo['cambio']}</div>
                <div class="spec-item">⛽ <strong>Combustível:</strong> {veiculo['combustivel']}</div>
                <div class="spec-item">🚪 <strong>Portas:</strong> {veiculo['portas']}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Preço e financiamento
            st.markdown(f'''
            <div class="price-section">
                <div class="vehicle-price">{preco_formatado}</div>
                <div class="vehicle-financing">
                    💰 <strong>Entrada:</strong> {entrada_formatada}<br>
                    📅 <strong>48x de:</strong> {parcela_formatada}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Botões de ação
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔍 Detalhes", key=f"details_{veiculo['id']}", use_container_width=True):
                    show_vehicle_details(veiculo)
            with col_btn2:
                whatsapp_url = f"https://wa.me/5584981885353?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - {preco_formatado}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button class="btn-whatsapp" style="width:100%">💬 WhatsApp</button></a>', unsafe_allow_html=True)
        
        st.markdown("---")

def show_vehicle_details(veiculo):
    """Mostra detalhes completos do veículo em um modal"""
    st.session_state[f"show_details_{veiculo['id']}"] = True
    
    with st.expander(f"🚗 Detalhes Completos - {veiculo['marca']} {veiculo['modelo']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if veiculo.get('foto_base64'):
                image_data = base64.b64decode(veiculo['foto_base64'])
                image = Image.open(io.BytesIO(image_data))
                st.image(image, use_column_width=True)
            else:
                st.image(generate_placeholder_image(veiculo), use_column_width=True)
        
        with col2:
            st.subheader("📋 Informações Técnicas")
            st.write(f"**Marca:** {veiculo['marca']}")
            st.write(f"**Modelo:** {veiculo['modelo']}")
            st.write(f"**Ano:** {veiculo['ano']}")
            st.write(f"**Cor:** {veiculo['cor']}")
            st.write(f"**KM:** {veiculo['km']:,}")
            st.write(f"**Placa:** {veiculo['placa'] or 'Não informada'}")
            st.write(f"**Combustível:** {veiculo['combustivel']}")
            st.write(f"**Câmbio:** {veiculo['cambio']}")
            st.write(f"**Portas:** {veiculo['portas']}")
            
            if veiculo.get('observacoes'):
                st.subheader("📝 Observações")
                st.write(veiculo['observacoes'])

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header com logo
    logo = load_logo()
    
    st.markdown('<div class="contact-bar">⭐ CONDIÇÕES ESPECIAIS • 📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Seg-Sex: 8h-18h | Sáb: 8h-12h</div>', unsafe_allow_html=True)
    
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        if logo:
            st.image(logo, width=100)
        else:
            st.markdown('<div style="font-size: 48px;">🚗</div>', unsafe_allow_html=True)
    
    with col_title:
        st.markdown('<div style="font-size: 32px; font-weight: 800; color: #d4af37; margin-top: 10px;">GARAGEM MULTIMARCAS</div>', unsafe_allow_html=True)
    
    # Hero Section
    st.markdown('''
    <div class="hero-section">
        <h1 style="color: white; font-size: 36px; font-weight: 800; margin-bottom: 10px;">
            CATÁLOGO PREMIUM
        </h1>
        <p style="color: #ccc; font-size: 18px; margin-bottom: 20px;">
            Os melhores veículos novos e seminovos com condições especiais
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Buscar dados do banco
    with st.spinner('🔄 Carregando veículos...'):
        db = LuxuryDatabase()
        veiculos = db.get_veiculos_estoque()
    
    # Filtros
    st.markdown('<div class="filters-section">', unsafe_allow_html=True)
    st.subheader("🎯 Filtros")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if veiculos:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca_filtro = st.selectbox("🏷️ Marca", marcas, key="marca_filter")
        else:
            marca_filtro = "Todas as marcas"
    
    with col2:
        if veiculos:
            anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("📅 Ano", anos, key="ano_filter")
        else:
            ano_filtro = "Todos os anos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos)) if veiculos else 0
            preco_max = int(max(v['preco_venda'] for v in veiculos)) if veiculos else 200000
            preco_filtro = st.slider("💰 Preço Máximo (R$)", preco_min, preco_max, preco_max, 1000, key="preco_filter")
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("🔃 Ordenar", 
                               ["Mais recentes", "Menor preço", "Maior preço", "Mais novo", "Menor KM"],
                               key="ordenacao_filter")
    
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
        elif ordenacao == "Mais novo":
            veiculos_filtrados.sort(key=lambda x: x['ano'], reverse=True)
        elif ordenacao == "Menor KM":
            veiculos_filtrados.sort(key=lambda x: x['km'])
        else:  # Mais recentes
            veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
    
    # Exibir resultados
    st.markdown(f'<div class="vehicle-counter">🚗 {len(veiculos_filtrados)} VEÍCULOS ENCONTRADOS</div>', unsafe_allow_html=True)
    
    # Exibir veículos
    if veiculos_filtrados:
        for veiculo in veiculos_filtrados:
            create_vehicle_card(veiculo)
    else:
        st.info("📝 Nenhum veículo encontrado com os filtros selecionados.")
    
    # Footer
    st.markdown('''
    <div class="luxury-footer">
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: 800; color: #d4af37; margin-bottom: 10px;">
                GARAGEM MULTIMARCAS
            </div>
            <div style="color: #ccc; margin-bottom: 15px;">
                ⭐ Sua escolha premium em veículos ⭐
            </div>
            <div style="color: #888; margin-bottom: 20px;">
                📞 (84) 98188-5353 • 📍 Mossoró/RN
            </div>
            <div style="color: #666; font-size: 12px;">
                © 2024 Garagem Multimarcas - Todos os direitos reservados
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
