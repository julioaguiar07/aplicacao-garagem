import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import psycopg2
import os
import math

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Garagem Multimarcas - Concessionária Premium",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CSS PREMIUM AVANÇADO
# =============================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header com efeito glassmorphism */
    .main-header {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    /* Cards de veículo - estilo premium */
    .vehicle-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    
    .vehicle-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(232, 142, 27, 0.1), transparent);
        transition: left 0.6s;
    }
    
    .vehicle-card:hover::before {
        left: 100%;
    }
    
    .vehicle-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: rgba(232, 142, 27, 0.4);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }
    
    .vehicle-image {
        width: 100%;
        height: 200px;
        border-radius: 15px;
        object-fit: cover;
        margin-bottom: 1rem;
        border: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    .price-badge {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 25px;
        font-weight: bold;
        font-size: 1.3rem;
        text-align: center;
        box-shadow: 0 5px 15px rgba(232, 142, 27, 0.3);
    }
    
    .feature-chip {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
        transition: all 0.3s ease;
    }
    
    .feature-chip:hover {
        background: rgba(232, 142, 27, 0.2);
        border-color: #e88e1b;
    }
    
    .status-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: linear-gradient(135deg, #27AE60, #2ECC71);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    
    /* Botões premium */
    .btn-premium {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        color: white;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.3rem 0;
    }
    
    .btn-premium:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(232, 142, 27, 0.4);
    }
    
    .btn-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        color: white;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.3rem 0;
    }
    
    .btn-whatsapp:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 211, 102, 0.4);
    }
    
    /* Modal premium */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 2rem;
    }
    
    .modal-content {
        background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
        border-radius: 25px;
        padding: 2rem;
        max-width: 900px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-3px);
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS
# =============================================

class PremiumDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        if self.database_url:
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            return psycopg2.connect(self.database_url, sslmode='require')
        return None
    
    def get_veiculos_estoque(self):
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, modelo, ano, marca, cor, preco_entrada, preco_venda, 
                       fornecedor, km, placa, chassi, combustivel, cambio, 
                       portas, observacoes, data_cadastro, status
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
# COMPONENTES PREMIUM
# =============================================

def generate_car_image(marca, modelo, cor):
    """Gera imagem placeholder personalizada baseada no carro"""
    colors = {
        'Prata': 'C0C0C0', 'Preto': '000000', 'Branco': 'FFFFFF', 
        'Vermelho': 'FF0000', 'Azul': '0000FF', 'Cinza': '808080',
        'Verde': '008000', 'Laranja': 'FFA500'
    }
    color_hex = colors.get(cor, '2d2d2d')
    
    return f"https://via.placeholder.com/400x250/{color_hex}/ffffff?text={marca}+{modelo}"

