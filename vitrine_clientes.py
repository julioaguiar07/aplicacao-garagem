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

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Veículos em Mossoró",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CSS PREMIUM PROFISSIONAL
# =============================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header profissional */
    .main-header {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    /* Cards de veículo - estilo concessionária */
    .vehicle-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    
    .vehicle-card:hover {
        transform: translateY(-5px);
        border-color: rgba(232, 142, 27, 0.4);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
    }
    
    .vehicle-image {
        width: 100%;
        height: 180px;
        border-radius: 12px;
        object-fit: cover;
        margin-bottom: 1rem;
        border: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    .price-badge {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
        margin-top: 1rem;
    }
    
    .feature-chip {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .status-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: linear-gradient(135deg, #27AE60, #2ECC71);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    
    /* Botões profissionais */
    .btn-primary {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        color: white;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.3rem 0;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(232, 142, 27, 0.4);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        color: white;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.3rem 0;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    
    .btn-whatsapp:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
    }
    
    /* Filtros sidebar */
    .sidebar-filter {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS
# =============================================

class VitrineDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        if self.database_url:
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            return psycopg2.connect(self.database_url, sslmode='require')
        return None
    
    def get_veiculos_estoque(self):
        """Busca veículos em estoque com fotos"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, modelo, ano, marca, cor, preco_venda, 
                       km, placa, combustivel, cambio, portas, observacoes,
                       data_cadastro, foto
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
    
    def registrar_interesse(self, nome, telefone, email, veiculo_id, mensagem):
        """Registra interesse do cliente"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contatos (nome, telefone, email, tipo, veiculo_interesse, data_contato, observacoes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (nome, telefone, email, 'Lead Cliente', f"Veículo ID: {veiculo_id}", datetime.now().date(), mensagem, 'Novo'))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao registrar interesse: {e}")
            return False
        finally:
            conn.close()

# =============================================
# COMPONENTES
# =============================================

def bytes_to_base64(image_bytes):
    """Converte bytes da imagem para base64"""
    if image_bytes:
        return base64.b64encode(image_bytes).decode()
    return None

def get_vehicle_image(veiculo):
    """Obtém a imagem do veículo (foto real ou placeholder)"""
    if veiculo.get('foto'):
        # Usa foto real do banco
        image_base64 = bytes_to_base64(veiculo['foto'])
        if image_base64:
            return f"data:image/jpeg;base64,{image_base64}"
    
    # Placeholder personalizado baseado na cor
    colors = {
        'Prata': 'C0C0C0', 'Preto': '000000', 'Branco': 'FFFFFF', 
        'Vermelho': 'FF0000', 'Azul': '0000FF', 'Cinza': '808080',
        'Verde': '008000', 'Laranja': 'FFA500'
    }
    color_hex = colors.get(veiculo['cor'], '2d2d2d')
    
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={veiculo['marca']}+{veiculo['modelo']}"

def vehicle_card(veiculo, index):
    """Card individual do veículo"""
    foto_url = get_vehicle_image(veiculo)
    
    st.markdown(f'''
    <div class="vehicle-card">
        <div class="status-badge">DISPONÍVEL</div>
        <img src="{foto_url}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}">
        
        <h4 style="margin: 0.5rem 0; color: white; font-size: 1.1rem;">{veiculo['marca']} {veiculo['modelo']}</h4>
        <p style="margin: 0.3rem 0; color: #a0a0a0; font-size: 0.9rem;">{veiculo['ano']} • {veiculo['km']:,} km</p>
        
        <div style="margin: 0.8rem 0;">
            <span class="feature-chip">⚙️ {veiculo['cambio']}</span>
            <span class="feature-chip">⛽ {veiculo['combustivel']}</span>
        </div>
        
        <div class="price-badge">
            R$ {veiculo['preco_venda']:,.2f}
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Ver Detalhes", key=f"view_{veiculo['id']}_{index}", use_container_width=True):
            st.session_state[f"selected_vehicle_{veiculo['id']}"] = True
    
    with col2:
        whatsapp_msg = f"Olá! Gostaria de mais informações sobre o {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}"
        whatsapp_url = f"https://wa.me/5584981885353?text={whatsapp_msg}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="btn-whatsapp">💬 WhatsApp</a>', unsafe_allow_html=True)

def vehicle_detail_view(veiculo):
    """Visualização detalhada do veículo"""
    foto_url = get_vehicle_image(veiculo)
    
    st.markdown("---")
    st.markdown(f"## 🚗 {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image(foto_url, use_column_width=True)
        
        # Preço em destaque
        st.markdown(f'''
        <div style="text-align: center; margin: 1rem 0;">
            <div class="price-badge" style="font-size: 1.5rem; display: inline-block;">
                R$ {veiculo['preco_venda']:,.2f}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Botões de ação
        whatsapp_msg = f"Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}"
        whatsapp_url = f"https://wa.me/5584981885353?text={whatsapp_msg}"
        
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="btn-whatsapp" style="margin-bottom: 0.5rem;">💬 Falar no WhatsApp</a>', unsafe_allow_html=True)
        
        if st.button("⬅️ Voltar para a lista", key=f"back_{veiculo['id']}", use_container_width=True):
            st.session_state[f"selected_vehicle_{veiculo['id']}"] = False
            st.rerun()
    
    with col2:
        st.markdown("### 📋 Especificações")
        
        # Características principais
        col_spec1, col_spec2 = st.columns(2)
        with col_spec1:
            st.metric("🎨 Cor", veiculo['cor'])
            st.metric("⛽ Combustível", veiculo['combustivel'])
            st.metric("🛣️ Quilometragem", f"{veiculo['km']:,} km")
        
        with col_spec2:
            st.metric("⚙️ Câmbio", veiculo['cambio'])
            st.metric("🚪 Portas", veiculo['portas'])
            st.metric("🏷️ Placa", veiculo['placa'] or "Não informada")
        
        # Descrição
        if veiculo['observacoes']:
            st.markdown("### 📝 Descrição")
            st.info(veiculo['observacoes'])
        
        # Simulador simples
        st.markdown("### 💰 Simular Parcelas")
        col_sim1, col_sim2 = st.columns(2)
        
        with col_sim1:
            entrada = st.number_input("Entrada (R$)", min_value=0, value=int(veiculo['preco_venda'] * 0.2), step=1000, key=f"entrada_{veiculo['id']}")
            parcelas = st.selectbox("Parcelas", [12, 24, 36, 48, 60], key=f"parcelas_{veiculo['id']}")
        
        with col_sim2:
            valor_financiado = veiculo['preco_venda'] - entrada
            if parcelas > 0:
                parcela = valor_financiado / parcelas
                st.metric("Valor da Parcela", f"R$ {parcela:,.2f}")
                st.metric("Total Financiado", f"R$ {valor_financiado:,.2f}")

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header profissional com logo
    st.markdown("""
    <div class="main-header">
        <div style="text-align: center;">
            <h1 style="margin:0; font-size: 2.8rem; background: linear-gradient(135deg, #e88e1b, #f4c220); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800;">
                GARAGEM MULTIMARCAS
            </h1>
            <p style="margin:0; color: #a0a0a0; font-size: 1.2rem; font-weight: 300;">Sua concessionária de confiança em Mossoró</p>
            <p style="margin:1rem 0 0 0; color: #666; font-size: 1rem;">
                📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Segunda a Sexta: 8h-18h
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar banco
    db = VitrineDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Sidebar de filtros
    st.sidebar.markdown("### 🔍 Buscar Veículos")
    
    with st.sidebar:
        with st.container():
            st.markdown('<div class="sidebar-filter">', unsafe_allow_html=True)
            
            # Filtro por marca
            marcas = list(set([v['marca'] for v in veiculos]))
            marca_selecionada = st.selectbox("Marca", ["Todas as marcas"] + sorted(marcas))
            
            # Filtro por preço
            if veiculos:
                preco_max = max(v['preco_venda'] for v in veiculos)
                preco_range = st.slider("Faixa de Preço (R$)", 0, int(preco_max * 1.1), 
                                      (0, int(preco_max)), 5000)
            
            # Filtro por ano
            anos = sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_selecionado = st.selectbox("Ano", ["Todos os anos"] + anos)
            
            # Filtro por combustível
            combustiveis = list(set([v['combustivel'] for v in veiculos]))
            combustivel_selecionado = st.multiselect("Combustível", combustiveis, default=combustiveis)
            
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
    
    # Verificar se há veículo selecionado para detalhes
    veiculo_detalhe = None
    for veiculo in veiculos_filtrados:
        if st.session_state.get(f"selected_vehicle_{veiculo['id']}"):
            veiculo_detalhe = veiculo
            break
    
    if veiculo_detalhe:
        # Mostrar detalhes do veículo
        vehicle_detail_view(veiculo_detalhe)
    else:
        # Mostrar catálogo
        st.markdown(f"### 🚗 Veículos Disponíveis ({len(veiculos_filtrados)})")
        
        if not veiculos_filtrados:
            st.info("""
            ## 🔍 Nenhum veículo encontrado
            *Tente ajustar os filtros para encontrar o veículo ideal para você!*
            
            **📞 Entre em contato:** (84) 98188-5353
            """)
        else:
            # Ordenação
            col_sort1, col_sort2 = st.columns([3, 1])
            with col_sort2:
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
            cols = st.columns(3)
            for i, veiculo in enumerate(veiculos_filtrados):
                with cols[i % 3]:
                    vehicle_card(veiculo, i)
    
    # Footer profissional
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 1rem;">
        <h4 style="color: #e88e1b; margin-bottom: 1rem;">Garagem Multimarcas</h4>
        <p style="margin: 0.5rem 0;">📞 (84) 98188-5353 | 📍 Mossoró - RN</p>
        <p style="margin: 0.5rem 0;">⏰ Segunda a Sexta: 8h-18h | Sábado: 8h-12h</p>
        <p style="margin: 1rem 0; font-size: 0.9rem; color: #888;">
            Todos os veículos com garantia • Financiamento facilitado • Melhores condições
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
