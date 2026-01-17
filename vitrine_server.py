# vitrine_server.py
import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template_string, send_from_directory, jsonify
import threading
import time

app = Flask(__name__)
DB_PATH = "canal_automotivo.db"

# Template HTML mínimo que será preenchido dinamicamente
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garagem Multimarcas - Veículos Premium</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* TODO: Adicionar todo o CSS da vitrine aqui */
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body>
    <div id="app">
        <h1>Carregando veículos...</h1>
    </div>
    
    <script>
        // API endpoint para buscar veículos
        fetch('/api/veiculos')
            .then(response => response.json())
            .then(data => {
                // Renderizar veículos aqui
                console.log('Veículos carregados:', data);
            });
    </script>
</body>
</html>
'''

def get_veiculos_estoque():
    """Busca veículos do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.id, v.marca, v.modelo, v.ano, v.cor, v.preco_venda,
                   v.km, v.combustivel, v.cambio, v.portas, v.placa,
                   v.observacoes, v.foto
            FROM veiculos v
            WHERE v.status = 'Em estoque'
            ORDER BY v.data_cadastro DESC
        ''')
        
        veiculos = []
        for row in cursor.fetchall():
            veiculo = {
                'id': row[0],
                'marca': row[1],
                'modelo': row[2],
                'ano': row[3],
                'cor': row[4],
                'preco_venda': float(row[5]),
                'km': row[6] if row[6] else 0,
                'combustivel': row[7] if row[7] else 'Não informado',
                'cambio': row[8] if row[8] else 'Não informado',
                'portas': row[9] if row[9] else 4,
                'placa': row[10] if row[10] else '',
                'observacoes': row[11] if row[11] else '',
                'foto_base64': row[12] if row[12] else None
            }
            veiculos.append(veiculo)
        
        conn.close()
        return veiculos
    except Exception as e:
        print(f"Erro ao buscar veículos: {e}")
        return []

@app.route('/')
def home():
    """Página principal da vitrine"""
    veiculos = get_veiculos_estoque()
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/veiculos')
def api_veiculos():
    """API para fornecer dados em JSON"""
    veiculos = get_veiculos_estoque()
    return jsonify(veiculos)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == "__main__":
    # Porta para a vitrine (diferente do Streamlit)
    port = int(os.environ.get("PORT", 5001))
    print(f"🚀 Servidor da vitrine iniciando na porta {port}...")
    print(f"🌐 Acesse: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
