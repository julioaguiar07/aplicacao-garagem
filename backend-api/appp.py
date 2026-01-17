from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json

app = FastAPI(title="API Garagem Multimarcas", version="1.0.0")

# Permitir acesso de qualquer site (depois você restringe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def get_db_connection():
    """Conecta ao banco de dados do Railway"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL não configurada!")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

@app.get("/api/veiculos")
async def get_veiculos():
    """Retorna todos os veículos em estoque"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                v.id,
                v.marca,
                v.modelo,
                v.ano,
                v.cor,
                v.preco_venda,
                v.km,
                v.combustivel,
                v.cambio,
                v.portas,
                v.placa,
                v.chassi,
                v.observacoes,
                v.data_cadastro,
                v.status,
                (
                    SELECT encode(arquivo, 'base64')
                    FROM documentos d 
                    WHERE d.veiculo_id = v.id 
                    AND d.tipo_documento = 'Foto'
                    LIMIT 1
                ) as foto_base64
            FROM veiculos v
            WHERE v.status = 'Em estoque'
            ORDER BY v.data_cadastro DESC
        """)
        
        veiculos = cursor.fetchall()
        conn.close()
        
        # Converter para formato amigável
        formatted_veiculos = []
        for v in veiculos:
            formatted_veiculos.append({
                'id': v['id'],
                'marca': v['marca'],
                'modelo': v['modelo'],
                'ano': v['ano'],
                'cor': v['cor'],
                'preco_venda': float(v['preco_venda']),
                'km': v['km'],
                'combustivel': v['combustivel'],
                'cambio': v['cambio'],
                'portas': v['portas'],
                'placa': v['placa'],
                'chassi': v['chassi'],
                'observacoes': v['observacoes'],
                'data_cadastro': v['data_cadastro'].isoformat() if v['data_cadastro'] else None,
                'foto': v['foto_base64'],
                'badge': '🎯 POUCO USO' if v['km'] < 30000 else '⭐ SEMI-NOVO' if v['km'] < 50000 else '🚗 DISPONÍVEL'
            })
        
        return {
            'success': True,
            'count': len(formatted_veiculos),
            'veiculos': formatted_veiculos,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )

@app.get("/api/veiculos/{veiculo_id}")
async def get_veiculo_detalhes(veiculo_id: int):
    """Retorna detalhes de um veículo específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM veiculos 
            WHERE id = %s AND status = 'Em estoque'
        """, (veiculo_id,))
        
        veiculo = cursor.fetchone()
        
        if not veiculo:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        
        # Buscar fotos
        cursor.execute("""
            SELECT 
                nome_documento,
                encode(arquivo, 'base64') as foto_base64
            FROM documentos 
            WHERE veiculo_id = %s AND tipo_documento = 'Foto'
            ORDER BY data_upload DESC
        """, (veiculo_id,))
        fotos = cursor.fetchall()
        
        conn.close()
        
        return {
            'success': True,
            'veiculo': {
                'id': veiculo['id'],
                'marca': veiculo['marca'],
                'modelo': veiculo['modelo'],
                'ano': veiculo['ano'],
                'cor': veiculo['cor'],
                'preco_venda': float(veiculo['preco_venda']),
                'km': veiculo['km'],
                'combustivel': veiculo['combustivel'],
                'cambio': veiculo['cambio'],
                'portas': veiculo['portas'],
                'placa': veiculo['placa'],
                'chassi': veiculo['chassi'],
                'observacoes': veiculo['observacoes']
            },
            'fotos': fotos,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )

@app.post("/api/contato")
async def registrar_contato(data: dict):
    """Registra contato de interesse"""
    try:
        nome = data.get('nome', '').strip()
        telefone = data.get('telefone', '').strip()
        email = data.get('email', '').strip()
        mensagem = data.get('mensagem', '').strip()
        veiculo_id = data.get('veiculo_id')
        
        if not nome or not telefone:
            raise HTTPException(status_code=400, detail="Nome e telefone são obrigatórios")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contatos 
            (nome, telefone, email, tipo, veiculo_interesse, observacoes, status, data_contato)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            nome,
            telefone,
            email,
            'Lead Site',
            f"Interesse no veículo ID: {veiculo_id}" if veiculo_id else "Site geral",
            mensagem,
            'Novo',
            datetime.now().date()
        ))
        
        contato_id = cursor.fetchone()['id']
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': 'Contato registrado com sucesso!',
            'contato_id': contato_id
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )

@app.get("/api/filtros")
async def get_filtros():
    """Retorna valores para filtros"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Marcas
        cursor.execute("""
            SELECT DISTINCT marca FROM veiculos 
            WHERE status = 'Em estoque' 
            ORDER BY marca
        """)
        marcas = [row['marca'] for row in cursor.fetchall()]
        
        # Preços
        cursor.execute("""
            SELECT 
                MIN(preco_venda) as min,
                MAX(preco_venda) as max
            FROM veiculos WHERE status = 'Em estoque'
        """)
        precos = cursor.fetchone()
        
        # Combustíveis
        cursor.execute("""
            SELECT DISTINCT combustivel FROM veiculos 
            WHERE status = 'Em estoque' AND combustivel IS NOT NULL
            ORDER BY combustivel
        """)
        combustiveis = [row['combustivel'] for row in cursor.fetchall()]
        
        # Câmbios
        cursor.execute("""
            SELECT DISTINCT cambio FROM veiculos 
            WHERE status = 'Em estoque' AND cambio IS NOT NULL
            ORDER BY cambio
        """)
        cambios = [row['cambio'] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'success': True,
            'marcas': marcas,
            'precos': precos,
            'combustiveis': combustiveis,
            'cambios': cambios
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )

@app.get("/health")
async def health():
    """Verifica se a API está online"""
    return {"status": "online", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
