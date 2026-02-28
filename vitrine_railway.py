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
            # SQLite
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

        # Processar dados
        marcas_set = set()
        for veiculo in veiculos:
            # Converter preço para float
            veiculo['preco_venda'] = float(veiculo['preco_venda']) if veiculo.get('preco_venda') else 0.0

            # Processar foto
            veiculo['foto_base64'] = processar_foto(veiculo.get('foto'))

            # Garantir tipos corretos
            veiculo['km'] = int(veiculo.get('km', 0)) if veiculo.get('km') else 0
            veiculo['portas'] = int(veiculo.get('portas', 4)) if veiculo.get('portas') else 4
            veiculo['ano'] = int(veiculo.get('ano', 2023)) if veiculo.get('ano') else 2023

            # Criar nome completo para exibição
            veiculo['nome_completo'] = f"{veiculo['marca']} {veiculo['modelo']}"
            
            # Versão (para manter compatibilidade com o template)
            veiculo['version'] = f"{veiculo['ano']} • {veiculo['combustivel']}"
            
            # Opcionais (simulados baseados em observações)
            veiculo['optionals'] = []
            if veiculo.get('observacoes'):
                # Quebrar observações em itens se houver vírgulas
                if ',' in veiculo['observacoes']:
                    veiculo['optionals'] = [item.strip() for item in veiculo['observacoes'].split(',')[:8]]
                else:
                    veiculo['optionals'] = [veiculo['observacoes']] if veiculo['observacoes'] else []
            
            # Adicionar itens padrão para enriquecer
            veiculo['optionals'].extend([
                f"Cambio {veiculo['cambio']}",
                f"{veiculo['combustivel']}",
                f"{veiculo['portas']} portas"
            ])
            
            # Remover duplicatas
            veiculo['optionals'] = list(dict.fromkeys(veiculo['optionals']))[:10]
            
            # Histórico simulado
            veiculo['history'] = f"Veículo {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} em excelente estado. Documentação em dia, único dono, revisões em concessionária autorizada." if veiculo['km'] < 50000 else f"Veículo {veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} com {veiculo['km']} km rodados. Bem conservado, pronto para uso."
            
            # Badge baseado em condições
            if veiculo['km'] < 10000:
                veiculo['badge'] = 'new'
                veiculo['badgeText'] = 'Zero Km'
            elif veiculo['km'] < 30000:
                veiculo['badge'] = 'deal'
                veiculo['badgeText'] = 'Seminovo'
            else:
                veiculo['badge'] = None
                veiculo['badgeText'] = ''
            
            # Potência simulada (para manter compatibilidade)
            veiculo['power'] = '180 cv'  # Padrão, você pode ajustar se tiver esse dado no banco
            
            # Criar array de imagens (apenas a foto disponível)
            if veiculo['foto_base64']:
                veiculo['images'] = [f"data:image/jpeg;base64,{veiculo['foto_base64']}"] * 2  # Duplicar para ter mais de uma
            else:
                # Imagens placeholder
                veiculo['images'] = [
                    "https://images.unsplash.com/photo-1503736334956-4c8f8e92946d?w=800&q=80",
                    "https://images.unsplash.com/photo-1549317661-bd32c8ce0729?w=800&q=80"
                ]
            
            # Adicionar marca ao set
            marcas_set.add(veiculo['marca'])

        return veiculos, sorted(list(marcas_set))

    except Exception as e:
        print(f"❌ Erro ao buscar veículos: {e}")
        return [], []
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

# =============================================
# ROTAS DA API
# =============================================
@app.route('/api/veiculos')
def api_veiculos():
    """API JSON para veículos"""
    veiculos, _ = get_veiculos_estoque()
    return jsonify(veiculos)

@app.route('/api/health')
def health():
    """Endpoint de saúde"""
    veiculos, _ = get_veiculos_estoque()
    return jsonify({
        "status": "healthy",
        "service": "vitrine-premium-carmelo",
        "timestamp": datetime.now().isoformat(),
        "veiculos_estoque": len(veiculos),
        "database": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
    })

@app.route('/api/stats')
def stats():
    """Estatísticas da vitrine"""
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
# ROTA PRINCIPAL - COM HTML PREMIUM ADAPTADO
# =============================================
@app.route('/')
def home():
    """Página principal da vitrine premium"""
    veiculos, marcas = get_veiculos_estoque()
    logo_base64 = get_logo_base64()

    # Estatísticas
    total_veiculos = len(veiculos)
    valor_total = sum(v['preco_venda'] for v in veiculos)
    media_preco = valor_total / total_veiculos if total_veiculos > 0 else 0

    # Converter veículos para JSON seguro
    veiculos_json = json.dumps(veiculos, default=str, ensure_ascii=False)

    # Lista de opções para filtros
    tipos = ["SUV", "Sedan", "Hatch", "Picape", "Coupé", "Elétrico"]
    transmissoes = ["Automático", "Manual", "CVT"]
    combustiveis = list(set(v['combustivel'] for v in veiculos if v.get('combustivel'))) or ["Flex", "Gasolina", "Diesel"]
    cores = list(set(v['cor'] for v in veiculos if v.get('cor'))) or ["Preto", "Branco", "Prata", "Cinza", "Vermelho", "Azul"]

    # HTML PREMIUM COMPLETO ADAPTADO
    html_template = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Carmelo Multimarcas | Veículos Premium</title>
<meta name="description" content="Carmelo Multimarcas - Os melhores veículos seminovos com qualidade e confiança garantidas em Mossoró/RN.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;500;600;700;900&family=Barlow+Condensed:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --orange: #e88e1b;
  --orange-bright: #f4c220;
  --orange-glow: rgba(232,142,27,0.3);
  --black: #0A0A0A;
  --dark: #111111;
  --dark2: #1A1A1A;
  --dark3: #222222;
  --dark4: #2A2A2A;
  --gray: #555555;
  --gray-light: #888888;
  --white: #FFFFFF;
  --white-dim: rgba(255,255,255,0.85);
  --white-soft: rgba(255,255,255,0.6);
  --white-ghost: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.1);
  --border-orange: rgba(232,142,27,0.4);
  --radius: 12px;
  --radius-sm: 8px;
  --transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior: smooth; }}

body {{
  font-family: 'Barlow', sans-serif;
  background: var(--black);
  color: var(--white);
  overflow-x: hidden;
}}

/* SCROLLBAR */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--dark); }}
::-webkit-scrollbar-thumb {{ background: var(--orange); border-radius: 3px; }}

/* ===== HEADER ===== */
#header {{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
  background: rgba(10,10,10,0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  transition: var(--transition);
}}

.header-inner {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 70px;
  display: flex;
  align-items: center;
  gap: 32px;
}}

.logo {{
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
}}

.logo-icon {{
  width: 42px;
  height: 42px;
  background: var(--orange);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-family: 'Bebas Neue', sans-serif;
  color: white;
  letter-spacing: -1px;
}}

.logo-text {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 26px;
  letter-spacing: 2px;
  color: var(--white);
  line-height: 1;
}}

.logo-text span {{ color: var(--orange); }}

nav {{ display: flex; align-items: center; gap: 4px; }}

nav a {{
  padding: 8px 14px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.5px;
  color: var(--white-soft);
  transition: var(--transition);
  white-space: nowrap;
  text-transform: uppercase;
}}

nav a:hover {{ color: var(--white); background: var(--white-ghost); }}
nav a.active {{ color: var(--orange); }}

.compare-btn {{
  position: relative;
  color: var(--white-soft) !important;
}}

.compare-count {{
  position: absolute;
  top: 2px; right: 2px;
  width: 18px; height: 18px;
  background: var(--orange);
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  display: none;
}}