def vehicle_mini_card(veiculo):
    """Card mini para catálogo em grid"""
    idade = datetime.now().year - veiculo['ano']
    foto_url = generate_car_image(veiculo['marca'], veiculo['modelo'], veiculo['cor'])
    
    st.markdown(f'''
    <div class="vehicle-card fade-in" onclick="this.querySelector('.btn-premium').click()">
        <div class="status-badge">DISPONÍVEL</div>
        <img src="{foto_url}" class="vehicle-image">
        
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
    
    # Botões invisíveis para controle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Ver Detalhes", key=f"view_{veiculo['id']}", use_container_width=True):
            st.session_state[f"selected_vehicle_{veiculo['id']}"] = True
    with col2:
        whatsapp_msg = f"Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}"
        whatsapp_url = f"https://wa.me/5584999999999?text={whatsapp_msg}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="text-decoration: none;"><button class="btn-whatsapp">💬 WhatsApp</button></a>', unsafe_allow_html=True)
        

def vehicle_detail_modal(veiculo):
    """Modal de detalhes completo"""
    idade = datetime.now().year - veiculo['ano']
    foto_url = generate_car_image(veiculo['marca'], veiculo['modelo'], veiculo['cor'])
    
    st.markdown(f'''
    <div class="modal-overlay">
        <div class="modal-content">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                    <img src="{foto_url}" style="width: 100%; border-radius: 15px; margin-bottom: 1rem;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="price-badge" style="font-size: 1.5rem;">
                            R$ {veiculo['preco_venda']:,.2f}
                        </div>
                        <div style="background: rgba(39, 174, 96, 0.2); color: #27AE60; padding: 0.8rem; border-radius: 15px; text-align: center; font-weight: bold;">
                            📅 {veiculo['ano']}
                        </div>
                    </div>
                </div>
                
                <div>
                    <h2 style="margin: 0 0 1rem 0; color: white; font-size: 2rem;">{veiculo['marca']} {veiculo['modelo']}</h2>
                    
                    <div style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem;">
                        <h4 style="margin: 0 0 1rem 0; color: #e88e1b;">📊 Especificações</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div><strong>🛣️ Quilometragem:</strong><br>{veiculo['km']:,} km</div>
                            <div><strong>🎨 Cor:</strong><br>{veiculo['cor']}</div>
                            <div><strong>⛽ Combustível:</strong><br>{veiculo['combustivel']}</div>
                            <div><strong>⚙️ Câmbio:</strong><br>{veiculo['cambio']}</div>
                            <div><strong>🚪 Portas:</strong><br>{veiculo['portas']}</div>
                            <div><strong>🏷️ Placa:</strong><br>{veiculo['placa'] or 'Não informada'}</div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem;">
                        <h4 style="margin: 0 0 1rem 0; color: #e88e1b;">📋 Descrição</h4>
                        <p style="margin: 0; color: #a0a0a0; line-height: 1.6;">{veiculo['observacoes'] or 'Veículo em excelente estado de conservação, com toda documentação em dia e pronto para negociação.'}</p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <button class="btn-whatsapp" onclick="window.open('https://wa.me/5584999999999?text=Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}', '_blank')">
                            💬 Falar no WhatsApp
                        </button>
                        <button class="btn-premium" onclick="document.getElementById('simulador-{veiculo['id']}').scrollIntoView()">
                            💰 Simular Financiamento
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def financiamento_simulator(veiculo):
    """Simulador de financiamento avançado"""
    st.markdown("---")
    st.markdown("#### 🏦 Simulador de Financiamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Condições")
        valor_veiculo = veiculo['preco_venda']
        entrada = st.slider("Entrada (R$)", 0, int(valor_veiculo), int(valor_veiculo * 0.2), 1000)
        parcelas = st.slider("Parcelas", 12, 84, 48)
        taxa_anual = st.slider("Taxa de juros (% ao ano)", 1.0, 30.0, 12.0)
    
    with col2:
        st.subheader("📈 Custo Mensal")
        seguro = st.number_input("Seguro (R$/mês)", 100, 500, 200)
        manutencao = st.number_input("Manutenção (R$/mês)", 50, 300, 100)
        
        # Cálculo das parcelas
        valor_financiado = valor_veiculo - entrada
        taxa_mensal = (1 + taxa_anual/100) ** (1/12) - 1
        
        if valor_financiado > 0:
            parcela_veiculo = valor_financiado * (taxa_mensal * (1 + taxa_mensal) ** parcelas) / ((1 + taxa_mensal) ** parcelas - 1)
            parcela_total = parcela_veiculo + seguro + manutencao
            
            # Resultado
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(39, 174, 96, 0.1), rgba(46, 204, 113, 0.1)); padding: 1.5rem; border-radius: 15px; border: 1px solid rgba(39, 174, 96, 0.3);">
                <h4 style="margin: 0 0 1rem 0; color: #27AE60;">💡 Projeção do Financiamento</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <p><strong>Parcela do veículo:</strong><br>R$ {parcela_veiculo:,.2f}</p>
                        <p><strong>Total com custos:</strong><br>R$ {parcela_total:,.2f}</p>
                    </div>
                    <div>
                        <p><strong>Total financiado:</strong><br>R$ {valor_financiado:,.2f}</p>
                        <p><strong>Total a pagar:</strong><br>R$ {entrada + (parcela_total * parcelas):,.2f}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def comparador_veiculos(veiculos_selecionados):
    """Comparador visual de veículos"""
    if len(veiculos_selecionados) < 2:
        return
    
    st.markdown("#### ⚖️ Comparador de Veículos")
    
    # Criar dados para comparação
    comparacao_data = []
    for veiculo in veiculos_selecionados:
        idade = datetime.now().year - veiculo['ano']
        comparacao_data.append({
            'Veículo': f"{veiculo['marca']} {veiculo['modelo']}",
            'Preço (R$)': veiculo['preco_venda'],
            'Ano': veiculo['ano'],
            'Idade (anos)': idade,
            'KM': veiculo['km'],
            'Combustível': veiculo['combustivel'],
            'Câmbio': veiculo['cambio']
        })
    
    # Gráfico comparativo
    fig = go.Figure()
    
    for i, veiculo in enumerate(comparacao_data):
        fig.add_trace(go.Bar(
            name=veiculo['Veículo'],
            x=['Preço', 'Ano', 'KM'],
            y=[veiculo['Preço (R$)']/1000, veiculo['Ano'], veiculo['KM']/1000],
            text=[f"R$ {veiculo['Preço (R$)']:,.0f}", f"{veiculo['Ano']}", f"{veiculo['KM']:,} km"],
            textposition='auto',
        ))
    
    fig.update_layout(
        title="Comparação entre Veículos",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=True,
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header Premium
    st.markdown("""
    <div class="main-header">
        <div style="text-align: center;">
            <h1 style="margin:0; font-size: 3.5rem; background: linear-gradient(135deg, #e88e1b, #f4c220, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 900;">
                🏎️ GARAGEM MULTIMARCAS
            </h1>
            <p style="margin:0; color: #a0a0a0; font-size: 1.4rem; font-weight: 300;">Concessionária Premium • Veículos Selecionados</p>
            <p style="margin:1rem 0 0 0; color: #666; font-size: 1.1rem;">
                📞 (84) 99999-9999 • 📍 Av. Principal, 123 • ⏰ Seg-Sex: 8h-18h
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar banco
    db = PremiumDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Sidebar Premium
    st.sidebar.markdown("### 🔍 Filtros Avançados")
    
    # Filtros
    marcas = list(set([v['marca'] for v in veiculos]))
    marca_selecionada = st.sidebar.selectbox("Marca", ["Todas as marcas"] + sorted(marcas))
    
    if veiculos:
        preco_max = max(v['preco_venda'] for v in veiculos)
        preco_range = st.sidebar.slider("Faixa de Preço (R$)", 0, int(preco_max * 1.1), 
                                      (0, int(preco_max)), 5000)
    
    anos = sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Ano", ["Todos os anos"] + anos)
    
    combustiveis = list(set([v['combustivel'] for v in veiculos]))
    combustivel_selecionado = st.sidebar.multiselect("Combustível", combustiveis, default=combustiveis)
    
    # Sistema de comparação
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚖️ Comparador")
    veiculos_comparar = st.sidebar.multiselect(
        "Selecione para comparar",
        [f"{v['marca']} {v['modelo']} {v['ano']}" for v in veiculos],
        max_selections=3
    )
    
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
    
    # Métricas em tempo real
    st.markdown("### 📊 Painel do Estoque")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_veiculos = len(veiculos_filtrados)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚗</div>
            <h3 style="margin: 0; color: white;">{total_veiculos}</h3>
            <p style="margin: 0; color: #a0a0a0;">Veículos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if veiculos_filtrados:
            preco_medio = sum(v['preco_venda'] for v in veiculos_filtrados) / len(veiculos_filtrados)
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💰</div>
                <h3 style="margin: 0; color: white;">R$ {preco_medio:,.0f}</h3>
                <p style="margin: 0; color: #a0a0a0;">Preço Médio</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if veiculos_filtrados:
            ano_medio = sum(v['ano'] for v in veiculos_filtrados) / len(veiculos_filtrados)
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📅</div>
                <h3 style="margin: 0; color: white;">{ano_medio:.0f}</h3>
                <p style="margin: 0; color: #a0a0a0;">Ano Médio</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        novos = len([v for v in veiculos_filtrados if v['ano'] >= datetime.now().year - 2])
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⭐</div>
            <h3 style="margin: 0; color: white;">{novos}</h3>
            <p style="margin: 0; color: #a0a0a0;">Semi-novos</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sistema de abas
    tab1, tab2, tab3, tab4 = st.tabs(["🏁 Catálogo", "📊 Análises", "⚖️ Comparar", "🏆 Destaques"])
    
    with tab1:
        # Controles de visualização
        col_view1, col_view2 = st.columns([3, 1])
        with col_view1:
            st.markdown(f"### 🎯 Veículos Selecionados ({len(veiculos_filtrados)})")
        with col_view2:
            ordenacao = st.selectbox("Ordenar por", 
                                   ["Mais Recentes", "Preço: Crescente", "Preço: Decrescente", "Ano: Mais Novo", "KM: Menor"])
        
        # Aplicar ordenação
        if ordenacao == "Preço: Crescente":
            veiculos_filtrados.sort(key=lambda x: x['preco_venda'])
        elif ordenacao == "Preço: Decrescente":
            veiculos_filtrados.sort(key=lambda x: x['preco_venda'], reverse=True)
        elif ordenacao == "Ano: Mais Novo":
            veiculos_filtrados.sort(key=lambda x: x['ano'], reverse=True)
        elif ordenacao == "KM: Menor":
            veiculos_filtrados.sort(key=lambda x: x['km'])
        else:
            veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
        
        # Grid de veículos
        if not veiculos_filtrados:
            st.info("""
            ## 🔍 Nenhum veículo encontrado
            *Tente ajustar os filtros para encontrar mais opções em nosso estoque.*
            """)
        else:
            # Layout responsivo em grid
            cols = st.columns(3)
            for i, veiculo in enumerate(veiculos_filtrados):
                with cols[i % 3]:
                    vehicle_mini_card(veiculo)
                    
                    # Modal de detalhes
                    if st.session_state.get(f"selected_vehicle_{veiculo['id']}"):
                        vehicle_detail_modal(veiculo)
                        financiamento_simulator(veiculo)
                        
                        # Botão para fechar modal
                        if st.button("✕ Fechar Detalhes", key=f"close_{veiculo['id']}", use_container_width=True):
                            st.session_state[f"selected_vehicle_{veiculo['id']}"] = False
                            st.rerun()
    
    with tab2:
        if veiculos_filtrados:
            st.markdown("### 📈 Análises do Estoque")
            
            df = pd.DataFrame(veiculos_filtrados)
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                # Distribuição por marca
                marca_count = df['marca'].value_counts()
                fig1 = px.pie(marca_count, values=marca_count.values, names=marca_count.index, 
                             title="Distribuição por Marca", hole=0.4)
                fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_graf2:
                # Preço vs Ano
                fig2 = px.scatter(df, x='ano', y='preco_venda', color='marca', size='km',
                                title="Relação Preço vs Ano", hover_data=['modelo'])
                fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        if veiculos_comparar:
            veiculos_para_comparar = []
            for v_str in veiculos_comparar:
                for v in veiculos:
                    if f"{v['marca']} {v['modelo']} {v['ano']}" == v_str:
                        veiculos_para_comparar.append(v)
                        break
            
            comparador_veiculos(veiculos_para_comparar)
        else:
            st.info("👆 Selecione veículos na sidebar para comparar")
    
    with tab4:
        st.markdown("### 🏆 Veículos em Destaque")
        
        if veiculos_filtrados:
            # Mais novos
            st.markdown("#### 🆕 Lançamentos Recentes")
            novos = sorted(veiculos_filtrados, key=lambda x: x['ano'], reverse=True)[:3]
            cols = st.columns(3)
            for i, veiculo in enumerate(novos):
                with cols[i]:
                    vehicle_mini_card(veiculo)
            
            # Menor KM
            st.markdown("#### 🛣️ Baixa Quilometragem")
            baixa_km = sorted(veiculos_filtrados, key=lambda x: x['km'])[:3]
            cols = st.columns(3)
            for i, veiculo in enumerate(baixa_km):
                with cols[i]:
                    vehicle_mini_card(veiculo)
    
    # Footer Premium
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 3rem 1rem;">
        <h3 style="color: #e88e1b; margin-bottom: 1rem;">🏎️ Garagem Multimarcas</h3>
        <p style="margin: 0.5rem 0;">📞 (84) 99999-9999 | 📍 Av. Principal, 123 - Mossoró/RN</p>
        <p style="margin: 0.5rem 0;">⏰ Segunda a Sexta: 8h-18h | Sábado: 8h-12h</p>
        <p style="margin: 1rem 0; font-size: 0.9rem; color: #888;">
            Concessionária autorizada • Todos os veículos com garantia • Financiamento facilitado
        </p>
        <p style="font-size: 0.8rem; color: #555;">© 2024 Garagem Multimarcas - Todos os direitos reservados</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
