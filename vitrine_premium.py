# vitrine_premium.py
import sqlite3
import json
import os
import base64
from datetime import datetime
from pathlib import Path

class VitrinePremium:
    def __init__(self, db_path="canal_automotivo.db"):
        self.db_path = db_path
        self.vitrine_path = "vitrine_premium.html"
        self.logo_path = "logoca.png"
        self.icon_path = "logo-icon.png"
        self.timbrado_path = "papeltimbrado.png"
        
    def get_veiculos_estoque(self):
        """Busca veículos em estoque do banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    v.id, v.marca, v.modelo, v.ano, v.cor, v.preco_venda,
                    v.km, v.combustivel, v.cambio, v.portas, v.placa,
                    v.chassi, v.observacoes, v.foto,
                    COALESCE(SUM(g.valor), 0) as total_gastos,
                    v.preco_entrada
                FROM veiculos v
                LEFT JOIN gastos g ON v.id = g.veiculo_id
                WHERE v.status = 'Em estoque'
                GROUP BY v.id
                ORDER BY v.data_cadastro DESC
            ''')
            
            veiculos = []
            for row in cursor.fetchall():
                # Processar foto
                foto_base64 = None
                if row[13]:  # Foto em BLOB
                    try:
                        if isinstance(row[13], bytes):
                            foto_base64 = base64.b64encode(row[13]).decode('utf-8')
                        elif isinstance(row[13], str):
                            foto_base64 = row[13]
                    except:
                        foto_base64 = None
                
                # Calcular margem
                custo_total = float(row[14]) + float(row[15])  # preco_entrada + gastos
                margem = ((float(row[5]) - custo_total) / custo_total * 100) if custo_total > 0 else 0
                
                veiculo = {
                    'id': row[0],
                    'marca': row[1],
                    'modelo': row[2],
                    'ano': row[3],
                    'cor': row[4],
                    'preco_venda': float(row[5]),
                    'km': int(row[6]) if row[6] else 0,
                    'combustivel': row[7] if row[7] else 'Flex',
                    'cambio': row[8] if row[8] else 'Manual',
                    'portas': int(row[9]) if row[9] else 4,
                    'placa': row[10] if row[10] else '',
                    'chassi': row[11] if row[11] else '',
                    'observacoes': row[12] if row[12] else '',
                    'foto_base64': foto_base64,
                    'total_gastos': float(row[15]),
                    'preco_entrada': float(row[14]),
                    'custo_total': custo_total,
                    'margem': margem,
                    'lucro': float(row[5]) - custo_total
                }
                veiculos.append(veiculo)
            
            return veiculos
            
        except Exception as e:
            print(f"Erro ao buscar veículos: {e}")
            return []
        finally:
            conn.close()
    
    def get_logo_base64(self):
        """Converte logo para base64"""
        try:
            if os.path.exists(self.logo_path):
                with open(self.logo_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode('utf-8')
        except:
            pass
        return None
    
    def get_timbrado_base64(self):
        """Converte papel timbrado para base64"""
        try:
            if os.path.exists(self.timbrado_path):
                with open(self.timbrado_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode('utf-8')
        except:
            pass
        return None
    
    def gerar_vitrine_html(self):
        """Gera o HTML completo da vitrine premium"""
        veiculos = self.get_veiculos_estoque()
        logo_base64 = self.get_logo_base64()
        timbrado_base64 = self.get_timbrado_base64()
        hoje = datetime.now()
        
        # Calcular estatísticas
        total_veiculos = len(veiculos)
        valor_total_estoque = sum(v['preco_venda'] for v in veiculos)
        media_preco = valor_total_estoque / total_veiculos if total_veiculos > 0 else 0
        
        # Agrupar marcas para filtros
        marcas = sorted(list(set(v['marca'] for v in veiculos)))
        
        # HTML COMPLETO
        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Garagem Multimarcas - Veículos Premium com procedência garantida">
    <meta name="keywords" content="carros, veículos, automóveis, concessionária, Mossoró">
    <title>Garagem Multimarcas - Veículos Premium</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="icon" type="image/x-icon" href="logo-icon.png">
    <style>
        :root {{
            --primary: #e88e1b;
            --primary-dark: #c77916;
            --secondary: #f4c220;
            --dark: #1a1a1a;
            --dark-light: #2d2d2d;
            --gray: #6c757d;
            --gray-light: #a0a0a0;
            --light: #f8f9fa;
            --success: #27AE60;
            --danger: #E74C3C;
            --warning: #F39C12;
            --info: #3498DB;
            --shadow-sm: 0 2px 10px rgba(0,0,0,0.05);
            --shadow: 0 4px 20px rgba(0,0,0,0.08);
            --shadow-lg: 0 12px 40px rgba(0,0,0,0.12);
            --shadow-primary: 0 8px 30px rgba(232, 142, 27, 0.2);
            --radius-sm: 8px;
            --radius: 16px;
            --radius-lg: 24px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: var(--dark);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* ===== HEADER ===== */
        .header {{
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
            padding: 1.5rem 0;
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            border-bottom: 4px solid var(--primary);
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 2rem;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 1rem;
            text-decoration: none;
            transition: transform 0.3s;
        }}

        .logo:hover {{
            transform: translateY(-2px);
        }}

        .logo-img {{
            height: 55px;
            width: auto;
            border-radius: var(--radius-sm);
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }}

        .logo-text {{
            display: flex;
            flex-direction: column;
        }}

        .logo-text h1 {{
            font-size: 1.8rem;
            font-weight: 800;
            color: white;
            line-height: 1.2;
            margin: 0;
        }}

        .logo-text span {{
            font-size: 0.9rem;
            color: var(--secondary);
            font-weight: 500;
        }}

        .header-contact {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}

        .contact-item {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            color: white;
            text-decoration: none;
            padding: 0.7rem 1.2rem;
            background: rgba(255,255,255,0.1);
            border-radius: var(--radius-sm);
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .contact-item:hover {{
            background: rgba(232, 142, 27, 0.2);
            border-color: var(--primary);
            transform: translateY(-2px);
        }}

        .contact-item i {{
            font-size: 1.2rem;
            color: var(--secondary);
        }}

        /* ===== HERO ===== */
        .hero {{
            background: linear-gradient(135deg, 
                rgba(26,26,26,0.95) 0%, 
                rgba(45,45,45,0.92) 100%),
                url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" opacity="0.05"><path fill="%23e88e1b" d="M0,200 Q300,100 600,200 T1200,200 L1200,400 L0,400 Z"/></svg>');
            background-size: cover;
            padding: 5rem 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, 
                var(--primary), 
                var(--secondary),
                var(--primary));
        }}

        .hero-content {{
            max-width: 800px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }}

        .hero h2 {{
            font-size: 3.5rem;
            font-weight: 900;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #ffffff, var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
        }}

        .hero p {{
            font-size: 1.3rem;
            color: #ddd;
            max-width: 600px;
            margin: 0 auto 2rem;
        }}

        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 3rem;
            flex-wrap: wrap;
        }}

        .stat-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--primary);
            line-height: 1;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: var(--gray-light);
            margin-top: 0.5rem;
        }}

        /* ===== FILTROS ===== */
        .filters-section {{
            max-width: 1400px;
            margin: -3rem auto 3rem;
            padding: 0 2rem;
        }}

        .filters-card {{
            background: white;
            border-radius: var(--radius-lg);
            padding: 2.5rem;
            box-shadow: var(--shadow-lg);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            border: 1px solid rgba(0,0,0,0.05);
            position: relative;
        }}

        .filters-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        }}

        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 0.7rem;
        }}

        .filter-label {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            color: var(--dark);
            font-size: 0.95rem;
        }}

        .filter-label i {{
            color: var(--primary);
            font-size: 1rem;
        }}

        .filter-select, .filter-input {{
            padding: 0.9rem 1.2rem;
            border: 2px solid #e9ecef;
            border-radius: var(--radius-sm);
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
            background: white;
            color: var(--dark);
            width: 100%;
        }}

        .filter-select:focus, .filter-input:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(232, 142, 27, 0.1);
        }}

        .filter-actions {{
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }}

        .btn-filter {{
            padding: 0.9rem 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            white-space: nowrap;
        }}

        .btn-filter:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-primary);
        }}

        .btn-filter.secondary {{
            background: transparent;
            border: 2px solid #e9ecef;
            color: var(--gray);
        }}

        .btn-filter.secondary:hover {{
            border-color: var(--primary);
            color: var(--primary);
        }}

        /* ===== RESULTADOS ===== */
        .results-info {{
            max-width: 1400px;
            margin: 0 auto 2rem;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .results-count {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .results-count span {{
            color: var(--primary);
            font-weight: 800;
            font-size: 1.5rem;
        }}

        .sort-options {{
            display: flex;
            gap: 1rem;
            align-items: center;
        }}

        .sort-label {{
            color: var(--gray);
            font-size: 0.9rem;
        }}

        .sort-select {{
            padding: 0.7rem 1.2rem;
            border: 2px solid #e9ecef;
            border-radius: var(--radius-sm);
            font-size: 0.95rem;
            background: white;
            color: var(--dark);
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
        }}

        .sort-select:hover {{
            border-color: var(--primary);
        }}

        /* ===== GRID DE VEÍCULOS ===== */
        .vehicles-section {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem 4rem;
        }}

        .vehicles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 2rem;
        }}

        .vehicle-card {{
            background: white;
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
            border: 1px solid rgba(0,0,0,0.05);
        }}

        .vehicle-card:hover {{
            transform: translateY(-12px);
            box-shadow: var(--shadow-lg);
            border-color: rgba(232, 142, 27, 0.2);
        }}

        .vehicle-card.highlight::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            z-index: 2;
        }}

        .vehicle-image {{
            position: relative;
            width: 100%;
            height: 250px;
            overflow: hidden;
            background: linear-gradient(135deg, #f5f5f5, #eaeaea);
        }}

        .vehicle-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .vehicle-card:hover .vehicle-image img {{
            transform: scale(1.08);
        }}

        .vehicle-badges {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 3;
        }}

        .badge {{
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .badge.available {{
            background: linear-gradient(135deg, var(--success), #2ECC71);
            color: white;
        }}

        .badge.financing {{
            background: linear-gradient(135deg, var(--info), #3498DB);
            color: white;
        }}

        .badge.highlight {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }}

        .vehicle-info {{
            padding: 1.8rem;
        }}

        .vehicle-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.8rem;
        }}

        .vehicle-title {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--dark);
            line-height: 1.2;
        }}

        .vehicle-year {{
            font-size: 1rem;
            color: var(--primary);
            font-weight: 700;
            background: rgba(232, 142, 27, 0.1);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            white-space: nowrap;
        }}

        .vehicle-subtitle {{
            color: var(--gray);
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }}

        .vehicle-subtitle i {{
            color: var(--primary);
        }}

        .specs-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.8rem;
            margin: 1.5rem 0;
        }}

        .spec-item {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.8rem;
            background: #f8f9fa;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            color: var(--dark);
            transition: all 0.3s;
        }}

        .spec-item:hover {{
            background: rgba(232, 142, 27, 0.05);
            transform: translateY(-2px);
        }}

        .spec-item i {{
            color: var(--primary);
            font-size: 1rem;
            min-width: 20px;
        }}

        .vehicle-price {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 2px solid #f0f0f0;
        }}

        .price-content {{
            display: flex;
            flex-direction: column;
        }}

        .price-main {{
            font-size: 2rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }}

        .price-label {{
            font-size: 0.85rem;
            color: var(--gray);
            margin-top: 0.3rem;
        }}

        .btn-details {{
            padding: 0.8rem 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            white-space: nowrap;
        }}

        .btn-details:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-primary);
        }}

        /* ===== MODAL ===== */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            overflow-y: auto;
            backdrop-filter: blur(5px);
        }}

        .modal.active {{
            display: flex;
            animation: modalFadeIn 0.3s ease;
        }}

        @keyframes modalFadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .modal-content {{
            background: white;
            border-radius: var(--radius-lg);
            max-width: 1000px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .modal-close {{
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            background: rgba(0,0,0,0.6);
            color: white;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }}

        .modal-close:hover {{
            background: var(--primary);
            transform: rotate(90deg);
        }}

        .modal-gallery {{
            position: relative;
            height: 450px;
            background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
        }}

        .modal-gallery img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            padding: 2rem;
        }}

        .modal-body {{
            padding: 3rem;
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 2.5rem;
            flex-wrap: wrap;
            gap: 1.5rem;
        }}

        .modal-title h2 {{
            font-size: 2.8rem;
            font-weight: 900;
            margin-bottom: 0.5rem;
            color: var(--dark);
            line-height: 1.1;
        }}

        .modal-subtitle {{
            font-size: 1.2rem;
            color: var(--gray);
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .modal-price {{
            text-align: right;
        }}

        .modal-price .price-main {{
            font-size: 2.8rem;
        }}

        .specs-full {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 2.5rem 0;
        }}

        .spec-full {{
            padding: 1.5rem;
            background: linear-gradient(135deg, #f8f9fa, #ffffff);
            border-radius: var(--radius);
            border-left: 4px solid var(--primary);
            transition: all 0.3s;
        }}

        .spec-full:hover {{
            transform: translateY(-3px);
            box-shadow: var(--shadow);
        }}

        .spec-full-label {{
            font-size: 0.85rem;
            color: var(--gray);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .spec-full-value {{
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }}

        .modal-description {{
            background: linear-gradient(135deg, #f8f9fa, #ffffff);
            padding: 2rem;
            border-radius: var(--radius);
            margin: 2.5rem 0;
            border: 1px solid rgba(0,0,0,0.05);
        }}

        .modal-description h4 {{
            margin-bottom: 1rem;
            color: var(--primary);
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }}

        .modal-description p {{
            color: var(--dark);
            line-height: 1.7;
        }}

        .contact-section {{
            background: linear-gradient(135deg, var(--dark), var(--dark-light));
            padding: 2.5rem;
            border-radius: var(--radius-lg);
            color: white;
            margin-top: 2.5rem;
            position: relative;
            overflow: hidden;
        }}

        .contact-section::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }}

        .contact-section h3 {{
            margin-bottom: 0.8rem;
            font-size: 1.8rem;
            font-weight: 800;
        }}

        .contact-section p {{
            color: rgba(255,255,255,0.8);
            margin-bottom: 1.5rem;
        }}

        .contact-buttons {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .btn-contact {{
            padding: 1.2rem 1.5rem;
            background: white;
            color: var(--primary);
            border: none;
            border-radius: var(--radius-sm);
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.8rem;
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            text-decoration: none;
        }}

        .btn-contact:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            color: var(--primary-dark);
        }}

        .btn-contact.whatsapp {{
            background: #25D366;
            color: white;
        }}

        .btn-contact.phone {{
            background: var(--primary);
            color: white;
        }}

        /* ===== WHATSAPP FLUTUANTE ===== */
        .whatsapp-float {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 75px;
            height: 75px;
            background: #25D366;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 30px rgba(37, 211, 102, 0.4);
            cursor: pointer;
            z-index: 999;
            transition: all 0.3s;
            text-decoration: none;
            animation: float 3s ease-in-out infinite;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}

        .whatsapp-float:hover {{
            transform: scale(1.15);
            box-shadow: 0 12px 40px rgba(37, 211, 102, 0.6);
            animation: none;
        }}

        .whatsapp-float i {{
            font-size: 2.8rem;
            color: white;
        }}

        /* ===== FOOTER ===== */
        .footer {{
            background: linear-gradient(135deg, var(--dark), var(--dark-light));
            color: white;
            padding: 4rem 2rem 1.5rem;
            margin-top: 4rem;
            border-top: 4px solid var(--primary);
        }}

        .footer-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 3rem;
        }}

        .footer-section h3 {{
            color: var(--primary);
            margin-bottom: 1.5rem;
            font-size: 1.3rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }}

        .footer-section p, .footer-section a {{
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            display: block;
            margin-bottom: 0.8rem;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }}

        .footer-section a:hover {{
            color: var(--primary);
            transform: translateX(5px);
        }}

        .footer-bottom {{
            text-align: center;
            color: rgba(255,255,255,0.5);
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 0.9rem;
        }}

        /* ===== LOADING ===== */
        .loading {{
            text-align: center;
            padding: 6rem 2rem;
        }}

        .spinner {{
            width: 60px;
            height: 60px;
            margin: 0 auto 1.5rem;
            border: 4px solid rgba(232, 142, 27, 0.1);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                gap: 1rem;
                padding: 0 1rem;
            }}

            .hero h2 {{
                font-size: 2.2rem;
            }}

            .hero-stats {{
                gap: 2rem;
            }}

            .filters-section {{
                padding: 0 1rem;
                margin: -2rem auto 2rem;
            }}

            .filters-card {{
                padding: 1.5rem;
                grid-template-columns: 1fr;
            }}

            .results-info {{
                flex-direction: column;
                align-items: stretch;
                gap: 1rem;
                padding: 0 1rem;
            }}

            .vehicles-section {{
                padding: 0 1rem 3rem;
            }}

            .vehicles-grid {{
                grid-template-columns: 1fr;
            }}

            .modal-content {{
                margin: 0.5rem;
            }}

            .modal-body {{
                padding: 2rem;
            }}

            .modal-title h2 {{
                font-size: 2rem;
            }}

            .contact-buttons {{
                grid-template-columns: 1fr;
            }}

            .whatsapp-float {{
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
            }}

            .whatsapp-float i {{
                font-size: 2.2rem;
            }}
        }}

        /* ===== NO RESULTS ===== */
        .no-results {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem 2rem;
            background: white;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
        }}

        .no-results i {{
            font-size: 4rem;
            color: var(--gray-light);
            margin-bottom: 1.5rem;
        }}

        .no-results h3 {{
            font-size: 1.5rem;
            color: var(--dark);
            margin-bottom: 1rem;
        }}

        .no-results p {{
            color: var(--gray);
            max-width: 400px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    <!-- HEADER -->
    <header class="header">
        <div class="header-content">
            <a href="#" class="logo">
                {"<img src='data:image/png;base64," + logo_base64 + "' alt='Garagem Multimarcas' class='logo-img'>" if logo_base64 else "<i class='fas fa-car'></i>"}
                <div class="logo-text">
                    <h1>Garagem Multimarcas</h1>
                    <span>Veículos Premium</span>
                </div>
            </a>
            <div class="header-contact">
                <a href="tel:+5584991359875" class="contact-item">
                    <i class="fas fa-phone"></i>
                    <span>(84) 99135-9875</span>
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
        <div class="hero-content">
            <h2>Encontre Seu Próximo Veículo</h2>
            <p>Qualidade, confiança e as melhores condições do mercado automotivo</p>
            
            <div class="hero-stats">
                <div class="stat-item">
                    <div class="stat-number">{total_veiculos}</div>
                    <div class="stat-label">Veículos</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">R$ {valor_total_estoque:,.0f}</div>
                    <div class="stat-label">Em Estoque</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">R$ {media_preco:,.0f}</div>
                    <div class="stat-label">Preço Médio</div>
                </div>
            </div>
        </div>
    </section>

    <!-- FILTROS -->
    <section class="filters-section">
        <div class="filters-card">
            <div class="filter-group">
                <label class="filter-label"><i class="fas fa-tag"></i> Marca</label>
                <select class="filter-select" id="filterMarca">
                    <option value="">Todas as marcas</option>
                    {''.join([f'<option value="{marca}">{marca}</option>' for marca in marcas])}
                </select>
            </div>
            <div class="filter-group">
                <label class="filter-label"><i class="fas fa-dollar-sign"></i> Preço máximo</label>
                <input type="number" class="filter-input" id="filterPreco" placeholder="R$ 0,00" step="1000">
            </div>
            <div class="filter-group">
                <label class="filter-label"><i class="fas fa-gas-pump"></i> Combustível</label>
                <select class="filter-select" id="filterCombustivel">
                    <option value="">Todos</option>
                    <option value="Gasolina">Gasolina</option>
                    <option value="Álcool">Álcool</option>
                    <option value="Flex">Flex</option>
                    <option value="Diesel">Diesel</option>
                    <option value="Elétrico">Elétrico</option>
                </select>
            </div>
            <div class="filter-group">
                <label class="filter-label"><i class="fas fa-cogs"></i> Câmbio</label>
                <select class="filter-select" id="filterCambio">
                    <option value="">Todos</option>
                    <option value="Automático">Automático</option>
                    <option value="Manual">Manual</option>
                    <option value="CVT">CVT</option>
                </select>
            </div>
            <div class="filter-actions">
                <button class="btn-filter secondary" id="btnReset">
                    <i class="fas fa-redo"></i> Limpar
                </button>
                <button class="btn-filter" id="btnFilter">
                    <i class="fas fa-filter"></i> Filtrar
                </button>
            </div>
        </div>
    </section>

    <!-- RESULTADOS -->
    <div class="results-info">
        <div class="results-count">
            <i class="fas fa-car"></i>
            <span id="vehicleCount">{total_veiculos}</span> veículos disponíveis
        </div>
        <div class="sort-options">
            <span class="sort-label">Ordenar por:</span>
            <select class="sort-select" id="sortBy">
                <option value="recent">Mais recentes</option>
                <option value="price-low">Menor preço</option>
                <option value="price-high">Maior preço</option>
                <option value="km">Menor KM</option>
                <option value="year">Ano mais novo</option>
            </select>
        </div>
    </div>

    <!-- GRID DE VEÍCULOS -->
    <div class="vehicles-section">
        <div class="vehicles-grid" id="vehiclesGrid">
            {self._gerar_grid_veiculos(veiculos)}
        </div>
    </div>

    <!-- MODAL DE DETALHES -->
    <div class="modal" id="modal">
        <div class="modal-content">
            <button class="modal-close" id="modalClose">
                <i class="fas fa-times"></i>
            </button>
            <div class="modal-gallery" id="modalGallery"></div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <!-- WHATSAPP FLUTUANTE -->
    <a href="https://wa.me/5584991359875?text=Olá! Gostaria de informações sobre os veículos disponíveis" 
       class="whatsapp-float" target="_blank" title="Fale conosco no WhatsApp">
        <i class="fab fa-whatsapp"></i>
    </a>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3><i class="fas fa-car"></i> Garagem Multimarcas</h3>
                <p>Veículos de qualidade com procedência garantida e atendimento personalizado.</p>
            </div>
            <div class="footer-section">
                <h3><i class="fas fa-phone"></i> Contato</h3>
                <a href="tel:+5584991359875">
                    <i class="fas fa-phone"></i> (84) 99135-9875
                </a>
                <a href="https://wa.me/5584991359875" target="_blank">
                    <i class="fab fa-whatsapp"></i> WhatsApp
                </a>
                <p><i class="fas fa-map-marker-alt"></i> Mossoró/RN</p>
            </div>
            <div class="footer-section">
                <h3><i class="fas fa-clock"></i> Horário</h3>
                <p><i class="fas fa-calendar-day"></i> Segunda a Sexta: 8h às 18h</p>
                <p><i class="fas fa-calendar-day"></i> Sábado: 8h às 12h</p>
            </div>
            <div class="footer-section">
                <h3><i class="fas fa-link"></i> Links</h3>
                <a href="#" onclick="location.reload()">
                    <i class="fas fa-sync-alt"></i> Atualizar Estoque
                </a>
                <a href="#" onclick="scrollToTop()">
                    <i class="fas fa-arrow-up"></i> Voltar ao Topo
                </a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; {hoje.year} Garagem Multimarcas. Todos os direitos reservados.</p>
            <p style="margin-top: 0.5rem; font-size: 0.8rem;">Desenvolvido com <i class="fas fa-heart" style="color: var(--primary);"></i> para o mercado automotivo</p>
        </div>
    </footer>

    <script>
        // DADOS DOS VEÍCULOS
        const vehiclesData = {json.dumps(veiculos, default=str)};
        let filteredVehicles = [...vehiclesData];
        const WHATSAPP_NUMBER = "5584991359875";

        // INICIALIZAR
        document.addEventListener('DOMContentLoaded', function() {{
            initFilters();
            setupEventListeners();
            updateVehicleCount();
        }});

        // INICIALIZAR FILTROS
        function initFilters() {{
            // Popular filtros já foi feito no HTML
            applyFilters();
        }}

        // CONFIGURAR EVENT LISTENERS
        function setupEventListeners() {{
            // Filtros
            document.getElementById('btnFilter').addEventListener('click', applyFilters);
            document.getElementById('btnReset').addEventListener('click', resetFilters);
            
            // Enter nos inputs
            document.getElementById('filterPreco').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') applyFilters();
            }});
            
            // Ordenação
            document.getElementById('sortBy').addEventListener('change', function() {{
                sortVehicles();
                renderVehicles();
            }});
            
            // Modal
            document.getElementById('modalClose').addEventListener('click', closeModal);
            document.getElementById('modal').addEventListener('click', function(e) {{
                if (e.target.id === 'modal') closeModal();
            }});
            
            // Fechar modal com ESC
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') closeModal();
            }});
        }}

        // APLICAR FILTROS
        function applyFilters() {{
            const marca = document.getElementById('filterMarca').value;
            const preco = parseFloat(document.getElementById('filterPreco').value) || Infinity;
            const combustivel = document.getElementById('filterCombustivel').value;
            const cambio = document.getElementById('filterCambio').value;

            filteredVehicles = vehiclesData.filter(v => {{
                return (!marca || v.marca === marca) &&
                       v.preco_venda <= preco &&
                       (!combustivel || v.combustivel === combustivel) &&
                       (!cambio || v.cambio === cambio);
            }});

            sortVehicles();
            renderVehicles();
            updateVehicleCount();
        }}

        // RESETAR FILTROS
        function resetFilters() {{
            document.getElementById('filterMarca').value = '';
            document.getElementById('filterPreco').value = '';
            document.getElementById('filterCombustivel').value = '';
            document.getElementById('filterCambio').value = '';
            document.getElementById('sortBy').value = 'recent';
            
            filteredVehicles = [...vehiclesData];
            sortVehicles();
            renderVehicles();
            updateVehicleCount();
        }}

        // ORDENAR VEÍCULOS
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
                case 'year':
                    filteredVehicles.sort((a, b) => b.ano - a.ano);
                    break;
                default: // recent
                    filteredVehicles.sort((a, b) => b.id - a.id);
            }}
        }}

        // RENDERIZAR VEÍCULOS
        function renderVehicles() {{
            const grid = document.getElementById('vehiclesGrid');
            
            if (filteredVehicles.length === 0) {{
                grid.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <h3>Nenhum veículo encontrado</h3>
                        <p>Tente ajustar os filtros ou volte mais tarde para ver novidades.</p>
                        <button class="btn-details" onclick="resetFilters()" style="margin-top: 1.5rem;">
                            <i class="fas fa-redo"></i> Limpar Filtros
                        </button>
                    </div>
                `;
                return;
            }}

            grid.innerHTML = filteredVehicles.map(vehicle => `
                <div class="vehicle-card ${{vehicle.margem > 15 ? 'highlight' : ''}}" onclick="openModal(${{vehicle.id}})">
                    <div class="vehicle-image">
                        ${{vehicle.foto_base64 ? 
                            `<img src="data:image/jpeg;base64,${{vehicle.foto_base64}}" alt="${{vehicle.marca}} ${{vehicle.modelo}}">` :
                            `<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #ccc;">
                                <i class="fas fa-car" style="font-size: 5rem;"></i>
                            </div>`
                        }}
                        <div class="vehicle-badges">
                            <div class="badge available">
                                <i class="fas fa-check"></i> Disponível
                            </div>
                            ${{vehicle.margem > 15 ? `
                                <div class="badge highlight">
                                    <i class="fas fa-star"></i> Destaque
                                </div>
                            ` : ''}}
                        </div>
                    </div>
                    <div class="vehicle-info">
                        <div class="vehicle-header">
                            <h3 class="vehicle-title">${{vehicle.marca}} ${{vehicle.modelo}}</h3>
                            <span class="vehicle-year">${{vehicle.ano}}</span>
                        </div>
                        <div class="vehicle-subtitle">
                            <i class="fas fa-palette"></i>
                            <span>${{vehicle.cor}}</span>
                            <i class="fas fa-id-card"></i>
                            <span>${{vehicle.placa || 'Placa não informada'}}</span>
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
                        <div class="vehicle-price">
                            <div class="price-content">
                                <div class="price-main">R$ ${{vehicle.preco_venda.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</div>
                                <span class="price-label">Preço à vista</span>
                            </div>
                            <button class="btn-details" onclick="event.stopPropagation(); openModal(${{vehicle.id}})">
                                <i class="fas fa-eye"></i> Detalhes
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        // ATUALIZAR CONTADOR
        function updateVehicleCount() {{
            document.getElementById('vehicleCount').textContent = filteredVehicles.length;
        }}

        // ABRIR MODAL
        function openModal(vehicleId) {{
            const vehicle = vehiclesData.find(v => v.id === vehicleId);
            if (!vehicle) return;

            const modal = document.getElementById('modal');
            const gallery = document.getElementById('modalGallery');
            const body = document.getElementById('modalBody');

            // Galeria
            gallery.innerHTML = vehicle.foto_base64 ?
                `<img src="data:image/jpeg;base64,${{vehicle.foto_base64}}" alt="${{vehicle.marca}} ${{vehicle.modelo}}">` :
                `<div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                    <i class="fas fa-car" style="font-size: 8rem; color: #666;"></i>
                </div>`;

            // Mensagem para WhatsApp
            const whatsappMsg = encodeURIComponent(`Olá! Tenho interesse no ${{vehicle.marca}} ${{vehicle.modelo}} ${{vehicle.ano}} - R$ ${{vehicle.preco_venda.toLocaleString('pt-BR')}}. Poderia me passar mais informações?`);
            
            // Conteúdo do modal
            body.innerHTML = `
                <div class="modal-header">
                    <div class="modal-title">
                        <h2>${{vehicle.marca}} ${{vehicle.modelo}}</h2>
                        <div class="modal-subtitle">
                            <span><i class="fas fa-calendar-alt"></i> ${{vehicle.ano}}</span>
                            <span><i class="fas fa-palette"></i> ${{vehicle.cor}}</span>
                            <span><i class="fas fa-id-card"></i> ${{vehicle.placa || 'N/I'}}</span>
                        </div>
                    </div>
                    <div class="modal-price">
                        <div class="price-main">R$ ${{vehicle.preco_venda.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</div>
                        <span class="price-label">Preço à vista</span>
                    </div>
                </div>

                <div class="specs-full">
                    <div class="spec-full">
                        <div class="spec-full-label"><i class="fas fa-road"></i> Quilometragem</div>
                        <div class="spec-full-value">${{vehicle.km.toLocaleString('pt-BR')}} km</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label"><i class="fas fa-gas-pump"></i> Combustível</div>
                        <div class="spec-full-value">${{vehicle.combustivel}}</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label"><i class="fas fa-cog"></i> Câmbio</div>
                        <div class="spec-full-value">${{vehicle.cambio}}</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label"><i class="fas fa-door-closed"></i> Portas</div>
                        <div class="spec-full-value">${{vehicle.portas}} portas</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label"><i class="fas fa-fingerprint"></i> Chassi</div>
                        <div class="spec-full-value">${{vehicle.chassi || 'Não informado'}}</div>
                    </div>
                    <div class="spec-full">
                        <div class="spec-full-label"><i class="fas fa-chart-line"></i> Margem</div>
                        <div class="spec-full-value">${{vehicle.margem.toFixed(1)}}%</div>
                    </div>
                </div>

                ${{vehicle.observacoes ? `
                    <div class="modal-description">
                        <h4><i class="fas fa-clipboard-list"></i> Observações</h4>
                        <p>${{vehicle.observacoes}}</p>
                    </div>
                ` : ''}}

                <div class="contact-section">
                    <h3>💬 Entre em Contato</h3>
                    <p>Fale conosco e agende uma visita para conhecer este veículo pessoalmente.</p>
                    
                    <div class="contact-buttons">
                        <a href="https://wa.me/${{WHATSAPP_NUMBER}}?text=${{whatsappMsg}}" target="_blank" class="btn-contact whatsapp">
                            <i class="fab fa-whatsapp"></i>
                            Falar no WhatsApp
                        </a>
                        <a href="tel:+${{WHATSAPP_NUMBER}}" class="btn-contact phone">
                            <i class="fas fa-phone"></i>
                            Ligar Agora
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

        // FECHAR MODAL
        function closeModal() {{
            document.getElementById('modal').classList.remove('active');
            document.body.style.overflow = 'auto';
        }}

        // ROLAR PARA O TOPO
        function scrollToTop() {{
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}

        // FORÇAR SCROLL PARA CIMA AO CARREGAR
        window.onload = function() {{
            setTimeout(() => {{
                scrollToTop();
            }}, 100);
        }};
    </script>
</body>
</html>'''
        
        # Salvar arquivo
        with open(self.vitrine_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return len(veiculos)
    
    def _gerar_grid_veiculos(self, veiculos):
        """Gera o HTML do grid de veículos"""
        if not veiculos:
            return '''
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>Nenhum veículo disponível no momento</h3>
                <p>Volte mais tarde para ver nossas novidades!</p>
            </div>
            '''
        
        items = []
        for veiculo in veiculos:
            item = f'''
            <div class="vehicle-card {'highlight' if veiculo['margem'] > 15 else ''}" onclick="openModal({veiculo['id']})">
                <div class="vehicle-image">
                    {f'<img src="data:image/jpeg;base64,{veiculo["foto_base64"]}" alt="{veiculo["marca"]} {veiculo["modelo"]}">' if veiculo['foto_base64'] else 
                     '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #ccc;"><i class="fas fa-car" style="font-size: 5rem;"></i></div>'}
                    <div class="vehicle-badges">
                        <div class="badge available">
                            <i class="fas fa-check"></i> Disponível
                        </div>
                        {f'<div class="badge highlight"><i class="fas fa-star"></i> Destaque</div>' if veiculo['margem'] > 15 else ''}
                    </div>
                </div>
                <div class="vehicle-info">
                    <div class="vehicle-header">
                        <h3 class="vehicle-title">{veiculo["marca"]} {veiculo["modelo"]}</h3>
                        <span class="vehicle-year">{veiculo["ano"]}</span>
                    </div>
                    <div class="vehicle-subtitle">
                        <i class="fas fa-palette"></i>
                        <span>{veiculo["cor"]}</span>
                        <i class="fas fa-id-card"></i>
                        <span>{veiculo["placa"] or "Placa não informada"}</span>
                    </div>
                    <div class="specs-grid">
                        <div class="spec-item">
                            <i class="fas fa-road"></i>
                            <span>{veiculo["km"]:,} km</span>
                        </div>
                        <div class="spec-item">
                            <i class="fas fa-gas-pump"></i>
                            <span>{veiculo["combustivel"]}</span>
                        </div>
                        <div class="spec-item">
                            <i class="fas fa-cog"></i>
                            <span>{veiculo["cambio"]}</span>
                        </div>
                        <div class="spec-item">
                            <i class="fas fa-door-closed"></i>
                            <span>{veiculo["portas"]} portas</span>
                        </div>
                    </div>
                    <div class="vehicle-price">
                        <div class="price-content">
                            <div class="price-main">R$ {veiculo["preco_venda"]:,.2f}</div>
                            <span class="price-label">Preço à vista</span>
                        </div>
                        <button class="btn-details" onclick="event.stopPropagation(); openModal({veiculo['id']})">
                            <i class="fas fa-eye"></i> Detalhes
                        </button>
                    </div>
                </div>
            </div>
            '''
            items.append(item)
        
        return '\n'.join(items)
    
    def atualizar_vitrine(self):
        """Atualiza a vitrine com dados atuais"""
        count = self.gerar_vitrine_html()
        print(f"✅ Vitrine premium atualizada com {count} veículos")
        return count

# === FUNÇÃO PARA INTEGRAR COM SEU APP.PY ===
def integrar_vitrine_no_app():
    """Adiciona seção da vitrine no seu app.py"""
    
    # Adicione esta função no seu app.py (na aba Configurações - tab7):
    '''
    # === VITRINE PREMIUM PARA CLIENTES ===
    st.markdown("---")
    st.markdown("#### 🌐 Vitrine Premium para Clientes")
    
    col_vit1, col_vit2, col_vit3 = st.columns(3)
    
    with col_vit1:
        if st.button("🔄 Atualizar Vitrine", use_container_width=True, help="Atualiza a vitrine com os veículos em estoque"):
            try:
                from vitrine_premium import VitrinePremium
                vitrine = VitrinePremium()
                count = vitrine.atualizar_vitrine()
                st.success(f"✅ Vitrine atualizada! **{count}** veículos disponíveis.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Erro ao atualizar vitrine: {e}")
    
    with col_vit2:
        # Verificar se arquivo existe
        if os.path.exists("vitrine_premium.html"):
            with open("vitrine_premium.html", "rb") as file:
                st.download_button(
                    label="📥 Baixar Vitrine",
                    data=file,
                    file_name="vitrine_garagem.html",
                    mime="text/html",
                    use_container_width=True,
                    help="Baixe o arquivo HTML para hospedar em seu site"
                )
        else:
            st.info("ℹ️ Gere a vitrine primeiro")
    
    with col_vit3:
        # Link para visualizar localmente
        vitrine_path = os.path.abspath("vitrine_premium.html")
        if os.path.exists("vitrine_premium.html"):
            st.markdown(f"""
            <a href="file://{vitrine_path}" target="_blank">
                <button style="width:100%; padding:12px; background:linear-gradient(135deg,#3498DB,#2980B9); color:white; border:none; border-radius:10px; font-weight:600; cursor:pointer;">
                    👁️ Abrir Vitrine
                </button>
            </a>
            """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Gere a vitrine primeiro")
    
    # Estatísticas da vitrine
    try:
        from vitrine_premium import VitrinePremium
        vitrine = VitrinePremium()
        veiculos = vitrine.get_veiculos_estoque()
        
        if veiculos:
            st.markdown("#### 📊 Estatísticas da Vitrine")
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("🚗 Veículos", len(veiculos))
            
            with col_stat2:
                valor_total = sum(v['preco_venda'] for v in veiculos)
                st.metric("💰 Valor Total", f"R$ {valor_total:,.0f}")
            
            with col_stat3:
                media_preco = valor_total / len(veiculos) if veiculos else 0
                st.metric("📊 Preço Médio", f"R$ {media_preco:,.0f}")
            
            with col_stat4:
                marcas = len(set(v['marca'] for v in veiculos))
                st.metric("🏷️ Marcas", marcas)
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
    '''

# === EXECUTAR PARA GERAR VITRINE ===
if __name__ == "__main__":
    vitrine = VitrinePremium()
    count = vitrine.atualizar_vitrine()
    
    print("\n" + "="*60)
    print("🎉 VITRINE PREMIUM GERADA COM SUCESSO!")
    print("="*60)
    print(f"📊 Total de veículos: {count}")
    print(f"📁 Arquivo gerado: vitrine_premium.html")
    print(f"🌐 Para visualizar: Abra o arquivo no navegador")
    print(f"📧 WhatsApp integrado: (84) 99135-9875")
    print("="*60)
    print("\n📋 INSTRUÇÕES:")
    print("1. O arquivo 'vitrine_premium.html' está pronto para usar")
    print("2. Para atualizar: Execute este script novamente")
    print("3. Para integrar no seu app.py: Use a função 'integrar_vitrine_no_app()'")
    print("4. Para hospedar: Faça upload do HTML em qualquer servidor web")
    print("\n✅ Pronto! A vitrine já está sincronizada com seu banco de dados.")
