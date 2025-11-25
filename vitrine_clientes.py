import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import psycopg2
import os

# =============================================
# CONFIGURAÇÃO DA PÁGINA (APENAS UMA VEZ)
# =============================================

st.set_page_config(
    page_title="Canal Automotivo - Vitrine de Veículos",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# BANCO DE DADOS (CONEXÃO DIRETA)
# =============================================

class VitrineDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        """Conecta diretamente ao PostgreSQL"""
        if self.database_url:
            # Corrigir URL se necessário
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            
            conn = psycopg2.connect(self.database_url, sslmode='require')
            return conn
        else:
            st.error("❌ Erro de conexão com o banco de dados")
            return None
    
    def get_veiculos_estoque(self):
        """Busca apenas veículos em estoque"""
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
# CSS PREMIUM
# =============================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    .car-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
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
    
    .contact-whatsapp {
        background: #25D366;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# COMPONENTES
# =============================================

def mostrar_veiculo_card(veiculo):
    """Mostra card individual do veículo"""
    idade = datetime.now().year - veiculo['ano']
    foto_url = "https://via.placeholder.com/400x250/2d2d2d/ffffff?text=Foto+do+Carro"
    
    st.markdown(f"""
    <div class="car-card">
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem; align-items: start;">
            <div>
                <img src="{foto_url}" style="width: 100%; border-radius: 12px;">
                <div class="price-tag" style="margin-top: 1rem; text-align: center;">
                    R$ {veiculo['preco_venda']:,.2f}
                </div>
            </div>
            <div>
                <h2 style="margin: 0 0 0.5rem 0; color: white;">{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}</h2>
                <div style="color: #a0a0a0; margin-bottom: 1rem;">
                    <span>📅 {idade} ano(s) • 🛣️ {veiculo['km']:,} km • 🎨 {veiculo['cor']}</span>
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <span class="feature-badge">⚙️ {veiculo['cambio']}</span>
                    <span class="feature-badge">⛽ {veiculo['combustivel']}</span>
                    <span class="feature-badge">🚪 {veiculo['portas']} portas</span>
                    <span class="feature-badge">🏷️ {veiculo['placa'] or 'Placa não informada'}</span>
                </div>
                
                <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0;">📋 Descrição</h4>
                    <p style="margin: 0; color: #a0a0a0;">{veiculo['observacoes'] or 'Veículo em excelente estado de conservação. Todas as revisões em dia.'}</p>
                </div>
                
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <a href="https://wa.me/5599999999999?text=Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}" 
                       target="_blank" class="contact-whatsapp">
                        💬 WhatsApp
                    </a>
                    <button onclick="document.getElementById('form-{veiculo['id']}').scrollIntoView()" 
                            style="background: linear-gradient(135deg, #e88e1b, #f4c220); border: none; border-radius: 8px; padding: 10px 20px; color: white; font-weight: bold; cursor: pointer;">
                        📞 Tenho Interesse
                    </button>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulário de interesse
    with st.expander("📝 Preencher formulário de interesse"):
        with st.form(f"interesse_form_{veiculo['id']}"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome completo*")
                telefone = st.text_input("Telefone*")
            with col2:
                email = st.text_input("Email")
                preferencia = st.selectbox("Melhor horário para contato", 
                                         ["Qualquer horário", "Manhã", "Tarde", "Noite"])
            
            mensagem = st.text_area("Mensagem (opcional)", 
                                  value=f"Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - R$ {veiculo['preco_venda']:,.2f}")
            
            if st.form_submit_button("📨 Enviar Interesse"):
                if nome and telefone:
                    db = VitrineDatabase()
                    success = db.registrar_interesse(nome, telefone, email, veiculo['id'], mensagem)
                    if success:
                        st.success("✅ Interesse registrado! Entraremos em contato em breve.")
                    else:
                        st.error("❌ Erro ao registrar interesse. Tente novamente.")
                else:
                    st.error("⚠️ Preencha pelo menos nome e telefone.")

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="margin:0; font-size: 3rem; background: linear-gradient(135deg, #e88e1b, #f4c220); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800;">
                🏁 CANAL AUTOMOTIVO
            </h1>
            <p style="margin:0; color: #a0a0a0; font-size: 1.3rem;">Sua concessionária de confiança</p>
            <p style="margin:1rem 0 0 0; color: #666; font-size: 1rem;">
                📞 (84) 99999-9999 • 📍 Av. Principal, 123 - Mossoró/RN
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Inicializar banco e buscar dados
    db = VitrineDatabase()
    veiculos = db.get_veiculos_estoque()
    
    # Sidebar com filtros
    st.sidebar.markdown("### 🔍 Filtros Avançados")
    
    # Filtro por marca
    marcas = list(set([v['marca'] for v in veiculos]))
    marca_selecionada = st.sidebar.selectbox("Marca", ["Todas as marcas"] + sorted(marcas))
    
    # Filtro por preço
    if veiculos:
        preco_max = max(v['preco_venda'] for v in veiculos)
        preco_min, preco_max_slider = st.sidebar.slider(
            "Faixa de Preço (R$)",
            0, int(preco_max * 1.1), (0, int(preco_max)),
            step=5000
        )
    
    # Filtro por ano
    if veiculos:
        anos = sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
        ano_selecionado = st.sidebar.selectbox("Ano", ["Todos os anos"] + anos)
    
    # Filtro por combustível
    combustiveis = list(set([v['combustivel'] for v in veiculos]))
    combustivel_selecionado = st.sidebar.multiselect("Combustível", combustiveis, default=combustiveis)
    
    # Aplicar filtros
    veiculos_filtrados = veiculos.copy()
    
    if marca_selecionada != "Todas as marcas":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == marca_selecionada]
    
    if veiculos:
        veiculos_filtrados = [v for v in veiculos_filtrados if preco_min <= v['preco_venda'] <= preco_max_slider]
    
    if ano_selecionado != "Todos os anos":
        veiculos_filtrados = [v for v in veiculos_filtrados if v['ano'] == ano_selecionado]
    
    if combustivel_selecionado:
        veiculos_filtrados = [v for v in veiculos_filtrados if v['combustivel'] in combustivel_selecionado]
    
    # Métricas
    st.markdown("### 📊 Nosso Estoque")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚗 Veículos", len(veiculos_filtrados))
    with col2:
        if veiculos_filtrados:
            preco_medio = sum(v['preco_venda'] for v in veiculos_filtrados) / len(veiculos_filtrados)
            st.metric("💰 Preço Médio", f"R$ {preco_medio:,.0f}")
    with col3:
        if veiculos_filtrados:
            ano_medio = sum(v['ano'] for v in veiculos_filtrados) / len(veiculos_filtrados)
            st.metric("📅 Ano Médio", f"{ano_medio:.0f}")
    with col4:
        st.metric("⭐ Novidades", f"{len([v for v in veiculos_filtrados if v['ano'] >= datetime.now().year - 1])}")
    
    # Ordenação
    col_sort1, col_sort2 = st.columns([3, 1])
    with col_sort1:
        st.markdown(f"### 🏁 Veículos Disponíveis ({len(veiculos_filtrados)})")
    with col_sort2:
        ordenacao = st.selectbox("Ordenar por", 
                               ["Mais Recentes", "Preço: Menor → Maior", "Preço: Maior → Menor", "Ano: Mais Novo", "KM: Menor"])
    
    # Aplicar ordenação
    if ordenacao == "Preço: Menor → Maior":
        veiculos_filtrados.sort(key=lambda x: x['preco_venda'])
    elif ordenacao == "Preço: Maior → Menor":
        veiculos_filtrados.sort(key=lambda x: x['preco_venda'], reverse=True)
    elif ordenacao == "Ano: Mais Novo":
        veiculos_filtrados.sort(key=lambda x: x['ano'], reverse=True)
    elif ordenacao == "KM: Menor":
        veiculos_filtrados.sort(key=lambda x: x['km'])
    else:  # Mais Recentes
        veiculos_filtrados.sort(key=lambda x: x['data_cadastro'], reverse=True)
    
    # Exibir veículos
    if not veiculos_filtrados:
        st.info("""
        ## 🔍 Nenhum veículo encontrado
        *Tente ajustar os filtros para encontrar mais opções.*
        """)
    else:
        for veiculo in veiculos_filtrados:
            mostrar_veiculo_card(veiculo)
            st.markdown("---")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <h3>🏁 Canal Automotivo</h3>
        <p>📞 (84) 99999-9999 | 📍 Av. Principal, 123 - Mossoró/RN</p>
        <p>⏰ Segunda a Sexta: 8h-18h | Sábado: 8h-12h</p>
        <p style="font-size: 0.8rem;">© 2024 Canal Automotivo - Todos os direitos reservados</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()