.compare-count.visible {{ display: flex; }}

.search-bar {{
  flex: 1;
  max-width: 380px;
  margin-left: auto;
  position: relative;
}}

.search-bar input {{
  width: 100%;
  padding: 10px 42px 10px 16px;
  background: var(--dark3);
  border: 1px solid var(--border);
  border-radius: 50px;
  color: var(--white);
  font-size: 13px;
  font-family: 'Barlow', sans-serif;
  outline: none;
  transition: var(--transition);
}}

.search-bar input:focus {{
  border-color: var(--orange);
  background: var(--dark2);
  box-shadow: 0 0 0 3px var(--orange-glow);
}}

.search-bar input::placeholder {{ color: var(--gray); }}

.search-bar svg {{
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray);
  pointer-events: none;
}}

.hamburger {{
  display: none;
  flex-direction: column;
  gap: 5px;
  cursor: pointer;
  padding: 8px;
  border: none;
  background: transparent;
}}

.hamburger span {{
  display: block;
  width: 24px;
  height: 2px;
  background: var(--white);
  border-radius: 2px;
  transition: var(--transition);
}}

/* ===== HERO BANNER ===== */
.hero {{
  margin-top: 70px;
  height: 420px;
  background: linear-gradient(135deg, var(--dark) 0%, var(--dark2) 50%, #1a0a00 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
}}

.hero::before {{
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(232,142,27,0.15) 0%, transparent 70%);
  pointer-events: none;
}}

.hero::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  pointer-events: none;
}}

.hero-content {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  position: relative;
  z-index: 1;
}}

.hero-tag {{
  display: inline-block;
  background: var(--orange);
  color: white;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}}

.hero h1 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(52px, 8vw, 96px);
  line-height: 0.9;
  letter-spacing: 3px;
  margin-bottom: 20px;
}}

.hero h1 span {{ color: var(--orange); }}

.hero p {{
  font-size: 16px;
  color: var(--white-soft);
  max-width: 480px;
  line-height: 1.6;
  margin-bottom: 28px;
}}

.hero-stats {{
  display: flex;
  gap: 36px;
}}

.hero-stat strong {{
  display: block;
  font-family: 'Bebas Neue', sans-serif;
  font-size: 36px;
  color: var(--orange);
  line-height: 1;
}}

.hero-stat span {{
  font-size: 12px;
  color: var(--white-soft);
  text-transform: uppercase;
  letter-spacing: 1px;
}}

/* ===== MAIN LAYOUT ===== */
.main-layout {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 28px;
}}

/* ===== FILTERS SIDEBAR ===== */
.sidebar {{
  position: sticky;
  top: 90px;
  height: fit-content;
  max-height: calc(100vh - 110px);
  overflow-y: auto;
}}

.sidebar::-webkit-scrollbar {{ width: 4px; }}

.filter-panel {{
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}}

.filter-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}}

.filter-header h3 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 20px;
  letter-spacing: 2px;
  color: var(--white);
}}

.clear-filters {{
  font-size: 11px;
  color: var(--orange);
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
  border: none;
  background: none;
  padding: 4px 8px;
  border-radius: 4px;
  transition: var(--transition);
}}

.clear-filters:hover {{ background: var(--orange-glow); }}

.filter-group {{ margin-bottom: 24px; }}

.filter-group label {{
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--gray-light);
  margin-bottom: 10px;
}}

.filter-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}

.chip {{
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 50px;
  font-size: 12px;
  font-weight: 500;
  color: var(--white-soft);
  cursor: pointer;
  transition: var(--transition);
  user-select: none;
}}

.chip:hover {{ border-color: var(--orange); color: var(--orange); }}
.chip.active {{ background: var(--orange); border-color: var(--orange); color: white; }}

.range-group {{ display: flex; flex-direction: column; gap: 8px; }}

.range-inputs {{
  display: flex;
  gap: 8px;
}}

.range-inputs input {{
  flex: 1;
  padding: 8px 10px;
  background: var(--dark3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--white);
  font-size: 12px;
  font-family: 'Barlow', sans-serif;
  outline: none;
  transition: var(--transition);
}}

.range-inputs input:focus {{
  border-color: var(--orange);
}}

.range-slider {{
  position: relative;
  height: 4px;
  background: var(--dark4);
  border-radius: 2px;
  margin: 10px 4px;
}}

.range-slider-track {{
  position: absolute;
  height: 100%;
  background: var(--orange);
  border-radius: 2px;
}}

input[type="range"] {{
  position: absolute;
  width: 100%;
  height: 4px;
  opacity: 0;
  cursor: pointer;
  top: 0;
  left: 0;
  pointer-events: none;
}}

.filter-select {{
  width: 100%;
  padding: 10px 12px;
  background: var(--dark3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--white);
  font-size: 13px;
  font-family: 'Barlow', sans-serif;
  outline: none;
  cursor: pointer;
  transition: var(--transition);
  appearance: none;
}}

.filter-select:focus {{ border-color: var(--orange); }}
.filter-select option {{ background: var(--dark3); }}

/* ===== CONTENT AREA ===== */
.content-area {{}}

.content-toolbar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}}

.results-info {{
  font-size: 14px;
  color: var(--white-soft);
}}

.results-info strong {{ color: var(--orange); }}

.toolbar-right {{
  display: flex;
  align-items: center;
  gap: 10px;
}}

.sort-select {{
  padding: 8px 14px;
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--white);
  font-size: 13px;
  font-family: 'Barlow', sans-serif;
  outline: none;
  cursor: pointer;
}}

.sort-select option {{ background: var(--dark2); }}

.view-toggle {{ display: flex; gap: 4px; }}

.view-btn {{
  width: 36px; height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--dark2);
  color: var(--gray-light);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}}

.view-btn.active {{ border-color: var(--orange); color: var(--orange); background: var(--orange-glow); }}

/* ===== VEHICLE GRID ===== */
.vehicle-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}}

.vehicle-grid.list-view {{
  grid-template-columns: 1fr;
}}

/* ===== VEHICLE CARD ===== */
.vehicle-card {{
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: var(--transition);
  cursor: pointer;
  position: relative;
  animation: fadeInUp 0.4s ease both;
}}

