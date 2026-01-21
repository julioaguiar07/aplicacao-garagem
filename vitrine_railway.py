# vitrine_railway.py
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
            # String com \xffd8... (hex string)
            if foto_data.startswith('\\x'):
                # Remove \x e converte hex para bytes
                try:
                    hex_str = foto_data.replace('\\x', '')
                    bytes_data = bytes.fromhex(hex_str)
                    return base64.b64encode(bytes_data).decode('utf-8')
                except:
                    return None
            
            # Se já for base64
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
            # PostgreSQL
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    v.id, v.marca, v.modelo, v.ano, v.cor, v.preco_venda,
                    v.km, v.combustivel, v.cambio, v.portas, v.placa,
                    v.chassi, v.observacoes, v.foto,
                    v.data_cadastro, v.status,
                    COALESCE(v.margem_negociacao, 30) as margem_negociacao
                FROM veiculos v
                WHERE v.status = 'Em estoque'
                ORDER BY v.data_cadastro DESC
            ''')
            rows = cursor.fetchall()
            veiculos = [dict(row) for row in rows]
        else:
            # SQLite
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    v.id, v.marca, v.modelo, v.ano, v.cor, v.preco_venda,
                    v.km, v.combustivel, v.cambio, v.portas, v.placa,
                    v.chassi, v.observacoes, v.foto,
                    v.data_cadastro, v.status,
                    COALESCE(v.margem_negociacao, 30) as margem_negociacao
                FROM veiculos v
                WHERE v.status = 'Em estoque'
                ORDER BY v.data_cadastro DESC
            ''')
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            veiculos = [dict(zip(columns, row)) for row in rows]
        
        # Processar dados
        for veiculo in veiculos:
            # Converter decimais
            if 'preco_venda' in veiculo:
                veiculo['preco_venda'] = float(veiculo['preco_venda'])
            
            # Processar foto
            veiculo['foto_base64'] = processar_foto(veiculo.get('foto'))
            
            # Garantir tipos corretos
            veiculo['km'] = int(veiculo.get('km', 0)) if veiculo.get('km') else 0
            veiculo['portas'] = int(veiculo.get('portas', 4)) if veiculo.get('portas') else 4
            veiculo['ano'] = int(veiculo.get('ano', 2023)) if veiculo.get('ano') else 2023
        
        return veiculos
        
    except Exception as e:
        print(f"❌ Erro ao buscar veículos: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_logo_base64():
    """Tenta carregar logo local ou usa placeholder"""
    try:
        # Tentar vários caminhos possíveis
        possible_paths = [
            "logoca.png",
            "./logoca.png",
            "/app/logoca.png",
            "logo-icon.png",
            "./logo-icon.png"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Não foi possível carregar logo: {e}")
    
    return None

def get_timbrado_base64():
    """Tenta carregar papel timbrado"""
    try:
        if os.path.exists("papeltimbrado.png"):
            with open("papeltimbrado.png", "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
    except:
        pass
    return None

# =============================================
# ROTAS DA API
# =============================================
@app.route('/api/veiculos')
def api_veiculos():
    """API JSON para veículos"""
    veiculos = get_veiculos_estoque()
    return jsonify(veiculos)

@app.route('/api/health')
def health():
    """Endpoint de saúde"""
    return jsonify({
        "status": "healthy",
        "service": "vitrine-garagem",
        "timestamp": datetime.now().isoformat(),
        "veiculos_estoque": len(get_veiculos_estoque()),
        "database": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
    })

@app.route('/api/stats')
def stats():
    """Estatísticas da vitrine"""
    veiculos = get_veiculos_estoque()
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
# ROTA PRINCIPAL - COM SEU HTML PREMIUM
# =============================================
@app.route('/')
def home():
    """Página principal da vitrine premium"""
    veiculos = get_veiculos_estoque()
    logo_base64 = get_logo_base64()
    timbrado_base64 = get_timbrado_base64()
    
    # Estatísticas
    total_veiculos = len(veiculos)
    valor_total = sum(v['preco_venda'] for v in veiculos)
    media_preco = valor_total / total_veiculos if total_veiculos > 0 else 0
    
    # Agrupar marcas para filtros
    marcas = sorted(list(set(v['marca'] for v in veiculos))) if veiculos else []
    
    # Converter veículos para JSON seguro
    veiculos_json = json.dumps(veiculos, default=str, ensure_ascii=False)
    
    # SEU HTML PREMIUM COMPLETO - COM DADOS DINÂMICOS
    html_template = f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carmelo Multimarcas - Veículos Premium</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,{logo_base64 if logo_base64 else ''}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --primary: #e88e1b;
            --primary-dark: #c77916;
            --secondary: #f4c220;
            --dark: #1a1a1a;
            --gray: #6c757d;
            --light-gray: #f8f9fa;
            --shadow: 0 4px 20px rgba(0,0,0,0.08);
            --shadow-hover: 0 12px 40px rgba(232, 142, 27, 0.15);
        }}

        body {{
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: var(--dark);
            line-height: 1.6;
        }}

        /* HEADER PREMIUM */
        .header {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            padding: 2rem 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .logo i {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .logo h1 {{
            font-size: 1.8rem;
            color: white;
            font-weight: 800;
        }}

        .header-contact {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}

        .contact-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
        }}

        .contact-item:hover {{
            color: var(--primary);
        }}

        .contact-item i {{
            font-size: 1.2rem;
        }}

        /* HERO SECTION */
        .hero {{
            background: linear-gradient(135deg, rgba(26,26,26,0.95) 0%, rgba(45,45,45,0.9) 100%),
                        url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400"><rect fill="%23e88e1b" opacity="0.1" width="1200" height="400"/></svg>');
            background-size: cover;
            padding: 4rem 2rem;
            text-align: center;
            color: white;
        }}

        .hero h2 {{
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #fff, var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero p {{
            font-size: 1.3rem;
            color: #ddd;
            max-width: 600px;
            margin: 0 auto;
        }}

        /* FILTROS MODERNOS */
        .filters {{
            max-width: 1400px;
            margin: -3rem auto 3rem;
            padding: 0 2rem;
        }}

        .filters-card {{
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: var(--shadow);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }}

        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .filter-group label {{
            font-weight: bold;
            color: var(--dark);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .filter-group select,
        .filter-group input {{
            padding: 0.8rem 1rem;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s;
            background: white;
        }}

        .filter-group select:focus,
        .filter-group input:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(232, 142, 27, 0.1);
        }}

        /* CONTADOR DE RESULTADOS */
        .results-info {{
            max-width: 1400px;
            margin: 0 auto 2rem;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .results-count {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--dark);
        }}

        .results-count span {{
            color: var(--primary);
            font-weight: 800;
        }}

        .sort-dropdown {{
            padding: 0.7rem 1.2rem;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 0.95rem;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .sort-dropdown:hover {{
            border-color: var(--primary);
        }}

        /* GRID DE VEÍCULOS */
        .vehicles-grid {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem 4rem;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}

        .vehicle-card {{
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
        }}

        .vehicle-card:hover {{
            transform: translateY(-12px);
            box-shadow: var(--shadow-hover);
        }}

        .vehicle-image {{
            position: relative;
            width: 100%;
            height: 250px;
            overflow: hidden;
            background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
        }}

        .vehicle-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .vehicle-card:hover .vehicle-image img {{
            transform: scale(1.1);
        }}

        .badge {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85rem;
            box-shadow: 0 4px 12px rgba(232, 142, 27, 0.3);
        }}

        .vehicle-info {{
            padding: 1.5rem;
        }}

        .vehicle-title {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--dark);
            margin-bottom: 0.5rem;
        }}

        .vehicle-subtitle {{
            color: var(--gray);
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .specs-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin: 1.5rem 0;
        }}

        .spec-item {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.7rem;
            background: #f8f9fa;
            border-radius: 10px;
            font-size: 0.9rem;
            color: var(--dark);
        }}

        .spec-item i {{
            color: var(--primary);
            font-size: 1.1rem;
        }}

        .price-section {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 2px solid #f0f0f0;
        }}

        .price {{
            font-size: 2rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .price-label {{
            font-size: 0.8rem;
            color: var(--gray);
            display: block;
            margin-top: -0.5rem;
        }}

        .btn-details {{
            padding: 0.8rem 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.95rem;
        }}

        .btn-details:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(232, 142, 27, 0.4);
        }}

        /* MODAL DE DETALHES */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            overflow-y: auto;
        }}

        .modal.active {{
            display: flex;
        }}

        .modal-content {{
            background: white;
            border-radius: 24px;
            max-width: 1000px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
        }}

        .modal-close {{
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            transition: all 0.3s;
        }}

        .modal-close:hover {{
            background: var(--primary);
            transform: rotate(90deg);
        }}

        .modal-gallery {{
            position: relative;
            height: 400px;
            background: #000;
        }}

        .modal-gallery img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}

        .modal-body {{
            padding: 2rem;
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 2rem;
        }}

        .modal-title h2 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }}

        .modal-price {{
            text-align: right;
        }}

        .modal-price .price {{
            font-size: 2.5rem;
        }}

        .specs-full {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}

        .spec-full {{
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }}

        .spec-full-label {{
            font-size: 0.85rem;
            color: var(--gray);
            margin-bottom: 0.3rem;
        }}

        .spec-full-value {{
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--dark);
        }}

        .contact-section {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 2rem;
            border-radius: 16px;
            color: white;
            margin-top: 2rem;
        }}

        .contact-buttons {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .btn-contact {{
            padding: 1rem 1.5rem;
            background: white;
            color: var(--primary);
            border: none;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.7rem;
            font-size: 1rem;
        }}

        .btn-contact:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        }}

        /* BOTÃO WHATSAPP FLUTUANTE */
        .whatsapp-float {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 70px;
            height: 70px;
            background: #25D366;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 24px rgba(37, 211, 102, 0.4);
            cursor: pointer;
            z-index: 999;
            transition: all 0.3s;
            text-decoration: none;
        }}

        .whatsapp-float:hover {{
            transform: scale(1.15);
            box-shadow: 0 8px 32px rgba(37, 211, 102, 0.6);
        }}

        .whatsapp-float i {{
            font-size: 2.5rem;
            color: white;
        }}

        /* FOOTER */
        .footer {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: white;
            padding: 3rem 2rem 1rem;
            margin-top: 4rem;
        }}

        .footer-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
        }}

        .footer-section h3 {{
            color: var(--primary);
            margin-bottom: 1rem;
        }}

        .footer-section p,
        .footer-section a {{
            color: #aaa;
            text-decoration: none;
            display: block;
            margin-bottom: 0.5rem;
        }}

        .footer-section a:hover {{
            color: var(--primary);
        }}

        .footer-bottom {{
            text-align: center;
            color: #666;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid #333;
        }}

        /* LOADING */
        .loading {{
            text-align: center;
            padding: 4rem 2rem;
        }}

        .spinner {{
            width: 50px;
            height: 50px;
            margin: 0 auto 1rem;
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* RESPONSIVE */
        @media (max-width: 768px) {{
            .hero h2 {{
                font-size: 2rem;
            }}

            .vehicles-grid {{
                grid-template-columns: 1fr;
            }}

            .filters-card {{
                grid-template-columns: 1fr;
            }}

            .header-contact {{
                display: none;
            }}

            .modal-content {{
                margin: 1rem;
            }}
        }}

        /* NO RESULTS */
        .no-results {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem 2rem;
            background: white;
            border-radius: 20px;
            box-shadow: var(--shadow);
        }}

        .no-results i {{
            font-size: 4rem;
            color: var(--gray);
            margin-bottom: 1.5rem;
        }}

        .no-results h3 {{
            font-size: 1.5rem;
            color: var(--dark);
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <!-- HEADER -->
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <img src="data:image/png;base64,{logo_base64}" alt="Logo Carmelo" style="height: 60px; width: auto; border-radius: 8px; object-fit: contain;">
                    <h1 style="margin: 0; font-size: 1.8rem; background: linear-gradient(135deg, #fff, var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">Carmelo Multimarcas</h1>
                </div>
            </div>
            <div class="header-contact">
                <a href="tel:+5584991359875" class="contact-item">
                    <i class="fas fa-phone"></i>
                    <span>(84) 3062-2434</span>
                </a>
                <a href="https://wa.me/5584991359875" class="contact-item" target="_blank">
                    <i class="fab fa-whatsapp"></i>
                    <span>WhatsApp</span>
                </a>
            </div>
        </div>
    </header>

    <!-- HERO -->
    <section class="hero">
        <h2>Encontre Seu Próximo Veículo</h2>
        <p>Qualidade, confiança e as melhores condições do mercado</p>
    </section>

    <!-- FILTROS -->
    <section class="filters">
        <div class="filters-card">
            <div class="filter-group">
                <label><i class="fas fa-tag"></i> Marca</label>
                <select id="filterMarca">
                    <option value="">Todas as marcas</option>
                    {' '.join([f'<option value="{marca}">{marca}</option>' for marca in marcas])}
                </select>
            </div>
            <div class="filter-group">
                <label><i class="fas fa-dollar-sign"></i> Preço máximo</label>
                <input type="number" id="filterPreco" placeholder="R$ 0,00">
            </div>
            <div class="filter-group">
                <label><i class="fas fa-gas-pump"></i> Combustível</label>
                <select id="filterCombustivel">
                    <option value="">Todos</option>
                    <option value="Gasolina">Gasolina</option>
                    <option value="Álcool">Álcool</option>
                    <option value="Flex">Flex</option>
                    <option value="Diesel">Diesel</option>
                </select>
            </div>
            <div class="filter-group">
                <label><i class="fas fa-cogs"></i> Câmbio</label>
                <select id="filterCambio">
                    <option value="">Todos</option>
                    <option value="Automático">Automático</option>
                    <option value="Manual">Manual</option>
                </select>
            </div>
        </div>
    </section>

    <!-- RESULTADOS -->
    <div class="results-info">
        <div class="results-count">
            <span id="vehicleCount">{total_veiculos}</span> veículos disponíveis
        </div>
        <select class="sort-dropdown" id="sortBy">
            <option value="recent">Mais recentes</option>
            <option value="price-low">Menor preço</option>
            <option value="price-high">Maior preço</option>
            <option value="km">Menor KM</option>
        </select>
    </div>

    <!-- GRID DE VEÍCULOS -->
    <div class="vehicles-grid" id="vehiclesGrid">
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Carregando veículos...</p>
        </div>
    </div>

    <!-- MODAL DE DETALHES -->
    <div class="modal" id="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">
                <i class="fas fa-times"></i>
            </button>
            <div class="modal-gallery" id="modalGallery"></div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <!-- WHATSAPP FLUTUANTE -->
    <a href="https://wa.me/5584991359875?text=Olá! Gostaria de informações sobre os veículos" 
       class="whatsapp-float" target="_blank" title="Fale conosco no WhatsApp">
        <i class="fab fa-whatsapp"></i>
    </a>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3>Carmelo Multimarcas</h3>
                <p>Veículos de qualidade com procedência garantida</p>
            </div>
            <div class="footer-section">
                <h3>Contato</h3>
                <p><i class="fas fa-phone"></i> (84) 3062-2434</p>
                <p><i class="fas fa-envelope"></i> contato@garagemmultimarcas.com.br</p>
                <p><i class="fas fa-map-marker-alt"></i> Mossoró/RN</p>
            </div>
            <div class="footer-section">
                <h3>Horário de Atendimento</h3>
                <p>Segunda a Sexta: 8h às 18h</p>
                <p>Sábado: 8h às 12h</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; {datetime.now().year} Carmelo Multimarcas. Todos os direitos reservados.</p>
        </div>
    </footer>

    <script>
        // CONFIGURAÇÃO
        const WHATSAPP_NUMBER = '558430622434';
        let vehicles = {veiculos_json};
        let filteredVehicles = [...vehicles];

        // INICIALIZAR
        document.addEventListener('DOMContentLoaded', function() {{
            initApp();
        }});

        function initApp() {{
            if (vehicles && vehicles.length > 0) {{
                document.getElementById('loading').style.display = 'none';
                renderVehicles();
            }} else {{
                document.getElementById('loading').innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-car"></i>
                        <h3>Nenhum veículo disponível</h3>
                        <p>Volte em breve para conferir nossas novidades!</p>
                    </div>
                `;
            }}
            
            setupEventListeners();
        }}

        function setupEventListeners() {{
            // Filtros
            document.getElementById('filterMarca').addEventListener('change', applyFilters);
            document.getElementById('filterPreco').addEventListener('input', applyFilters);
            document.getElementById('filterCombustivel').addEventListener('change', applyFilters);
            document.getElementById('filterCambio').addEventListener('change', applyFilters);
            document.getElementById('sortBy').addEventListener('change', () => {{
                sortVehicles();
                renderVehicles();
            }});
            
            // Modal
            document.getElementById('modal').addEventListener('click', (e) => {{
                if (e.target.id === 'modal') closeModal();
            }});
            
            // Fechar modal com ESC
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'Escape') closeModal();
            }});
        }}

        function renderVehicles() {{
            const grid = document.getElementById('vehiclesGrid');
            document.getElementById('vehicleCount').textContent = filteredVehicles.length;
            
            if (filteredVehicles.length === 0) {{
                grid.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <h3>Nenhum veículo encontrado</h3>
                        <p>Tente ajustar os filtros de busca.</p>
                        <button class="btn-details" onclick="resetFilters()" style="margin-top: 1rem;">
                            Limpar Filtros
                        </button>
                    </div>
                `;
                return;
            }}

            grid.innerHTML = filteredVehicles.map(vehicle => `
                <div class="vehicle-card" onclick="openModal(${{vehicle.id}})">
                    <div class="vehicle-image">
                        ${{vehicle.foto_base64 ? 
                            `<img src="data:image/jpeg;base64,${{vehicle.foto_base64}}" alt="${{vehicle.marca}} ${{vehicle.modelo}}">` :
                            '<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 5rem; color: #ccc;"><i class="fas fa-car"></i></div>'
                        }}
                        <div class="badge">Disponível</div>
                    </div>
                    <div class="vehicle-info">
                        <h3 class="vehicle-title">${{vehicle.marca}} ${{vehicle.modelo}}</h3>
                        <div class="vehicle-subtitle">
                            <span>${{vehicle.ano}}</span>
                            <span>•</span>
                            <span>${{vehicle.cor}}</span>
                        </div>
                        <div class="specs-grid">
                            <div class="spec-item">
                                <i class="fas fa-road"></i>
                                <span>${{vehicle.km.toLocaleString('pt-BR')}} km</span>
                            </div>
                            <div class="spec-item">
                                <i class="fas fa-gas-pump"></i>
                                <span>${{vehicle.combustivel}}</span>
                            </div>
                            <div class="spec-item">
                                <i class="fas fa-cog"></i>
                                <span>${{vehicle.cambio}}</span>
                            </div>
                            <div class="spec-item">
                                <i class="fas fa-door-closed"></i>
                                <span>${{vehicle.portas}} portas</span>
                            </div>
                        </div>
                        <div class="price-section">
                            <div>
                                <div class="price">R$ ${{vehicle.preco_venda.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</div>
                                <span class="price-label">à vista</span>
                            </div>
                            <button class="btn-details" onclick="event.stopPropagation(); openModal(${{vehicle.id}})">
                                Ver Detalhes
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function applyFilters() {{
            const marca = document.getElementById('filterMarca').value;
            const preco = parseFloat(document.getElementById('filterPreco').value) || Infinity;
            const combustivel = document.getElementById('filterCombustivel').value;
            const cambio = document.getElementById('filterCambio').value;

            filteredVehicles = vehicles.filter(v => {{
                return (!marca || v.marca === marca) &&
                       v.preco_venda <= preco &&
                       (!combustivel || v.combustivel === combustivel) &&
                       (!cambio || v.cambio === cambio);
            }});

            sortVehicles();
            renderVehicles();
        }}

        function resetFilters() {{
            document.getElementById('filterMarca').value = '';
            document.getElementById('filterPreco').value = '';
            document.getElementById('filterCombustivel').value = '';
            document.getElementById('filterCambio').value = '';
            document.getElementById('sortBy').value = 'recent';
            
            filteredVehicles = [...vehicles];
            sortVehicles();
            renderVehicles();
        }}

        function sortVehicles() {{
            const sortBy = document.getElementById('sortBy').value;
            
            switch(sortBy) {{
                case 'price-low':
                    filteredVehicles.sort((a, b) => a.preco_venda - b.preco_venda);
                    break;
                case 'price-high':
                    filteredVehicles.sort((a, b) => b.preco_venda - a.preco_venda);
                    break;
                case 'km':
                    filteredVehicles.sort((a, b) => a.km - b.km);
                    break;
            }}
        }}

        function openModal(vehicleId) {{
            const vehicle = vehicles.find(v => v.id == vehicleId);
            if (!vehicle) return;

            const modal = document.getElementById('modal');
            const gallery = document.getElementById('modalGallery');
            const body = document.getElementById('modalBody');

            // Galeria
            gallery.innerHTML = vehicle.foto_base64 ?
                `<img src="data:image/jpeg;base64,${{vehicle.foto_base64}}" alt="${{vehicle.marca}} ${{vehicle.modelo}}">` :
                '<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 8rem; color: #666;"><i class="fas fa-car"></i></div>';

            // Mensagem WhatsApp
            const whatsappMsg = encodeURIComponent(`Olá! Tenho interesse no ${{vehicle.marca}} ${{vehicle.modelo}} ${{vehicle.ano}} - R$ ${{vehicle.preco_venda.toLocaleString('pt-BR')}}. Poderia me passar mais informações?`);
            
            body.innerHTML = `
                <div class="modal-header">
                    <div class="modal-title">
                        <h2>${{vehicle.marca}} ${{vehicle.modelo}}</h2>
                        <p style="color: var(--gray); font-size: 1.2rem;">${{vehicle.ano}} • ${{vehicle.cor}} • ${{vehicle.placa || 'Placa não informada'}}</p>
                    </div>
                    <div class="modal-price">
                        <div class="price">R$ ${{vehicle.preco_venda.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</div>
                        <span class="price-label">Preço à vista</span>
                    </div>
                </div>

                <div class="specs-full">
                    <div class="spec-full">
                        <div class="spec-full-label">Quilometragem</div>
                        <div class="spec-full-value"><i class="fas fa-road"></i> ${{vehicle.km.toLocaleString('pt-BR')}} km</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label">Combustível</div>
                        <div class="spec-full-value"><i class="fas fa-gas-pump"></i> ${{vehicle.combustivel}}</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label">Câmbio</div>
                        <div class="spec-full-value"><i class="fas fa-cog"></i> ${{vehicle.cambio}}</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label">Portas</div>
                        <div class="spec-full-value"><i class="fas fa-door-closed"></i> ${{vehicle.portas}} portas</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label">Placa</div>
                        <div class="spec-full-value"><i class="fas fa-id-card"></i> ${{vehicle.placa || 'Não informada'}}</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label">Cor</div>
                        <div class="spec-full-value"><i class="fas fa-palette"></i> ${{vehicle.cor}}</div>
                    </div>
                </div>

                ${{vehicle.observacoes ? `
                    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; margin: 2rem 0;">
                        <h4 style="margin-bottom: 1rem; color: var(--primary);"><i class="fas fa-clipboard-list"></i> Observações</h4>
                        <p style="color: var(--gray); line-height: 1.6;">${{vehicle.observacoes}}</p>
                    </div>
                ` : ''}}

                <div class="contact-section">
                    <h3 style="margin-bottom: 0.5rem;">💬 Entre em Contato</h3>
                    <p>Fale conosco e agende uma visita para conhecer este veículo pessoalmente</p>
                    
                    <div class="contact-buttons">
                        <a href="https://wa.me/${{WHATSAPP_NUMBER}}?text=${{whatsappMsg}}" target="_blank" style="text-decoration: none;">
                            <button class="btn-contact" style="background: #25D366; color: white;">
                                <i class="fab fa-whatsapp"></i>
                                Falar no WhatsApp
                            </button>
                        </a>
                        <a href="tel:+${{WHATSAPP_NUMBER}}" style="text-decoration: none;">
                            <button class="btn-contact">
                                <i class="fas fa-phone"></i>
                                Ligar Agora
                            </button>
                        </a>
                        <button class="btn-contact" onclick="closeModal()" style="background: #6c757d; color: white;">
                            <i class="fas fa-times"></i>
                            Fechar
                        </button>
                    </div>
                </div>
            `;

            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal() {{
            document.getElementById('modal').classList.remove('active');
            document.body.style.overflow = 'auto';
        }}
    </script>
</body>
</html>
'''
    
    return render_template_string(html_template)

# =============================================
# INICIALIZAÇÃO
# =============================================
if __name__ == "__main__":
    # Modo desenvolvimento local
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print("CATÁLOGO - CARMELO MULTIMARCAS")
    print("=" * 60)
    print(f"🌐 Modo: {'Produção (Railway)' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Desenvolvimento'}")
    print(f"🔧 Porta: {port}")
    print(f"🗄️  Banco: {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite'}")
    print("=" * 60)
    
    # Só roda servidor de desenvolvimento se não estiver no Railway
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        print("⚡ Iniciando servidor de desenvolvimento...")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("✅ Pronto para produção com Gunicorn")
        print(f"🔗 A aplicação será servida pelo Gunicorn na porta {port}")
