import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from PIL import Image
import io

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="Vitrine de Veículos - Canal Automotivo",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================
# CSS PREMIUM - MESMO ESTILO DA APLICAÇÃO PRINCIPAL
# =============================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    .header-premium {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0 2rem 0;
        position: relative;
    }
    
    .header-premium::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #e88e1b, #f4c220, #ffca02);
    }
    
    .car-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .car-card:hover {
        transform: translateY(-5px);
        border-color: rgba(232, 142, 27, 0.3);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .price-tag {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .feature-badge {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .contact-floating {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 1rem 2rem;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 5px 20px rgba(232, 142, 27, 0.4);
        z-index: 1000;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .contact-floating:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 25px rgba(232, 142, 27, 0.6);
    }
    
    .filter-sidebar {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .comparison-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #e88e1b;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# BANCO DE DADOS (SIMPLIFICADO PARA CLIENTES)
# =============================================

class ClientDatabase:
    def __init__(self):
        # Reutiliza a conexão do banco principal
        from app import db
        self.db = db
    
    def get_veiculos_estoque(self):
        """Busca apenas veículos em estoque para clientes"""
        try:
            veiculos = self.db.get_veiculos()
            return [v for v in veiculos if v.get('status') == 'Em estoque']
        except:
            return []
    
    def registrar_interesse(self, nome, telefone, email, veiculo_id, mensagem):
        """Registra interesse de cliente em um veículo"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO contatos (nome, telefone, email, tipo, veiculo_interesse, data_contato, observacoes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (nome, telefone, email, 'Lead Cliente', f"Veículo ID: {veiculo_id}", datetime.now().date(), mensagem, 'Novo'))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False

# =============================================
# COMPONENTES REUTILIZÁVEIS
# =============================================

def car_card(veiculo, expanded_view=False):
    """Componente de card de veículo"""
    
    # Calcular características
    ano_atual = datetime.now().year
    idade = ano_atual - veiculo['ano']
    
    # Foto placeholder (você pode implementar fotos reais depois)
    foto_url = "https://via.placeholder.com/300x200/2d2d2d/ffffff?text=Foto+do+Veículo"
    
    if expanded_view:
        # Vista expandida (detalhes completos)
        st.markdown(f"""
        <div class="car-card">
            <div style="display: grid; grid-template-columns: 300px 1fr; gap: 2rem; align-items: start;">
                <div>
                    <img src="{foto_url}" style="width: 100%; border-radius: 12px;">
                    <div class="price-tag" style="margin-top: 1rem; text-align: center;">
                        R$ {veiculo['preco_venda']:,.2f}
                    </div>
                </div>
                <div>
                    <h2 style="margin: 0 0 0.5rem 0; color: white;">{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}</h2>
                    <div style="color: #a0a0a0; margin-bottom: 1.5rem;">
                        <span>📅 {idade} ano(s) • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}</span>
                    </div>
                    
                    <div style="margin-bottom: 1.5rem;">
                        <span class="feature-badge">⚙️ {veiculo['cambio']}</span>
                        <span class="feature-badge">⛽ {veiculo['combustivel']}</span>
                        <span class="feature-badge">🚪 {veiculo['portas']} portas</span>
                        <span class="feature-badge">🏷️ {veiculo['placa'] or 'Placa não informada'}</span>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <h4 style="margin: 0 0 0.5rem 0;">📋 Descrição</h4>
                        <p style="margin: 0; color: #a0a0a0;">{veiculo['observacoes'] or 'Veículo em excelente estado de conservação. Todas as revisões em dia.'}</p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <button onclick="document.getElementById('form-{veiculo['id']}').scrollIntoView()" style="background: linear-gradient(135deg, #e88e1b, #f4c220); border: none; border-radius: 8px; padding: 12px; color: white; font-weight: bold; cursor: pointer;">
                            📞 Tenho Interesse
                        </button>
                        <button onclick="window.open('https://wa.me/5599999999999?text=Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}', '_blank')" style="background: #25D366; border: none; border-radius: 8px; padding: 12px; color: white; font-weight: bold; cursor: pointer;">
                            💬 WhatsApp
                        </button>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Vista compacta (lista)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(foto_url, use_column_width=True)
        with col2:
            st.markdown(f"""
            <div style="padding: 1rem;">
                <h3 style="margin: 0 0 0.5rem 0; color: white;">{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}</h3>
                <div style="color: #a0a0a0; margin-bottom: 1rem;">
                    <span>📅 {idade} ano(s) • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}</span>
                </div>
                <div style="margin-bottom: 1rem;">
                    <span class="feature-badge">⚙️ {veiculo['cambio']}</span>
                    <span class="feature-badge">⛽ {veiculo['combustivel']}</span>
                </div>
                <div class="price-tag" style="display: inline-block;">
                    R$ {veiculo['preco_venda']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

def simulador_financiamento(veiculo_preco):
    """Simulador de financiamento"""
    st.markdown("#### 💰 Simulador de Financiamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entrada = st.number_input(
            "Valor de Entrada (R$)", 
            min_value=0.0, 
            value=veiculo_preco * 0.2,
            max_value=veiculo_preco,
            step=1000.0
        )
        parcelas = st.slider("Número de Parcelas", 12, 84, 48)
    
    with col2:
        taxa_anual = st.slider("Taxa de Juros (% ao ano)", 1.0, 30.0, 12.0)
        seguro = st.number_input("Seguro (R$/mês)", min_value=0.0, value=200.0)
    
    # Cálculo das parcelas
    valor_financiado = veiculo_preco - entrada
    taxa_mensal = (1 + taxa_anual/100) ** (1/12) - 1
    
    if valor_financiado > 0 and taxa_mensal > 0:
        parcela = valor_financiado * (taxa_mensal * (1 + taxa_mensal) ** parcelas) / ((1 + taxa_mensal) ** parcelas - 1)
        parcela_total = parcela + seguro
        
        # Resultado
        st.markdown(f"""
        <div style="background: rgba(39, 174, 96, 0.1); padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h4 style="margin: 0 0 1rem 0; color: #27AE60;">📋 Resultado da Simulação</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <p><strong>Valor Financiado:</strong><br>R$ {valor_financiado:,.2f}</p>
                    <p><strong>Parcela do Veículo:</strong><br>R$ {parcela:,.2f}</p>
                </div>
                <div>
                    <p><strong>Parcela Total (c/ seguro):</strong><br>R$ {parcela_total:,.2f}</p>
                    <p><strong>Total a Pagar:</strong><br>R$ {entrada + (parcela_total * parcelas):,.2f}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💰 Financiamento não necessário para este valor.")

def comparador_veiculos(veiculos_selecionados):
    """Comparador de veículos"""
    if len(veiculos_selecionados) < 2:
        return
    
    st.markdown("#### ⚖️ Comparação entre Veículos")
    
    # Criar dados para comparação
    dados_comparacao = []
    for veiculo in veiculos_selecionados:
        idade = datetime.now().year - veiculo['ano']
        dados_comparacao.append({
            'Veículo': f"{veiculo['marca']} {veiculo['modelo']}",
            'Preço': f"R$ {veiculo['preco_venda']:,.2f}",
            'Ano': veiculo['ano'],
            'Idade': f"{idade} ano(s)",
            'KM': f"{veiculo['km']:,}",
            'Combustível': veiculo['combustivel'],
            'Câmbio': veiculo['cambio'],
            'Portas': veiculo['portas'],
            'Cor': veiculo['cor']
        })
    
    # Mostrar tabela comparativa
    df_comparacao = pd.DataFrame(dados_comparacao)
    st.dataframe(df_comparacao, use_container_width=True)
    
    # Gráfico comparativo de preços
    fig = px.bar(
        df_comparacao, 
        x='Veículo', 
        y='Preço',
        title="Comparação de Preços",
        color='Veículo',
        color_discrete_sequence=['#e88e1b', '#3498db', '#27AE60']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# PÁGINA PRINCIPAL - VITRINE
# =============================================

def main():
    # Header Premium
    col_logo, col_title = st.columns([1, 3])
    
    with col_logo:
        st.markdown("""
        <div style="text-align: center;">
            <div style="font-size: 3rem;">🏁</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_title:
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="margin:0; font-size: 2.5rem; background: linear-gradient(135deg, #ffffff, #e0e0e0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800;">
                Canal Automotivo
            </h1>
            <p style="margin:0; color: #a0a0a0; font-size: 1.2rem;">Encontre o carro dos seus sonhos</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Inicializar banco
    client_db = ClientDatabase()
    
    # Buscar veículos
    veiculos = client_db.get_veiculos_estoque()
    
    # Sidebar de Filtros
    st.sidebar.markdown("### 🔍 Filtros")
    
    # Filtro por marca
    marcas = list(set([v['marca'] for v in veiculos]))
    marca_selecionada = st.sidebar.selectbox("Marca", ["Todas"] + sorted(marcas))
    
    # Filtro por preço
    preco_min, preco_max = st.sidebar.slider(
        "Faixa de Preço (R$)",
        min_value=0,
        max_value=500000,
        value=(0, 200000),
        step=10000
    )
    
    # Filtro por ano
    anos = sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
    ano_min, ano_max = st.sidebar.select_slider(
        "Ano do Veículo",
        options=anos,
        value=(min(anos), max(anos))
    )
    
    # Filtro por combustível
    combustiveis = list(set([v['combustivel'] for v in veiculos]))
    combustivel_selecionado = st.sidebar.multiselect("Combustível", combustiveis, default=combustiveis)
    
    # NOVO: Sistema de Comparação na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚖️ Comparador")
    
    veiculos_options = [f"{v['id']} - {v['marca']} {v['modelo']} {v['ano']}" for v in veiculos]
    veiculos_comparar = st.sidebar.multiselect(
        "Selecione veículos para comparar (máx 3)",
        veiculos_options,
        max_selections=3
    )
    
    # Aplicar filtros
    veiculos_filtrados = veiculos.copy()
    
    if marca_selecionada != "Todas":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == marca_selecionada]
    
    veiculos_filtrados = [v for v in veiculos_filtrados if preco_min <= v['preco_venda'] <= preco_max]
    veiculos_filtrados = [v for v in veiculos_filtrados if ano_min <= v['ano'] <= ano_max]
    
    if combustivel_selecionado:
        veiculos_filtrados = [v for v in veiculos_filtrados if v['combustivel'] in combustivel_selecionado]
    
    # Métricas
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    
    with col_met1:
        st.metric("🚗 Veículos", len(veiculos_filtrados))
    with col_met2:
        if veiculos_filtrados:
            preco_medio = sum(v['preco_venda'] for v in veiculos_filtrados) / len(veiculos_filtrados)
            st.metric("💰 Preço Médio", f"R$ {preco_medio:,.0f}")
    with col_met3:
        if veiculos_filtrados:
            ano_medio = sum(v['ano'] for v in veiculos_filtrados) / len(veiculos_filtrados)
            st.metric("📅 Ano Médio", f"{ano_medio:.0f}")
    with col_met4:
        st.metric("⭐ Destaques", f"{len([v for v in veiculos_filtrados if v['ano'] >= datetime.now().year - 2])}")
    
    # Modo de visualização
    col_view1, col_view2, col_view3 = st.columns([2, 1, 1])
    
    with col_view1:
        st.markdown(f"### 🏁 Veículos Encontrados ({len(veiculos_filtrados)})")
    
    with col_view2:
        view_mode = st.selectbox("Visualização", ["Cards", "Lista"])
    
    with col_view3:
        sort_by = st.selectbox("Ordenar por", ["Preço: Menor-Maior", "Preço: Maior-Menor", "Ano: Mais Novo", "Ano: Mais Antigo", "KM: Menor"])
    
    # Ordenar veículos
    if sort_by == "Preço: Menor-Maior":
        veiculos_filtrados.sort(key=lambda x: x['preco_venda'])
    elif sort_by == "Preço: Maior-Menor":
        veiculos_filtrados.sort(key=lambda x: x['preco_venda'], reverse=True)
    elif sort_by == "Ano: Mais Novo":
        veiculos_filtrados.sort(key=lambda x: x['ano'], reverse=True)
    elif sort_by == "Ano: Mais Antigo":
        veiculos_filtrados.sort(key=lambda x: x['ano'])
    elif sort_by == "KM: Menor":
        veiculos_filtrados.sort(key=lambda x: x['km'])
    
    # Exibir veículos
    if not veiculos_filtrados:
        st.info("🔍 Nenhum veículo encontrado com os filtros selecionados.")
        return
    
    # Sistema de abas para navegação - AGORA COM MAIS ABAS
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Lista de Veículos", "💰 Simulador", "⚖️ Comparar", "📊 Análises", "🏆 Destaques"])
    
    with tab1:
        if view_mode == "Cards":
            # Visualização em grid de cards
            cols = st.columns(3)
            for i, veiculo in enumerate(veiculos_filtrados):
                with cols[i % 3]:
                    with st.container():
                        car_card(veiculo, expanded_view=False)
                        
                        # Botão para ver detalhes
                        if st.button("Ver Detalhes", key=f"btn_{veiculo['id']}", use_container_width=True):
                            st.session_state[f"selected_car_{veiculo['id']}"] = True
                        
                        # Mostrar detalhes expandidos se selecionado
                        if st.session_state.get(f"selected_car_{veiculo['id']}"):
                            car_card(veiculo, expanded_view=True)
                            
                            # NOVO: Simulador para este veículo
                            simulador_financiamento(veiculo['preco_venda'])
                            
                            # Formulário de interesse
                            with st.form(f"interesse_form_{veiculo['id']}"):
                                st.markdown("### 📞 Tenho Interesse")
                                col_form1, col_form2 = st.columns(2)
                                
                                with col_form1:
                                    nome = st.text_input("Seu Nome*", key=f"nome_{veiculo['id']}")
                                    telefone = st.text_input("Telefone*", key=f"tel_{veiculo['id']}")
                                
                                with col_form2:
                                    email = st.text_input("Email", key=f"email_{veiculo['id']}")
                                    preferencia_contato = st.selectbox(
                                        "Melhor horário", 
                                        ["Qualquer horário", "Manhã", "Tarde", "Noite"],
                                        key=f"horario_{veiculo['id']}"
                                    )
                                
                                mensagem = st.text_area(
                                    "Mensagem (opcional)",
                                    value=f"Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}",
                                    key=f"msg_{veiculo['id']}"
                                )
                                
                                if st.form_submit_button("Enviar Interesse", use_container_width=True):
                                    if nome and telefone:
                                        success = client_db.registrar_interesse(
                                            nome, telefone, email, veiculo['id'], mensagem
                                        )
                                        if success:
                                            st.success("✅ Interesse registrado! Entraremos em contato em breve.")
                                        else:
                                            st.error("❌ Erro ao registrar interesse.")
                                    else:
                                        st.error("⚠️ Preencha pelo menos nome e telefone.")
        else:
            # Visualização em lista
            for veiculo in veiculos_filtrados:
                car_card(veiculo, expanded_view=True)
                st.markdown("---")
    
    with tab2:
        st.markdown("### 💰 Simulador de Financiamento")
        st.info("Use este simulador para planejar a compra do seu veículo")
        
        valor_veiculo = st.number_input(
            "Valor do Veículo (R$)",
            min_value=1000.0,
            max_value=500000.0,
            value=50000.0,
            step=1000.0
        )
        
        simulador_financiamento(valor_veiculo)
    
    with tab3:
        # Comparador de veículos
        if veiculos_comparar:
            # Converter IDs selecionados para objetos veículo
            veiculos_para_comparar = []
            for v_str in veiculos_comparar:
                veiculo_id = int(v_str.split(" - ")[0])
                veiculo = next((v for v in veiculos if v['id'] == veiculo_id), None)
                if veiculo:
                    veiculos_para_comparar.append(veiculo)
            
            comparador_veiculos(veiculos_para_comparar)
        else:
            st.info("👆 Selecione veículos na sidebar para comparar")
    
    with tab4:
        st.markdown("### 📊 Análise do Estoque")
        
        if veiculos_filtrados:
            # Gráfico de preços por marca
            df = pd.DataFrame(veiculos_filtrados)
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                fig = px.box(df, x='marca', y='preco_venda', title="Distribuição de Preços por Marca")
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col_graf2:
                # Contagem por combustível
                combustivel_count = df['combustivel'].value_counts()
                fig = px.pie(values=combustivel_count.values, names=combustivel_count.index, title="Distribuição por Combustível")
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabela comparativa
            st.markdown("### 📋 Comparativo entre Marcas")
            stats_df = df.groupby('marca').agg({
                'preco_venda': ['count', 'mean', 'min', 'max'],
                'ano': 'mean',
                'km': 'mean'
            }).round(2)
            
            st.dataframe(stats_df, use_container_width=True)
    
    with tab5:
        st.markdown("### 🏆 Veículos em Destaque")
        
        # Veículos mais novos
        novos = sorted(veiculos_filtrados, key=lambda x: x['ano'], reverse=True)[:3]
        st.markdown("#### 🆕 Mais Novos")
        cols = st.columns(3)
        for i, veiculo in enumerate(novos):
            with cols[i]:
                car_card(veiculo, expanded_view=False)
        
        # Veículos com menor KM
        st.markdown("#### 🛣️ Menor Quilometragem")
        baixa_km = sorted(veiculos_filtrados, key=lambda x: x['km'])[:3]
        cols = st.columns(3)
        for i, veiculo in enumerate(baixa_km):
            with cols[i]:
                car_card(veiculo, expanded_view=False)
    
    # Botão flutuante de contato
    st.markdown("""
    <div class="contact-floating" onclick="window.open('https://wa.me/5599999999999', '_blank')">
        💬 Fale Conosco
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()