@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(20px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

.vehicle-card:hover {{
  transform: translateY(-4px);
  border-color: var(--border-orange);
  box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px var(--border-orange);
}}

.card-badges {{
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

.badge {{
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}}

.badge-new {{ background: #00C851; color: white; }}
.badge-deal {{ background: var(--orange); color: white; }}
.badge-sale {{ background: #E91E63; color: white; }}

.compare-toggle {{
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
  width: 30px; height: 30px;
  border-radius: 6px;
  background: rgba(0,0,0,0.6);
  border: 1px solid var(--border);
  color: var(--white-soft);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  backdrop-filter: blur(4px);
}}

.compare-toggle:hover {{ border-color: var(--orange); color: var(--orange); }}
.compare-toggle.active {{ background: var(--orange); border-color: var(--orange); color: white; }}

.card-image-wrapper {{
  overflow: hidden;
  position: relative;
  height: 180px;
}}

.card-image {{
  width: 100%;
  height: 180px;
  object-fit: cover;
  display: block;
  transition: transform 0.5s ease;
  background: var(--dark3);
}}

.vehicle-card:hover .card-image {{ transform: scale(1.03); }}

.card-body {{
  padding: 16px;
}}

.card-name {{
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: var(--white);
  margin-bottom: 12px;
  line-height: 1.2;
  letter-spacing: 0.3px;
}}

.card-specs {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 14px;
}}

.card-spec {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--gray-light);
}}

.card-spec svg {{ color: var(--orange); flex-shrink: 0; }}

.card-spec span {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

.card-price {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 28px;
  color: var(--orange);
  letter-spacing: 1px;
  line-height: 1;
  margin-bottom: 14px;
}}

.card-price-old {{
  font-size: 13px;
  color: var(--gray);
  text-decoration: line-through;
  margin-bottom: 4px;
  font-family: 'Barlow', sans-serif;
}}

.card-actions {{
  display: flex;
  gap: 8px;
}}

.btn-primary {{
  flex: 1;
  padding: 10px 14px;
  background: var(--orange);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: var(--transition);
  font-family: 'Barlow', sans-serif;
}}

.btn-primary:hover {{
  background: var(--orange-bright);
  box-shadow: 0 4px 16px var(--orange-glow);
  transform: translateY(-1px);
}}

.btn-secondary {{
  padding: 10px 12px;
  background: transparent;
  color: var(--white-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-family: 'Barlow', sans-serif;
}}

.btn-secondary:hover {{
  border-color: var(--orange);
  color: var(--orange);
}}

/* ===== MODAL OVERLAY ===== */
.modal-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.85);
  z-index: 2000;
  backdrop-filter: blur(8px);
  animation: fadeIn 0.2s ease;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}

.modal-overlay.active {{ display: flex; align-items: center; justify-content: center; }}

.modal {{
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: 16px;
  max-width: 960px;
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  animation: slideUp 0.3s ease;
}}

@keyframes slideUp {{
  from {{ opacity: 0; transform: translateY(40px) scale(0.97); }}
  to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}

.modal-close {{
  position: absolute;
  top: 16px; right: 16px;
  z-index: 10;
  width: 36px; height: 36px;
  background: var(--dark3);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--white);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}}

.modal-close:hover {{ background: var(--orange); border-color: var(--orange); }}

/* ===== DETAIL MODAL ===== */
.detail-gallery {{
  position: relative;
  height: 340px;
  background: var(--dark3);
  overflow: hidden;
  border-radius: 16px 16px 0 0;
}}

.gallery-main-img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}

.gallery-nav {{
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px; height: 40px;
  background: rgba(0,0,0,0.6);
  border: 1px solid var(--border);
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  backdrop-filter: blur(4px);
}}

.gallery-nav:hover {{ background: var(--orange); border-color: var(--orange); }}
.gallery-prev {{ left: 16px; }}
.gallery-next {{ right: 16px; }}

.gallery-thumbs {{
  display: flex;
  gap: 8px;
  padding: 12px 24px;
  overflow-x: auto;
  background: var(--dark3);
}}

.gallery-thumb {{
  width: 72px;
  height: 52px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: var(--transition);
  flex-shrink: 0;
}}

.gallery-thumb.active {{ border-color: var(--orange); }}

.detail-content {{
  padding: 28px;
}}

.detail-header {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}}

.detail-title h2 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 36px;
  letter-spacing: 2px;
  color: var(--white);
  line-height: 1;
  margin-bottom: 6px;
}}

.detail-title .version {{
  font-size: 14px;
  color: var(--orange);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}}

.detail-price-block {{
  text-align: right;
}}

.detail-price {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 44px;
  color: var(--orange);
  letter-spacing: 2px;
  line-height: 1;
}}

.detail-price-label {{
  font-size: 11px;
  color: var(--gray-light);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 4px;
}}

.detail-specs-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
  background: var(--dark3);
  border-radius: var(--radius);
  padding: 20px;
}}

.detail-spec {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

.detail-spec-label {{
  font-size: 10px;
  color: var(--gray-light);
  text-transform: uppercase;
  letter-spacing: 1px;
}}

.detail-spec-value {{
  font-size: 14px;
  font-weight: 600;
  color: var(--white);
}}

.detail-section {{
  margin-bottom: 20px;
}}

.detail-section h4 {{
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--orange);
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}}

.optionals-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 6px;
}}

.optional-item {{
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--white-soft);
}}

.optional-item::before {{
  content: '';
  width: 6px; height: 6px;
  background: var(--orange);
  border-radius: 50%;
  flex-shrink: 0;
}}

.detail-actions {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}}

.btn-whatsapp {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  background: #25D366;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: var(--transition);
  font-family: 'Barlow', sans-serif;
  text-decoration: none;
}}

.btn-whatsapp:hover {{
  background: #1eb455;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37,211,102,0.3);
}}

.btn-share {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  background: transparent;
  color: var(--white-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  font-family: 'Barlow', sans-serif;
}}

.btn-share:hover {{ border-color: var(--orange); color: var(--orange); }}

.btn-proposal {{
  flex: 1;
  min-width: 180px;
  padding: 14px 24px;
  background: var(--orange);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: var(--transition);
  font-family: 'Barlow', sans-serif;
}}

.btn-proposal:hover {{
  background: var(--orange-bright);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--orange-glow);
}}

/* ===== PROPOSAL MODAL ===== */
.proposal-modal {{
  max-width: 560px;
  padding: 36px;
}}

.proposal-modal h3 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 30px;
  letter-spacing: 2px;
  margin-bottom: 6px;
}}

.proposal-modal p {{
  font-size: 14px;
  color: var(--white-soft);
  margin-bottom: 24px;
}}

.form-group {{
  margin-bottom: 16px;
}}

.form-group label {{
  display: block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--gray-light);
  margin-bottom: 6px;
}}

.form-group input,
.form-group textarea,
.form-group select {{
  width: 100%;
  padding: 12px 14px;
  background: var(--dark3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--white);
  font-size: 14px;
  font-family: 'Barlow', sans-serif;
  outline: none;
  transition: var(--transition);
}}

.form-group input:focus,
.form-group textarea:focus {{
  border-color: var(--orange);
  box-shadow: 0 0 0 3px var(--orange-glow);
}}

.form-group textarea {{ height: 90px; resize: vertical; }}

.contact-options {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}

.contact-option {{
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 50px;
  cursor: pointer;
  transition: var(--transition);
  font-size: 13px;
  color: var(--white-soft);
  user-select: none;
}}

.contact-option input {{ display: none; }}

.contact-option:hover {{ border-color: var(--orange); color: var(--orange); }}
.contact-option.selected {{ background: var(--orange); border-color: var(--orange); color: white; }}

.form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}

.success-message {{
  display: none;
  text-align: center;
  padding: 40px 20px;
}}

.success-message .success-icon {{
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #00C851, #007d2d);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 28px;
}}

.success-message h4 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 28px;
  letter-spacing: 2px;
  margin-bottom: 8px;
}}

.success-message p {{ color: var(--white-soft); font-size: 14px; }}

/* ===== COMPARE PAGE ===== */
.compare-page {{
  display: none;
  position: fixed;
  inset: 0;
  background: var(--black);
  z-index: 1500;
  overflow-y: auto;
  padding: 24px;
  padding-top: 90px;
}}

.compare-page.active {{ display: block; }}

.compare-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}}

.compare-header h2 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 36px;
  letter-spacing: 3px;
}}

.compare-table-wrapper {{
  max-width: 1400px;
  margin: 0 auto;
  overflow-x: auto;
}}

.compare-table {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 600px;
}}

.compare-table th,
.compare-table td {{
  padding: 14px 18px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}}

.compare-table th:first-child,
.compare-table td:first-child {{
  width: 140px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--gray-light);
  background: var(--dark2);
  border-right: 1px solid var(--border);
  position: sticky;
  left: 0;
  z-index: 5;
}}

.compare-table th {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--gray-light);
  background: var(--dark2);
}}

.compare-table th.vehicle-col {{
  background: var(--dark3);
  text-align: center;
}}

.compare-car-header {{
  text-align: center;
}}

