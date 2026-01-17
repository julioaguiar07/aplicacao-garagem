import streamlit as st
import psycopg2
import os
import base64

# Configuração da página
st.set_page_config(
    page_title="Garagem Multimarcas - Catálogo",
    page_icon="🚗",
    layout="wide"
)

# Função para conectar ao banco
@st.cache_resource
def get_database_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url, sslmode='require')
    else:
        st.error("❌ DATABASE_URL não configurada!")
        st.stop()

# Função para buscar veículos
@st.cache_data(ttl=60)
def get_veiculos_estoque():
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                id, marca, modelo, ano, cor, preco_venda, km, 
                combustivel, cambio, portas, placa, observacoes, foto
            FROM veiculos 
            WHERE status = 'Em estoque'
            ORDER BY data_cadastro DESC
        """)
        
        colunas = [desc[0] for desc in cursor.description]
        veiculos = []
        
        for row in cursor.fetchall():
            veiculo = dict(zip(colunas, row))
            # Converter foto para base64 se existir
            if veiculo['foto']:
                veiculo['foto_base64'] = base64.b64encode(veiculo['foto']).decode()
            else:
                veiculo['foto_base64'] = None
            veiculos.append(veiculo)
        
        return veiculos
    except Exception as e:
        st.error(f"Erro ao buscar veículos: {e}")
        return []
    finally:
        conn.close()

# CSS Personalizado
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .header-catalogo {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .veiculo-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        transition: transform 0.3s;
    }
    
    .veiculo-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(232, 142, 27, 0.15);
    }
    
    .veiculo-imagem {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .veiculo-titulo {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }
    
    .veiculo-preco {
        font-size: 1.8rem;
        font-weight: 800;
        color: #e88e1b;
        margin-top: 1rem;
    }
    
    .spec-badge {
        display: inline-block;
        background: #f8f9fa;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="header-catalogo">
    <h1>🚗 Garagem Multimarcas</h1>
    <p>Encontre o veículo perfeito para você</p>
</div>
""", unsafe_allow_html=True)

# FILTROS
col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

veiculos = get_veiculos_estoque()

with col_filtro1:
    marcas = ["Todas"] + sorted(list(set([v['marca'] for v in veiculos])))
    filtro_marca = st.selectbox("🏷️ Marca", marcas)

with col_filtro2:
    filtro_preco = st.number_input("💰 Preço máximo", min_value=0, value=0, step=10000)

with col_filtro3:
    combustiveis = ["Todos"] + sorted(list(set([v['combustivel'] for v in veiculos])))
    filtro_combustivel = st.selectbox("⛽ Combustível", combustiveis)

# APLICAR FILTROS
veiculos_filtrados = veiculos.copy()

if filtro_marca != "Todas":
    veiculos_filtrados = [v for v in veiculos_filtrados if v['marca'] == filtro_marca]

if filtro_preco > 0:
    veiculos_filtrados = [v for v in veiculos_filtrados if v['preco_venda'] <= filtro_preco]

if filtro_combustivel != "Todos":
    veiculos_filtrados = [v for v in veiculos_filtrados if v['combustivel'] == filtro_combustivel]

# CONTADOR
st.markdown(f"### 📦 {len(veiculos_filtrados)} veículos disponíveis")

# GRID DE VEÍCULOS (3 por linha)
for i in range(0, len(veiculos_filtrados), 3):
    cols = st.columns(3)
    
    for j in range(3):
        if i + j < len(veiculos_filtrados):
            veiculo = veiculos_filtrados[i + j]
            
            with cols[j]:
                # Card do veículo
                st.markdown('<div class="veiculo-card">', unsafe_allow_html=True)
                
                # Foto
                if veiculo['foto_base64']:
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{veiculo["foto_base64"]}" class="veiculo-imagem" />',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="veiculo-imagem" style="background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 3rem;">🚗</div>',
                        unsafe_allow_html=True
                    )
                
                # Informações
                st.markdown(f'<div class="veiculo-titulo">{veiculo["marca"]} {veiculo["modelo"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<p style="color: #6c757d;">{veiculo["ano"]} • {veiculo["cor"]}</p>', unsafe_allow_html=True)
                
                # Especificações
                st.markdown(f"""
                <div>
                    <span class="spec-badge">🛣️ {veiculo['km']:,} km</span>
                    <span class="spec-badge">⛽ {veiculo['combustivel']}</span>
                    <span class="spec-badge">⚙️ {veiculo['cambio']}</span>
                    <span class="spec-badge">🚪 {veiculo['portas']} portas</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Preço
                preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.markdown(f'<div class="veiculo-preco">{preco_formatado}</div>', unsafe_allow_html=True)
                
                # Botão WhatsApp
                mensagem = f"Olá! Tenho interesse no {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}"
                link_whatsapp = f"https://wa.me/5584999999999?text={mensagem}"
                
                st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
                    <button style="
                        background: linear-gradient(135deg, #25D366, #128C7E);
                        color: white;
                        border: none;
                        padding: 0.8rem;
                        border-radius: 10px;
                        width: 100%;
                        font-weight: 600;
                        cursor: pointer;
                        margin-top: 1rem;
                    ">
                        💬 Falar no WhatsApp
                    </button>
                </a>
                ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 2rem;">
    <p style="margin: 0; font-weight: 600;">Garagem Multimarcas</p>
    <p style="margin: 0.5rem 0;">📞 (84) 99999-9999 | 📧 contato@garagemmultimarcas.com.br</p>
    <p style="margin: 0;">📍 Av. Lauro Monte, 475 - Mossoró/RN</p>
</div>
''', unsafe_allow_html=True)
if __name__ == "__main__":
    main()
