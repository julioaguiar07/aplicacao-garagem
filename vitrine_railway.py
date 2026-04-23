import os
import sqlite3
import json
import base64
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# =============================================
# CONEXÃO COM BANCO DE DADOS
# =============================================
def get_db_connection():
    """Conecta ao banco de dados (PostgreSQL Railway ou SQLite local)"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url and database_url.startswith('postgresql://'):
        # PostgreSQL no Railway
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    else:
        # SQLite local (desenvolvimento)
        conn = sqlite3.connect("canal_automotivo.db")
        conn.row_factory = sqlite3.Row
        return conn

# =============================================
# FUNÇÃO AUXILIAR PARA PROCESSAR FOTOS
# =============================================
def processar_foto(foto_data):
    """Processa a foto independentemente do formato"""
    if not foto_data:
        return None

    try:
        # Se já for bytes (PostgreSQL bytea)
        if isinstance(foto_data, bytes):
            return base64.b64encode(foto_data).decode('utf-8')

        # Se for memoryview (PostgreSQL)
        if isinstance(foto_data, memoryview):
            return base64.b64encode(foto_data.tobytes()).decode('utf-8')

        # Se for string com \x (hex string)
        if isinstance(foto_data, str):
            if foto_data.startswith('\\x'):
                try:
                    hex_str = foto_data.replace('\\x', '')
                    bytes_data = bytes.fromhex(hex_str)
                    return base64.b64encode(bytes_data).decode('utf-8')
                except:
                    return None

            if len(foto_data) > 100 and ('/' in foto_data or '+' in foto_data):
                return foto_data

        return None

    except Exception as e:
        print(f"❌ Erro ao processar foto: {e}")
        return None

# =============================================
# FUNÇÕES DE BANCO DE DADOS
# =============================================
def get_veiculos_estoque():
    """Busca veículos em estoque do banco"""
    conn = None
    try:
        conn = get_db_connection()

        if isinstance(conn, psycopg2.extensions.connection):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    v.id, v.marca, v.modelo, v.ano, v.cor, 
                    v.preco_venda, v.km, v.combustivel, v.cambio, 
                    v.portas, v.placa, v.chassi, v.observacoes, v.foto,
                    v.data_cadastro, v.status
                FROM veiculos v
                WHERE v.status = 'Em estoque'
                ORDER BY v.data_cadastro DESC
            ''')
            rows = cursor.fetchall()
            veiculos = [dict(row) for row in rows]
        else:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    v.id, v.marca, v.modelo, v.ano, v.cor, 
                    v.preco_venda, v.km, v.combustivel, v.cambio, 
                    v.portas, v.placa, v.chassi, v.observacoes, v.foto,
                    v.data_cadastro, v.status
                FROM veiculos v
                WHERE v.status = 'Em estoque'
                ORDER BY v.data_cadastro DESC
            ''')
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            veiculos = [dict(zip(columns, row)) for row in rows]

        marcas_set = set()
        for veiculo in veiculos:
            veiculo['preco_venda'] = float(veiculo['preco_venda']) if veiculo.get('preco_venda') else 0.0
            veiculo['foto_base64'] = processar_foto(veiculo.get('foto'))
            veiculo['km'] = int(veiculo.get('km', 0)) if veiculo.get('km') else 0
            veiculo['portas'] = int(veiculo.get('portas', 4)) if veiculo.get('portas') else 4
            veiculo['ano'] = int(veiculo.get('ano', 2023)) if veiculo.get('ano') else 2023
            veiculo['nome_completo'] = f"{veiculo['marca']} {veiculo['modelo']}"
            veiculo['version'] = f"{veiculo['ano']} • {veiculo['combustivel']}"
            
            veiculo['optionals'] = []
            if veiculo.get('observacoes'):
                if ',' in veiculo['observacoes']:
                    veiculo['optionals'] = [item.strip() for item in veiculo['observacoes'].split(',')[:8]]
                else:
                    veiculo['optionals'] = [veiculo['observacoes']] if veiculo['observacoes'] else []
            
            veiculo['optionals'].extend([
                f"Cambio {veiculo['cambio']}",
                f"{veiculo['combustivel']}",
                f"{veiculo['portas']} portas"
            ])
            veiculo['optionals'] = list(dict.fromkeys(veiculo['optionals']))[:10]
            veiculo['history'] = f"Veículo {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} em excelente estado." if veiculo['km'] < 50000 else f"Veículo {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} com {veiculo['km']} km rodados. Bem conservado, pronto para uso."
            
            if veiculo['km'] < 10000:
                veiculo['badge'] = 'new'
                veiculo['badgeText'] = 'Zero Km'
            elif veiculo['km'] < 30000:
                veiculo['badge'] = 'deal'
                veiculo['badgeText'] = 'Seminovo'
            else:
                veiculo['badge'] = None
                veiculo['badgeText'] = ''
            
            veiculo['power'] = 'Consultar Loja'
            
            if veiculo['foto_base64']:
                veiculo['images'] = [f"data:image/jpeg;base64,{veiculo['foto_base64']}"] * 2
            else:
                veiculo['images'] = [
                    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1200&q=80",
                    "https://images.unsplash.com/photo-1549317661-bd32c8ce0729?w=1200&q=80"
                ]
            
            marcas_set.add(veiculo['marca'])

        return veiculos, sorted(list(marcas_set))

    except Exception as e:
        print(f"❌ Erro ao buscar veículos: {e}")
        return [], []
    finally:
        if conn:
            conn.close()

def get_logo_base64():
    try:
        possible_paths = ["logoca.png", "./logoca.png", "/app/logoca.png", "logo-icon.png", "./logo-icon.png"]
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Não foi possível carregar logo: {e}")
    return None

def get_favicon_base64():
    try:
        if os.path.exists("logo-icon.png"):
            with open("logo-icon.png", "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Erro ao carregar favicon: {e}")
    return None

# =============================================
# ROTA PRINCIPAL - PORSCHE CINEMATIC EXPERIENCE
# =============================================
@app.route('/')
def home():
    veiculos, marcas = get_veiculos_estoque()
    logo_base64 = get_logo_base64()
    favicon_base64 = get_favicon_base64()
    
    veiculos_json = json.dumps(veiculos, default=str, ensure_ascii=False)
    tipos = ["SUV", "Sedan", "Hatch", "Picape", "Coupé", "Elétrico"]
    transmissoes = ["Automático", "Manual", "CVT"]

    html_template = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carmelo Multimarcas | Experiência Premium</title>
    <link rel="icon" href="data:image/png;base64,{favicon_base64}" type="image/png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --porsche-white: #ffffff;
            --porsche-black: #000000;
            --porsche-orange: #ff4d00;
            --porsche-gray: #666666;
            --porsche-light-gray: #e6e6e6;
            --transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--porsche-white);
            color: var(--porsche-black);
            overflow-x: hidden;
            scroll-behavior: smooth;
        }}

        /* HEADER TRANSPARENTE QUE FICA BRANCO AO ROLAR */
        header {{
            position: fixed;
            top: 0; width: 100%;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 50px;
            z-index: 1000;
            transition: var(--transition);
            background: transparent;
        }}

        header.scrolled {{
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--porsche-light-gray);
            height: 70px;
        }}

        .logo-container {{ height: 40px; }}
        .logo-img {{ height: 100%; width: auto; object-fit: contain; filter: brightness(0) invert(1); transition: var(--transition); }}
        header.scrolled .logo-img {{ filter: none; }}

        .header-nav {{ display: flex; gap: 40px; }}
        .header-nav a {{
            text-decoration: none;
            color: white;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: var(--transition);
        }}
        header.scrolled .header-nav a {{ color: var(--porsche-black); }}
        .header-nav a:hover {{ color: var(--porsche-orange) !important; }}

        /* HERO SECTION CINEMATOGRÁFICA */
        .hero-cinematic {{
            height: 100vh;
            width: 100%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 0 10%;
            background: #000;
            overflow: hidden;
        }}

        .hero-bg {{
            position: absolute;
            inset: 0;
            background: linear-gradient(to right, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0) 100%),
                        url('https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1920&q=80');
            background-size: cover;
            background-position: center;
            z-index: 1;
        }}

        .hero-content {{
            position: relative;
            z-index: 2;
            color: white;
            max-width: 800px;
        }}

        .hero-content h1 {{
            font-size: clamp(48px, 8vw, 110px);
            font-weight: 800;
            line-height: 0.9;
            letter-spacing: -4px;
            margin-bottom: 30px;
            text-transform: uppercase;
        }}

        .hero-btn {{
            display: inline-block;
            padding: 20px 45px;
            border: 1px solid white;
            color: white;
            text-decoration: none;
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: var(--transition);
            background: transparent;
        }}

        .hero-btn:hover {{
            background: white;
            color: black;
        }}

        .scroll-indicator {{
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 2;
            color: white;
            animation: bounce 2s infinite;
            cursor: pointer;
        }}

        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0) translateX(-50%); }}
            40% {{ transform: translateY(-10px) translateX(-50%); }}
            60% {{ transform: translateY(-5px) translateX(-50%); }}
        }}

        /* VITRINE TÉCNICA (CLEAN LUXURY) */
        .showcase-section {{
            padding: 100px 50px;
            max-width: 1500px;
            margin: 0 auto;
        }}

        .showcase-header {{
            margin-bottom: 60px;
        }}

        .showcase-header h2 {{
            font-size: 42px;
            font-weight: 700;
            letter-spacing: -1px;
            margin-bottom: 15px;
        }}

        .showcase-layout {{
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 60px;
        }}

        /* FILTROS */
        .sidebar {{ position: sticky; top: 100px; height: fit-content; }}
        .filter-group {{ margin-bottom: 35px; border-bottom: 1px solid var(--porsche-light-gray); padding-bottom: 25px; }}
        .filter-label {{ font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; display: block; }}
        
        .search-box input {{
            width: 100%;
            padding: 15px;
            background: #f8f8f8;
            border: 1px solid transparent;
            font-family: inherit;
            font-size: 14px;
            transition: var(--transition);
        }}
        .search-box input:focus {{ background: white; border-color: black; outline: none; }}

        .custom-select {{
            width: 100%;
            padding: 15px;
            background: #f8f8f8;
            border: none;
            font-size: 14px;
            cursor: pointer;
        }}

        /* GRID DE VEÍCULOS */
        .vehicle-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 40px;
        }}

        .vehicle-card {{
            cursor: pointer;
            transition: var(--transition);
            border-bottom: 1px solid transparent;
            padding-bottom: 20px;
        }}

        .vehicle-card:hover {{ border-color: var(--porsche-light-gray); }}

        .card-img-box {{
            aspect-ratio: 16/10;
            background: #f2f2f2;
            overflow: hidden;
            position: relative;
            margin-bottom: 25px;
        }}

        .card-img-box img {{
            width: 100%; height: 100%; object-fit: cover;
            transition: transform 1s ease;
        }}

        .vehicle-card:hover .card-img-box img {{ transform: scale(1.08); }}

        .card-info h3 {{ font-size: 24px; font-weight: 700; margin-bottom: 5px; }}
        .card-price-row {{ margin: 15px 0; }}
        .price-label {{ font-size: 12px; color: var(--porsche-gray); text-transform: uppercase; }}
        .price-value {{ font-size: 20px; font-weight: 700; color: var(--porsche-black); }}

        .card-specs {{ display: flex; gap: 10px; margin-top: 20px; }}
        .spec-tag {{ background: #f2f2f2; padding: 6px 12px; font-size: 12px; font-weight: 600; border-radius: 2px; }}

        /* COMPARAÇÃO REFORÇADA */
        .compare-btn-card {{
            margin-top: 25px;
            width: 100%;
            padding: 15px;
            background: white;
            border: 1px solid black;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: var(--transition);
        }}

        .compare-btn-card:hover {{ background: black; color: white; }}
        .compare-btn-card.active {{ background: var(--porsche-orange); border-color: var(--porsche-orange); color: white; }}

        /* FLOATING COMPARE BAR */
        .compare-floating-bar {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: black;
            color: white;
            padding: 15px 30px;
            border-radius: 4px;
            display: none;
            align-items: center;
            gap: 20px;
            z-index: 900;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease;
        }}

        @keyframes slideIn {{ from {{ transform: translateX(100%); }} to {{ transform: translateX(0); }} }}

        /* MODAIS */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: white;
            z-index: 2000;
            display: none;
            overflow-y: auto;
            padding: 60px;
        }}
        .modal-overlay.active {{ display: block; }}
        .modal-close {{ position: fixed; top: 40px; right: 40px; background: black; color: white; border: none; width: 45px; height: 45px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 2100; }}

        /* FOOTER */
        footer {{ background: #fafafa; padding: 80px 50px; border-top: 1px solid var(--porsche-light-gray); }}
        .footer-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 50px; max-width: 1500px; margin: 0 auto; }}
        .footer-col h4 {{ font-size: 14px; text-transform: uppercase; margin-bottom: 25px; letter-spacing: 1px; }}
        .footer-col p {{ font-size: 14px; color: var(--porsche-gray); line-height: 1.8; }}

        @media (max-width: 1024px) {{
            .showcase-layout {{ grid-template-columns: 1fr; }}
            header {{ padding: 0 25px; }}
            .hero-content h1 {{ font-size: 60px; }}
        }}
    </style>
</head>
<body>

    <header id="mainHeader">
        <div class="logo-container">
            {f'<img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="Logo">' if logo_base64 else '<div style="font-weight:800;font-size:24px;letter-spacing:-1px;color:white;" id="textLogo">CARMELO</div>'}
        </div>
        <nav class="header-nav">
            <a href="#estoque">Modelos</a>
            <a href="#sobre">Sobre</a>
            <a href="#contato">Contato</a>
        </nav>
        <div class="header-actions">
            <button class="hero-btn" style="padding: 10px 25px; font-size: 11px;" onclick="openCompare()">Comparar (<span id="compareCountTop">0</span>)</button>
        </div>
    </header>

    <section class="hero-cinematic">
        <div class="hero-bg"></div>
        <div class="hero-content">
            <div style="font-weight: 700; text-transform: uppercase; letter-spacing: 4px; font-size: 14px; margin-bottom: 20px;">Sinta a Emoção</div>
            <h1>A PERFORMANCE<br>QUE VOCÊ MERECE.</h1>
            <a href="#estoque" class="hero-btn">Explorar Coleção</a>
        </div>
        <div class="scroll-indicator" onclick="document.getElementById('estoque').scrollIntoView()">
            <svg width="30" height="30" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m19 9-7 7-7-7"/></svg>
        </div>
    </section>

    <section class="showcase-section" id="estoque">
        <div class="showcase-header">
            <h2>Que modelo gostaria de configurar?</h2>
            <p style="color: var(--porsche-gray);">Explore nossa curadoria de veículos com laudo cautelar e garantia premium.</p>
        </div>

        <div class="showcase-layout">
            <aside class="sidebar">
                <div class="filter-group">
                    <label class="filter-label">Procurar</label>
                    <div class="search-box">
                        <input type="text" id="searchInput" placeholder="Ex: Cayenne, 911, SUV..." oninput="filterVehicles()">
                    </div>
                </div>

                <div class="filter-group">
                    <label class="filter-label">Marca</label>
                    <select id="filterMarca" class="custom-select" onchange="filterVehicles()">
                        <option value="">Todas as Marcas</option>
                        {"".join([f'<option value="{m}">{m}</option>' for m in marcas])}
                    </select>
                </div>

                <div class="filter-group">
                    <label class="filter-label">Câmbio</label>
                    <select id="filterCambio" class="custom-select" onchange="filterVehicles()">
                        <option value="">Todos os Câmbios</option>
                        {"".join([f'<option value="{c}">{c}</option>' for c in transmissoes])}
                    </select>
                </div>

                <div style="background: #f8f8f8; padding: 30px; border-radius: 4px;">
                    <div style="font-weight: 800; font-size: 14px; text-transform: uppercase; margin-bottom: 10px;">Comparar Selecionados</div>
                    <p style="font-size: 13px; color: var(--porsche-gray); margin-bottom: 20px;">Selecione até 4 modelos para ver as diferenças técnicas lado a lado.</p>
                    <button class="hero-btn" style="border-color: black; color: black; width: 100%; text-align: center;" onclick="openCompare()">Ver Comparação</button>
                </div>
            </aside>

            <main>
                <div class="vehicle-grid" id="vehicleGrid">
                    <!-- Injected via JS -->
                </div>
            </main>
        </div>
    </section>

    <footer id="sobre">
        <div class="footer-grid">
            <div class="footer-col">
                <h4>Carmelo Multimarcas</h4>
                <p>Referência em Mossoró/RN para quem busca exclusividade, transparência e os melhores veículos seminovos do mercado.</p>
            </div>
            <div class="footer-col">
                <h4>Onde Estamos</h4>
                <p>Av. Principal, 1000<br>Mossoró - Rio Grande do Norte</p>
            </div>
            <div class="footer-col">
                <h4>Atendimento</h4>
                <p>WhatsApp: (84) 99999-9999<br>E-mail: contato@carmelo.com.br</p>
            </div>
        </div>
        <div style="max-width: 1500px; margin: 60px auto 0; padding-top: 40px; border-top: 1px solid var(--porsche-light-gray); font-size: 12px; color: var(--porsche-gray);">
            &copy; {datetime.now().year} Carmelo Multimarcas. Todos os direitos reservados.
        </div>
    </footer>

    <!-- COMPARAR BARRA FLUTUANTE -->
    <div class="compare-floating-bar" id="compareBar">
        <div style="font-weight: 700; font-size: 14px;"><span id="compareCount">0</span> Modelos Selecionados</div>
        <button class="hero-btn" style="padding: 8px 20px; font-size: 10px; border-color: white;" onclick="openCompare()">Comparar Agora</button>
    </div>

    <!-- MODAL DETALHES -->
    <div class="modal-overlay" id="detailModal">
        <button class="modal-close" onclick="closeModal()">
            <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M6 18 18 6M6 6l12 12"/></svg>
        </button>
        <div id="modalContent"></div>
    </div>

    <!-- COMPARAR VIEW -->
    <div class="modal-overlay" id="compareView">
        <button class="modal-close" onclick="closeCompare()">
            <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M6 18 18 6M6 6l12 12"/></svg>
        </button>
        <div style="max-width: 1300px; margin: 0 auto;">
            <h2 style="font-size: 48px; font-weight: 800; margin-bottom: 50px;">Comparação Detalhada</h2>
            <div id="compareTableContainer" style="overflow-x: auto;"></div>
        </div>
    </div>

    <script>
        const vehicles = {veiculos_json};
        let compareList = [];

        // Header Scroll Effect
        window.addEventListener('scroll', () => {{
            const header = document.getElementById('mainHeader');
            const textLogo = document.getElementById('textLogo');
            if (window.scrollY > 100) {{
                header.classList.add('scrolled');
                if(textLogo) textLogo.style.color = 'black';
            }} else {{
                header.classList.remove('scrolled');
                if(textLogo) textLogo.style.color = 'white';
            }}
        }});

        function formatPrice(p) {{
            return 'R$ ' + p.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}

        function renderVehicles(list) {{
            const grid = document.getElementById('vehicleGrid');
            grid.innerHTML = list.map(v => `
                <div class="vehicle-card" onclick="openDetail(${{v.id}})">
                    <div class="card-img-box">
                        <img src="${{v.images[0]}}" alt="${{v.nome_completo}}" loading="lazy">
                    </div>
                    <div class="card-info">
                        <h3>${{v.marca}} ${{v.modelo}}</h3>
                        <div class="card-price-row">
                            <div class="price-label">A partir de</div>
                            <div class="price-value">${{formatPrice(v.preco_venda)}}</div>
                        </div>
                        <div class="card-specs">
                            <span class="spec-tag">${{v.ano}}</span>
                            <span class="spec-tag">${{v.km.toLocaleString('pt-BR')}} KM</span>
                            <span class="spec-tag">${{v.cambio}}</span>
                        </div>
                        <button class="compare-btn-card ${{compareList.some(c => c.id === v.id) ? 'active' : ''}}" 
                                onclick="event.stopPropagation(); toggleCompare(${{v.id}})">
                            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                                <path d="M8 3 4 7l4 4M16 3l4 4-4 4M14 20V4M10 20V4"/>
                            </svg>
                            ${{compareList.some(c => c.id === v.id) ? 'Remover da Comparação' : 'Comparar Modelo'}}
                        </button>
                    </div>
                </div>
            `).join('');
        }}

        function filterVehicles() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const marca = document.getElementById('filterMarca').value;
            const cambio = document.getElementById('filterCambio').value;

            const filtered = vehicles.filter(v => {{
                const matchSearch = v.nome_completo.toLowerCase().includes(search) || v.marca.toLowerCase().includes(search);
                const matchMarca = !marca || v.marca === marca;
                const matchCambio = !cambio || v.cambio === cambio;
                return matchSearch && matchMarca && matchCambio;
            }});
            renderVehicles(filtered);
        }}

        function toggleCompare(id) {{
            const v = vehicles.find(x => x.id === id);
            const index = compareList.findIndex(c => c.id === id);

            if (index > -1) {{
                compareList.splice(index, 1);
            }} else if (compareList.length < 4) {{
                compareList.push(v);
            }} else {{
                alert('Máximo de 4 modelos para comparação.');
            }}

            updateCompareUI();
            renderVehicles(vehicles);
        }}

        function updateCompareUI() {{
            const count = compareList.length;
            document.getElementById('compareCount').textContent = count;
            document.getElementById('compareCountTop').textContent = count;
            document.getElementById('compareBar').style.display = count > 0 ? 'flex' : 'none';
        }}

        function openDetail(id) {{
            const v = vehicles.find(x => x.id === id);
            if (!v) return;

            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <div style="display:grid; grid-template-columns: 1.5fr 1fr; gap: 80px;">
                    <div>
                        <img src="${{v.images[0]}}" style="width:100%; border-radius:4px; margin-bottom:40px;">
                        <h4 style="text-transform:uppercase; font-size:14px; margin-bottom:20px; border-bottom:1px solid #eee; padding-bottom:10px;">Histórico e Condição</h4>
                        <p style="color:#666; line-height:1.8;">${{v.history}}</p>
                    </div>
                    <div>
                        <div style="text-transform:uppercase; letter-spacing:3px; font-size:12px; color:#999; margin-bottom:10px;">${{v.marca}}</div>
                        <h2 style="font-size:48px; font-weight:800; margin-bottom:30px; line-height:1;">${{v.modelo}}</h2>
                        
                        <div style="background:#f9f9f9; padding:30px; margin-bottom:40px;">
                            <div style="font-size:14px; color:#666; margin-bottom:5px;">Preço de Venda</div>
                            <div style="font-size:36px; font-weight:800; color:var(--porsche-orange);">${{formatPrice(v.preco_venda)}}</div>
                        </div>

                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:30px; margin-bottom:50px;">
                            <div><div style="font-size:11px; text-transform:uppercase; color:#999;">Ano</div><div style="font-weight:700;">${{v.ano}}</div></div>
                            <div><div style="font-size:11px; text-transform:uppercase; color:#999;">Quilometragem</div><div style="font-weight:700;">${{v.km.toLocaleString('pt-BR')}} KM</div></div>
                            <div><div style="font-size:11px; text-transform:uppercase; color:#999;">Câmbio</div><div style="font-weight:700;">${{v.cambio}}</div></div>
                            <div><div style="font-size:11px; text-transform:uppercase; color:#999;">Combustível</div><div style="font-weight:700;">${{v.combustivel}}</div></div>
                        </div>

                        <div style="margin-bottom:50px;">
                            <h4 style="text-transform:uppercase; font-size:13px; margin-bottom:20px;">Destaques do Veículo</h4>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                                ${{v.optionals.map(opt => `<div style="font-size:13px; display:flex; align-items:center; gap:10px;"><span style="width:5px; height:5px; background:black; border-radius:50%;"></span>${{opt}}</div>`).join('')}}
                            </div>
                        </div>

                        <a href="https://wa.me/5584999999999?text=Tenho interesse no ${{v.nome_completo}}" target="_blank" class="hero-btn" style="background:black; color:white; width:100%; text-align:center; border:none;">Solicitar Proposta</a>
                    </div>
                </div>
            `;
            document.getElementById('detailModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal() {{ document.getElementById('detailModal').classList.remove('active'); document.body.style.overflow = 'auto'; }}

        function openCompare() {{
            if (compareList.length < 2) {{ alert('Selecione pelo menos 2 modelos.'); return; }}
            const container = document.getElementById('compareTableContainer');
            let html = '<table style="width:100%; border-collapse:collapse; min-width:800px;">';
            html += '<tr><th style="padding:20px; border-bottom:1px solid #eee; text-align:left; width:200px;">Especificações</th>';
            compareList.forEach(v => {{
                html += `<td style="padding:20px; border-bottom:1px solid #eee;">
                    <img src="${{v.images[0]}}" style="width:100%; height:150px; object-fit:cover; margin-bottom:15px;">
                    <div style="font-weight:800; font-size:18px;">${{v.nome_completo}}</div>
                </td>`;
            }});
            html += '</tr>';

            const fields = [
                {{label: 'Preço', key: 'preco_venda', fmt: formatPrice}},
                {{label: 'Ano', key: 'ano'}},
                {{label: 'KM', key: 'km', fmt: v => v.toLocaleString('pt-BR') + ' KM'}},
                {{label: 'Câmbio', key: 'cambio'}},
                {{label: 'Combustível', key: 'combustivel'}},
                {{label: 'Cor', key: 'cor'}}
            ];

            fields.forEach(f => {{
                html += `<tr><th style="padding:20px; border-bottom:1px solid #eee; text-align:left; font-size:12px; text-transform:uppercase; color:#999;">${{f.label}}</th>`;
                compareList.forEach(v => {{
                    html += `<td style="padding:20px; border-bottom:1px solid #eee; font-weight:600;">${{f.fmt ? f.fmt(v[f.key]) : v[f.key]}}</td>`;
                }});
                html += '</tr>';
            }});
            html += '</table>';
            container.innerHTML = html;
            document.getElementById('compareView').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeCompare() {{ document.getElementById('compareView').classList.remove('active'); document.body.style.overflow = 'auto'; }}

        renderVehicles(vehicles);
    </script>
</body>
</html>'''
    return render_template_string(html_template)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