.compare-car-img {{
  width: 100%;
  max-width: 180px;
  height: 110px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  margin-bottom: 10px;
}}

.compare-car-name {{
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--white);
  line-height: 1.2;
  margin-bottom: 6px;
}}

.compare-table tr:nth-child(even) td {{ background: rgba(255,255,255,0.02); }}
.compare-table tr:nth-child(even) td:first-child {{ background: var(--dark2); }}

.highlight-best {{
  color: #00C851 !important;
  font-weight: 700;
}}

.compare-remove {{
  display: block;
  margin: 8px auto 0;
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--gray-light);
  font-size: 11px;
  cursor: pointer;
  transition: var(--transition);
  font-family: 'Barlow', sans-serif;
}}

.compare-remove:hover {{ border-color: #E91E63; color: #E91E63; }}

/* ===== ABOUT & CONTACT SECTIONS ===== */
.section-page {{
  display: none;
  min-height: calc(100vh - 70px);
  padding: 60px 24px;
  max-width: 900px;
  margin: 70px auto 0;
}}

.section-page.active {{ display: block; }}

.section-page h2 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 56px;
  letter-spacing: 4px;
  margin-bottom: 8px;
  line-height: 1;
}}

.section-page h2 span {{ color: var(--orange); }}

.section-page .subtitle {{
  font-size: 16px;
  color: var(--white-soft);
  margin-bottom: 40px;
  max-width: 500px;
}}

.about-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}}

.about-card {{
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  transition: var(--transition);
}}

.about-card:hover {{ border-color: var(--border-orange); }}

.about-icon {{
  font-size: 32px;
  margin-bottom: 12px;
}}

.about-card h4 {{
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--white);
  margin-bottom: 8px;
}}

.about-card p {{
  font-size: 13px;
  color: var(--white-soft);
  line-height: 1.6;
}}

.contact-form-full {{
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 36px;
}}

.contact-form-full h3 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 28px;
  letter-spacing: 2px;
  margin-bottom: 20px;
}}

/* ===== HOME PAGE ===== */
#home-page {{ display: block; }}

/* ===== MOBILE OVERLAY NAV ===== */
.mobile-nav {{
  display: none;
  position: fixed;
  inset: 70px 0 0;
  background: rgba(10,10,10,0.98);
  z-index: 999;
  padding: 32px 24px;
  flex-direction: column;
  gap: 8px;
  backdrop-filter: blur(20px);
}}

.mobile-nav.open {{ display: flex; }}

.mobile-nav a {{
  padding: 14px 16px;
  font-size: 18px;
  font-family: 'Barlow Condensed', sans-serif;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--white-soft);
  text-decoration: none;
  border-radius: 8px;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 10px;
}}

.mobile-nav a:hover {{ color: var(--orange); background: var(--white-ghost); }}

/* ===== FILTER MOBILE TOGGLE ===== */
.mobile-filter-btn {{
  display: none;
  width: 100%;
  padding: 12px 16px;
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--white);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  font-family: 'Barlow', sans-serif;
}}

/* ===== NO RESULTS ===== */
.no-results {{
  grid-column: 1/-1;
  text-align: center;
  padding: 60px 20px;
}}

.no-results h3 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 36px;
  letter-spacing: 2px;
  color: var(--gray);
  margin-bottom: 8px;
}}

.no-results p {{ color: var(--gray); }}

/* ===== FOOTER ===== */
footer {{
  margin-top: 60px;
  background: var(--dark2);
  border-top: 1px solid var(--border);
  padding: 48px 24px 24px;
}}

.footer-inner {{
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.5fr repeat(3, 1fr);
  gap: 40px;
  margin-bottom: 40px;
}}

.footer-brand .logo {{ margin-bottom: 14px; display: inline-flex; }}
.footer-brand p {{ font-size: 13px; color: var(--white-soft); line-height: 1.7; max-width: 240px; }}

.footer-col h5 {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--gray-light);
  margin-bottom: 14px;
}}

.footer-col a {{
  display: block;
  font-size: 13px;
  color: var(--white-soft);
  text-decoration: none;
  margin-bottom: 8px;
  transition: var(--transition);
}}

.footer-col a:hover {{ color: var(--orange); }}

.footer-col .contact-info {{
  font-size: 13px;
  color: var(--white-soft);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}}

.footer-bottom {{
  max-width: 1400px;
  margin: 0 auto;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--gray);
  flex-wrap: wrap;
  gap: 8px;
}}

/* ===== TOAST ===== */
.toast {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  background: var(--dark2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  font-size: 13px;
  color: var(--white);
  min-width: 240px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  display: flex;
  align-items: center;
  gap: 10px;
}}

.toast.show {{ transform: translateY(0); opacity: 1; }}
.toast-icon {{ font-size: 18px; }}

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {{
  .main-layout {{ grid-template-columns: 1fr; }}
  .sidebar {{ position: static; height: auto; max-height: none; display: none; }}
  .sidebar.open {{ display: block; margin-bottom: 16px; }}
  .mobile-filter-btn {{ display: flex; }}
  .hero {{ height: 340px; }}
  .footer-inner {{ grid-template-columns: 1fr 1fr; gap: 28px; }}
}}

@media (max-width: 768px) {{
  nav {{ display: none; }}
  .hamburger {{ display: flex; }}
  .search-bar {{ max-width: 200px; }}
  .hero h1 {{ font-size: 52px; }}
  .hero-stats {{ gap: 20px; }}
  .hero-stat strong {{ font-size: 28px; }}
  .vehicle-grid {{ grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }}
  .footer-inner {{ grid-template-columns: 1fr; gap: 20px; }}
  .form-row {{ grid-template-columns: 1fr; }}
  .detail-header {{ flex-direction: column; }}
  .detail-price-block {{ text-align: left; }}
  .compare-table th:first-child,
  .compare-table td:first-child {{ width: 100px; padding: 10px 12px; }}
  .compare-table th,
  .compare-table td {{ padding: 10px 12px; }}
}}

@media (max-width: 480px) {{
  .header-inner {{ gap: 12px; }}
  .search-bar {{ max-width: 150px; }}
  .hero {{ height: 280px; }}
  .hero h1 {{ font-size: 42px; }}
  .hero p {{ display: none; }}
  .vehicle-grid {{ grid-template-columns: 1fr 1fr; }}
  .card-specs {{ grid-template-columns: 1fr; }}
  .card-image-wrapper {{ height: 140px; }}
  .card-image {{ height: 140px; }}
}}
</style>
</head>
<body>

<!-- HEADER -->
<header id="header">
  <div class="header-inner">
    <a class="logo" href="#" onclick="showPage('home')">
      <img src="data:image/png;base64,{logo_base64}" alt="Carmelo Multimarcas" style="height: 50px; width: auto; border-radius: 8px;">
    </a>
    <nav>
      <a href="#" class="active" onclick="showPage('home')">Início</a>
      <a href="#" onclick="showPage('home')">Estoque</a>
      <a href="#" class="compare-btn" onclick="showComparePage()">
        Comparar
        <span class="compare-count" id="compareCount">0</span>
      </a>
      <a href="#" onclick="showPage('about')">Sobre</a>
      <a href="#" onclick="showPage('contact')">Contato</a>
    </nav>
    <div class="search-bar">
      <input type="text" id="searchInput" placeholder="Buscar veículo..." oninput="applyFilters()">
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    </div>
    <button class="hamburger" id="hamburger" onclick="toggleMobileNav()">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<!-- MOBILE NAV -->
