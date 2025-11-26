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
# CSS SIMPLES E FUNCIONAL
# =============================================

st.markdown('''
<style>
    .stApp {
        background: #f8f9fa;
    }
    
    .vehicle-card {
        background: white;
        border-radius: 12px;
        padding: 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        overflow: hidden;
    }
    
    .vehicle-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .card-content {
        padding: 15px;
    }
    
    .vehicle-price {
        font-size: 20px;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    
    .vehicle-name {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    
    .vehicle-details {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 14px;
        color: #7f8c8d;
    }
    
    .vehicle-specs {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        font-size: 13px;
        color: #7f8c8d;
    }
    
    .badge {
        background: #e88e1b;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 700;
        margin-bottom: 5px;
        display: inline-block;
    }
    
    .badge-new {
        background: #27ae60;
    }
    
    .badge-lowkm {
        background: #e88e1b;
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
    """Gera imagem placeholder"""
    color_map = {
        'Prata': 'c0c0c0', 'Preto': '2c3e50', 'Branco': 'ecf0f1',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513'
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
    """Cria um card de veículo usando componentes Streamlit"""
    
    with st.container():
        # Container do card
        st.markdown('<div class="vehicle-card">', unsafe_allow_html=True)
        
        # Badges
        idade = datetime.now().year - veiculo['ano']
        badges = []
        if idade <= 1:
            badges.append(("🆕 NOVO", "badge-new"))
        if veiculo['km'] < 20000:
            badges.append(("⭐ BAIXA KM", "badge-lowkm"))
        
        # Imagem
        if veiculo.get('foto_base64'):
            try:
                image_data = base64.b64decode(veiculo['foto_base64'])
                image = Image.open(io.BytesIO(image_data))
                st.image(image, use_column_width=True)
            except:
                st.image(generate_placeholder_image(veiculo), use_column_width=True)
        else:
            st.image(generate_placeholder_image(veiculo), use_column_width=True)
        
        # Conteúdo do card
        col_content = st.columns(1)[0]
        with col_content:
            # Badges
            if badges:
                for badge_text, badge_class in badges:
                    st.markdown(f'<div class="badge {badge_class}">{badge_text}</div>', unsafe_allow_html=True)
            
            # Preço
            preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            st.markdown(f'<div class="vehicle-price">{preco_formatado}</div>', unsafe_allow_html=True)
            
            # Nome
            st.markdown(f'<div class="vehicle-name">{veiculo["marca"]} {veiculo["modelo"]}</div>', unsafe_allow_html=True)
            
            # Detalhes (Ano e KM)
            km_formatado = f"{veiculo['km']:,} km".replace(',', '.')
            st.markdown(f'''
            <div class="vehicle-details">
                <span>{veiculo["ano"]}</span>
                <span>{km_formatado}</span>
            </div>
            ''', unsafe_allow_html=True)
            
            # Especificações
            st.markdown(f'''
            <div class="vehicle-specs">
                <div>⚙️ {veiculo["cambio"]}</div>
                <div>⛽ {veiculo["combustivel"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Botões
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔍 Detalhes", key=f"details_{veiculo['id']}", use_container_width=True):
                    show_vehicle_details(veiculo)
            with col_btn2:
                whatsapp_url = f"https://wa.me/5584981885353?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; background: #25D366; color: white; border: none; border-radius: 6px; padding: 8px; font-weight: 600; cursor: pointer;">💬 WhatsApp</button></a>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_vehicle_details(veiculo):
    """Mostra detalhes completos do veículo"""
    with st.expander(f"🚗 Detalhes Completos - {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}", expanded=True):
        # Imagem
        if veiculo.get('foto_base64'):
            try:
                image_data = base64.b64decode(veiculo['foto_base64'])
                image = Image.open(io.BytesIO(image_data))
                st.image(image, use_column_width=True)
            except:
                st.image(generate_placeholder_image(veiculo), use_column_width=True)
        else:
            st.image(generate_placeholder_image(veiculo), use_column_width=True)
        
        # Informações
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Informações")
            st.write(f"**Marca:** {veiculo['marca']}")
            st.write(f"**Modelo:** {veiculo['modelo']}")
            st.write(f"**Ano:** {veiculo['ano']}")
            st.write(f"**Cor:** {veiculo['cor']}")
            st.write(f"**KM:** {veiculo['km']:,}")
        
        with col2:
            st.subheader("⚙️ Especificações")
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

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header
    logo = load_logo()
    
    st.markdown('<div style="background: #e88e1b; color: white; padding: 12px 0; text-align: center; font-weight: 700; font-size: 14px;">⭐ CONDIÇÕES ESPECIAIS • 📞 (84) 98188-5353 • 📍 Mossoró/RN</div>', unsafe_allow_html=True)
    
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
    <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 40px 0 30px; text-align: center; color: white;">
        <h1 style="font-size: 36px; font-weight: 800; margin-bottom: 10px;">CATÁLOGO DE VEÍCULOS</h1>
        <p style="font-size: 18px; opacity: 0.9;">Encontre o carro dos seus sonhos com as melhores condições</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Buscar dados do banco
    with st.spinner('Carregando veículos...'):
        db = LuxuryDatabase()
        veiculos = db.get_veiculos_estoque()
    
    # Filtros
    st.markdown('<div style="background: white; padding: 25px; border-radius: 12px; margin: 30px 0; border: 1px solid #e0e0e0;">', unsafe_allow_html=True)
    st.subheader("🔍 FILTRAR VEÍCULOS")
    
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
    st.markdown(f'<div style="background: #e88e1b; color: white; padding: 10px 20px; border-radius: 20px; font-weight: 700; display: inline-block; margin-bottom: 20px;">🚗 {len(veiculos_filtrados)} VEÍCULOS ENCONTRADOS</div>', unsafe_allow_html=True)
    
    # Grid de veículos
    if veiculos_filtrados:
        # Criar grid com columns
        cols_per_row = 3
        for i in range(0, len(veiculos_filtrados), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(veiculos_filtrados):
                    with cols[j]:
                        create_vehicle_card(veiculos_filtrados[i + j])
    else:
        st.info("📝 Nenhum veículo encontrado com os filtros selecionados.")
    
    # Footer
    st.markdown('''
    <div style="background: #2c3e50; padding: 40px 0 20px; margin-top: 50px; color: white; text-align: center;">
        <div style="font-size: 24px; font-weight: 800; color: #e88e1b; margin-bottom: 10px;">GARAGEM MULTIMARCAS</div>
        <div style="color: #bdc3c7; margin-bottom: 15px;">⭐ Sua escolha certa em veículos ⭐</div>
        <div style="color: #95a5a6; margin-bottom: 20px;">📞 (84) 98188-5353 • 📍 Mossoró/RN</div>
        <div style="color: #7f8c8d; font-size: 12px;">© 2024 Garagem Multimarcas</div>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
