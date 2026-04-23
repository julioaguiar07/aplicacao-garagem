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
                    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800&q=80",
                    "https://images.unsplash.com/photo-1549317661-bd32c8ce0729?w=800&q=80"
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
# ROTAS DA API
# =============================================
@app.route('/api/veiculos')
def api_veiculos():
    veiculos, _ = get_veiculos_estoque()
    return jsonify(veiculos)

# =============================================
# ROTA PRINCIPAL - PORSCHE CLEAN LUXURY STYLE
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
    <title>Vitrine Automotiva | Porsche Style</title>
    <link rel="icon" href="data:image/png;base64,{favicon_base64}" type="image/png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --porsche-white: #f2f2f2;
            --porsche-black: #000000;
            --porsche-orange: #ff4d00; /* Laranja Vibrante Porsche */
            --porsche-gray: #666666;
            --porsche-light-gray: #e6e6e6;
            --text-dark: #191919;
            --text-muted: #626669;
            --bg-white: #ffffff;
            --transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-white);
            color: var(--text-dark);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        /* HEADER PORSCHE STYLE */
        header {{
            position: sticky;
            top: 0;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--porsche-light-gray);
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 40px;
            z-index: 1000;
        }}

        .logo-container {{
            height: 40px;
            display: flex;
            align-items: center;
        }}

        .logo-img {{
            height: 100%;
            width: auto;
            object-fit: contain;
        }}

        .header-nav {{
            display: flex;
            gap: 32px;
        }}

        .header-nav a {{
            text-decoration: none;
            color: var(--text-dark);
            font-size: 14px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: var(--transition);
        }}

        .header-nav a:hover {{ color: var(--porsche-orange); }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 24px;
        }}

        /* COMPARE FLOATING BUTTON */
        .compare-action-btn {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--porsche-black);
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            transition: var(--transition);
            border: none;
        }}

        .compare-action-btn:hover {{
            background: var(--porsche-orange);
            transform: translateY(-2px);
        }}

        .compare-count-badge {{
            background: white;
            color: var(--porsche-black);
            width: 18px; height: 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
        }}

        /* HERO SECTION */
        .hero {{
            padding: 80px 40px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .hero h1 {{
            font-size: 48px;
            font-weight: 600;
            margin-bottom: 16px;
            letter-spacing: -1px;
        }}

        .hero p {{
            font-size: 18px;
            color: var(--text-muted);
            max-width: 600px;
        }}

        /* FILTERS SIDEBAR STYLE */
        .main-content {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 40px;
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }}

        .sidebar {{
            position: sticky;
            top: 112px;
            height: fit-content;
        }}

        .filter-group {{
            margin-bottom: 32px;
            border-bottom: 1px solid var(--porsche-light-gray);
            padding-bottom: 24px;
        }}

        .filter-title {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .search-input {{
            width: 100%;
            padding: 12px 16px;
            background: var(--porsche-white);
            border: 1px solid transparent;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
            outline: none;
            transition: var(--transition);
        }}

        .search-input:focus {{
            background: white;
            border-color: var(--porsche-black);
        }}

        .filter-select {{
            width: 100%;
            padding: 12px;
            background: var(--porsche-white);
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
        }}

        /* VEHICLE CARDS PORSCHE STYLE */
        .vehicle-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 32px;
        }}

        .vehicle-card {{
            background: white;
            transition: var(--transition);
            cursor: pointer;
            position: relative;
            display: flex;
            flex-direction: column;
        }}

        .card-image-wrapper {{
            aspect-ratio: 16/10;
            overflow: hidden;
            background: var(--porsche-white);
            position: relative;
        }}

        .card-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.6s ease;
        }}

        .vehicle-card:hover .card-image {{
            transform: scale(1.05);
        }}

        .card-content {{
            padding: 24px 0;
        }}

        .card-badge {{
            position: absolute;
            top: 12px; left: 12px;
            background: white;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            border-radius: 2px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 5;
        }}

        .card-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .card-price-label {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 8px;
        }}

        .card-price {{
            font-size: 18px;
            font-weight: 600;
            color: var(--text-dark);
        }}

        .card-specs {{
            margin-top: 16px;
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .spec-pill {{
            background: var(--porsche-white);
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 500;
        }}

        /* IMPROVED COMPARE UI ON CARD */
        .card-compare-btn {{
            margin-top: 20px;
            width: 100%;
            padding: 12px;
            background: white;
            border: 1px solid var(--porsche-black);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}

        .card-compare-btn:hover {{
            background: var(--porsche-black);
            color: white;
        }}

        .card-compare-btn.active {{
            background: var(--porsche-orange);
            border-color: var(--porsche-orange);
            color: white;
        }}

        /* MODAL */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(255, 255, 255, 0.95);
            z-index: 2000;
            display: none;
            overflow-y: auto;
            padding: 40px;
        }}

        .modal-overlay.active {{ display: block; }}

        .modal-container {{
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
        }}

        .modal-close {{
            position: fixed;
            top: 40px; right: 40px;
            background: var(--porsche-black);
            color: white;
            width: 40px; height: 40px;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2100;
        }}

        .detail-grid {{
            display: grid;
            grid-template-columns: 1.5fr 1fr;
            gap: 60px;
        }}

        .detail-gallery img {{
            width: 100%;
            border-radius: 4px;
        }}

        .detail-info h2 {{
            font-size: 36px;
            margin-bottom: 24px;
        }}

        .detail-price-box {{
            padding: 24px 0;
            border-top: 1px solid var(--porsche-light-gray);
            border-bottom: 1px solid var(--porsche-light-gray);
            margin-bottom: 32px;
        }}

        .btn-whatsapp {{
            display: block;
            width: 100%;
            padding: 18px;
            background: var(--porsche-black);
            color: white;
            text-align: center;
            text-decoration: none;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-radius: 4px;
            transition: var(--transition);
        }}

        .btn-whatsapp:hover {{
            background: var(--porsche-orange);
        }}

        /* COMPARE VIEW */
        .compare-view {{
            position: fixed;
            inset: 0;
            background: white;
            z-index: 3000;
            display: none;
            padding: 60px;
            overflow-y: auto;
        }}

        .compare-view.active {{ display: block; }}

        .compare-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 40px;
        }}

        .compare-table th, .compare-table td {{
            padding: 24px;
            border-bottom: 1px solid var(--porsche-light-gray);
            text-align: left;
        }}

        .compare-table th {{
            font-size: 12px;
            text-transform: uppercase;
            color: var(--text-muted);
            width: 200px;
        }}

        /* FOOTER */
        footer {{
            background: var(--porsche-white);
            padding: 80px 40px;
            border-top: 1px solid var(--porsche-light-gray);
        }}

        .footer-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 40px;
        }}

        .footer-col h4 {{
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }}

        .footer-col p {{
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 12px;
        }}

        @media (max-width: 1024px) {{
            .main-content {{ grid-template-columns: 1fr; }}
            .sidebar {{ position: static; }}
            .detail-grid {{ grid-template-columns: 1fr; }}
            .footer-content {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

    <header>
        <div class="logo-container">
            {f'<img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="Logo">' if logo_base64 else '<div style="font-weight:800;font-size:24px;letter-spacing:-1px;">CARMELO</div>'}
        </div>
        <nav class="header-nav">
            <a href="#estoque">Modelos</a>
            <a href="#sobre">Sobre</a>
            <a href="#contato">Contato</a>
        </nav>
        <div class="header-actions">
            <button class="compare-action-btn" onclick="openCompare()">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8 3 4 7l4 4M16 3l4 4-4 4M14 20V4M10 20V4"/></svg>
                Comparar
                <div id="compareBadge" class="compare-count-badge">0</div>
            </button>
        </div>
    </header>

    <section class="hero">
        <h1>Que modelo gostaria<br>de configurar?</h1>
        <p>Explore nossa seleção exclusiva de veículos premium com garantia de qualidade e performance.</p>
    </section>

    <div class="main-content">
        <aside class="sidebar">
            <div class="filter-group">
                <div class="filter-title">Procurar</div>
                <input type="text" class="search-input" id="searchInput" placeholder="Ex: Cayenne, 911, SUV..." oninput="filterVehicles()">
            </div>
            
            <div class="filter-group">
                <div class="filter-title">Marca</div>
                <select id="filterMarca" class="filter-select" onchange="filterVehicles()">
                    <option value="">Todas as Marcas</option>
                    {"".join([f'<option value="{m}">{m}</option>' for m in marcas])}
                </select>
            </div>

            <div class="filter-group">
                <div class="filter-title">Câmbio</div>
                <select id="filterCambio" class="filter-select" onchange="filterVehicles()">
                    <option value="">Todos os Câmbios</option>
                    {"".join([f'<option value="{c}">{c}</option>' for c in transmissoes])}
                </select>
            </div>

            <div style="background: #f8f8f8; padding: 24px; border-radius: 4px;">
                <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px;">Comparar veículos</div>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 16px;">Selecione até 4 modelos para ver as diferenças detalhadas.</p>
                <button class="compare-action-btn" style="width: 100%; justify-content: center;" onclick="openCompare()">Ver Comparação</button>
            </div>
        </aside>

        <main id="estoque">
            <div class="vehicle-grid" id="vehicleGrid">
                <!-- Injected via JS -->
            </div>
        </main>
    </div>

    <footer id="sobre">
        <div class="footer-content">
            <div class="footer-col">
                <h4>Carmelo Multimarcas</h4>
                <p>Referência em veículos premium e atendimento personalizado.</p>
            </div>
            <div class="footer-col">
                <h4>Localização</h4>
                <p>Av. Principal, Mossoró - RN</p>
                <p>Segunda a Sábado: 08h às 18h</p>
            </div>
            <div class="footer-col">
                <h4>Contato</h4>
                <p>WhatsApp: (84) 99999-9999</p>
                <p>E-mail: contato@carmelo.com.br</p>
            </div>
        </div>
        <div style="max-width: 1400px; margin: 40px auto 0; padding-top: 40px; border-top: 1px solid var(--porsche-light-gray); font-size: 12px; color: var(--text-muted);">
            &copy; {datetime.now().year} Carmelo Multimarcas. Todos os direitos reservados.
        </div>
    </footer>

    <!-- MODAL DETALHES -->
    <div class="modal-overlay" id="detailModal">
        <button class="modal-close" onclick="closeModal()">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M6 18 18 6M6 6l12 12"/></svg>
        </button>
        <div class="modal-container" id="modalContent">
            <!-- Injected via JS -->
        </div>
    </div>

    <!-- COMPARAR VIEW -->
    <div class="compare-view" id="compareView">
        <div style="max-width: 1200px; margin: 0 auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 60px;">
                <h2 style="font-size: 40px;">Comparação de Modelos</h2>
                <button class="compare-action-btn" onclick="closeCompare()">Voltar</button>
            </div>
            <div id="compareTableContainer"></div>
        </div>
    </div>

    <script>
        const vehicles = {veiculos_json};
        let compareList = [];

        function formatPrice(p) {{
            return 'R$ ' + p.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}

        function renderVehicles(list) {{
            const grid = document.getElementById('vehicleGrid');
            grid.innerHTML = list.map(v => `
                <div class="vehicle-card" onclick="openDetail(${{v.id}})">
                    ${{v.badge ? `<div class="card-badge">${{v.badgeText}}</div>` : ''}}
                    <div class="card-image-wrapper">
                        <img src="${{v.images[0]}}" class="card-image" alt="${{v.nome_completo}}" loading="lazy">
                    </div>
                    <div class="card-content">
                        <div class="card-title">${{v.marca}} ${{v.modelo}}</div>
                        <div class="card-price-label">A partir de</div>
                        <div class="card-price">${{formatPrice(v.preco_venda)}}</div>
                        
                        <div class="card-specs">
                            <span class="spec-pill">${{v.ano}}</span>
                            <span class="spec-pill">${{v.km.toLocaleString('pt-BR')}} KM</span>
                            <span class="spec-pill">${{v.cambio}}</span>
                        </div>

                        <button class="card-compare-btn ${{compareList.some(c => c.id === v.id) ? 'active' : ''}}" 
                                onclick="event.stopPropagation(); toggleCompare(${{v.id}})">
                            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
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
                alert('Máximo de 4 modelos.');
            }}

            updateCompareBadge();
            renderVehicles(vehicles);
        }}

        function updateCompareBadge() {{
            const badge = document.getElementById('compareBadge');
            badge.textContent = compareList.length;
            badge.style.display = compareList.length > 0 ? 'flex' : 'none';
        }}

        function openDetail(id) {{
            const v = vehicles.find(x => x.id === id);
            if (!v) return;

            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-gallery">
                        <img src="${{v.images[0]}}" alt="${{v.nome_completo}}">
                        <div style="margin-top:20px; font-size:14px; color:var(--text-muted);">
                            ${{v.history}}
                        </div>
                    </div>
                    <div class="detail-info">
                        <div style="text-transform:uppercase; letter-spacing:2px; font-size:12px; margin-bottom:8px;">${{v.marca}}</div>
                        <h2>${{v.modelo}}</h2>
                        
                        <div class="detail-price-box">
                            <div style="font-size:14px; color:var(--text-muted); margin-bottom:4px;">Preço de Venda</div>
                            <div style="font-size:32px; font-weight:600; color:var(--porsche-orange);">${{formatPrice(v.preco_venda)}}</div>
                        </div>

                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:40px;">
                            <div>
                                <div style="font-size:12px; text-transform:uppercase; color:var(--text-muted);">Ano</div>
                                <div style="font-weight:600;">${{v.ano}}</div>
                            </div>
                            <div>
                                <div style="font-size:12px; text-transform:uppercase; color:var(--text-muted);">Quilometragem</div>
                                <div style="font-weight:600;">${{v.km.toLocaleString('pt-BR')}} KM</div>
                            </div>
                            <div>
                                <div style="font-size:12px; text-transform:uppercase; color:var(--text-muted);">Câmbio</div>
                                <div style="font-weight:600;">${{v.cambio}}</div>
                            </div>
                            <div>
                                <div style="font-size:12px; text-transform:uppercase; color:var(--text-muted);">Combustível</div>
                                <div style="font-weight:600;">${{v.combustivel}}</div>
                            </div>
                        </div>

                        <div style="margin-bottom:40px;">
                            <h4 style="font-size:14px; text-transform:uppercase; margin-bottom:16px;">Equipamentos de Série</h4>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                                ${{v.optionals.map(opt => `<div style="font-size:13px; display:flex; align-items:center; gap:8px;"><span style="width:4px; height:4px; background:black; border-radius:50%;"></span>${{opt}}</div>`).join('')}}
                            </div>
                        </div>

                        <a href="https://wa.me/5584999999999?text=Tenho interesse no ${{v.nome_completo}}" target="_blank" class="btn-whatsapp">Tenho Interesse</a>
                    </div>
                </div>
            `;
            document.getElementById('detailModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.remove('active');
            document.body.style.overflow = 'auto';
        }}

        function openCompare() {{
            if (compareList.length < 2) {{
                alert('Selecione pelo menos 2 modelos para comparar.');
                return;
            }}

            const container = document.getElementById('compareTableContainer');
            let html = '<table class="compare-table">';
            
            // Header
            html += '<tr><th>Modelo</th>';
            compareList.forEach(v => {{
                html += `<td>
                    <img src="${{v.images[0]}}" style="width:100%; height:120px; object-fit:cover; border-radius:4px; margin-bottom:12px;">
                    <div style="font-weight:700;">${{v.nome_completo}}</div>
                </td>`;
            }});
            html += '</tr>';

            // Rows
            const fields = [
                {{label: 'Preço', key: 'preco_venda', fmt: formatPrice}},
                {{label: 'Ano', key: 'ano'}},
                {{label: 'KM', key: 'km', fmt: v => v.toLocaleString('pt-BR') + ' KM'}},
                {{label: 'Câmbio', key: 'cambio'}},
                {{label: 'Combustível', key: 'combustivel'}},
                {{label: 'Cor', key: 'cor'}}
            ];

            fields.forEach(f => {{
                html += `<tr><th>${{f.label}}</th>`;
                compareList.forEach(v => {{
                    html += `<td>${{f.fmt ? f.fmt(v[f.key]) : v[f.key]}}</td>`;
                }});
                html += '</tr>';
            }});

            html += '</table>';
            container.innerHTML = html;
            document.getElementById('compareView').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeCompare() {{
            document.getElementById('compareView').classList.remove('active');
            document.body.style.overflow = 'auto';
        }}

        renderVehicles(vehicles);
        window.onclick = e => {{ if(e.target.classList.contains('modal-overlay')) closeModal(); }}
    </script>
</body>
</html>'''
    return render_template_string(html_template)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