<div class="mobile-nav" id="mobileNav">
  <a href="#" onclick="showPage('home');toggleMobileNav()">🏠 Início</a>
  <a href="#" onclick="showPage('home');toggleMobileNav()">🚗 Estoque</a>
  <a href="#" onclick="showComparePage();toggleMobileNav()">⚖️ Comparar</a>
  <a href="#" onclick="showPage('about');toggleMobileNav()">ℹ️ Sobre</a>
  <a href="#" onclick="showPage('contact');toggleMobileNav()">📞 Contato</a>
</div>

<!-- HOME PAGE -->
<div id="home-page">
    
  <!-- HERO -->
  <section class="hero">
    <div class="hero-content">
      <div class="hero-tag">⚡ Veículos de qualidade em Mossoró/RN</div>
      <h1>ENCONTRE<br>SEU <span>CARRO</span><br>IDEAL</h1>
      <p>Seminovos e novos com procedência, garantia e os melhores preços do mercado.</p>
      <div class="hero-stats">
        <div class="hero-stat">
          <strong>{total_veiculos}+</strong>
          <span>Veículos</span>
        </div>
      </div>
    </div>
  </section>

  <!-- MAIN LAYOUT -->
  <div class="main-layout">
    <!-- SIDEBAR FILTERS -->
    <aside class="sidebar" id="sidebar">
      <div class="filter-panel">
        <div class="filter-header">
          <h3>Filtros</h3>
          <button class="clear-filters" onclick="clearFilters()">Limpar tudo</button>
        </div>

        <div class="filter-group">
          <label>Câmbio</label>
          <div class="filter-chips" id="transmissionFilter">
            {''.join([f'<div class="chip" onclick="toggleChip(this, &quot;transmission&quot;)">{t}</div>' for t in transmissoes])}
          </div>
        </div>

        <div class="filter-group">
          <label>Combustível</label>
          <div class="filter-chips" id="fuelFilter">
            {''.join([f'<div class="chip" onclick="toggleChip(this, &quot;fuel&quot;)">{c}</div>' for c in combustiveis[:5]])}
          </div>
        </div>

        <div class="filter-group">
          <label>Marca</label>
          <select class="filter-select" id="brandFilter" onchange="applyFilters()">
            <option value="">Todas as marcas</option>
            {''.join([f'<option value="{marca}">{marca}</option>' for marca in marcas])}
          </select>
        </div>

        <div class="filter-group">
          <label>Faixa de Preço</label>
          <div class="range-inputs">
            <input type="number" id="priceMin" placeholder="Mín" oninput="applyFilters()">
            <input type="number" id="priceMax" placeholder="Máx" oninput="applyFilters()">
          </div>
        </div>

        <div class="filter-group">
          <label>Ano</label>
          <div class="range-inputs">
            <input type="number" id="yearMin" placeholder="De" min="2010" max="2025" oninput="applyFilters()">
            <input type="number" id="yearMax" placeholder="Até" min="2010" max="2025" oninput="applyFilters()">
          </div>
        </div>

        <div class="filter-group">
          <label>Km Máximo</label>
          <div class="range-inputs">
            <input type="number" id="kmMax" placeholder="Km máx" oninput="applyFilters()">
          </div>
        </div>

        <div class="filter-group">
          <label>Cor</label>
          <select class="filter-select" id="colorFilter" onchange="applyFilters()">
            <option value="">Todas as cores</option>
            {''.join([f'<option value="{cor}">{cor}</option>' for cor in cores[:8]])}
          </select>
        </div>

      </div>
    </aside>

    <!-- CONTENT -->
    <main class="content-area">
      <button class="mobile-filter-btn" id="mobileFilterBtn" onclick="toggleSidebar()">
        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M3 6h18M7 12h10M11 18h2"/></svg>
        Filtros
      </button>

      <div class="content-toolbar">
        <div class="results-info">
          Exibindo <strong id="resultsCount">{total_veiculos}</strong> veículos
        </div>
        <div class="toolbar-right">
          <select class="sort-select" id="sortSelect" onchange="applyFilters()">
            <option value="default">Relevância</option>
            <option value="price-asc">Menor preço</option>
            <option value="price-desc">Maior preço</option>
            <option value="year-desc">Mais novos</option>
            <option value="km-asc">Menor KM</option>
          </select>
          <div class="view-toggle">
            <button class="view-btn active" id="gridViewBtn" onclick="setView('grid')" title="Grade">
              <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M1 2.5A1.5 1.5 0 0 1 2.5 1h3A1.5 1.5 0 0 1 7 2.5v3A1.5 1.5 0 0 1 5.5 7h-3A1.5 1.5 0 0 1 1 5.5v-3zm8 0A1.5 1.5 0 0 1 10.5 1h3A1.5 1.5 0 0 1 15 2.5v3A1.5 1.5 0 0 1 13.5 7h-3A1.5 1.5 0 0 1 9 5.5v-3zm-8 8A1.5 1.5 0 0 1 2.5 9h3A1.5 1.5 0 0 1 7 10.5v3A1.5 1.5 0 0 1 5.5 15h-3A1.5 1.5 0 0 1 1 13.5v-3zm8 0A1.5 1.5 0 0 1 10.5 9h3A1.5 1.5 0 0 1 15 10.5v3A1.5 1.5 0 0 1 13.5 15h-3A1.5 1.5 0 0 1 9 13.5v-3z"/></svg>
            </button>
            <button class="view-btn" id="listViewBtn" onclick="setView('list')" title="Lista">
              <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/></svg>
            </button>
          </div>
        </div>
      </div>

      <div class="vehicle-grid" id="vehicleGrid"></div>
    </main>
  </div>

  <!-- FOOTER -->
  <footer>
    <div class="footer-inner">
      <div class="footer-brand">
        <a class="logo" href="#">
          <div class="logo-icon">CM</div>
          <div class="logo-text">Carmelo<span>Multimarcas</span></div>
        </a>
        <p>Especialistas em veículos seminovos e novos em Mossoró/RN. Qualidade, transparência e os melhores preços do mercado.</p>
      </div>
      <div class="footer-col">
        <h5>Navegação</h5>
        <a href="#" onclick="showPage('home')">Início</a>
        <a href="#" onclick="showPage('home')">Estoque</a>
        <a href="#" onclick="showComparePage()">Comparar</a>
        <a href="#" onclick="showPage('about')">Sobre nós</a>
      </div>
      <div class="footer-col">
        <h5>Contato</h5>
        <div class="contact-info">📍 Av. Lauro Monte, 475 - Mossoró/RN</div>
        <div class="contact-info">📞 (84) 3062-2434</div>
        <div class="contact-info">📧 contato@carmelomultimarcas.com.br</div>
        <div class="contact-info">🕐 Seg–Sex: 8h–18h, Sáb: 8h–12h</div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© {datetime.now().year} Carmelo Multimarcas. Todos os direitos reservados.</span>
      <span>Powered by Júlio Aguiar</span>
    </div>
  </footer>

</div><!-- end home-page -->

