import sqlite3
import pandas as pd
import datetime
import os

class Database:
    def __init__(self):
        self.db_path = "canal_automotivo.db"
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de veículos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS veiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modelo TEXT NOT NULL,
                ano INTEGER NOT NULL,
                marca TEXT NOT NULL,
                cor TEXT NOT NULL,
                preco_entrada REAL NOT NULL,
                preco_venda REAL NOT NULL,
                fornecedor TEXT NOT NULL,
                km INTEGER,
                placa TEXT,
                chassi TEXT,
                combustivel TEXT,
                cambio TEXT,
                portas INTEGER,
                observacoes TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Em estoque'
            )
        ''')
        
        # Tabela de gastos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                veiculo_id INTEGER NOT NULL,
                tipo_gasto TEXT NOT NULL,
                valor REAL NOT NULL,
                data DATE NOT NULL,
                descricao TEXT,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
            )
        ''')
        
        # Tabela de vendas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                veiculo_id INTEGER NOT NULL,
                comprador TEXT NOT NULL,
                valor REAL NOT NULL,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contrato_path TEXT,
                FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
            )
        ''')
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                email TEXT,
                nivel_acesso TEXT DEFAULT 'usuario',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Usuário admin padrão
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (username, password_hash, nome, nivel_acesso)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin123', 'Administrador', 'admin'))
        
        conn.commit()
        conn.close()
    
    # Métodos para veículos
    def get_veiculos(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql('SELECT * FROM veiculos ORDER BY data_cadastro DESC', conn)
        conn.close()
        return df.to_dict('records')
    
    def add_veiculo(self, veiculo_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO veiculos 
            (modelo, ano, marca, cor, preco_entrada, preco_venda, fornecedor, km, placa, chassi, combustivel, cambio, portas, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            veiculo_data['modelo'], veiculo_data['ano'], veiculo_data['marca'],
            veiculo_data['cor'], veiculo_data['preco_entrada'], veiculo_data['preco_venda'],
            veiculo_data['fornecedor'], veiculo_data['km'], veiculo_data['placa'],
            veiculo_data['chassi'], veiculo_data['combustivel'], veiculo_data['cambio'],
            veiculo_data['portas'], veiculo_data['observacoes']
        ))
        
        conn.commit()
        conn.close()
    
    # Métodos para gastos
    def get_gastos(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql('SELECT * FROM gastos ORDER BY data DESC', conn)
        conn.close()
        return df.to_dict('records')
    
    def add_gasto(self, gasto_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO gastos (veiculo_id, tipo_gasto, valor, data, descricao)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            gasto_data['veiculo_id'], gasto_data['tipo_gasto'], gasto_data['valor'],
            gasto_data['data'], gasto_data['descricao']
        ))
        
        conn.commit()
        conn.close()
    
    # Métodos para vendas
    def get_vendas(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql('SELECT * FROM vendas ORDER BY data_venda DESC', conn)
        conn.close()
        return df.to_dict('records')
    
    def add_venda(self, venda_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vendas (veiculo_id, comprador, valor, contrato_path)
            VALUES (?, ?, ?, ?)
        ''', (
            venda_data['veiculo_id'], venda_data['comprador'], 
            venda_data['valor'], venda_data['contrato_path']
        ))
        
        # Atualizar status do veículo
        cursor.execute('''
            UPDATE veiculos SET status = 'Vendido' WHERE id = ?
        ''', (venda_data['veiculo_id'],))
        
        conn.commit()
        conn.close()
    
    # Métodos para usuários
    def verificar_login(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM usuarios WHERE username = ? AND password_hash = ?
        ''', (username, password))
        
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario:
            return {
                'id': usuario[0],
                'username': usuario[1],
                'nome': usuario[3],
                'email': usuario[4],
                'nivel_acesso': usuario[5]
            }
        return None

# Instância global do banco
db = Database()