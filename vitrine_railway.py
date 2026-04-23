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
                    "https://images.unsplash.com/photo-1503736334956-4c8f8e92946d?w=800&q=80",
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

def get_autocore_logo_base64():
    try:
        possible_paths = ["autocore.png", "./autocore.png", "/app/autocore.png"]
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Não foi possível carregar logo AutoCore: {e}")
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

@app.route('/api/health')
def health():
    veiculos, _ = get_veiculos_estoque()
    return jsonify({
        "status": "healthy",
        "service": "vitrine-porsche-style",
        "timestamp": datetime.now().isoformat(),
        "veiculos_estoque": len(veiculos),
        "database": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
    })

@app.route('/api/stats')
def stats():
    veiculos, _ = get_veiculos_estoque()
    total_veiculos = len(veiculos)
    valor_total = sum(v['preco_venda'] for v in veiculos)
    media_preco = valor_total / total_veiculos if total_veiculos > 0 else 0
    marcas = len(set(v['marca'] for v in veiculos))

    return jsonify({
        "total_veiculos": total_veiculos,
        "valor_total": valor_total,
        "media_preco": media_preco,
        "marcas_diferentes": marcas,
        "timestamp": datetime.now().isoformat()
    })

# =============================================
# ROTA PRINCIPAL - DESIGN LUXUOSO PORSCHE STYLE
# =============================================
@app.route('/')
def home():
    veiculos, marcas = get_veiculos_estoque()
    autocore_logo_base64 = get_autocore_logo_base64()
    favicon_base64 = get_favicon_base64()
    total_veiculos = len(veiculos)
    valor_total = sum(v['preco_venda'] for v in veiculos)
    
    veiculos_json = json.dumps(veiculos, default=str, ensure_ascii=False)

    tipos = ["SUV", "Sedan", "Hatch", "Picape", "Coupé", "Elétrico"]
    transmissoes = ["Automático", "Manual", "CVT"]
    combustiveis = list(set(v['combustivel'] for v in veiculos if v.get('combustivel'))) or ["Flex", "Gasolina", "Diesel"]
    cores = list(set(v['cor'] for v in veiculos if v.get('cor'))) or ["Preto", "Branco", "Prata", "Cinza", "Vermelho", "Azul"]

    html_template = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Auto | Experiência de Luxo</title>
    <link rel="icon" href="data:image/png;base64,{favicon_base64}" type="image/png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #000000;
            --secondary: #1a1a1a;
            --accent: #d4af37; /* Dourado luxo */
            --accent-hover: #b8962e;
            --text: #ffffff;
            --text-muted: #a0a0a0;
            --bg: #050505;
            --card-bg: #121212;
            --border: rgba(255, 255, 255, 0.1);
            --radius: 4px; /* Estilo mais sóbrio/porsche */
            --transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            overflow-x: hidden;
        }}

        h1, h2, h3, .logo-text {{
            font-family: 'Playfair Display', serif;
            letter-spacing: -0.02em;
        }}

        /* SCROLLBAR */
        ::-webkit-scrollbar {{ width: 4px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--accent); }}

        /* HEADER */
        header {{
            position: fixed;
            top: 0; width: 100%;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 5%;
            background: rgba(5, 5, 5, 0.8);
            backdrop-filter: blur(20px);
            z-index: 1000;
            border-bottom: 1px solid var(--border);
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 15px;
            text-decoration: none;
            color: var(--text);
        }}

        .logo-text {{
            font-size: 24px;
            text-transform: uppercase;
            letter-spacing: 4px;
        }}

        .logo-text span {{ color: var(--accent); }}

        nav {{ display: flex; gap: 30px; }}
        nav a {{
            text-decoration: none;
            color: var(--text-muted);
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: var(--transition);
        }}
        nav a:hover, nav a.active {{ color: var(--accent); }}

        .header-actions {{ display: flex; align-items: center; gap: 20px; }}
        
        .compare-badge-container {{
            position: relative;
            cursor: pointer;
        }}
        .compare-badge {{
            position: absolute;
            top: -8px; right: -8px;
            background: var(--accent);
            color: black;
            font-size: 10px;
            font-weight: 700;
            width: 18px; height: 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: var(--transition);
        }}
        .compare-badge.visible {{ opacity: 1; }}

        /* HERO */
        .hero {{
            height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0 10%;
            background: linear-gradient(to right, rgba(0,0,0,0.8), transparent), 
                        url('https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1920&q=80');
            background-size: cover;
            background-position: center;
            margin-bottom: 50px;
        }}

        .hero-content h1 {{
            font-size: clamp(40px, 8vw, 80px);
            line-height: 1.1;
            margin-bottom: 20px;
            max-width: 800px;
        }}

        .hero-content p {{
            font-size: 18px;
            color: var(--text-muted);
            max-width: 500px;
            margin-bottom: 40px;
        }}

        .btn-primary {{
            display: inline-block;
            padding: 18px 40px;
            background: var(--accent);
            color: black;
            text-decoration: none;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 12px;
            transition: var(--transition);
            border: none;
            cursor: pointer;
        }}
        .btn-primary:hover {{
            background: var(--accent-hover);
            transform: translateY(-2px);
        }}

        /* FILTERS BAR */
        .filters-container {{
            padding: 0 5%;
            margin-bottom: 40px;
        }}

        .search-wrapper {{
            position: relative;
            margin-bottom: 30px;
        }}

        .search-wrapper input {{
            width: 100%;
            background: transparent;
            border: none;
            border-bottom: 1px solid var(--border);
            padding: 20px 0;
            font-size: 24px;
            color: var(--text);
            font-family: 'Playfair Display', serif;
            outline: none;
        }}

        .search-wrapper input::placeholder {{ color: var(--text-muted); opacity: 0.3; }}

        .filter-tags {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}

        .filter-select {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 20px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            outline: none;
            cursor: pointer;
            transition: var(--transition);
        }}
        .filter-select:hover {{ border-color: var(--accent); }}

        /* VEHICLE GRID */
        .vehicle-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 30px;
            padding: 0 5%;
            margin-bottom: 80px;
        }}

        .vehicle-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }}

        .vehicle-card:hover {{
            border-color: rgba(212, 175, 55, 0.3);
            transform: translateY(-10px);
        }}

        .card-image-container {{
            height: 280px;
            overflow: hidden;
            position: relative;
        }}

        .card-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 1.2s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .vehicle-card:hover .card-image {{
            transform: scale(1.1);
        }}

        .card-badge {{
            position: absolute;
            top: 20px; left: 20px;
            background: var(--accent);
            color: black;
            padding: 5px 12px;
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            z-index: 10;
        }}

        .compare-toggle {{
            position: absolute;
            top: 20px; right: 20px;
            width: 40px; height: 40px;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 10;
            transition: var(--transition);
        }}
        .compare-toggle.active {{ background: var(--accent); border-color: var(--accent); color: black; }}
        .compare-toggle:hover {{ border-color: var(--accent); }}

        .card-info {{
            padding: 30px;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
        }}

        .card-title h3 {{
            font-size: 22px;
            margin-bottom: 5px;
        }}

        .card-subtitle {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .card-price {{
            font-family: 'Playfair Display', serif;
            font-size: 24px;
            color: var(--accent);
        }}

        .card-specs {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }}

        .spec-item {{
            display: flex;
            flex-direction: column;
        }}

        .spec-label {{
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }}

        .spec-value {{
            font-size: 13px;
            font-weight: 600;
        }}

        /* MODAL */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.95);
            z-index: 2000;
            display: none;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(10px);
        }}

        .modal-overlay.active {{ display: flex; }}

        .modal-container {{
            width: 90%;
            max-width: 1200px;
            height: 90vh;
            background: var(--bg);
            border: 1px solid var(--border);
            position: relative;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .modal-close {{
            position: absolute;
            top: 30px; right: 30px;
            background: transparent;
            border: none;
            color: var(--text);
            cursor: pointer;
            z-index: 100;
        }}

        .modal-body {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            height: 100%;
        }}

        .modal-gallery {{
            background: #000;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .modal-gallery img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        .modal-details {{
            padding: 60px;
            overflow-y: auto;
            border-left: 1px solid var(--border);
        }}

        .detail-price {{
            font-size: 48px;
            color: var(--accent);
            margin: 20px 0;
        }}

        .detail-specs {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 40px 0;
        }}

        .optionals-list {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }}

        .optional-item {{
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .optional-item::before {{
            content: '';
            width: 5px; height: 5px;
            background: var(--accent);
        }}

        .modal-actions {{
            margin-top: 50px;
            display: flex;
            gap: 20px;
        }}

        /* COMPARE PAGE */
        .compare-container {{
            position: fixed;
            inset: 0;
            background: var(--bg);
            z-index: 3000;
            display: none;
            padding: 100px 5%;
            overflow-y: auto;
        }}
        .compare-container.active {{ display: block; }}

        .compare-grid {{
            display: grid;
            grid-template-columns: 200px repeat(auto-fill, minmax(300px, 1fr));
            gap: 2px;
            background: var(--border);
            border: 1px solid var(--border);
        }}

        .compare-cell {{
            background: var(--bg);
            padding: 20px;
            display: flex;
            align-items: center;
        }}

        .compare-header-cell {{
            background: var(--card-bg);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 12px;
            color: var(--accent);
        }}

        /* FOOTER */
        footer {{
            padding: 100px 5% 50px;
            background: var(--secondary);
            border-top: 1px solid var(--border);
        }}

        .footer-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1.5fr;
            gap: 50px;
            margin-bottom: 80px;
        }}

        .footer-col h4 {{
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 14px;
            margin-bottom: 30px;
            color: var(--accent);
        }}

        .footer-col p, .footer-col a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 14px;
            display: block;
            margin-bottom: 15px;
            transition: var(--transition);
        }}

        .footer-col a:hover {{ color: var(--text); }}

        .footer-bottom {{
            padding-top: 40px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-muted);
        }}

        /* RESPONSIVE */
        @media (max-width: 1024px) {{
            .modal-body {{ grid-template-columns: 1fr; }}
            .modal-details {{ padding: 30px; }}
            .footer-grid {{ grid-template-columns: 1fr 1fr; }}
        }}

        @media (max-width: 768px) {{
            .hero {{ height: 60vh; }}
            .vehicle-grid {{ grid-template-columns: 1fr; }}
            nav {{ display: none; }}
        }}

        /* ANIMATIONS */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .reveal {{
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
    </style>
</head>
<body>

    <header>
        <a href="#" class="logo">
            <div class="logo-text">PREMIUM<span>AUTO</span></div>
        </a>
        <nav>
            <a href="#estoque" class="active">Estoque</a>
            <a href="#sobre">Sobre</a>
            <a href="#contato">Contato</a>
        </nav>
        <div class="header-actions">
            <div class="compare-badge-container" onclick="openCompare()">
                <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path d="M8 3 4 7l4 4M16 3l4 4-4 4M14 20V4M10 20V4"/>
                </svg>
                <div id="compareBadge" class="compare-badge">0</div>
            </div>
            <button class="btn-primary" style="padding: 12px 25px; font-size: 10px;" onclick="document.getElementById('estoque').scrollIntoView()">Ver Estoque</button>
        </div>
    </header>

    <section class="hero">
        <div class="hero-content reveal">
            <h1>A ARTE DA<br>PERFORMANCE</h1>
            <p>Descubra nossa curadoria exclusiva de veículos que transcendem a engenharia comum.</p>
            <button class="btn-primary" onclick="document.getElementById('estoque').scrollIntoView()">Explorar Coleção</button>
        </div>
    </section>

    <main id="estoque">
        <div class="filters-container reveal">
            <div class="search-wrapper">
                <input type="text" id="searchInput" placeholder="BUSCAR POR MODELO OU MARCA..." oninput="filterVehicles()">
            </div>
            <div class="filter-tags">
                <select id="filterMarca" class="filter-select" onchange="filterVehicles()">
                    <option value="">Todas as Marcas</option>
                    {"".join([f'<option value="{m}">{m}</option>' for m in marcas])}
                </select>
                <select id="filterTipo" class="filter-select" onchange="filterVehicles()">
                    <option value="">Todos os Tipos</option>
                    {"".join([f'<option value="{t}">{t}</option>' for t in tipos])}
                </select>
                <select id="filterCambio" class="filter-select" onchange="filterVehicles()">
                    <option value="">Câmbio</option>
                    {"".join([f'<option value="{c}">{c}</option>' for c in transmissoes])}
                </select>
            </div>
        </div>

        <div class="vehicle-grid" id="vehicleGrid">
            <!-- Veículos injetados via JS -->
        </div>
    </main>

    <footer id="sobre">
        <div class="footer-grid">
            <div class="footer-col">
                <div class="logo-text" style="margin-bottom: 20px;">PREMIUM<span>AUTO</span></div>
                <p>Especialistas em veículos de alta performance e luxo. Oferecemos uma experiência personalizada para clientes que buscam o extraordinário.</p>
            </div>
            <div class="footer-col">
                <h4>Menu</h4>
                <a href="#">Estoque</a>
                <a href="#">Financiamento</a>
                <a href="#">Sobre Nós</a>
                <a href="#">Contato</a>
            </div>
            <div class="footer-col">
                <h4>Contato</h4>
                <p>Av. Principal, 1000<br>Mossoró - RN</p>
                <p>(84) 99999-9999</p>
                <p>contato@premiumauto.com.br</p>
            </div>
            <div class="footer-col">
                <h4>Newsletter</h4>
                <p>Receba novidades sobre novos veículos em primeira mão.</p>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <input type="email" placeholder="SEU E-MAIL" style="background: transparent; border: 1px solid var(--border); padding: 10px; color: white; flex: 1;">
                    <button class="btn-primary" style="padding: 10px 20px;">OK</button>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; {datetime.now().year} Premium Auto. Todos os direitos reservados.</p>
            <div style="display: flex; gap: 20px;">
                <a href="#" style="color: var(--text-muted); text-decoration: none;">Instagram</a>
                <a href="#" style="color: var(--text-muted); text-decoration: none;">YouTube</a>
            </div>
        </div>
    </footer>

    <!-- MODAL DE DETALHES -->
    <div class="modal-overlay" id="detailModal">
        <div class="modal-container" id="modalContainer">
            <button class="modal-close" onclick="closeModal()">
                <svg width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M6 18 18 6M6 6l12 12"/></svg>
            </button>
            <div class="modal-body" id="modalBody">
                <!-- Conteúdo injetado via JS -->
            </div>
        </div>
    </div>

    <!-- PÁGINA DE COMPARAÇÃO -->
    <div class="compare-container" id="comparePage">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 50px;">
            <h2 style="font-size: 40px;">COMPARAÇÃO DE <span style="color: var(--accent);">VEÍCULOS</span></h2>
            <button class="btn-primary" onclick="closeCompare()">Voltar ao Estoque</button>
        </div>
        <div class="compare-grid" id="compareGrid">
            <!-- Grid de comparação injetado via JS -->
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
            grid.innerHTML = list.map((v, i) => `
                <div class="vehicle-card reveal" style="animation-delay: ${{i * 0.1}}s" onclick="openDetail(${{v.id}})">
                    ${{v.badge ? `<div class="card-badge">${{v.badgeText}}</div>` : ''}}
                    <div class="compare-toggle ${{compareList.some(c => c.id === v.id) ? 'active' : ''}}" 
                         onclick="event.stopPropagation(); toggleCompare(${{v.id}})">
                        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path d="M8 3 4 7l4 4M16 3l4 4-4 4M14 20V4M10 20V4"/>
                        </svg>
                    </div>
                    <div class="card-image-container">
                        <img src="${{v.images[0]}}" class="card-image" alt="${{v.nome_completo}}">
                    </div>
                    <div class="card-info">
                        <div class="card-header">
                            <div class="card-title">
                                <h3>${{v.marca}} ${{v.modelo}}</h3>
                                <div class="card-subtitle">${{v.ano}} • ${{v.km.toLocaleString('pt-BR')}} KM</div>
                            </div>
                            <div class="card-price">${{formatPrice(v.preco_venda)}}</div>
                        </div>
                        <div class="card-specs">
                            <div class="spec-item">
                                <span class="spec-label">Câmbio</span>
                                <span class="spec-value">${{v.cambio}}</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Combustível</span>
                                <span class="spec-value">${{v.combustivel}}</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Cor</span>
                                <span class="spec-value">${{v.cor}}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function filterVehicles() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const marca = document.getElementById('filterMarca').value;
            const tipo = document.getElementById('filterTipo').value;
            const cambio = document.getElementById('filterCambio').value;

            const filtered = vehicles.filter(v => {{
                const matchSearch = v.nome_completo.toLowerCase().includes(search) || v.marca.toLowerCase().includes(search);
                const matchMarca = !marca || v.marca === marca;
                const matchCambio = !cambio || v.cambio === cambio;
                // Nota: O campo 'tipo' pode precisar de mapeamento no seu banco, aqui filtramos se existir
                return matchSearch && matchMarca && matchCambio;
            }});

            renderVehicles(filtered);
        }}

        function openDetail(id) {{
            const v = vehicles.find(x => x.id === id);
            if (!v) return;

            const modalBody = document.getElementById('modalBody');
            modalBody.innerHTML = `
                <div class="modal-gallery">
                    <img src="${{v.images[0]}}" alt="${{v.nome_completo}}">
                </div>
                <div class="modal-details">
                    <div class="card-subtitle">${{v.marca}}</div>
                    <h2 style="font-size: 40px; margin-bottom: 10px;">${{v.modelo}}</h2>
                    <div class="detail-price">${{formatPrice(v.preco_venda)}}</div>
                    
                    <p style="color: var(--text-muted); margin-bottom: 30px;">${{v.history}}</p>
                    
                    <div class="detail-specs">
                        <div class="spec-item">
                            <span class="spec-label">Ano</span>
                            <span class="spec-value">${{v.ano}}</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Quilometragem</span>
                            <span class="spec-value">${{v.km.toLocaleString('pt-BR')}} KM</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Câmbio</span>
                            <span class="spec-value">${{v.cambio}}</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Combustível</span>
                            <span class="spec-value">${{v.combustivel}}</span>
                        </div>
                    </div>

                    <h4 style="text-transform: uppercase; letter-spacing: 2px; font-size: 14px; color: var(--accent);">Opcionais e Destaques</h4>
                    <div class="optionals-list">
                        ${{v.optionals.map(opt => `<div class="optional-item">${{opt}}</div>`).join('')}}
                    </div>

                    <div class="modal-actions">
                        <a href="https://wa.me/5584999999999?text=Olá, tenho interesse no ${{v.nome_completo}}" target="_blank" class="btn-primary" style="flex: 1; text-align: center;">Tenho Interesse</a>
                        <button class="btn-primary" style="background: transparent; border: 1px solid var(--accent); color: var(--accent);" onclick="toggleCompare(${{v.id}}); closeModal();">Comparar</button>
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

        function toggleCompare(id) {{
            const v = vehicles.find(x => x.id === id);
            const index = compareList.findIndex(c => c.id === id);

            if (index > -1) {{
                compareList.splice(index, 1);
            }} else if (compareList.length < 4) {{
                compareList.push(v);
            }} else {{
                alert('Você pode comparar no máximo 4 veículos.');
            }}

            updateCompareBadge();
            renderVehicles(vehicles); // Re-render to update toggle buttons
        }}

        function updateCompareBadge() {{
            const badge = document.getElementById('compareBadge');
            badge.textContent = compareList.length;
            badge.classList.toggle('visible', compareList.length > 0);
        }}

        function openCompare() {{
            if (compareList.length < 2) {{
                alert('Selecione pelo menos 2 veículos para comparar.');
                return;
            }}

            const grid = document.getElementById('compareGrid');
            const rows = [
                {{ label: 'Modelo', key: 'modelo' }},
                {{ label: 'Marca', key: 'marca' }},
                {{ label: 'Preço', key: 'preco_venda', format: formatPrice }},
                {{ label: 'Ano', key: 'ano' }},
                {{ label: 'KM', key: 'km', format: v => v.toLocaleString('pt-BR') + ' KM' }},
                {{ label: 'Câmbio', key: 'cambio' }},
                {{ label: 'Combustível', key: 'combustivel' }},
                {{ label: 'Cor', key: 'cor' }}
            ];

            let html = '';
            
            // Header Row (Images)
            html += `<div class="compare-cell compare-header-cell">Veículo</div>`;
            compareList.forEach(v => {{
                html += `
                    <div class="compare-cell" style="flex-direction: column; align-items: flex-start;">
                        <img src="${{v.images[0]}}" style="width: 100%; height: 120px; object-fit: cover; margin-bottom: 10px;">
                        <div style="font-weight: 700;">${{v.nome_completo}}</div>
                    </div>
                `;
            }});

            // Data Rows
            rows.forEach(row => {{
                html += `<div class="compare-cell compare-header-cell">${{row.label}}</div>`;
                compareList.forEach(v => {{
                    const val = row.format ? row.format(v[row.key]) : v[row.key];
                    html += `<div class="compare-cell">${{val}}</div>`;
                }});
            }});

            grid.style.gridTemplateColumns = `200px repeat(${{compareList.length}}, 1fr)`;
            grid.innerHTML = html;
            document.getElementById('comparePage').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeCompare() {{
            document.getElementById('comparePage').classList.remove('active');
            document.body.style.overflow = 'auto';
        }}

        // Initial Render
        renderVehicles(vehicles);

        // Close modal on click outside
        window.onclick = function(event) {{
            const modal = document.getElementById('detailModal');
            if (event.target == modal) closeModal();
        }}
    </script>
</body>
</html>'''
    return render_template_string(html_template)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