<!-- ABOUT PAGE -->
<div class="section-page" id="about-page">
  <h2>SOBRE A<br><span>CARMELO MULTIMARCAS</span></h2>
  <p class="subtitle">Mais de 10 anos conectando pessoas aos melhores veículos do mercado em Mossoró e região.</p>

  <div class="about-grid">
    <div class="about-card">
      <div class="about-icon">🏆</div>
      <h4>Qualidade Garantida</h4>
      <p>Todos os veículos passam por inspeção técnica rigorosa com laudos detalhados.</p>
    </div>
    <div class="about-card">
      <div class="about-icon">🛡️</div>
      <h4>Garantia Estendida</h4>
      <p>Oferecemos garantia de 3 a 12 meses em todos os veículos do nosso estoque.</p>
    </div>
    <div class="about-card">
      <div class="about-icon">💳</div>
      <h4>Financiamento Fácil</h4>
      <p>Parceria com os principais bancos. Aprovação rápida com as melhores taxas.</p>
    </div>
    <div class="about-card">
      <div class="about-icon">🤝</div>
      <h4>Equipe Especializada</h4>
      <p>Time de consultores experientes e apaixonados por automóveis prontos para ajudar.</p>
    </div>
    <div class="about-card">
      <div class="about-icon">🚗</div>
      <h4>Avaliação Grátis</h4>
      <p>Avaliamos seu veículo sem custo. Aceitamos na troca com as melhores condições.</p>
    </div>
    <div class="about-card">
      <div class="about-icon">⭐</div>
      <h4>Atendimento 5 estrelas</h4>
      <p>Mais de 500 clientes satisfeitos. Reputação impecável no mercado.</p>
    </div>
  </div>
</div>

<!-- CONTACT PAGE -->
<div class="section-page" id="contact-page">
  <h2>ENTRE EM<br><span>CONTATO</span></h2>
  <p class="subtitle">Estamos prontos para te ajudar a encontrar o veículo perfeito.</p>
  <div class="contact-form-full">
    <h3>Envie uma mensagem</h3>
    <div class="form-row">
      <div class="form-group">
        <label>Nome completo *</label>
        <input type="text" id="contactName" placeholder="Seu nome">
      </div>
      <div class="form-group">
        <label>E-mail *</label>
        <input type="email" id="contactEmail" placeholder="seu@email.com">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Celular *</label>
        <input type="tel" id="contactPhone" placeholder="(84) 99999-9999">
      </div>
      <div class="form-group">
        <label>Assunto</label>
        <input type="text" id="contactSubject" placeholder="Ex: Dúvida sobre financiamento">
      </div>
    </div>
    <div class="form-group">
      <label>Mensagem</label>
      <textarea id="contactMessage" placeholder="Como podemos te ajudar?"></textarea>
    </div>
    <button class="btn-proposal" style="width:100%;margin-top:4px;font-size:15px;padding:16px" onclick="sendContact()">Enviar Mensagem</button>
  </div>
</div>

<!-- DETAIL MODAL -->
<div class="modal-overlay" id="detailModal">
  <div class="modal" id="detailContent">
    <button class="modal-close" onclick="closeModal('detailModal')">
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
    </button>
    <!-- Content injected by JS -->
  </div>
</div>

<!-- PROPOSAL MODAL -->
<div class="modal-overlay" id="proposalModal">
  <div class="modal proposal-modal" id="proposalContent">
    <button class="modal-close" onclick="closeModal('proposalModal')">
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
    </button>
    <h3>Solicitar <span style="color:var(--orange)">Proposta</span></h3>
    <p id="proposalCarName">Preencha seus dados e entraremos em contato.</p>

    <div id="proposalForm">
      <div class="form-row">
        <div class="form-group">
          <label>Nome completo *</label>
          <input type="text" id="propName" placeholder="Seu nome">
        </div>
        <div class="form-group">
          <label>E-mail *</label>
          <input type="email" id="propEmail" placeholder="seu@email.com">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Celular *</label>
          <input type="tel" id="propPhone" placeholder="(84) 99999-9999">
        </div>
        <div class="form-group">
          <label>Telefone</label>
          <input type="tel" id="propPhone2" placeholder="(opcional)">
        </div>
      </div>
      <div class="form-group">
        <label>Forma de contato preferida</label>
        <div class="contact-options">
          <label class="contact-option" onclick="selectContact(this)"><input type="radio" name="contact">📧 E-mail</label>
          <label class="contact-option" onclick="selectContact(this)"><input type="radio" name="contact">📞 Telefone</label>
          <label class="contact-option" onclick="selectContact(this)"><input type="radio" name="contact">💬 WhatsApp</label>
        </div>
      </div>
      <div class="form-group">
        <label>Mensagem</label>
        <textarea id="propMessage" placeholder="Tenho interesse neste veículo..."></textarea>
      </div>
      <button class="btn-proposal" style="width:100%;font-size:15px;padding:16px" onclick="submitProposal()">Enviar Proposta</button>
    </div>

    <div class="success-message" id="successMessage">
      <div class="success-icon">✓</div>
      <h4>Proposta Enviada!</h4>
      <p>Recebemos sua solicitação. Nossa equipe entrará em contato em até 2 horas.</p>
    </div>
  </div>
</div>

<!-- COMPARE PAGE -->
<div class="compare-page" id="comparePage">
  <div class="compare-header">
    <h2>⚖️ Comparar <span style="color:var(--orange)">Veículos</span></h2>
    <button class="btn-secondary" onclick="closeComparePage()">← Voltar ao estoque</button>
  </div>
  <div class="compare-table-wrapper">
    <table class="compare-table" id="compareTable"></table>
  </div>
</div>

<!-- TOAST -->
<div class="toast" id="toast">
  <span class="toast-icon"></span>
  <span id="toastMsg"></span>
</div>

<script>
// ===== DATA =====
const vehicles = {veiculos_json};

console.log('Veículos carregados:', vehicles);
console.log('Primeiro veículo:', vehicles[0]);

// ===== STATE =====
let compareList = [];
let currentVehicle = null;
let currentGalleryIndex = 0;
let activeFilters = {{ type: [], transmission: [], fuel: [] }};

// ===== INIT =====
renderVehicles(vehicles);

function formatPrice(p) {{
  return 'R$ ' + p.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
}}

function formatKm(k) {{
  return k.toLocaleString('pt-BR') + ' km';
}}

