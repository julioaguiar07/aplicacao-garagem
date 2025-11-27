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
    page_title="Garagem Multimarcas",
    page_icon="logo-icon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
                            veiculo['foto_base64'] = base64.b64encode(veiculo['foto']).decode('utf-8')
                        elif isinstance(veiculo['foto'], memoryview):
                            veiculo['foto_base64'] = base64.b64encode(veiculo['foto'].tobytes()).decode('utf-8')
                        else:
                            veiculo['foto_base64'] = None
                    except Exception as e:
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
        'Prata': 'c0c0c0', 'Preto': '1a1a1a', 'Branco': 'ffffff',
        'Vermelho': 'e74c3c', 'Azul': '3498db', 'Cinza': '7f8c8d',
        'Verde': '27ae60', 'Laranja': 'e67e22', 'Marrom': '8b4513',
        'Bege': 'f5deb3', 'Dourado': 'd4af37', 'Vinho': '722f37'
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
    """Cria um card de veículo usando Streamlit nativo"""
    
    # Determinar imagem
    image_src = generate_placeholder_image(veiculo)
    if veiculo.get('foto_base64'):
        try:
            base64.b64decode(veiculo['foto_base64'])
            image_src = f"data:image/jpeg;base64,{veiculo['foto_base64']}"
        except:
            image_src = generate_placeholder_image(veiculo)
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges = []
    if idade <= 1:
        badges.append("🆕 NOVO")
    if veiculo['km'] < 20000:
        badges.append("⭐ BAIXA KM")
    
    # Cálculo de financiamento
    entrada = veiculo['preco_venda'] * 0.2
    parcela = (veiculo['preco_venda'] - entrada) / 48
    
    # Formatar dados
    preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    parcela_formatada = f"R$ {parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    km_formatado = f"{veiculo['km']:,} km".replace(',', '.')
    
    # Criar card usando Streamlit
    with st.container():
        # Container principal do card
        st.markdown("""
        <style>
            .vehicle-card {
                background: #1a1a1a;
                border-radius: 16px;
                border: 1px solid #333;
                transition: all 0.3s ease;
                overflow: hidden;
                margin-bottom: 25px;
                height: 100%;
            }
            .vehicle-card:hover {
                transform: translateY(-5px);
                border-color: #e88e1b;
                box-shadow: 0 10px 30px rgba(232, 142, 27, 0.2);
            }
            .image-container {
                position: relative;
                width: 100%;
                height: 200px;
                overflow: hidden;
                background: #2d2d2d;
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
            .badges-container {
                position: absolute;
                top: 12px;
                left: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .badge {
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .badge-new {
                background: #27ae60;
                color: white;
            }
            .badge-lowkm {
                background: #e88e1b;
                color: #1a1a1a;
            }
            .card-content {
                padding: 20px;
            }
            .vehicle-price {
                font-size: 22px;
                font-weight: 800;
                color: #e88e1b;
                margin-bottom: 8px;
            }
            .vehicle-name {
                font-size: 18px;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 12px;
                line-height: 1.3;
            }
            .vehicle-details {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                font-size: 14px;
                color: #b0b0b0;
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
                font-size: 13px;
                color: #888;
            }
            .spec-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .price-info {
                margin-bottom: 15px;
            }
            .parcel-info {
                font-size: 12px;
                color: #888;
                text-align: center;
            }
            .btn-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            .btn-details {
                background: #333;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                text-decoration: none;
                display: block;
            }
            .btn-details:hover {
                background: #444;
            }
            .btn-whatsapp {
                background: #25D366;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                text-decoration: none;
                display: block;
                text-align: center;
                transition: all 0.3s ease;
            }
            .btn-whatsapp:hover {
                background: #20bd5c;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Card HTML
        card_html = f'''
        <div class="vehicle-card">
            <div class="image-container">
                <img src="{image_src}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
                <div class="badges-container">
        '''
        
        for badge in badges:
            if "NOVO" in badge:
                card_html += '<div class="badge badge-new">🆕 NOVO</div>'
            elif "BAIXA KM" in badge:
                card_html += '<div class="badge badge-lowkm">⭐ BAIXA KM</div>'
        
        card_html += f'''
                </div>
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
                
                <div class="price-info">
                    <div class="parcel-info">ou 48x de {parcela_formatada}</div>
                </div>
                
                <div class="btn-container">
                    <button class="btn-details" onclick="showVehicleDetails({veiculo['id']})">
                        🔍 Detalhes
                    </button>
                    <a href="https://wa.me/558430622434?text=Olá! Gostaria de informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - Placa: {veiculo['placa']}" 
                       target="_blank" class="btn-whatsapp">
                        💬 WhatsApp
                    </a>
                </div>
            </div>
        </div>
        '''
        
        st.markdown(card_html, unsafe_allow_html=True)

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # CSS global para remover scroll duplo
    st.markdown("""
    <style>
        /* Remove scrollbars do Streamlit */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* Header fixo */
        .stApp {
            background: #0f0f0f;
        }
        /* Remove espaçamento extra */
        div[data-testid="stVerticalBlock"] {
            gap: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Buscar dados do banco
    with st.spinner('🔄 Carregando veículos...'):
        db = LuxuryDatabase()
        veiculos = db.get_veiculos_estoque()
    
    # Header com logo
    logo = load_logo()
    if logo:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=200)
    
    # Título principal
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #e88e1b; font-size: 3rem; margin-bottom: 1rem;">GARAGEM MULTIMARCAS</h1>
        <p style="color: #b0b0b0; font-size: 1.2rem;">Os melhores veículos novos e seminovos com condições especiais de pagamento</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra de contato
    st.markdown("""
    <div style="background: #e88e1b; color: #1a1a1a; padding: 12px; text-align: center; font-weight: 700; font-size: 14px; border-radius: 8px; margin-bottom: 2rem;">
        📞 (84) 93062-2434 • 📍 Mossoró/RN • ⏰ Seg-Sex: 8h-17:20h Sab:8-12h
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros
    st.markdown("### 🔍 FILTRAR VEÍCULOS")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if veiculos:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca_filtro = st.selectbox("🏷️ Marca", marcas, key="marca_filtro")
        else:
            marca_filtro = "Todas as marcas"
    
    with col2:
        if veiculos:
            anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("📅 Ano", anos, key="ano_filtro")
        else:
            ano_filtro = "Todos os anos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos)) if veiculos else 0
            preco_max = int(max(v['preco_venda'] for v in veiculos)) if veiculos else 200000
            preco_filtro = st.slider("💰 Preço Máximo (R$)", preco_min, preco_max, preco_max, 1000, key="preco_filtro")
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("🔃 Ordenar", ["Mais recentes", "Menor preço", "Maior preço", "Menor KM"], key="ordenacao")
    
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
    
    # Contador de veículos
    st.markdown(f"""
    <div style="background: #e88e1b; color: #1a1a1a; padding: 12px 24px; border-radius: 25px; font-weight: 800; font-size: 14px; display: inline-block; margin: 1rem 0;">
        🚗 {len(veiculos_filtrados)} VEÍCULOS ENCONTRADOS
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de veículos
    if not veiculos_filtrados:
        st.markdown("""
        <div style="text-align: center; padding: 80px 20px; color: #888;">
            <div style="font-size: 64px; margin-bottom: 20px;">🚗</div>
            <h3 style="color: #e88e1b; margin-bottom: 10px;">Nenhum veículo encontrado</h3>
            <p>Tente ajustar os filtros para encontrar mais opções!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Criar grid responsivo
        cols = st.columns(3)
        for i, veiculo in enumerate(veiculos_filtrados):
            with cols[i % 3]:
                create_vehicle_card(veiculo)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #888;">
        <div style="font-size: 24px; font-weight: 800; color: #e88e1b; margin-bottom: 10px;">GARAGEM MULTIMARCAS</div>
        <div style="color: #888; margin-bottom: 20px;">📞 (84) 93062-2434 / (84) 98188-5353 • 📍 Rua José Damião, 61 Santo Antonio/Área Urbana - Mossoró/RN</div>
        <div style="color: #666; font-size: 12px;">© Powered by Júlio Aguiar - Todos os direitos reservados</div>
    </div>
    """, unsafe_allow_html=True)
    
    # JavaScript para modal de detalhes
    st.markdown("""
    <script>
    function showVehicleDetails(vehicleId) {
        alert('Detalhes do veículo ID: ' + vehicleId + '\\n\\nEsta funcionalidade será implementada em breve!');
    }
    
    // Fallback para imagens que não carregam
    document.addEventListener('DOMContentLoaded', function() {
        const images = document.querySelectorAll('.vehicle-image');
        images.forEach(img => {
            img.onerror = function() {
                const altText = this.alt || 'Veículo';
                const marcaModelo = altText.split(' ').slice(0, 2).join('+');
                const cor = '3498db';
                this.src = `https://via.placeholder.com/400x250/${cor}/ffffff?text=${marcaModelo}`;
            };
        });
    });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
