import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2
import os
from PIL import Image
import base64
import io
from streamlit.components.v1 import html

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
                
                # Processar foto se existir - CORREÇÃO AQUI
                if tem_foto and veiculo.get('foto'):
                    try:
                        if isinstance(veiculo['foto'], bytes):
                            # Converter bytes para base64 corretamente
                            veiculo['foto_base64'] = base64.b64encode(veiculo['foto']).decode('utf-8')
                        elif isinstance(veiculo['foto'], memoryview):
                            # Se for memoryview, converter para bytes primeiro
                            veiculo['foto_base64'] = base64.b64encode(veiculo['foto'].tobytes()).decode('utf-8')
                        else:
                            veiculo['foto_base64'] = None
                    except Exception as e:
                        print(f"Erro ao processar foto: {e}")
                        veiculo['foto_base64'] = None
                else:
                    veiculo['foto_base64'] = None
                
                veiculos.append(veiculo)
            
            return veiculos
            
        except Exception as e:
            print(f"Erro ao buscar veículos: {e}")
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

def create_vehicle_card_html(veiculo):
    """Cria HTML de um card de veículo"""
    
    # CORREÇÃO: Verificar se a foto base64 é válida
    image_src = generate_placeholder_image(veiculo)  # Default para placeholder
    
    if veiculo.get('foto_base64'):
        try:
            # Testar se a base64 é válida
            base64.b64decode(veiculo['foto_base64'])
            image_src = f"data:image/jpeg;base64,{veiculo['foto_base64']}"
        except:
            # Se base64 for inválido, usar placeholder
            image_src = generate_placeholder_image(veiculo)
    
    # Determinar badges
    idade = datetime.now().year - veiculo['ano']
    badges_html = ""
    if idade <= 1:
        badges_html += '<div class="badge badge-new">🆕 NOVO</div>'
    if veiculo['km'] < 20000:
        badges_html += '<div class="badge badge-lowkm">⭐ BAIXA KM</div>'
    
    # Cálculo de financiamento
    entrada = veiculo['preco_venda'] * 0.2
    parcela = (veiculo['preco_venda'] - entrada) / 48
    
    # Formatar dados
    preco_formatado = f"R$ {veiculo['preco_venda']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    parcela_formatada = f"R$ {parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    km_formatado = f"{veiculo['km']:,} km".replace(',', '.')
    
    # CORREÇÃO: Adicionar mais informações nos detalhes
    detalhes_info = f"""
    Marca: {veiculo['marca']}
    Modelo: {veiculo['modelo']}
    Ano: {veiculo['ano']}
    Cor: {veiculo['cor']}
    KM: {km_formatado}
    Câmbio: {veiculo['cambio']}
    Combustível: {veiculo['combustivel']}
    Portas: {veiculo['portas']}
    Preço: {preco_formatado}
    Placa: {veiculo['placa'] or 'Não informada'}
    
    Financiamento:
    • Entrada: R$ {entrada:,.2f}
    • 48x de: {parcela_formatada}
    """
    
    card_html = f'''
    <div class="vehicle-card">
        <div class="image-container">
            <img src="{image_src}" class="vehicle-image" alt="{veiculo['marca']} {veiculo['modelo']}" 
                 onerror="this.src='{generate_placeholder_image(veiculo)}'">
            <div class="badges-container">
                {badges_html}
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
                <button class="btn-details" onclick="showVehicleDetails({veiculo['id']}, `{detalhes_info.replace('`', "'")}`)">
                    🔍 Detalhes
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

def render_vehicle_grid_html(veiculos):
    """Renderiza grid completo de veículos em HTML"""
    if not veiculos:
        return '''
        <div class="no-vehicles">
            <div class="no-vehicles-icon">🚗</div>
            <h3>Nenhum veículo encontrado</h3>
            <p>Tente ajustar os filtros para encontrar mais opções!</p>
        </div>
        '''
    
    grid_html = '<div class="vehicles-grid">'
    for veiculo in veiculos:
        grid_html += create_vehicle_card_html(veiculo)
    grid_html += '</div>'
    
    return grid_html

def get_full_html_page(veiculos_filtrados, filtros_html):
    """Retorna a página HTML completa"""
    
    logo = load_logo()
    logo_html = ''
    if logo:
        try:
            # Converter logo para base64 corretamente
            buffered = io.BytesIO()
            logo.save(buffered, format="PNG")
            logo_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Garagem Multimarcas">'
        except Exception as e:
            logo_html = '<div class="logo-placeholder">🚗</div>'
    
    vehicles_grid_html = render_vehicle_grid_html(veiculos_filtrados)
    
    full_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Garagem Multimarcas - Catálogo Premium</title>
        <style>
            /* Reset e configurações base */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: #0f0f0f;
                color: #ffffff;
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                line-height: 1.6;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            
            /* Header */
            .contact-bar {{
                background: #e88e1b;
                color: #1a1a1a;
                padding: 12px 0;
                text-align: center;
                font-weight: 700;
                font-size: 14px;
            }}
            
            .header {{
                background: #1a1a1a;
                padding: 20px 0;
                border-bottom: 3px solid #e88e1b;
            }}
            
            .header-content {{
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .logo {{
                height: 60px;
                width: auto;
            }}
            
            .logo-placeholder {{
                font-size: 40px;
                color: #e88e1b;
            }}
            
            .brand-title {{
                font-size: 32px;
                font-weight: 800;
                color: #e88e1b;
                text-align: center;
                flex: 1;
            }}
            
            /* Hero Section */
            .hero-section {{
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                padding: 50px 0;
                text-align: center;
                margin-bottom: 30px;
            }}
            
            .hero-title {{
                font-size: 42px;
                font-weight: 800;
                margin-bottom: 15px;
                background: linear-gradient(135deg, #e88e1b, #f4c220);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .hero-subtitle {{
                font-size: 18px;
                color: #b0b0b0;
                max-width: 600px;
                margin: 0 auto;
            }}
            
            /* Filtros */
            .filters-section {{
                background: #1a1a1a;
                padding: 30px;
                border-radius: 16px;
                margin: 40px 0;
                border: 1px solid #333;
            }}
            
            .filter-title {{
                font-size: 24px;
                font-weight: 700;
                color: #e88e1b;
                margin-bottom: 25px;
                text-align: center;
            }}
            
            /* Grid de Cards */
            .vehicles-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 25px;
                margin: 40px 0;
            }}
            
            /* Card do veículo */
            .vehicle-card {{
                background: #1a1a1a;
                border-radius: 16px;
                border: 1px solid #333;
                transition: all 0.3s ease;
                overflow: hidden;
                position: relative;
            }}
            
            .vehicle-card:hover {{
                transform: translateY(-5px);
                border-color: #e88e1b;
                box-shadow: 0 10px 30px rgba(232, 142, 27, 0.2);
            }}
            
            .image-container {{
                position: relative;
                width: 100%;
                height: 200px;
                overflow: hidden;
                background: #2d2d2d;
            }}
            
            .vehicle-image {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: transform 0.3s ease;
            }}
            
            .vehicle-card:hover .vehicle-image {{
                transform: scale(1.05);
            }}
            
            .badges-container {{
                position: absolute;
                top: 12px;
                left: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            
            .badge {{
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .badge-new {{
                background: #27ae60;
                color: white;
            }}
            
            .badge-lowkm {{
                background: #e88e1b;
                color: #1a1a1a;
            }}
            
            .card-content {{
                padding: 20px;
            }}
            
            .vehicle-price {{
                font-size: 22px;
                font-weight: 800;
                color: #e88e1b;
                margin-bottom: 8px;
            }}
            
            .vehicle-name {{
                font-size: 18px;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 12px;
                line-height: 1.3;
            }}
            
            .vehicle-details {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                font-size: 14px;
                color: #b0b0b0;
            }}
            
            .vehicle-year {{
                font-weight: 600;
                color: #e88e1b;
            }}
            
            .vehicle-km {{
                font-weight: 500;
            }}
            
            .vehicle-specs {{
                display: flex;
                gap: 15px;
                margin-bottom: 15px;
                font-size: 13px;
                color: #888;
            }}
            
            .spec-item {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            
            .price-info {{
                margin-bottom: 15px;
            }}
            
            .parcel-info {{
                font-size: 12px;
                color: #888;
                text-align: center;
            }}
            
            .btn-container {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }}
            
            .btn-details {{
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
            }}
            
            .btn-details:hover {{
                background: #444;
            }}
            
            .btn-whatsapp {{
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
            }}
            
            .btn-whatsapp:hover {{
                background: #20bd5c;
            }}
            
            /* Contador */
            .vehicle-counter {{
                background: #e88e1b;
                color: #1a1a1a;
                padding: 12px 24px;
                border-radius: 25px;
                font-weight: 800;
                font-size: 14px;
                display: inline-block;
                margin-bottom: 20px;
            }}
            
            /* Sem veículos */
            .no-vehicles {{
                text-align: center;
                padding: 80px 20px;
                color: #888;
            }}
            
            .no-vehicles-icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            
            .no-vehicles h3 {{
                color: #e88e1b;
                margin-bottom: 10px;
            }}
            
            /* Footer */
            .footer {{
                background: #1a1a1a;
                padding: 50px 0 30px;
                margin-top: 60px;
                border-top: 1px solid #333;
                text-align: center;
            }}
            
            .footer-brand {{
                font-size: 24px;
                font-weight: 800;
                color: #e88e1b;
                margin-bottom: 10px;
            }}
            
            .footer-contact {{
                color: #888;
                margin-bottom: 20px;
            }}
            
            .footer-copyright {{
                color: #666;
                font-size: 12px;
            }}
            
            /* Modal de detalhes */
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.8);
            }}
            
            .modal-content {{
                background: #1a1a1a;
                margin: 5% auto;
                padding: 30px;
                border-radius: 16px;
                border: 2px solid #e88e1b;
                width: 90%;
                max-width: 600px;
                position: relative;
            }}
            
            .close {{
                color: #e88e1b;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                position: absolute;
                right: 20px;
                top: 15px;
            }}
            
            .close:hover {{
                color: #f4c220;
            }}
            
            .details-title {{
                color: #e88e1b;
                margin-bottom: 20px;
                text-align: center;
            }}
            
            .details-content {{
                white-space: pre-line;
                line-height: 1.8;
                color: #b0b0b0;
            }}
            
            /* Responsividade */
            @media (max-width: 768px) {{
                .vehicles-grid {{
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                }}
                
                .brand-title {{
                    font-size: 24px;
                }}
                
                .hero-title {{
                    font-size: 32px;
                }}
                
                .modal-content {{
                    width: 95%;
                    margin: 10% auto;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="contact-bar">
            ⭐ CONDIÇÕES ESPECIAIS • 📞 (84) 98188-5353 • 📍 Mossoró/RN • ⏰ Seg-Sex: 8h-18h
        </div>
        
        <div class="header">
            <div class="container">
                <div class="header-content">
                    {logo_html}
                    <div class="brand-title">GARAGEM MULTIMARCAS</div>
                </div>
            </div>
        </div>
        
        <div class="hero-section">
            <div class="container">
                <h1 class="hero-title">CATÁLOGO PREMIUM</h1>
                <p class="hero-subtitle">Os melhores veículos novos e seminovos com condições especiais de pagamento</p>
            </div>
        </div>
        
        <div class="container">
            {filtros_html}
            
            <div class="vehicle-counter">🚗 {len(veiculos_filtrados)} VEÍCULOS ENCONTRADOS</div>
            
            {vehicles_grid_html}
        </div>
        
        <!-- Modal para detalhes -->
        <div id="detailsModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <h2 class="details-title">🚗 Detalhes do Veículo</h2>
                <div id="modalBody" class="details-content"></div>
            </div>
        </div>
        
        <div class="footer">
            <div class="container">
                <div class="footer-brand">GARAGEM MULTIMARCAS</div>
                <div class="footer-contact">📞 (84) 98188-5353 • 📍 Mossoró/RN</div>
                <div class="footer-copyright">© 2024 Garagem Multimarcas - Todos os direitos reservados</div>
            </div>
        </div>
        
        <script>
            function showVehicleDetails(vehicleId, details) {{
                document.getElementById('modalBody').textContent = details;
                document.getElementById('detailsModal').style.display = 'block';
            }}
            
            function closeModal() {{
                document.getElementById('detailsModal').style.display = 'none';
            }}
            
            // Fechar modal ao clicar fora
            window.onclick = function(event) {{
                const modal = document.getElementById('detailsModal');
                if (event.target === modal) {{
                    closeModal();
                }}
            }}
            
            // Fallback para imagens que não carregam
            document.addEventListener('DOMContentLoaded', function() {{
                const images = document.querySelectorAll('.vehicle-image');
                images.forEach(img => {{
                    img.onerror = function() {{
                        const altText = this.alt || 'Veículo';
                        const marcaModelo = altText.split(' ').slice(0, 2).join('+');
                        const cor = '3498db'; // Cor padrão
                        this.src = `https://via.placeholder.com/400x250/${{cor}}/ffffff?text=${{marcaModelo}}`;
                    }};
                }});
            }});
        </script>
    </body>
    </html>
    '''
    
    return full_html

# =============================================
# PÁGINA PRINCIPAL
# =============================================

def main():
    # Buscar dados do banco
    with st.spinner('🔄 Carregando veículos...'):
        db = LuxuryDatabase()
        veiculos = db.get_veiculos_estoque()
    
    # Filtros usando Streamlit
    st.markdown("""
    <style>
    .stApp {
        background: #0f0f0f;
    }
    </style>
    """, unsafe_allow_html=True)

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
            
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if veiculos:
            marcas = ["Todas as marcas"] + sorted(list(set([v['marca'] for v in veiculos])))
            marca_filtro = st.selectbox("🏷️ Marca", marcas)
        else:
            marca_filtro = "Todas as marcas"
    
    with col2:
        if veiculos:
            anos = ["Todos os anos"] + sorted(list(set([v['ano'] for v in veiculos])), reverse=True)
            ano_filtro = st.selectbox("📅 Ano", anos)
        else:
            ano_filtro = "Todos os anos"
    
    with col3:
        if veiculos:
            preco_min = int(min(v['preco_venda'] for v in veiculos)) if veiculos else 0
            preco_max = int(max(v['preco_venda'] for v in veiculos)) if veiculos else 200000
            preco_filtro = st.slider("💰 Preço Máximo (R$)", preco_min, preco_max, preco_max, 1000)
        else:
            preco_filtro = 100000
    
    with col4:
        ordenacao = st.selectbox("🔃 Ordenar", ["Mais recentes", "Menor preço", "Maior preço", "Menor KM"])
    # Gerar HTML completo
    filtros_html = f"""
    <div class="filters-section">
        <div class="filter-title">🔍 FILTRAR VEÍCULOS</div>
        <div style="color: #b0b0b0; text-align: center; margin-bottom: 20px;">
            Filtros aplicados: {marca_filtro} • {ano_filtro} • Até R$ {preco_filtro:,}
        </div>
    </div>
    """
    
    full_html = get_full_html_page(veiculos_filtrados, filtros_html)
    
    # Renderizar HTML usando components
    html(full_html, height=2000, scrolling=True)

if __name__ == "__main__":
    main()