// ===== RENDER VEHICLES =====
function renderVehicles(list) {{
  const grid = document.getElementById('vehicleGrid');
  document.getElementById('resultsCount').textContent = list.length;

  if (list.length === 0) {{
    grid.innerHTML = `
      <div class="no-results">
        <h3>Nenhum veículo encontrado</h3>
        <p>Tente ajustar os filtros para ver mais resultados.</p>
      </div>`;
    return;
  }}

  grid.innerHTML = list.map((v, i) => `
    <div class="vehicle-card" style="animation-delay:${{i * 0.05}}s">
      ${{v.badge ? `<div class="card-badges"><span class="badge badge-${{v.badge}}">${{v.badgeText}}</span></div>` : ''}}
      <button class="compare-toggle ${{compareList.find(c=>c.id===v.id)?'active':''}}"
        onclick="event.stopPropagation();toggleCompare(${{v.id}})" title="Comparar">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M8 3 4 7l4 4M16 3l4 4-4 4M14 20V4M10 20V4"/></svg>
      </button>
      <div class="card-image-wrapper" onclick="openDetail(${{v.id}})">
        <img class="card-image" src="${{v.images[0]}}" alt="${{v.nome_completo}}" loading="lazy">
      </div>
      <div class="card-body" onclick="openDetail(${{v.id}})">
        <div class="card-name">${{v.nome_completo}} ${{v.version}}</div>
        <div class="card-specs">
          <div class="card-spec">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
            <span>${{v.ano}}</span>
          </div>
          <div class="card-spec">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
            <span>${{formatKm(v.km)}}</span>
          </div>
          <div class="card-spec">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
            <span>${{v.transmission}}</span>
          </div>
          <div class="card-spec">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"/></svg>
            <span>${{v.fuel}}</span>
          </div>
        </div>
        ${{v.oldPrice ? `<div class="card-price-old">${{formatPrice(v.oldPrice)}}</div>` : ''}}
        <div class="card-price">${{formatPrice(v.preco_venda)}}</div>
        <div class="card-actions" onclick="event.stopPropagation()">
          <button class="btn-primary" onclick="openDetail(${{v.id}})">Ver detalhes</button>
          <button class="btn-secondary" onclick="openWhatsApp(${{v.id}})" title="WhatsApp">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.124.557 4.126 1.533 5.862L0 24l6.342-1.493C8.037 23.445 9.985 24 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818c-1.891 0-3.647-.514-5.16-1.408l-.368-.218-3.819.9.972-3.718-.24-.38C2.58 15.52 2.182 13.81 2.182 12c0-5.418 4.4-9.818 9.818-9.818 5.418 0 9.818 4.4 9.818 9.818 0 5.418-4.4 9.818-9.818 9.818z"/></svg>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}}

// ===== FILTERS =====
function toggleChip(el, filterKey) {{
  const val = el.textContent.trim();
  el.classList.toggle('active');
  const idx = activeFilters[filterKey].indexOf(val);
  if (idx === -1) activeFilters[filterKey].push(val);
  else activeFilters[filterKey].splice(idx, 1);
  applyFilters();
}}

function applyFilters() {{
  const search = document.getElementById('searchInput').value.toLowerCase();
  const brand = document.getElementById('brandFilter').value;
  const color = document.getElementById('colorFilter').value;
  const priceMin = parseFloat(document.getElementById('priceMin').value) || 0;
  const priceMax = parseFloat(document.getElementById('priceMax').value) || Infinity;
  const yearMin = parseInt(document.getElementById('yearMin').value) || 0;
  const yearMax = parseInt(document.getElementById('yearMax').value) || 9999;
  const kmMax = parseFloat(document.getElementById('kmMax').value) || Infinity;
  const sort = document.getElementById('sortSelect').value;

  let filtered = vehicles.filter(v => {{
    if (search && !`${{v.nome_completo}} ${{v.marca}} ${{v.modelo}}`.toLowerCase().includes(search)) return false;
    if (brand && v.marca !== brand) return false;
    if (color && v.cor !== color) return false;
    if (v.preco_venda < priceMin || v.preco_venda > priceMax) return false;
    if (v.ano < yearMin || v.ano > yearMax) return false;
    if (v.km > kmMax) return false;
    if (activeFilters.transmission.length && !activeFilters.transmission.includes(v.transmission)) return false;
    if (activeFilters.fuel.length && !activeFilters.fuel.includes(v.fuel)) return false;
    return true;
  }});

  if (sort === 'price-asc') filtered.sort((a,b) => a.preco_venda - b.preco_venda);
  else if (sort === 'price-desc') filtered.sort((a,b) => b.preco_venda - a.preco_venda);
  else if (sort === 'year-desc') filtered.sort((a,b) => b.ano - a.ano);
  else if (sort === 'km-asc') filtered.sort((a,b) => a.km - b.km);

  renderVehicles(filtered);
}}

function clearFilters() {{
  document.getElementById('searchInput').value = '';
  document.getElementById('brandFilter').value = '';
  document.getElementById('colorFilter').value = '';
  document.getElementById('priceMin').value = '';
  document.getElementById('priceMax').value = '';
  document.getElementById('yearMin').value = '';
  document.getElementById('yearMax').value = '';
  document.getElementById('kmMax').value = '';
  activeFilters = {{ type: [], transmission: [], fuel: [] }};
  document.querySelectorAll('.chip.active').forEach(c => c.classList.remove('active'));
  applyFilters();
}}

// ===== DETAIL MODAL =====
function openDetail(id) {{
  const v = vehicles.find(x => x.id == id);
  if (!v) return;
  currentVehicle = v;
  currentGalleryIndex = 0;

  const modal = document.getElementById('detailModal');
  const content = document.getElementById('detailContent');

  content.innerHTML = `
    <button class="modal-close" onclick="closeModal('detailModal')">
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
    </button>
    <div class="detail-gallery" id="detailGallery">
      <img class="gallery-main-img" id="galleryMain" src="${{v.images[0]}}" alt="${{v.nome_completo}}">
      ${{v.images.length > 1 ? `
        <button class="gallery-nav gallery-prev" onclick="changeGallery(-1)">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <button class="gallery-nav gallery-next" onclick="changeGallery(1)">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
        </button>` : ''}}
    </div>
    <div class="gallery-thumbs">
      ${{v.images.map((img, i) => `
        <img class="gallery-thumb ${{i===0?'active':''}}" src="${{img}}" alt="" onclick="setGallery(${{i}})">
      `).join('')}}
    </div>
    <div class="detail-content">
      <div class="detail-header">
        <div class="detail-title">
          <h2>${{v.nome_completo}}</h2>
          <div class="version">${{v.version}}</div>
        </div>
        <div class="detail-price-block">
          ${{v.oldPrice ? `<div style="font-size:14px;color:var(--gray);text-decoration:line-through;text-align:right">${{formatPrice(v.oldPrice)}}</div>` : ''}}
          <div class="detail-price">${{formatPrice(v.preco_venda)}}</div>
          <div class="detail-price-label">Preço à vista</div>
        </div>
      </div>

      <div class="detail-specs-grid">
        <div class="detail-spec"><div class="detail-spec-label">Ano</div><div class="detail-spec-value">${{v.ano}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Quilometragem</div><div class="detail-spec-value">${{formatKm(v.km)}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Câmbio</div><div class="detail-spec-value">${{v.transmission}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Combustível</div><div class="detail-spec-value">${{v.fuel}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Cor</div><div class="detail-spec-value">${{v.cor}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Potência</div><div class="detail-spec-value">${{v.power}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Portas</div><div class="detail-spec-value">${{v.portas}}</div></div>
        <div class="detail-spec"><div class="detail-spec-label">Placa</div><div class="detail-spec-value">${{v.placa || 'N/I'}}</div></div>
      </div>

      <div class="detail-section">
        <h4>Itens & Opcionais</h4>
        <div class="optionals-grid">
          ${{v.optionals.map(o => `<div class="optional-item">${{o}}</div>`).join('')}}
        </div>
      </div>

      <div class="detail-section">
        <h4>Histórico do Veículo</h4>
        <p style="font-size:14px;color:var(--white-soft);line-height:1.7">${{v.history}}</p>
      </div>

      <div class="detail-actions">
        <button class="btn-proposal" onclick="openProposal(${{v.id}})">📋 Solicitar Proposta</button>
        <a class="btn-whatsapp" href="https://wa.me/558430622434?text=Olá! Tenho interesse no ${{encodeURIComponent(v.nome_completo+' '+v.ano)}}" target="_blank">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.124.557 4.126 1.533 5.862L0 24l6.342-1.493C8.037 23.445 9.985 24 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818c-1.891 0-3.647-.514-5.16-1.408l-.368-.218-3.819.9.972-3.718-.24-.38C2.58 15.52 2.182 13.81 2.182 12c0-5.418 4.4-9.818 9.818-9.818 5.418 0 9.818 4.4 9.818 9.818 0 5.418-4.4 9.818-9.818 9.818z"/></svg>
          WhatsApp
        </a>
        <button class="btn-share" onclick="shareVehicle(${{v.id}})">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
          Compartilhar
        </button>
      </div>
    </div>
  `;

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}}

function changeGallery(dir) {{
  const v = currentVehicle;
  if (!v) return;
  currentGalleryIndex = (currentGalleryIndex + dir + v.images.length) % v.images.length;
  setGallery(currentGalleryIndex);
}}

function setGallery(idx) {{
  if (!currentVehicle) return;
  currentGalleryIndex = idx;
  document.getElementById('galleryMain').src = currentVehicle.images[idx];
  document.querySelectorAll('.gallery-thumb').forEach((t,i) => {{
    t.classList.toggle('active', i === idx);
  }});
}}

function openWhatsApp(id) {{
  const v = vehicles.find(x => x.id == id);
  if (!v) return;
  window.open(`https://wa.me/558430622434?text=Olá! Tenho interesse no ${{encodeURIComponent(v.nome_completo+' '+v.ano+' - '+formatPrice(v.preco_venda))}}`, '_blank');
}}

function shareVehicle(id) {{
  const v = vehicles.find(x => x.id == id);
  if (navigator.share) {{
    navigator.share({{ title: v.nome_completo, text: formatPrice(v.preco_venda), url: window.location.href }});
  }} else {{
    navigator.clipboard.writeText(window.location.href);
    showToast('🔗 Link copiado para a área de transferência!');
  }}
}}

// ===== PROPOSAL MODAL =====
function openProposal(id) {{
  const v = vehicles.find(x => x.id == id);
  closeModal('detailModal');
  document.getElementById('proposalCarName').textContent = `Interesse em: ${{v.nome_completo}} ${{v.ano}} — ${{formatPrice(v.preco_venda)}}`;
  document.getElementById('proposalForm').style.display = 'block';
  document.getElementById('successMessage').style.display = 'none';
  document.getElementById('proposalModal').classList.add('active');
  document.body.style.overflow = 'hidden';
}}

function selectContact(el) {{
  document.querySelectorAll('.contact-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
}}

function submitProposal() {{
  const name = document.getElementById('propName').value.trim();
  const email = document.getElementById('propEmail').value.trim();
  const phone = document.getElementById('propPhone').value.trim();
  if (!name || !email || !phone) {{
    showToast('⚠️ Preencha todos os campos obrigatórios.');
    return;
  }}
  document.getElementById('proposalForm').style.display = 'none';
  document.getElementById('successMessage').style.display = 'block';
}}

function sendContact() {{
  const name = document.getElementById('contactName').value.trim();
  const email = document.getElementById('contactEmail').value.trim();
  const phone = document.getElementById('contactPhone').value.trim();
  if (!name || !email || !phone) {{
    showToast('⚠️ Preencha os campos obrigatórios (nome, e-mail, celular).');
    return;
  }}
  showToast('✅ Mensagem enviada com sucesso!');
}}

// ===== COMPARE =====
function toggleCompare(id) {{
  const v = vehicles.find(x => x.id == id);
  if (!v) return;
  const idx = compareList.findIndex(c => c.id === id);
  if (idx === -1) {{
    if (compareList.length >= 4) {{
      showToast('⚠️ Máximo de 4 veículos para comparar.');
      return;
    }}
    compareList.push(v);
    showToast(`✅ ${{v.nome_completo}} adicionado à comparação.`);
  }} else {{
    compareList.splice(idx, 1);
    showToast(`❌ ${{v.nome_completo}} removido da comparação.`);
  }}
  updateCompareCount();
  applyFilters();
}}

function updateCompareCount() {{
  const el = document.getElementById('compareCount');
  el.textContent = compareList.length;
  el.classList.toggle('visible', compareList.length > 0);
}}

function showComparePage() {{
  if (compareList.length < 2) {{
    showToast('⚠️ Selecione ao menos 2 veículos para comparar.');
    return;
  }}
  renderCompareTable();
  document.getElementById('comparePage').classList.add('active');
  document.body.style.overflow = 'hidden';
}}

function closeComparePage() {{
  document.getElementById('comparePage').classList.remove('active');
  document.body.style.overflow = '';
}}

function removeFromCompare(id) {{
  compareList = compareList.filter(v => v.id !== id);
  updateCompareCount();
  if (compareList.length < 2) {{
    closeComparePage();
    applyFilters();
    showToast('ℹ️ Você precisa de ao menos 2 veículos para comparar.');
    return;
  }}
  renderCompareTable();
  applyFilters();
}}

function renderCompareTable() {{
  const table = document.getElementById('compareTable');
  const minPrice = Math.min(...compareList.map(v => v.preco_venda));
  const minKm = Math.min(...compareList.map(v => v.km));
  const maxYear = Math.max(...compareList.map(v => v.ano));

  const rows = [
    {{ key: 'Foto', fn: v => `<img class="compare-car-img" src="${{v.images[0]}}" alt="${{v.nome_completo}}"><div class="compare-car-name">${{v.nome_completo}}<br>${{v.ano}}</div><button class="compare-remove" onclick="removeFromCompare(${{v.id}})">✕ Remover</button>` }},
    {{ key: 'Preço', fn: v => `<span class="${{v.preco_venda === minPrice ? 'highlight-best' : ''}}">${{formatPrice(v.preco_venda)}}</span>` }},
    {{ key: 'Ano', fn: v => `<span class="${{v.ano === maxYear ? 'highlight-best' : ''}}">${{v.ano}}</span>` }},
    {{ key: 'Quilometragem', fn: v => `<span class="${{v.km === minKm ? 'highlight-best' : ''}}">${{formatKm(v.km)}}</span>` }},
    {{ key: 'Câmbio', fn: v => v.transmission }},
    {{ key: 'Combustível', fn: v => v.fuel }},
    {{ key: 'Cor', fn: v => v.cor }},
    {{ key: 'Portas', fn: v => v.portas }},
    {{ key: 'Opcionais', fn: v => v.optionals.slice(0,4).join(', ') + (v.optionals.length > 4 ? '...' : '') }},
    {{ key: 'Histórico', fn: v => v.history.substring(0,50) + '...' }}
  ];

  table.innerHTML = `
    <thead>
      <tr>
        <th>Especificação</th>
        ${{compareList.map(v => `<th class="vehicle-col">${{v.marca}}</th>`).join('')}}
      </tr>
    </thead>
    <tbody>
      ${{rows.map(row => `
        <tr>
          <td>${{row.key}}</td>
          ${{compareList.map(v => `<td style="text-align:center;font-size:13px;color:var(--white-dim)">${{row.fn(v)}}</td>`).join('')}}
        </tr>
      `).join('')}}
    </tbody>
  `;
}}

// ===== NAV =====
function showPage(page) {{
  document.getElementById('home-page').style.display = page === 'home' ? 'block' : 'none';
  document.getElementById('about-page').classList.toggle('active', page === 'about');
  document.getElementById('contact-page').classList.toggle('active', page === 'contact');
  window.scrollTo(0, 0);
}}

function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
}}

function toggleMobileNav() {{
  document.getElementById('mobileNav').classList.toggle('open');
}}

function setView(mode) {{
  const grid = document.getElementById('vehicleGrid');
  const gBtn = document.getElementById('gridViewBtn');
  const lBtn = document.getElementById('listViewBtn');
  if (mode === 'grid') {{
    grid.classList.remove('list-view');
    gBtn.classList.add('active');
    lBtn.classList.remove('active');
  }} else {{
    grid.classList.add('list-view');
    lBtn.classList.add('active');
    gBtn.classList.remove('active');
  }}
}}

// ===== MODAL HELPERS =====
function closeModal(id) {{
  document.getElementById(id).classList.remove('active');
  document.body.style.overflow = '';
}}

// Close on overlay click
document.getElementById('detailModal').addEventListener('click', function(e) {{
  if (e.target === this) closeModal('detailModal');
}});
document.getElementById('proposalModal').addEventListener('click', function(e) {{
  if (e.target === this) closeModal('proposalModal');
}});

// ===== TOAST =====
function showToast(msg) {{
  const toast = document.getElementById('toast');
  document.getElementById('toastMsg').textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}}

// Keyboard ESC
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') {{
    closeModal('detailModal');
    closeModal('proposalModal');
    closeComparePage();
  }}
}});
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
    print("VITRINE PREMIUM - CARMELO MULTIMARCAS")
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
