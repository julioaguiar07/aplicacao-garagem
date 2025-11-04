import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import sqlite3
import hashlib
import os
import io
from PIL import Image, ImageDraw, ImageFont
import secrets
import hmac
import time
from functools import wraps
import psycopg2
import time
import textwrap

# =============================================
# INICIALIZAÇÃO DE SESSION STATE
# =============================================

# Garante que as variáveis de sessão existam
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'ultimo_submit' not in st.session_state:
    st.session_state.ultimo_submit = 0
if 'form_blocked' not in st.session_state:
    st.session_state.form_blocked = False

# Estados específicos para vendas
if 'veiculo_venda_selecionado' not in st.session_state:
    st.session_state.veiculo_venda_selecionado = None
if 'valor_venda_atual' not in st.session_state:
    st.session_state.valor_venda_atual = 0.0
    
# =============================================
# FUNÇÃO PARA PREVENIR LOOP DE SUBMIT
# =============================================

def prevenir_loop_submit():
    """Previne múltiplos submits rápidos - VERSÃO SUPER RESTRITIVA"""
    if 'ultimo_submit' not in st.session_state:
        st.session_state.ultimo_submit = 0
    
    agora = time.time()
    # 5 segundos para máxima segurança
    if agora - st.session_state.ultimo_submit < 5:
        tempo_restante = 5 - (agora - st.session_state.ultimo_submit)
        st.warning(f"⏳ Aguarde {tempo_restante:.1f} segundos...")
        st.stop()
    
    st.session_state.ultimo_submit = agora
    return True

# =============================================
# FUNÇÃO PARA RESETAR FORMULÁRIOS
# =============================================

def resetar_formulario():
    """Reseta o estado do formulário após submit bem-sucedido"""
    st.session_state.ultimo_submit = 0

def forcar_atualizacao_gastos():
    """Força a atualização dos dados de gastos no cache"""
    if 'cache_gastos' in st.session_state:
        del st.session_state.cache_gastos
    if 'cache_veiculos' in st.session_state:
        del st.session_state.cache_veiculos
    if 'cache_dashboard' in st.session_state:
        del st.session_state.cache_dashboard

# =============================================
# SISTEMA DE CACHE PARA ATUALIZAÇÃO RÁPIDA
# =============================================

@st.cache_data(ttl=30)  # Cache de 30 segundos
def get_veiculos_cache(_db, filtro_status=None):
    """Cache para veículos"""
    return _db.get_veiculos(filtro_status)

@st.cache_data(ttl=30)
def get_gastos_cache(_db, veiculo_id=None):
    """Cache para gastos"""
    return _db.get_gastos(veiculo_id)

@st.cache_data(ttl=30)
def get_vendas_cache(_db):
    """Cache para vendas"""
    return _db.get_vendas()

@st.cache_data(ttl=30)
def get_fluxo_caixa_cache(_db, data_inicio=None, data_fim=None):
    """Cache para fluxo de caixa"""
    return _db.get_fluxo_caixa(data_inicio, data_fim)

@st.cache_data(ttl=30)
def get_financiamentos_cache(_db, veiculo_id=None):
    """Cache para financiamentos"""
    return _db.get_financiamentos(veiculo_id)

@st.cache_data(ttl=30)
def get_contatos_cache(_db):
    """Cache para contatos"""
    return _db.get_contatos()
    
# =============================================
# FUNÇÃO AUXILIAR PARA DATAS - CORRIGIDA PARA POSTGRESQL
# =============================================

def formatar_data(data):
    """Formata data para exibição, funcionando com SQLite e PostgreSQL"""
    if data is None:
        return "Data inválida"
    
    try:
        # ✅ CORREÇÃO PARA POSTGRESQL: Verificar se é Timestamp
        if hasattr(data, 'strftime'):
            # Timestamp do PostgreSQL
            return data.strftime('%d/%m/%Y')
        elif isinstance(data, str):
            # String do SQLite
            if len(data) >= 10:
                # Converter de YYYY-MM-DD para DD/MM/YYYY
                return f"{data[8:10]}/{data[5:7]}/{data[0:4]}"
            return data
        elif hasattr(data, 'date'):
            # Date object
            return data.strftime('%d/%m/%Y')
        else:
            return str(data)
    except Exception as e:
        print(f"⚠️ Erro ao formatar data {data} ({type(data)}): {e}")
        return "Data inválida"
        
  # =============================================
# FUNÇÕES AUXILIARES PARA POSTGRESQL
# =============================================

def converter_data_postgresql(data):
    """Converte data do PostgreSQL para formato legível"""
    try:
        if hasattr(data, 'strftime'):
            return data.strftime('%Y-%m-%d')
        elif isinstance(data, str):
            return data[:10] if len(data) >= 10 else data
        return str(data)
    except:
        return "Data inválida"

def processar_timestamp_postgresql(timestamp):
    """Processa timestamp do PostgreSQL para análise"""
    try:
        if hasattr(timestamp, 'date'):
            return timestamp.date()
        elif hasattr(timestamp, 'strftime'):
            return timestamp
        elif isinstance(timestamp, str):
            return datetime.datetime.strptime(timestamp[:10], '%Y-%m-%d').date()
        return timestamp
    except:
        return datetime.datetime.now().date()      
# =============================================
# CONFIGURAÇÃO DA PÁGINA - DEVE SER O PRIMEIRO COMANDO
# =============================================

st.set_page_config(
    page_title="Canal Automotivo - Sistema Completo",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def atualizar_margem_veiculo(veiculo_id, nova_margem):
    """Atualiza a margem de negociação de um veículo"""
    conn = sqlite3.connect("canal_automotivo.db")
    cursor = conn.cursor()
    
    # Buscar preço de entrada
    cursor.execute('SELECT preco_entrada FROM veiculos WHERE id = ?', (veiculo_id,))
    resultado = cursor.fetchone()
    
    if resultado:
        preco_entrada = resultado[0]
        novo_preco_venda = preco_entrada * (1 + nova_margem/100)
        
        # Atualizar no banco
        cursor.execute('''
            UPDATE veiculos 
            SET preco_venda = ?, margem_negociacao = ? 
            WHERE id = ?
        ''', (novo_preco_venda, nova_margem, veiculo_id))
        
        conn.commit()
    
    conn.close()
    return True
    
def gerar_papel_timbrado(texto, nome_arquivo="documento_timbrado.png", margem_esquerda=50, margem_direita=50, margem_topo=200, espacamento_linhas=8):
    """Gera um documento com papel timbrado personalizado.
    - quebra o texto automaticamente por largura,
    - expande a imagem se necessário (mantendo o timbrado no topo).
    """
    try:
        # Carregar a imagem do papel timbrado
        timbrado = Image.open("papeltimbrado.png")
        img = timbrado.copy()
        draw = ImageDraw.Draw(img)

        # Carregar fonte (ajuste caminho/tamanho conforme desejar)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()

        largura_disponivel = img.width - margem_esquerda - margem_direita

        # Função que recebe um parágrafo (sem \n) e retorna lista de linhas ajustadas em pixels
        def quebrar_paragrafo(paragrafo):
            palavras = paragrafo.split()
            if not palavras:
                return ['']  # linha em branco mantém espaçamento entre parágrafos
            linhas = []
            linha_atual = palavras[0]
            for palavra in palavras[1:]:
                teste = linha_atual + ' ' + palavra
                # medir largura do texto de teste
                bbox = draw.textbbox((0,0), teste, font=font)
                largura_teste = bbox[2] - bbox[0]
                if largura_teste <= largura_disponivel:
                    linha_atual = teste
                else:
                    linhas.append(linha_atual)
                    linha_atual = palavra
            linhas.append(linha_atual)
            return linhas

        # Processar o texto: preservar parágrafos (separados por '\n\n' ou '\n')
        # Aqui tratamos cada linha do usuário: respeitamos que ele pode ter quebras manuais.
        paragrafos = texto.split('\n')
        linhas_finais = []
        for p in paragrafos:
            # Se o usuário colocou uma linha vazia, mantemos linha vazia
            if p.strip() == '':
                linhas_finais.append('')
            else:
                linhas_finais.extend(quebrar_paragrafo(p))

        # calcular altura necessária
        # altura de linha: usar bbox de uma amostra ou font.getmetrics
        sample_bbox = draw.textbbox((0,0), "Ay", font=font)
        altura_linha = (sample_bbox[3] - sample_bbox[1]) + espacamento_linhas

        y_pos = margem_topo
        linha_count = len(linhas_finais)
        altura_necessaria = y_pos + linha_count * altura_linha + 50  # 50 = margem inferior

        # Se passar da imagem, expandir
        if altura_necessaria > img.height:
            extra = altura_necessaria - img.height
            new_height = img.height + extra
            # Criar nova imagem com altura maior e mesmo modo
            new_img = Image.new(img.mode, (img.width, new_height), (255,255,255,0) if img.mode=='RGBA' else (255,255,255))
            # Colar o timbrado original no topo
            new_img.paste(img, (0,0))
            img = new_img
            draw = ImageDraw.Draw(img)

        # Escrever as linhas
        for linha in linhas_finais:
            draw.text((margem_esquerda, y_pos), linha, fill="black", font=font)
            y_pos += altura_linha

        # Salvar
        img.save(nome_arquivo)
        return nome_arquivo

    except Exception as e:
        # Se estiver usando streamlit, st.error; senão, levantar
        try:
            import streamlit as st
            st.error(f"Erro ao gerar papel timbrado: {e}")
        except:
            print(f"Erro ao gerar papel timbrado: {e}")
        return None

def seção_papel_timbrado():
    st.markdown("#### 🖋️ Gerador de Documentos com Papel Timbrado")
    
    # Formulário separado para entrada de texto
    with st.form("papel_timbrado_form", clear_on_submit=True):
        texto_documento = st.text_area("Texto do Documento", height=200, 
                                      placeholder="Digite o conteúdo do documento aqui...\nExemplo:\nCONTRATO DE VENDA\n\nEntre as partes:\nVendedor: Sua Loja\nComprador: João Silva\nVeículo: Honda Civic 2023\nValor: R$ 80.000,00")
        
        nome_documento = st.text_input("Nome do Arquivo", value="documento_oficial", placeholder="nome_do_arquivo (sem extensão)")
        
        submitted = st.form_submit_button("👁️ Gerar Documento")
    
    # Processamento fora do formulário para evitar loop
    if submitted:
        if not prevenir_loop_submit():
            st.stop()
            
        if texto_documento:
            nome_arquivo = f"{nome_documento}.png"
            arquivo_gerado = gerar_papel_timbrado(texto_documento, nome_arquivo)
            
            if arquivo_gerado:
                # Mostrar prévia
                st.image(arquivo_gerado, caption="Prévia do Documento", use_column_width=True)
                
                # Botão de download FORA do formulário
                with open(arquivo_gerado, "rb") as file:
                    st.download_button(
                        label="📥 Baixar Documento Final",
                        data=file,
                        file_name=nome_arquivo,
                        mime="image/png",
                        key="download_timbrado"
                    )
                resetar_formulario()
        else:
            st.error("❌ Digite algum texto para gerar o documento!")
            

# =============================================
# SISTEMA DE SEGURANÇA
# =============================================

import hashlib
import secrets
import hmac

def hash_password(password):
    """Cria hash seguro da senha com salt"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()
    return f"{password_hash}:{salt}"

def verify_password(stored_password, provided_password):
    """Verifica se a senha está correta"""
    try:
        stored_hash, salt = stored_password.split(':')
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hmac.compare_digest(stored_hash, computed_hash)
    except:
        return False

def login_seguro(username, password):
    """Sistema de login seguro"""
    if not username or not password:
        st.error("⚠️ Por favor, preencha todos os campos!")
        return None
    
    usuario = db.verificar_login(username, password)
    
    if usuario:
        return usuario
    else:
        st.error("❌ Usuário ou senha incorretos!")
        return None

# =============================================
# BANCO DE DADOS ADAPTADO - FUNCIONA LOCAL E NA NUVEM
# =============================================

# Importar funções de hash UMA VEZ no topo
from auth import hash_password, verify_password

class Database:
    def __init__(self):
        self.db_path = "canal_automotivo.db"
        self.init_db()
        
    def atualizar_estrutura_banco(self):
        """Atualiza a estrutura do banco se necessário - CORRIGIDO PARA POSTGRESQL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar se a coluna margem_negociacao existe
            if os.getenv('DATABASE_URL'):  # PostgreSQL
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'veiculos' AND column_name = 'margem_negociacao'
                """)
                colunas = [col[0] for col in cursor.fetchall()]
            else:  # SQLite
                cursor.execute("PRAGMA table_info(veiculos)")
                colunas = [col[1] for col in cursor.fetchall()]
            
            if 'margem_negociacao' not in colunas:
                print("🔄 Adicionando coluna 'margem_negociacao'...")
                if os.getenv('DATABASE_URL'):
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN margem_negociacao REAL DEFAULT 30')
                else:
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN margem_negociacao REAL DEFAULT 30')
                conn.commit()
                print("✅ Coluna 'margem_negociacao' adicionada!")
                
        except Exception as e:
            print(f"❌ Erro ao atualizar estrutura: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def get_sqlalchemy_connection(self):
        """Retorna conexão SQLAlchemy para pandas"""
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Para PostgreSQL no Railway
            return database_url
        else:
            # Para SQLite local
            return f"sqlite:///{self.db_path}"    
    def get_connection(self):
        """Conecta ao banco de dados correto"""
        
        database_url = os.getenv('DATABASE_URL')
        
        if database_url and database_url.startswith('postgresql://'):
            print("✅ Conectando ao PostgreSQL...")
            try:
                conn = psycopg2.connect(database_url, sslmode='require')
                print("🎉 PostgreSQL conectado com sucesso!")
                return conn
            except Exception as e:
                print(f"❌ Erro PostgreSQL: {e}")
        
        print("🔄 Usando SQLite...")
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar se estamos usando PostgreSQL
        usando_postgres = os.getenv('DATABASE_URL') is not None
        
        print(f"🗄️  Criando tabelas para: {'PostgreSQL' if usando_postgres else 'SQLite'}")
    
        # Tabela de veículos
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS veiculos (
                    id SERIAL PRIMARY KEY,
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
        else:
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
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gastos (
                    id SERIAL PRIMARY KEY,
                    veiculo_id INTEGER NOT NULL,
                    tipo_gasto TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data DATE NOT NULL,
                    descricao TEXT,
                    categoria TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER NOT NULL,
                    tipo_gasto TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data DATE NOT NULL,
                    descricao TEXT,
                    categoria TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
    
        # Tabela de vendas
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id SERIAL PRIMARY KEY,
                    veiculo_id INTEGER NOT NULL,
                    comprador_nome TEXT NOT NULL,
                    comprador_cpf TEXT,
                    comprador_endereco TEXT,
                    valor_venda REAL NOT NULL,
                    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contrato_path TEXT,
                    status TEXT DEFAULT 'Concluída',
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER NOT NULL,
                    comprador_nome TEXT NOT NULL,
                    comprador_cpf TEXT,
                    comprador_endereco TEXT,
                    valor_venda REAL NOT NULL,
                    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contrato_path TEXT,
                    status TEXT DEFAULT 'Concluída',
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
    
        # Tabela de documentos
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documentos (
                    id SERIAL PRIMARY KEY,
                    veiculo_id INTEGER NOT NULL,
                    nome_documento TEXT NOT NULL,
                    tipo_documento TEXT NOT NULL,
                    arquivo BYTEA,
                    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER NOT NULL,
                    nome_documento TEXT NOT NULL,
                    tipo_documento TEXT NOT NULL,
                    arquivo BLOB,
                    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
    
        # Tabela de fluxo de caixa
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fluxo_caixa (
                    id SERIAL PRIMARY KEY,
                    data DATE NOT NULL,
                    descricao TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    categoria TEXT,
                    valor REAL NOT NULL,
                    veiculo_id INTEGER,
                    status TEXT DEFAULT 'Pendente',
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fluxo_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data DATE NOT NULL,
                    descricao TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    categoria TEXT,
                    valor REAL NOT NULL,
                    veiculo_id INTEGER,
                    status TEXT DEFAULT 'Pendente',
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
    
        # Tabela de contatos
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contatos (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    telefone TEXT,
                    email TEXT,
                    tipo TEXT,
                    veiculo_interesse TEXT,
                    data_contato DATE,
                    status TEXT DEFAULT 'Novo',
                    observacoes TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contatos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT,
                    email TEXT,
                    tipo TEXT,
                    veiculo_interesse TEXT,
                    data_contato DATE,
                    status TEXT DEFAULT 'Novo',
                    observacoes TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
        # Tabela de usuários
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    email TEXT,
                    nivel_acesso TEXT DEFAULT 'usuario',
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
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
    
        # Tabela de financiamentos
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financiamentos (
                    id SERIAL PRIMARY KEY,
                    veiculo_id INTEGER NOT NULL,
                    tipo_financiamento TEXT NOT NULL,
                    valor_total REAL NOT NULL,
                    valor_entrada REAL,
                    num_parcelas INTEGER,
                    data_contrato DATE,
                    status TEXT DEFAULT 'Ativo',
                    observacoes TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financiamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER NOT NULL,
                    tipo_financiamento TEXT NOT NULL,
                    valor_total REAL NOT NULL,
                    valor_entrada REAL,
                    num_parcelas INTEGER,
                    data_contrato DATE,
                    status TEXT DEFAULT 'Ativo',
                    observacoes TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
                )
            ''')
    
        # Tabela de parcelas
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parcelas (
                    id SERIAL PRIMARY KEY,
                    financiamento_id INTEGER NOT NULL,
                    numero_parcela INTEGER NOT NULL,
                    valor_parcela REAL NOT NULL,
                    data_vencimento DATE NOT NULL,
                    data_pagamento DATE,
                    status TEXT DEFAULT 'Pendente',
                    forma_pagamento TEXT,
                    observacoes TEXT,
                    arquivo_comprovante BYTEA,
                    FOREIGN KEY (financiamento_id) REFERENCES financiamentos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parcelas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    financiamento_id INTEGER NOT NULL,
                    numero_parcela INTEGER NOT NULL,
                    valor_parcela REAL NOT NULL,
                    data_vencimento DATE NOT NULL,
                    data_pagamento DATE,
                    status TEXT DEFAULT 'Pendente',
                    forma_pagamento TEXT,
                    observacoes TEXT,
                    arquivo_comprovante BLOB,
                    FOREIGN KEY (financiamento_id) REFERENCES financiamentos (id)
                )
            ''')
    
        # Tabela de documentos financeiros
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documentos_financeiros (
                    id SERIAL PRIMARY KEY,
                    veiculo_id INTEGER,
                    financiamento_id INTEGER,
                    tipo_documento TEXT NOT NULL,
                    nome_arquivo TEXT NOT NULL,
                    arquivo BYTEA NOT NULL,
                    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id),
                    FOREIGN KEY (financiamento_id) REFERENCES financiamentos (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documentos_financeiros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER,
                    financiamento_id INTEGER,
                    tipo_documento TEXT NOT NULL,
                    nome_arquivo TEXT NOT NULL,
                    arquivo BLOB NOT NULL,
                    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos (id),
                    FOREIGN KEY (financiamento_id) REFERENCES financiamentos (id)
                )
            ''')
    
        # Tabela de logs de acesso
        if usando_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs_acesso (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER,
                    username TEXT,
                    data_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    sucesso BOOLEAN,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs_acesso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    username TEXT,
                    data_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    sucesso BOOLEAN,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')
    
        # Inserir usuário admin se não existir
        if usando_postgres:
            cursor.execute('''
                INSERT INTO usuarios (username, password_hash, nome, nivel_acesso)
                SELECT 'admin', %s, 'Administrador', 'admin'
                WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE username = 'admin')
            ''', (hash_password('admin123'),))
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (username, password_hash, nome, nivel_acesso)
                VALUES (?, ?, ?, ?)
            ''', ('admin', hash_password('admin123'), 'Administrador', 'admin'))
    
        conn.commit()
        conn.close()
        print("✅ Todas as tabelas criadas/verificadas com sucesso!")

    # =============================================
    # MÉTODOS ORIGINAIS - ADAPTADOS PARA AMBOS OS BANCOS
    # =============================================
        
    def salvar_foto_veiculo(self, veiculo_id, foto_bytes):
        """Salva a foto do veículo no banco"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Primeiro verificar se a coluna 'foto' existe
            if os.getenv('DATABASE_URL'):
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'veiculos' AND column_name = 'foto'
                """)
            else:
                cursor.execute("PRAGMA table_info(veiculos)")
            
            colunas = [col[1] if os.getenv('DATABASE_URL') else col[1] for col in cursor.fetchall()]
            
            # Se a coluna não existir, adicionar
            if 'foto' not in colunas:
                if os.getenv('DATABASE_URL'):
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN foto BYTEA')
                else:
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN foto BLOB')
                conn.commit()
            
            # Agora salvar a foto
            if os.getenv('DATABASE_URL'):
                cursor.execute('UPDATE veiculos SET foto = %s WHERE id = %s', (foto_bytes, veiculo_id))
            else:
                cursor.execute('UPDATE veiculos SET foto = ? WHERE id = ?', (foto_bytes, veiculo_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao salvar foto: {e}")
            return False
        finally:
            conn.close()
        
    def get_veiculos(self, filtro_status=None):
        """Busca veículos - CORRIGIDO PARA COLUNAS DUPLICADAS"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            # ✅ CORREÇÃO: Query mais específica para evitar colunas duplicadas
            query = '''
                SELECT 
                    v.id, v.modelo, v.ano, v.marca, v.cor, 
                    v.preco_entrada, v.preco_venda, v.fornecedor, 
                    v.km, v.placa, v.chassi, v.combustivel, 
                    v.cambio, v.portas, v.observacoes, 
                    v.data_cadastro, v.status,
                    COALESCE(v.margem_negociacao, 30) as margem_negociacao, v.renavam
                FROM veiculos v
            '''
            
            # Aplicar filtro de status
            if filtro_status and filtro_status != 'Todos':
                query += f" WHERE v.status = '{filtro_status}'"
            
            query += ' ORDER BY v.data_cadastro DESC'
            
            # ✅ CORREÇÃO: Usar pandas com nomes de colunas explícitos
            df = pd.read_sql(query, engine)
            
            # ✅ CORREÇÃO: Remover colunas duplicadas se existirem
            df = df.loc[:, ~df.columns.duplicated()]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar veículos: {e}")
            return []
        finally:
            engine.dispose()
    
    def add_veiculo(self, veiculo_data):
        """Adiciona veículo com tratamento robusto de erros"""
        print(f"🔍 DEBUG add_veiculo - Iniciando cadastro...")
        print(f"📦 Dados recebidos: {veiculo_data}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calcular preço de venda
        margem = veiculo_data.get('margem_negociacao', 30)
        preco_venda = veiculo_data['preco_entrada'] * (1 + margem/100)
        
        print(f"💰 Margem: {margem}% | Preço venda: R$ {preco_venda:,.2f}")
        
        try:
            # VERIFICAR qual banco estamos usando
            usando_postgres = os.getenv('DATABASE_URL') is not None
            print(f"🗄️  Banco: {'PostgreSQL' if usando_postgres else 'SQLite'}")
            
            if usando_postgres:
                # ✅ PostgreSQL
                cursor.execute('''
                    INSERT INTO veiculos 
                    (modelo, ano, marca, cor, preco_entrada, preco_venda, fornecedor, km, placa, chassi, renavam, combustivel, cambio, portas, observacoes, margem_negociacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    veiculo_data['modelo'], veiculo_data['ano'], veiculo_data['marca'],
                    veiculo_data['cor'], veiculo_data['preco_entrada'], preco_venda,
                    veiculo_data['fornecedor'], veiculo_data['km'], veiculo_data['placa'],
                    veiculo_data['chassi'], veiculo_data.get('renavam', ''),
                    veiculo_data['combustivel'], veiculo_data['cambio'],
                    veiculo_data['portas'], veiculo_data['observacoes'], margem
                ))
                veiculo_id = cursor.fetchone()[0]
                print(f"✅ PostgreSQL - Veículo cadastrado com ID: {veiculo_id}")
            else:
                # ✅ SQLite
                cursor.execute('''
                    INSERT INTO veiculos 
                    (modelo, ano, marca, cor, preco_entrada, preco_venda, fornecedor, km, placa, chassi, renavam, combustivel, cambio, portas, observacoes, margem_negociacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    veiculo_data['modelo'], veiculo_data['ano'], veiculo_data['marca'],
                    veiculo_data['cor'], veiculo_data['preco_entrada'], preco_venda,
                    veiculo_data['fornecedor'], veiculo_data['km'], veiculo_data['placa'],
                    veiculo_data['chassi'], veiculo_data['combustivel'], veiculo_data['cambio'],
                    veiculo_data['portas'], veiculo_data['observacoes'], margem
                ))
                veiculo_id = cursor.lastrowid
                print(f"✅ SQLite - Veículo cadastrado com ID: {veiculo_id}")
            
            conn.commit()
            print("💾 Commit realizado com sucesso!")
            return veiculo_id
            
        except Exception as e:
            print(f"❌ ERRO NO CADASTRO: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update_veiculo_status(self, veiculo_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('UPDATE veiculos SET status = %s WHERE id = %s', (status, veiculo_id))
        else:
            cursor.execute('UPDATE veiculos SET status = ? WHERE id = ?', (status, veiculo_id))
            
        conn.commit()
        conn.close()
        return True
    
    # Métodos para gastos
    def get_gastos(self, veiculo_id=None):
        """Busca gastos com SQLAlchemy"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            query = '''
                SELECT g.*, v.marca, v.modelo 
                FROM gastos g 
                LEFT JOIN veiculos v ON g.veiculo_id = v.id
            '''
            
            if veiculo_id:
                query += f' WHERE g.veiculo_id = {veiculo_id}'
            
            query += ' ORDER BY g.data DESC'
            
            # ✅ CORREÇÃO: Usar SQLAlchemy
            df = pd.read_sql(query, engine)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar gastos: {e}")
            return []
        finally:
            engine.dispose()
    
    def add_gasto(self, gasto_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('''
                INSERT INTO gastos (veiculo_id, tipo_gasto, valor, data, descricao, categoria)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                gasto_data['veiculo_id'], gasto_data['tipo_gasto'], gasto_data['valor'],
                gasto_data['data'], gasto_data['descricao'], gasto_data.get('categoria', 'Outros')
            ))
        else:
            cursor.execute('''
                INSERT INTO gastos (veiculo_id, tipo_gasto, valor, data, descricao, categoria)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                gasto_data['veiculo_id'], gasto_data['tipo_gasto'], gasto_data['valor'],
                gasto_data['data'], gasto_data['descricao'], gasto_data.get('categoria', 'Outros')
            ))
        
        conn.commit()
        conn.close()
        return True
    
    # Métodos para vendas
    def get_vendas(self):
        """Busca vendas - CORRIGIDO PARA POSTGRESQL"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            # ✅ CORREÇÃO: Query com aliases explícitos e nomes consistentes
            query = '''
                SELECT 
                    v.id,
                    v.veiculo_id,
                    v.comprador_nome,
                    v.comprador_cpf,
                    v.comprador_endereco,
                    v.valor_venda,
                    v.data_venda,
                    v.contrato_path,
                    v.status,
                    vei.marca,
                    vei.modelo, 
                    vei.ano, 
                    vei.cor
                FROM vendas v 
                LEFT JOIN veiculos vei ON v.veiculo_id = vei.id 
                ORDER BY v.data_venda DESC
            '''
            
            df = pd.read_sql(query, engine)
            df = df.loc[:, ~df.columns.duplicated()]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar vendas: {e}")
            return []
        finally:
            engine.dispose()
    
    def add_venda(self, venda_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if os.getenv('DATABASE_URL'):
                cursor.execute('''
                    INSERT INTO vendas (veiculo_id, comprador_nome, comprador_cpf, comprador_endereco, valor_venda, contrato_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    venda_data['veiculo_id'], venda_data['comprador_nome'], venda_data['comprador_cpf'],
                    venda_data['comprador_endereco'], venda_data['valor_venda'], venda_data.get('contrato_path')
                ))
            else:
                cursor.execute('''
                    INSERT INTO vendas (veiculo_id, comprador_nome, comprador_cpf, comprador_endereco, valor_venda, contrato_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    venda_data['veiculo_id'], venda_data['comprador_nome'], venda_data['comprador_cpf'],
                    venda_data['comprador_endereco'], venda_data['valor_venda'], venda_data.get('contrato_path')
                ))
            
            # ✅ CORREÇÃO CRÍTICA: Atualizar status do veículo para Vendido
            if os.getenv('DATABASE_URL'):
                cursor.execute('UPDATE veiculos SET status = %s WHERE id = %s', ('Vendido', venda_data['veiculo_id']))
            else:
                cursor.execute('UPDATE veiculos SET status = ? WHERE id = ?', ('Vendido', venda_data['veiculo_id']))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao registrar venda: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # Métodos para documentos
    def get_documentos(self, veiculo_id=None):
        """Busca documentos com SQLAlchemy"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            query = '''
                SELECT d.*, v.marca, v.modelo 
                FROM documentos d 
                LEFT JOIN veiculos v ON d.veiculo_id = v.id
            '''
            if veiculo_id:
                query += f' WHERE d.veiculo_id = {veiculo_id}'
            query += ' ORDER BY d.data_upload DESC'
            
            # ✅ CORREÇÃO: Usar SQLAlchemy
            df = pd.read_sql(query, engine)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar documentos: {e}")
            return []
        finally:
            engine.dispose()
    
    def add_documento(self, documento_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('''
                INSERT INTO documentos (veiculo_id, nome_documento, tipo_documento, arquivo, observacoes)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                documento_data['veiculo_id'], documento_data['nome_documento'], 
                documento_data['tipo_documento'], documento_data['arquivo'],
                documento_data.get('observacoes', '')
            ))
        else:
            cursor.execute('''
                INSERT INTO documentos (veiculo_id, nome_documento, tipo_documento, arquivo, observacoes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                documento_data['veiculo_id'], documento_data['nome_documento'], 
                documento_data['tipo_documento'], documento_data['arquivo'],
                documento_data.get('observacoes', '')
            ))
        
        conn.commit()
        conn.close()
        return True
    
    # Métodos para fluxo de caixa
    def get_fluxo_caixa(self, data_inicio=None, data_fim=None):
        """Busca fluxo de caixa com SQLAlchemy"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            query = '''
                SELECT fc.*, v.marca, v.modelo 
                FROM fluxo_caixa fc 
                LEFT JOIN veiculos v ON fc.veiculo_id = v.id
            '''
            conditions = []
            if data_inicio:
                conditions.append(f"fc.data >= '{data_inicio}'")
            if data_fim:
                conditions.append(f"fc.data <= '{data_fim}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += ' ORDER BY fc.data DESC'
            
            # ✅ CORREÇÃO: Usar SQLAlchemy
            df = pd.read_sql(query, engine)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar fluxo de caixa: {e}")
            return []
        finally:
            engine.dispose()
    
    def add_fluxo_caixa(self, fluxo_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('''
                INSERT INTO fluxo_caixa (data, descricao, tipo, categoria, valor, veiculo_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                fluxo_data['data'], fluxo_data['descricao'], fluxo_data['tipo'],
                fluxo_data['categoria'], fluxo_data['valor'], 
                fluxo_data.get('veiculo_id'), fluxo_data.get('status', 'Pendente')
            ))
        else:
            cursor.execute('''
                INSERT INTO fluxo_caixa (data, descricao, tipo, categoria, valor, veiculo_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                fluxo_data['data'], fluxo_data['descricao'], fluxo_data['tipo'],
                fluxo_data['categoria'], fluxo_data['valor'], 
                fluxo_data.get('veiculo_id'), fluxo_data.get('status', 'Pendente')
            ))
        
        conn.commit()
        conn.close()
        return True
    
    # Métodos para contatos
    def get_contatos(self):
        """Busca contatos com SQLAlchemy"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            query = 'SELECT * FROM contatos ORDER BY data_contato DESC'
            
            # ✅ CORREÇÃO: Usar SQLAlchemy
            df = pd.read_sql(query, engine)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar contatos: {e}")
            return []
        finally:
            engine.dispose()
    
    def add_contato(self, contato_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('''
                INSERT INTO contatos (nome, telefone, email, tipo, veiculo_interesse, data_contato, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                contato_data['nome'], contato_data.get('telefone'), contato_data.get('email'),
                contato_data['tipo'], contato_data.get('veiculo_interesse'), 
                contato_data.get('data_contato'), contato_data.get('observacoes')
            ))
        else:
            cursor.execute('''
                INSERT INTO contatos (nome, telefone, email, tipo, veiculo_interesse, data_contato, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                contato_data['nome'], contato_data.get('telefone'), contato_data.get('email'),
                contato_data['tipo'], contato_data.get('veiculo_interesse'), 
                contato_data.get('data_contato'), contato_data.get('observacoes')
            ))
        
        conn.commit()
        conn.close()
        return True
    
    # Métodos para usuários
    def verificar_login(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar se estamos usando PostgreSQL
        usando_postgres = os.getenv('DATABASE_URL') is not None
        
        print(f"🔐 MÉTODO verificar_login CHAMADO:")
        print(f"   Username: '{username}'")
        print(f"   Banco: {'PostgreSQL' if usando_postgres else 'SQLite'}")
        
        try:
            if usando_postgres:
                # ✅ PostgreSQL - usar %s
                cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
            else:
                # ✅ SQLite - usar ?
                cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
            
            usuario = cursor.fetchone()
            
            if usuario:
                print(f"✅ Usuário encontrado no banco: {usuario[1]}")
                
                # Verificar senha
                from auth import verify_password
                senha_correta = verify_password(usuario[2], password)
                print(f"🔒 Senha correta: {senha_correta}")
                
                if senha_correta:
                    return {
                        'id': usuario[0],
                        'username': usuario[1],
                        'nome': usuario[3],
                        'email': usuario[4],
                        'nivel_acesso': usuario[5]
                    }
            else:
                print("❌ Usuário NÃO encontrado no banco")
            
            return None
            
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            return None
        finally:
            conn.close()
    # Métodos para financiamentos
    def add_financiamento(self, financiamento_data):
        """Adiciona financiamento e marca veículo como VENDIDO"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if os.getenv('DATABASE_URL'):
                cursor.execute('''
                    INSERT INTO financiamentos 
                    (veiculo_id, tipo_financiamento, valor_total, valor_entrada, num_parcelas, data_contrato, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    financiamento_data['veiculo_id'],
                    financiamento_data['tipo_financiamento'],
                    financiamento_data['valor_total'],
                    financiamento_data.get('valor_entrada', 0),
                    financiamento_data.get('num_parcelas', 1),
                    financiamento_data.get('data_contrato'),
                    financiamento_data.get('observacoes', '')
                ))
                financiamento_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO financiamentos 
                    (veiculo_id, tipo_financiamento, valor_total, valor_entrada, num_parcelas, data_contrato, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    financiamento_data['veiculo_id'],
                    financiamento_data['tipo_financiamento'],
                    financiamento_data['valor_total'],
                    financiamento_data.get('valor_entrada', 0),
                    financiamento_data.get('num_parcelas', 1),
                    financiamento_data.get('data_contrato'),
                    financiamento_data.get('observacoes', '')
                ))
                financiamento_id = cursor.lastrowid
            
            # ✅ CORREÇÃO CRÍTICA: Atualizar status do veículo para VENDIDO
            if os.getenv('DATABASE_URL'):
                cursor.execute('UPDATE veiculos SET status = %s WHERE id = %s', 
                             ('Vendido', financiamento_data['veiculo_id']))
            else:
                cursor.execute('UPDATE veiculos SET status = ? WHERE id = ?', 
                             ('Vendido', financiamento_data['veiculo_id']))
            
            # Criar parcelas automaticamente se for parcelado
            if financiamento_data.get('num_parcelas', 1) > 1:
                valor_parcela = (financiamento_data['valor_total'] - financiamento_data.get('valor_entrada', 0)) / financiamento_data['num_parcelas']
                data_contrato = datetime.datetime.strptime(financiamento_data['data_contrato'], '%Y-%m-%d') if isinstance(financiamento_data['data_contrato'], str) else financiamento_data['data_contrato']
                
                for i in range(financiamento_data['num_parcelas']):
                    data_vencimento = data_contrato + datetime.timedelta(days=30*(i+1))
                    
                    if os.getenv('DATABASE_URL'):
                        cursor.execute('''
                            INSERT INTO parcelas (financiamento_id, numero_parcela, valor_parcela, data_vencimento)
                            VALUES (%s, %s, %s, %s)
                        ''', (financiamento_id, i+1, valor_parcela, data_vencimento))
                    else:
                        cursor.execute('''
                            INSERT INTO parcelas (financiamento_id, numero_parcela, valor_parcela, data_vencimento)
                            VALUES (?, ?, ?, ?)
                        ''', (financiamento_id, i+1, valor_parcela, data_vencimento))
            
            conn.commit()
            return financiamento_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erro ao cadastrar financiamento: {e}")
            return None
        finally:
            conn.close()

    def get_financiamentos(self, veiculo_id=None):
        """Busca financiamentos com SQLAlchemy"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            # Verificar se estamos usando PostgreSQL
            usando_postgres = os.getenv('DATABASE_URL') is not None
            
            query = '''
                SELECT f.*, v.marca, v.modelo, v.ano, v.placa,
            '''
            
            if usando_postgres:
                query += '''
                    (SELECT COUNT(*) FROM parcelas p WHERE p.financiamento_id = f.id AND p.status = 'Pendente') as parcelas_pendentes,
                    (SELECT SUM(p.valor_parcela) FROM parcelas p WHERE p.financiamento_id = f.id AND p.status = 'Pendente') as total_pendente
                '''
            else:
                query += '''
                    (SELECT COUNT(*) FROM parcelas p WHERE p.financiamento_id = f.id AND p.status = "Pendente") as parcelas_pendentes,
                    (SELECT SUM(p.valor_parcela) FROM parcelas p WHERE p.financiamento_id = f.id AND p.status = "Pendente") as total_pendente
                '''
            
            query += '''
                FROM financiamentos f
                LEFT JOIN veiculos v ON f.veiculo_id = v.id
            '''
            
            if veiculo_id:
                query += f' WHERE f.veiculo_id = {veiculo_id}'
            
            query += ' ORDER BY f.data_contrato DESC'
            
            # ✅ CORREÇÃO: Usar SQLAlchemy
            df = pd.read_sql(query, engine)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar financiamentos: {e}")
            return []
        finally:
            engine.dispose()
            
    def get_parcelas(self, financiamento_id=None, status=None):
        """Busca parcelas com SQLAlchemy"""
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.get_sqlalchemy_connection())
        
        try:
            # Verificar se estamos usando PostgreSQL
            usando_postgres = os.getenv('DATABASE_URL') is not None
            
            query = '''
                SELECT p.*, f.tipo_financiamento, v.marca, v.modelo
                FROM parcelas p
                LEFT JOIN financiamentos f ON p.financiamento_id = f.id
                LEFT JOIN veiculos v ON f.veiculo_id = v.id
            '''
            
            conditions = []
            if financiamento_id:
                conditions.append(f"p.financiamento_id = {financiamento_id}")
            if status:
                if usando_postgres:
                    conditions.append(f"p.status = '{status}'")
                else:
                    conditions.append(f'p.status = "{status}"')
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += ' ORDER BY p.data_vencimento ASC'
            
            # ✅ CORREÇÃO: Usar SQLAlchemy
            df = pd.read_sql(query, engine)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erro ao buscar parcelas: {e}")
            return []
        finally:
            engine.dispose()

    def update_parcela_status(self, parcela_id, status, data_pagamento=None, forma_pagamento=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar se estamos usando PostgreSQL
            usando_postgres = os.getenv('DATABASE_URL') is not None
            
            if usando_postgres:
                cursor.execute('''
                    UPDATE parcelas 
                    SET status = %s, data_pagamento = %s, forma_pagamento = %s
                    WHERE id = %s
                ''', (status, data_pagamento, forma_pagamento, parcela_id))
            else:
                cursor.execute('''
                    UPDATE parcelas 
                    SET status = ?, data_pagamento = ?, forma_pagamento = ?
                    WHERE id = ?
                ''', (status, data_pagamento, forma_pagamento, parcela_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar parcela: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # Método para documentos financeiros
    def add_documento_financeiro(self, documento_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('''
                INSERT INTO documentos_financeiros 
                (veiculo_id, financiamento_id, tipo_documento, nome_arquivo, arquivo, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                documento_data.get('veiculo_id'),
                documento_data.get('financiamento_id'),
                documento_data['tipo_documento'],
                documento_data['nome_arquivo'],
                documento_data['arquivo'],
                documento_data.get('observacoes', '')
            ))
        else:
            cursor.execute('''
                INSERT INTO documentos_financeiros 
                (veiculo_id, financiamento_id, tipo_documento, nome_arquivo, arquivo, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                documento_data.get('veiculo_id'),
                documento_data.get('financiamento_id'),
                documento_data['tipo_documento'],
                documento_data['nome_arquivo'],
                documento_data['arquivo'],
                documento_data.get('observacoes', '')
            ))
        
        conn.commit()
        conn.close()
        return True
    
    def delete_veiculo(self, veiculo_id):
        """Exclui um veículo e seus registros relacionados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Primeiro verificar se o veículo existe e não foi vendido
            if os.getenv('DATABASE_URL'):
                cursor.execute('SELECT status FROM veiculos WHERE id = %s', (veiculo_id,))
            else:
                cursor.execute('SELECT status FROM veiculos WHERE id = ?', (veiculo_id,))
            
            resultado = cursor.fetchone()
            if not resultado:
                return False, "Veículo não encontrado"
            
            if resultado[0] == 'Vendido':
                return False, "Não é possível excluir veículos vendidos"
            
            # Excluir registros relacionados
            if os.getenv('DATABASE_URL'):
                cursor.execute('DELETE FROM gastos WHERE veiculo_id = %s', (veiculo_id,))
                cursor.execute('DELETE FROM documentos WHERE veiculo_id = %s', (veiculo_id,))
                cursor.execute('DELETE FROM veiculos WHERE id = %s', (veiculo_id,))
            else:
                cursor.execute('DELETE FROM gastos WHERE veiculo_id = ?', (veiculo_id,))
                cursor.execute('DELETE FROM documentos WHERE veiculo_id = ?', (veiculo_id,))
                cursor.execute('DELETE FROM veiculos WHERE id = ?', (veiculo_id,))
            
            conn.commit()
            return True, "Veículo excluído com sucesso"
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao excluir veículo: {e}")
            return False, f"Erro ao excluir: {str(e)}"
        finally:
            conn.close()    
            

# Instância global do banco
db = Database()
db.atualizar_estrutura_banco()  

# =============================================
# DEBUG - VERIFICAR O QUE ESTÁ ACONTECENDO
# =============================================

def debug_database():
    """Verifica o estado do banco e usuários"""
    print("🔍 INICIANDO DEBUG DO BANCO...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Verificar se a tabela usuarios existe
    try:
        # ✅ CORREÇÃO: Usar a query correta para cada banco
        if os.getenv('DATABASE_URL'):
            # PostgreSQL
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'usuarios'
            """)
        else:
            # SQLite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        
        tabela_existe = cursor.fetchone()
        print(f"📊 Tabela 'usuarios' existe: {tabela_existe is not None}")
        
        # Verificar usuários na tabela
        cursor.execute('SELECT * FROM usuarios')
        usuarios = cursor.fetchall()
        
        print(f"👥 Usuários encontrados: {len(usuarios)}")
        for usuario in usuarios:
            print(f"   ID: {usuario[0]}, Username: '{usuario[1]}', Hash: '{usuario[2][:50]}...', Nome: '{usuario[3]}'")
            
    except Exception as e:
        print(f"❌ Erro ao verificar tabela: {e}")
    
    conn.close()

def criar_usuario_admin_seguro():
    """Garante que existe um admin seguro"""
    print("🔄 Verificando usuário admin...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        admin_existe = cursor.fetchone()[0]
        
        if admin_existe == 0:
            from auth import hash_password
            cursor.execute('''
                INSERT INTO usuarios (username, password_hash, nome, nivel_acesso)
                VALUES (?, ?, ?, ?)
            ''', ('admin', hash_password('Admin123!'), 'Administrador', 'admin'))
            conn.commit()
            print("✅ Admin criado: admin / Admin123!")
        else:
            print("✅ Admin já existe")
            
    except Exception as e:
        print(f"❌ Erro ao verificar admin: {e}")
    
    conn.close()

# Executar debug
debug_database()
criar_usuario_admin_seguro()  # ← NOVA FUNÇÃO
debug_database()

def criar_usuario_admin_se_necessario():
    """Cria usuário admin se não existir no banco"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Verificar se existe algum usuário
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Banco vazio - criar usuário admin
        print("⚠️  Banco vazio - criando usuário admin...")
        from auth import hash_password
        
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, nome, nivel_acesso)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hash_password('admin123'), 'Administrador', 'admin'))
        
        conn.commit()
        print("✅ Usuário admin criado com sucesso!")
    
    conn.close()

# Executar na inicialização
criar_usuario_admin_se_necessario()

# =============================================
# CSS COMPLETO - DESIGN PREMIUM
# =============================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem;
        padding-right: 2rem;
        background: transparent;
    }
    
    .header-premium {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0 2rem 0;
        position: relative;
    }
    
    .header-premium::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #e88e1b, #f4c220, #ffca02);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(232, 142, 27, 0.3);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        color: white;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 5px 15px rgba(232, 142, 27, 0.4);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
        background: rgba(255, 255, 255, 0.05);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px 16px;
        color: #a0a0a0;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
    }
    
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        color: white;
    }
        /* Melhorias para as tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
        background: rgba(255, 255, 255, 0.05);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 12px 16px;
        color: #a0a0a0;
        flex: 1;
        text-align: center;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================
# AUTENTICAÇÃO
# =============================================

def check_auth():
    # Inicializa sempre as variáveis de sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    return st.session_state.autenticado

def login_page():
    """Página de login premium com design moderno"""
    
    # CSS personalizado
    st.markdown("""
    <style>
        /* Fundo escuro elegante */
        .stApp {
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        }
        
        /* Container principal centralizado */
        .main .block-container {
            padding-top: 0;
            padding-bottom: 0;
        }
        
        /* Esconde elementos do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Card de login */
        .login-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 3rem 2.5rem;
            margin: 4rem auto;
            max-width: 450px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            position: relative;
        }
        
        .login-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #e88e1b, #f4c220, #ffca02);
            border-radius: 24px 24px 0 0;
        }
        
        /* Logo e branding */
        .logo-section {
            text-align: center;
            margin-bottom: 2.5rem;
        }
        
        .brand-text h1 {
            color: white;
            font-size: 2rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            background: linear-gradient(135deg, #ffffff, #e0e0e0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .brand-text p {
            color: #a0a0a0;
            margin: 0;
            font-size: 1rem;
        }
        
        /* Inputs personalizados */
        .stTextInput>div>div>input, 
        .stTextInput>div>div>input:focus {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            color: white;
            padding: 14px 16px;
            font-size: 1rem;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #e88e1b;
            box-shadow: 0 0 0 2px rgba(232, 142, 27, 0.2);
        }
        
        .stTextInput>div>div>input::placeholder {
            color: #888;
        }
        
        /* Labels dos inputs */
        .stTextInput label {
            color: #e0e0e0 !important;
            font-weight: 500;
            font-size: 0.9rem;
        }
        
        /* Botão de login */
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #e88e1b, #f4c220);
            border: none;
            border-radius: 12px;
            padding: 14px;
            font-weight: 600;
            color: white;
            font-size: 1rem;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(232, 142, 27, 0.4);
            background: linear-gradient(135deg, #f4c220, #ffca02);
        }       
        
        .credentials-title {
            color: #e88e1b;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            font-size: 0.9rem;
        }
        
        .credentials-text {
            color: #a0a0a0;
            margin: 0;
            font-size: 0.85rem;
        }
        
        /* Footer */
        .login-footer {
            text-align: center;
            margin-top: 2rem;
            color: #666;
            font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Container principal
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:

        # Tenta carregar e exibir a logo
        try:
            # Função para carregar a logo
            def get_base64_of_bin_file(bin_file):
                with open(bin_file, 'rb') as f:
                    data = f.read()
                return base64.b64encode(data).decode()
            
            logo_base64 = get_base64_of_bin_file("logoca.png")
            
            # Exibe a logo centralizada
            st.markdown(
                f'<div style="text-align: center; margin-bottom: 2rem;">'
                f'<img src="data:image/png;base64,{logo_base64}" style="height: 80px; border-radius: 12px;">'
                f'</div>',
                unsafe_allow_html=True
            )
        except:
            # Placeholder se a logo não carregar
            st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="height: 80px; width: 80px; background: linear-gradient(135deg, #e88e1b, #f4c220); border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.5rem;">
                    CA
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Formulário de login
        with st.form("login_form"):
            st.markdown("### Acesso ao Sistema")
            
            username = st.text_input(
                "Usuário",
                placeholder="Digite seu nome de usuário",
                key="username_login"
            )
            
            password = st.text_input(
                "Senha", 
                type="password",
                placeholder="Digite sua senha",
                key="password_login"
            )
            
            submitted = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submitted:
                if username and password:
                    usuario = login_seguro(username, password)
                    if usuario:
                        st.session_state.autenticado = True
                        st.session_state.usuario = usuario
                        st.success(f"✅ Bem-vindo, {usuario['nome']}!")
                        st.rerun()
                else:
                    st.error("⚠️ Por favor, preencha todos os campos!")
        
        
        st.markdown("</div>", unsafe_allow_html=True)  # Fecha o login-card

def logout():
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.rerun()

# =============================================
# VERIFICAÇÃO DE LOGIN
# =============================================

if not check_auth():
    login_page()
    st.stop()

# =============================================
# FUNÇÕES DO SISTEMA
# =============================================

def calcular_dre():
    """Calcula DRE com cache para performance"""
    vendas = get_vendas_cache(db)
    gastos = get_gastos_cache(db)
    fluxo = get_fluxo_caixa_cache(db)
    
    receitas = sum(v['valor_venda'] for v in vendas)
    despesas = sum(g['valor'] for g in gastos)
    outras_despesas = sum(f['valor'] for f in fluxo if f['tipo'] == 'Saída' and f['categoria'] != 'Vendas')
    
    lucro_bruto = receitas - despesas
    lucro_liquido = lucro_bruto - outras_despesas
    
    return {
        'receitas': receitas,
        'despesas': despesas,
        'outras_despesas': outras_despesas,
        'lucro_bruto': lucro_bruto,
        'lucro_liquido': lucro_liquido
    }

def calcular_estatisticas_veiculos():
    """Calcula estatísticas com cache para performance"""
    veiculos = get_veiculos_cache(db)
    vendas = get_vendas_cache(db)
    gastos = get_gastos_cache(db)
    
    # Estatísticas básicas
    total_veiculos = len(veiculos)
    veiculos_estoque = len([v for v in veiculos if v['status'] == 'Em estoque'])
    veiculos_vendidos = len([v for v in veiculos if v['status'] == 'Vendido'])
    
    # Gastos por veículo
    gastos_por_veiculo = {}
    for gasto in gastos:
        veiculo_id = gasto['veiculo_id']
        if veiculo_id not in gastos_por_veiculo:
            gastos_por_veiculo[veiculo_id] = 0
        gastos_por_veiculo[veiculo_id] += gasto['valor']
    
    # Gastos por categoria
    gastos_por_categoria = {}
    for gasto in gastos:
        categoria = gasto['categoria'] or 'Outros'
        if categoria not in gastos_por_categoria:
            gastos_por_categoria[categoria] = 0
        gastos_por_categoria[categoria] += gasto['valor']
    
    return {
        'total_veiculos': total_veiculos,
        'veiculos_estoque': veiculos_estoque,
        'veiculos_vendidos': veiculos_vendidos,
        'gastos_por_categoria': gastos_por_categoria,
        'gastos_por_veiculo': gastos_por_veiculo
    }

def gerar_contrato_venda(dados_venda):
    """Gera contrato de compra e venda automático formatado"""
    
    # Cálculo da descrição do pagamento
    if dados_venda['num_parcelas'] > 1:
        valor_parcela = (dados_venda['valor_total'] - dados_venda['valor_entrada']) / dados_venda['num_parcelas']
        descricao_pagamento = f"ESTOU RECEBENDO R$ {dados_venda['valor_entrada']:,.2f} DE ENTRADA, E RECEBENDO {dados_venda['num_parcelas']}X DE R$ {valor_parcela:,.2f}"
        
        if dados_venda.get('tem_troca') and dados_venda.get('troca_valor', 0) > 0:
            descricao_pagamento = f"ESTOU RECEBENDO UM CARRO {dados_venda['troca_marca_modelo']} PLACA {dados_venda['troca_placa']}, E RECEBENDO {dados_venda['valor_total']:,.2f} SENDO DIVIDIDO EM {dados_venda['num_parcelas']}X DE {valor_parcela:,.2f}"
    else:
        descricao_pagamento = f"R$ {dados_venda['valor_total']:,.2f} À VISTA"

    contrato_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 40px;
            color: #000;
        }}
        .underline {{
            text-decoration: underline;
        }}
        .center {{
            text-align: center;
        }}
        .clausula {{
            margin-top: 20px;
            margin-bottom: 15px;
        }}
        .clausula-titulo {{
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .assinaturas {{
            margin-top: 50px;
        }}
        .assinatura-line {{
            border-top: 1px solid #000;
            margin-top: 40px;
            padding-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #000;
            padding: 8px;
            text-align: center;
        }}
        .checklist-title {{
            font-weight: bold;
            margin-top: 30px;
        }}
    </style>
</head>
<body>

    <div class="center">
        <h2><u>CONTRATO DE COMPRA E VENDA DE VEÍCULO</u></h2>
    </div>

    <p><strong>VENDEDOR:</strong> <u>GARAGEM VEICULOS E LOCAÇÕES LTDA</u>, pessoa jurídica de direito privado, 
    inscrita no CNPJ nº 23.193.404/0001-44, com sede na Av. Lauro Monte, nº 475, sala B, Abolição, CEP: 59.619-000, Mossoró/RN.</p>

    <p><strong>COMPRADOR:</strong> <u>{dados_venda['comprador_nome']}</u>, CPF nº {dados_venda['comprador_cpf']}, 
    residente e domiciliado na {dados_venda['comprador_endereco']}.</p>

    <p><em>As partes acima identificadas têm, entre si, justo e acertado o presente Contrato de Compra e Venda de Veículo à prazo, 
    que se regerá pelas cláusulas seguintes e pelas condições descritas no presente.</em></p>

    <div class="clausula">
        <div class="clausula-titulo">DO OBJETO DO CONTRATO</div>
        <p><strong>Cláusula 1ª.</strong> O presente contrato tem como OBJETO a venda, realizada entre <strong>VENDEDOR</strong> e <strong>COMPRADOR</strong>, 
        compreendendo a um Veículo com as seguintes descrições: <strong>Marca/Modelo/Versão</strong>: {dados_venda['veiculo_marca']}/{dados_venda['veiculo_modelo']}, 
        <strong>Placa</strong>: {dados_venda['veiculo_placa']}, <strong>Renavam</strong>: {dados_venda['veiculo_renavam']}, 
        <strong>Ano de Fabricação</strong>: {dados_venda['veiculo_ano_fabricacao']}, <strong>Ano Modelo</strong>: {dados_venda['veiculo_ano_modelo']}, 
        <strong>Chassi</strong>: {dados_venda['veiculo_chassi']}.</p>
    </div>

    <div class="clausula">
        <div class="clausula-titulo">DAS OBRIGAÇÕES</div>
        <p><strong>Cláusula 2ª.</strong> O veículo objeto do presente contrato está sendo entregue pelo <strong>VENDEDOR</strong> ao <strong>COMPRADOR</strong> 
        na data da assinatura deste contrato, a partir da qual o <strong>COMPRADOR</strong> será responsável por todas as despesas, taxas, impostos e multas 
        por infrações cometidas a partir do horário em que o contrato for assinado, inclusive o IPVA do corrente ano.</p>
    </div>

    <div class="clausula">
        <div class="clausula-titulo">DA TRANSFERÊNCIA DE PROPRIEDADE DO VEÍCULO</div>
        <p><strong>Cláusula 3ª.</strong> O Documento Único de Transferência (DUT) será entregue ao <strong>COMPRADOR</strong>, 
        devidamente preenchido e assinado com reconhecimento de firma, no prazo de 05 (cinco) dias após a quitação.</p>
        <p><strong>Parágrafo único:</strong> O <strong>COMPRADOR</strong> está ciente do atual estado em que se encontra o bem, objeto do presente contrato, 
        recebendo-o nestas condições, nada mais tendo a reclamar, eis que vistoriou o mesmo.</p>
    </div>

    <div class="clausula">
        <div class="clausula-titulo">DO PREÇO E DO PAGAMENTO</div>
        <p><strong>Cláusula 4ª.</strong> O <strong>COMPRADOR</strong> pagará ao <strong>VENDEDOR</strong>, pela compra do veículo objeto deste contrato, {descricao_pagamento}.</p>
        <p><strong>Parágrafo primeiro:</strong> O atraso de qualquer parcela, acarretará multa de 5% (cinco por cento) do valor da parcela, e juros de 1% (um por cento) ao mês.</p>
    </div>

    <div class="clausula">
        <div class="clausula-titulo">DA GARANTIA</div>
        <p><strong>Cláusula 5ª.</strong> A <strong>VENDEDORA</strong> responde pelo bom estado e funcionamento em relação a defeitos e/ou vícios relacionados somente ao motor e câmbio do veículo pelo prazo de 90 dias, a contar da data de sua entrega, ou até os primeiros 5.000 km rodados pelo <strong>COMPRADOR</strong>, tudo conforme art. 26, II, da lei nº 8.078/90 (código de defesa do Consumidor), O VEICULO SAI HOJE {dados_venda['data_venda']} COM {dados_venda['km_atual']} KM.</p>
    </div>

    <!-- CONTINUA COM AS OUTRAS CLÁUSULAS... -->

    <div class="assinaturas">
        <p>Por estarem assim justos e contratados, firmam o presente instrumento, em duas vias de igual teor, juntamente com 2 (duas) testemunhas.</p>
        
        <p>Mossoró/RN, {dados_venda['data_venda']}.</p>

        <div class="assinatura-line">
            <p><strong>JOSE CARLOS ALVES DE MELO FILHO</strong><br>
            CPF nº 059.571.594-09<br>
            <strong>(VENDEDOR)</strong></p>
        </div>

        <div class="assinatura-line">
            <p><strong>{dados_venda['comprador_nome']}</strong><br>
            CPF nº {dados_venda['comprador_cpf']}<br>
            <strong>(COMPRADOR)</strong></p>
        </div>

        <p><strong>TESTEMUNHAS</strong></p>
        <p><strong>NOME:</strong> {dados_venda['testemunha1_nome']}<br>
        <strong>CPF:</strong> {dados_venda['testemunha1_cpf']}</p>

        <p><strong>NOME:</strong> {dados_venda['testemunha2_nome']}<br>
        <strong>CPF:</strong> {dados_venda['testemunha2_cpf']}</p>
    </div>

</body>
</html>
"""
    return contrato_html
# =============================================
# HEADER PRINCIPAL
# =============================================

usuario = st.session_state.usuario

# Header com logo à esquerda e título centralizado
col_logo, col_title, col_user = st.columns([1, 2, 1])

with col_logo:
    # Logo à esquerda
    try:
        logo = Image.open("logoca.png")
        st.image(logo, width=120)
    except:
        st.markdown("""
        <div style="font-size: 3rem;">
            🚗
        </div>
        """, unsafe_allow_html=True)

with col_title:
    # Título centralizado e maior
    st.markdown("""
    <div style="text-align: center;">
        <h1 style="margin:0; font-size: 2.2rem; background: linear-gradient(135deg, #ffffff, #e0e0e0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800;">
            Gerenciamento Garagem Multimarcas
        </h1>
        <p style="margin:0; color: #a0a0a0; font-size: 1rem;">Sistema Completo de Gestão Automotiva</p>
    </div>
    """, unsafe_allow_html=True)

with col_user:
    # Info do usuário à direita
    st.markdown(f"""
    <div style="text-align: right;">
        <p style="margin:0; font-weight: 600;">{usuario['nome']}</p>
        <p style="margin:0; color: #a0a0a0; font-size: 0.8rem;">{usuario['nivel_acesso']}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================
# MENU PRINCIPAL 
# =============================================

st.markdown("""
<style>
    .full-width-tabs .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        width: 100%;
        display: flex;
        justify-content: space-between;
    }
    .full-width-tabs .stTabs [data-baseweb="tab"] {
        flex: 1;
        text-align: center;
        font-size: 0.9rem;
        font-weight: 600;
        padding: 12px 8px;
        white-space: nowrap;
    }
    .full-width-tabs .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #e88e1b, #f4c220);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Container com a classe personalizada
with st.container():
    st.markdown('<div class="full-width-tabs">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 DASHBOARD", "🚗 VEÍCULOS", "💰 VENDAS & FINANCIAMENTOS", "📄 DOCUMENTOS", 
        "💸 FLUXO DE CAIXA", "📞 CONTATOS", "⚙️ CONFIGURAÇÕES"
    ])
    st.markdown('</div>', unsafe_allow_html=True)

with tab1:
    # DASHBOARD COMPLETO
    st.markdown("""
    <div class="glass-card">
        <h2>📊 Dashboard Gerencial</h2>
        <p style="color: #a0a0a0;">Visão completa do seu negócio em tempo real</p>
    </div>
    """, unsafe_allow_html=True)

    # Métricas principais
    veiculos = db.get_veiculos()
    vendas = db.get_vendas()
    gastos = db.get_gastos()
    dre = calcular_dre()
    stats = calcular_estatisticas_veiculos()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Estoque</h4>
            <h2>{stats['veiculos_estoque']}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">veículos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Vendas</h4>
            <h2 style="color: #27AE60;">{stats['veiculos_vendidos']}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">realizadas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Faturamento</h4>
            <h2 style="color: #27AE60;">R$ {dre['receitas']:,.0f}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Gastos</h4>
            <h2 style="color: #E74C3C;">R$ {dre['despesas']:,.0f}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">totais</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Lucro</h4>
            <h2 style="color: {'#27AE60' if dre['lucro_liquido'] >= 0 else '#E74C3C'}">R$ {dre['lucro_liquido']:,.0f}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">líquido</p>
        </div>
        """, unsafe_allow_html=True)

    # =============================================
    # ANÁLISE ESTRATÉGICA DO ESTOQUE - VISÃO AVANÇADA
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div class="glass-card">
        <h2>📊 Análise Inteligente do Estoque</h2>
        <p style="color: #a0a0a0;">Insights estratégicos sobre sua carteira de veículos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar e processar dados
    veiculos_estoque = [v for v in veiculos if v['status'] == 'Em estoque']
    veiculos_com_custos = []
    
    for veiculo in veiculos_estoque:
        gastos_veiculo = db.get_gastos(veiculo['id'])
        total_gastos = sum(g['valor'] for g in gastos_veiculo)
        custo_total = veiculo['preco_entrada'] + total_gastos
        lucro_potencial = veiculo['preco_venda'] - custo_total
        # ✅ MARGEM AJUSTADA: 0-20% conforme solicitado pelo cliente
        margem_potencial = (lucro_potencial / custo_total * 100) if custo_total > 0 else 0
        
        veiculos_com_custos.append({
            **veiculo,
            'total_gastos': total_gastos,
            'custo_total': custo_total,
            'lucro_potencial': lucro_potencial,
            'margem_potencial': margem_potencial
        })
    
    if veiculos_com_custos:
        # ANÁLISE 1: TABELA DETALHADA POR MARCA - COM CABEÇALHO CLARO
        st.markdown("#### 📋 Performance por Marca - Visão Detalhada")
        
        # CABEÇALHO EXPLICATIVO DA TABELA
        st.markdown("""
        <div style="background: rgba(232, 142, 27, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <h4 style="margin:0; color: #e88e1b;">📖 Legenda da Tabela:</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; margin-top: 0.5rem; font-size: 0.9rem;">
                <div><strong>Marca</strong></div>
                <div><strong>Qtd Veículos</strong></div>
                <div><strong>Investimento Total</strong></div>
                <div><strong>Margem Média</strong></div>
                <div><strong>Lucro Potencial</strong></div>
                <div><strong>Status Margem</strong></div>
            </div>
            <div style="font-size: 0.8rem; color: #a0a0a0; margin-top: 0.5rem;">
                ✅ Boa (≥11%) • ⚠️ Média (5-10%) • ❌ Baixa (<5%)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Agrupar por marca
        dados_marca = {}
        for veiculo in veiculos_com_custos:
            marca = veiculo['marca']
            if marca not in dados_marca:
                dados_marca[marca] = {
                    'quantidade': 0,
                    'investimento_total': 0,
                    'gastos_total': 0,
                    'compra_total': 0,
                    'margem_media': 0,
                    'lucro_total': 0,
                    'veiculos': []
                }
            
            dados_marca[marca]['quantidade'] += 1
            dados_marca[marca]['investimento_total'] += veiculo['custo_total']
            dados_marca[marca]['gastos_total'] += veiculo['total_gastos']
            dados_marca[marca]['compra_total'] += veiculo['preco_entrada']
            dados_marca[marca]['margem_media'] += veiculo['margem_potencial']
            dados_marca[marca]['lucro_total'] += veiculo['lucro_potencial']
            dados_marca[marca]['veiculos'].append(veiculo)
        
        # Calcular médias
        for marca in dados_marca:
            dados_marca[marca]['margem_media'] /= dados_marca[marca]['quantidade']
        
        # Criar DataFrame para tabela
        tabela_dados = []
        for marca, dados in dados_marca.items():
            tabela_dados.append({
                'Marca': marca,
                'Quantidade': dados['quantidade'],
                'Investimento_Total': dados['investimento_total'],
                'Compra_Total': dados['compra_total'],
                'Gastos_Total': dados['gastos_total'],
                'Margem_Media': dados['margem_media'],
                'Lucro_Potencial': dados['lucro_total']
            })
        
        # Ordenar por investimento total (maior primeiro)
        tabela_dados.sort(key=lambda x: x['Investimento_Total'], reverse=True)
        
        # CABEÇALHO DA TABELA
        st.markdown("""
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; font-weight: bold;">
            <div>🚗 MARCA</div>
            <div>📦 QTD VEÍCULOS</div>
            <div>💰 INVESTIMENTO TOTAL</div>
            <div>📊 MARGEM MÉDIA</div>
            <div>💵 LUCRO POTENCIAL</div>
            <div>🎯 STATUS</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar tabela estilizada
        for i, linha in enumerate(tabela_dados):
            cor_fundo = "rgba(255,255,255,0.02)" if i % 2 == 0 else "rgba(255,255,255,0.05)"
            
            # ✅ CRITÉRIOS DE MARGEM AJUSTADOS: 0-20%
            margem = linha['Margem_Media']
            if margem >= 11:
                cor_margem = "#27AE60"
                emoji_status = "✅"
                texto_status = "Boa"
            elif margem >= 5:
                cor_margem = "#F39C12" 
                emoji_status = "⚠️"
                texto_status = "Média"
            else:
                cor_margem = "#E74C3C"
                emoji_status = "❌"
                texto_status = "Baixa"
            
            st.markdown(f"""
            <div style="padding: 1rem; margin: 0.5rem 0; background: {cor_fundo}; border-radius: 8px; border-left: 4px solid {cor_margem};">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                    <div><strong>{linha['Marca']}</strong></div>
                    <div>{linha['Quantidade']} veículos</div>
                    <div>R$ {linha['Investimento_Total']:,.2f}</div>
                    <div style="color: {cor_margem}; font-weight: bold;">{margem:.1f}%</div>
                    <div>R$ {linha['Lucro_Potencial']:,.2f}</div>
                    <div style="color: {cor_margem}; font-weight: bold;" title="Margem {texto_status}">{emoji_status} {texto_status}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ANÁLISE 2: GRÁFICO DE BARRAS EMPILHADAS - COMPOSIÇÃO REAL DE CUSTOS
        st.markdown("#### 🏗️ Composição Real de Custos por Marca")
        
        # Top 8 marcas por investimento
        top_marcas = sorted(dados_marca.items(), key=lambda x: x[1]['investimento_total'], reverse=True)[:8]
        
        custos_compra = []
        custos_gastos = []
        nomes_marcas = []
        
        for marca, dados in top_marcas:
            custos_compra.append(dados['compra_total'])
            custos_gastos.append(dados['gastos_total'])
            nomes_marcas.append(marca)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='💰 Custo de Compra',
            x=nomes_marcas,
            y=custos_compra,
            marker_color='#e88e1b',
            hovertemplate='<b>%{x}</b><br>Custo Compra: R$ %{y:,.2f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='🔧 Gastos com Preparação',
            x=nomes_marcas,
            y=custos_gastos,
            marker_color='#3498db',
            hovertemplate='<b>%{x}</b><br>Gastos: R$ %{y:,.2f}<extra></extra>'
        ))
        
        # ANÁLISE 3: GRÁFICO INTERATIVO - TOP MODELOS POR RENTABILIDADE
        st.markdown("#### 📈 Top Modelos por Rentabilidade")
        
        # Preparar dados por modelo
        dados_modelo = {}
        for veiculo in veiculos_com_custos:
            modelo_key = f"{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']}"
            if modelo_key not in dados_modelo:
                dados_modelo[modelo_key] = {
                    'marca': veiculo['marca'],
                    'modelo': veiculo['modelo'],
                    'ano': veiculo['ano'],
                    'quantidade': 0,
                    'investimento_total': 0,
                    'custo_total': 0,
                    'preco_venda_total': 0,
                    'lucro_total': 0,
                    'margem_media': 0,
                    'veiculos': []
                }
            
            dados_modelo[modelo_key]['quantidade'] += 1
            dados_modelo[modelo_key]['investimento_total'] += veiculo['custo_total']
            dados_modelo[modelo_key]['custo_total'] += veiculo['custo_total']
            dados_modelo[modelo_key]['preco_venda_total'] += veiculo['preco_venda']
            dados_modelo[modelo_key]['lucro_total'] += veiculo['lucro_potencial']
            dados_modelo[modelo_key]['margem_media'] += veiculo['margem_potencial']
            dados_modelo[modelo_key]['veiculos'].append(veiculo)
        
        # Calcular médias
        for modelo in dados_modelo:
            dados_modelo[modelo]['margem_media'] /= dados_modelo[modelo]['quantidade']
        
        # Converter para lista e ordenar por lucro total
        modelos_ordenados = sorted(
            [(modelo, dados) for modelo, dados in dados_modelo.items()], 
            key=lambda x: x[1]['lucro_total'], 
            reverse=True
        )
        
        # Seletor de quantidade
        col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
        with col_sel1:
            num_modelos = st.slider(
                "**Selecione quantos modelos mostrar:**",
                min_value=3,
                max_value=min(15, len(modelos_ordenados)),
                value=5,
                step=1,
                help="Escolha quantos modelos deseja visualizar no gráfico"
            )
        
        with col_sel2:
            ordenar_por = st.selectbox(
                "**Ordenar por:**",
                ["Lucro Total", "Margem Média", "Investimento"],
                help="Selecione o critério de ordenação"
            )
        
        with col_sel3:
            tipo_grafico = st.selectbox(
                "**Tipo de gráfico:**",
                ["Barras + Linha", "Apenas Barras", "Apenas Linha"],
                help="Escolha a visualização do gráfico"
            )
        
        # Reordenar conforme seleção
        if ordenar_por == "Lucro Total":
            modelos_ordenados = sorted(modelos_ordenados, key=lambda x: x[1]['lucro_total'], reverse=True)
        elif ordenar_por == "Margem Média":
            modelos_ordenados = sorted(modelos_ordenados, key=lambda x: x[1]['margem_media'], reverse=True)
        else:  # Investimento
            modelos_ordenados = sorted(modelos_ordenados, key=lambda x: x[1]['investimento_total'], reverse=True)
        
        # Pegar top N modelos
        top_modelos = modelos_ordenados[:num_modelos]
        
        if top_modelos:
            # Preparar dados para o gráfico
            nomes_modelos = [f"{dados['marca']} {dados['modelo']}\n({dados['ano']})" for modelo, dados in top_modelos]
            valores_investimento = [dados['investimento_total'] for modelo, dados in top_modelos]
            valores_margem = [dados['margem_media'] for modelo, dados in top_modelos]
            valores_lucro = [dados['lucro_total'] for modelo, dados in top_modelos]
            
            fig = go.Figure()
            
            # Adicionar barras de investimento (se selecionado)
            if tipo_grafico in ["Barras + Linha", "Apenas Barras"]:
                fig.add_trace(go.Bar(
                    name='💰 Investimento Total',
                    x=nomes_modelos,
                    y=valores_investimento,
                    marker_color='#e88e1b',
                    yaxis='y',
                    opacity=0.8,
                    hovertemplate='<b>%{x}</b><br>Investimento: R$ %{y:,.2f}<br>Lucro: R$ %{customdata:,.2f}<extra></extra>',
                    customdata=valores_lucro
                ))
            
            # Adicionar linha de margem (se selecionado)
            if tipo_grafico in ["Barras + Linha", "Apenas Linha"]:
                fig.add_trace(go.Scatter(
                    name='📊 Margem Média (%)',
                    x=nomes_modelos,
                    y=valores_margem,
                    mode='lines+markers+text',
                    yaxis='y2',
                    line=dict(color='#27AE60', width=3),
                    marker=dict(size=10, color='#27AE60'),
                    text=[f"{margem:.1f}%" for margem in valores_margem],
                    textposition="top center",
                    hovertemplate='<b>%{x}</b><br>Margem: %{y:.1f}%<extra></extra>'
                ))
            
            # Configuração do layout
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=600,
                title=f"Top {num_modelos} Modelos por {ordenar_por}",
                xaxis=dict(
                    title="Modelo",
                    tickangle=-45
                ),
                yaxis=dict(
                    title="Investimento Total (R$)",
                    titlefont=dict(color='#e88e1b'),
                    tickfont=dict(color='#e88e1b'),
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)'
                ),
                yaxis2=dict(
                    title="Margem Média (%)",
                    titlefont=dict(color='#27AE60'),
                    tickfont=dict(color='#27AE60'),
                    overlaying='y',
                    side='right',
                    range=[0, max(valores_margem) * 1.2 if valores_margem else 20],
                    showgrid=False
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Adicionar linhas de referência para margem
            fig.add_hline(y=15, line_dash="dash", line_color="#27AE60", opacity=0.5, 
                          annotation_text="Meta 15%", annotation_position="top right")
            fig.add_hline(y=10, line_dash="dash", line_color="#F39C12", opacity=0.3,
                          annotation_text="Mínimo 10%", annotation_position="bottom right")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela resumo dos modelos
            st.markdown("#### 📋 Detalhes dos Modelos Selecionados")
            
            # Cabeçalho da tabela
            st.markdown("""
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; font-weight: bold;">
                <div>🚗 MODELO</div>
                <div>💰 INVESTIMENTO</div>
                <div>💵 LUCRO</div>
                <div>📊 MARGEM</div>
                <div>🎯 STATUS</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Dados da tabela
            for i, (modelo_nome, dados) in enumerate(top_modelos):
                cor_fundo = "rgba(255,255,255,0.02)" if i % 2 == 0 else "rgba(255,255,255,0.05)"
                
                # Critérios de margem
                margem = dados['margem_media']
                if margem >= 11:
                    cor_margem = "#27AE60"
                    emoji_status = "✅"
                    texto_status = "Boa"
                elif margem >= 5:
                    cor_margem = "#F39C12" 
                    emoji_status = "⚠️"
                    texto_status = "Média"
                else:
                    cor_margem = "#E74C3C"
                    emoji_status = "❌"
                    texto_status = "Baixa"
                
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; background: {cor_fundo}; border-radius: 8px; border-left: 4px solid {cor_margem};">
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                        <div>
                            <strong>{dados['marca']} {dados['modelo']}</strong><br>
                            <small style="color: #a0a0a0;">{dados['ano']} • {dados['quantidade']} un.</small>
                        </div>
                        <div>R$ {dados['investimento_total']:,.2f}</div>
                        <div>R$ {dados['lucro_total']:,.2f}</div>
                        <div style="color: {cor_margem}; font-weight: bold;">{margem:.1f}%</div>
                        <div style="color: {cor_margem}; font-weight: bold;">{emoji_status} {texto_status}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.info("📝 Nenhum modelo encontrado para análise")
        
        # ANÁLISE 3: GRÁFICO DE BARRAS - MARGEM vs INVESTIMENTO
        st.markdown("#### 📈 Rentabilidade vs Volume de Investimento")
        
        # Preparar dados
        marcas_investimento = []
        valores_investimento = []
        valores_margem = []
        
        for marca, dados in top_marcas:
            marcas_investimento.append(marca)
            valores_investimento.append(dados['investimento_total'])
            valores_margem.append(dados['margem_media'])
        
        fig = go.Figure()
        
        # Barras de investimento
        fig.add_trace(go.Bar(
            name='📦 Investimento Total',
            x=marcas_investimento,
            y=valores_investimento,
            marker_color='#e88e1b',
            yaxis='y',
            opacity=0.7
        ))
        
        # Linha de margem
        fig.add_trace(go.Scatter(
            name='📊 Margem Média (%)',
            x=marcas_investimento,
            y=valores_margem,
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='#27AE60', width=3),
            marker=dict(size=8, color='#27AE60')
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=500,
            title="Relação: Investimento vs Margem por Marca",
            xaxis_title="Marca",
            yaxis=dict(
                title="Investimento Total (R$)",
                titlefont=dict(color='#e88e1b'),
                tickfont=dict(color='#e88e1b')
            ),
            yaxis2=dict(
                title="Margem Média (%)",
                titlefont=dict(color='#27AE60'),
                tickfont=dict(color='#27AE60'),
                overlaying='y',
                side='right'
            ),
            showlegend=True
        )
        
        # ✅ LINHAS DE REFERÊNCIA AJUSTADAS: 0-20%
        fig.add_hline(y=15, line_dash="dash", line_color="#27AE60", opacity=0.5, 
                      annotation_text="Meta 15%", annotation_position="top right")
        fig.add_hline(y=10, line_dash="dash", line_color="#F39C12", opacity=0.3,
                      annotation_text="Mínimo 10%", annotation_position="bottom right")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ANÁLISE 4: RESUMO EXECUTIVO
        st.markdown("#### 🎯 Resumo Executivo do Estoque")
        
        total_investido = sum(dados['investimento_total'] for dados in dados_marca.values())
        total_lucro_potencial = sum(dados['lucro_total'] for dados in dados_marca.values())
        margem_geral = (total_lucro_potencial / total_investido * 100) if total_investido > 0 else 0
        total_veiculos = len(veiculos_com_custos)
        
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        with col_res1:
            st.metric("🚗 Veículos em Estoque", total_veiculos)
        
        with col_res2:
            st.metric("🏦 Total Investido", f"R$ {total_investido:,.2f}")
        
        with col_res3:
            st.metric("📈 Lucro Potencial", f"R$ {total_lucro_potencial:,.2f}")
        
        with col_res4:
            # Cor da métrica baseada na margem geral
            delta_color = "normal"
            if margem_geral >= 15:
                delta_color = "normal"
            elif margem_geral >= 10:
                delta_color = "off"
            else:
                delta_color = "inverse"
                
            st.metric("📊 Margem Geral", f"{margem_geral:.1f}%", delta_color=delta_color)
        
        # Marcas com melhor performance
        marcas_ordenadas_margem = sorted(dados_marca.items(), key=lambda x: x[1]['margem_media'], reverse=True)
        
        st.markdown("**🏆 Top 3 Marcas por Rentabilidade:**")
        col_top1, col_top2, col_top3 = st.columns(3)
        
        for i, (marca, dados) in enumerate(marcas_ordenadas_margem[:3]):
            with [col_top1, col_top2, col_top3][i]:
                # Cor baseada na margem
                if dados['margem_media'] >= 15:
                    cor_fundo = "rgba(39, 174, 96, 0.1)"
                    cor_texto = "#27AE60"
                elif dados['margem_media'] >= 10:
                    cor_fundo = "rgba(243, 156, 18, 0.1)"
                    cor_texto = "#F39C12"
                else:
                    cor_fundo = "rgba(231, 76, 60, 0.1)"
                    cor_texto = "#E74C3C"
                    
                st.markdown(f"""
                <div style="padding: 1rem; background: {cor_fundo}; border-radius: 8px; text-align: center;">
                    <h4>#{i+1} {marca}</h4>
                    <p style="margin: 0; font-size: 1.2rem; color: {cor_texto}; font-weight: bold;">
                        {dados['margem_media']:.1f}%
                    </p>
                    <p style="margin: 0; color: #a0a0a0; font-size: 0.8rem;">
                        {dados['quantidade']} veículos • R$ {dados['lucro_total']:,.0f}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        st.info("📝 Nenhum veículo em estoque para análise")

    
    # =============================================
    # ANÁLISES ESTRATÉGICAS
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div class="glass-card">
        <h2>📈 Análises Estratégicas e Performance</h2>
        <p style="color: #a0a0a0;">Métricas avançadas para tomada de decisão inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros para as análises
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    with col_filtro1:
        periodo_analise = st.selectbox("📅 Período de Análise", 
                                     ["Últimos 30 dias", "Últimos 90 dias", "Últimos 6 meses", "Este ano", "Todo período"])
    with col_filtro2:
        marcas_veiculos = list(set([v['marca'] for v in veiculos]))
        marca_filtro = st.selectbox("🚗 Filtrar por Marca", 
                                  ["Todas"] + marcas_veiculos)
    
    # Calcular dados filtrados
    data_atual = datetime.datetime.now()
    if periodo_analise == "Últimos 30 dias":
        data_corte = data_atual - datetime.timedelta(days=30)
    elif periodo_analise == "Últimos 90 dias":
        data_corte = data_atual - datetime.timedelta(days=90)
    elif periodo_analise == "Últimos 6 meses":
        data_corte = data_atual - datetime.timedelta(days=180)
    elif periodo_analise == "Este ano":
        data_corte = datetime.datetime(data_atual.year, 1, 1)
    else:
        data_corte = datetime.datetime(2000, 1, 1)  # Data muito antiga
    
    # Filtrar veículos
    veiculos_filtrados = []
    for veiculo in veiculos:
        data_cadastro = veiculo['data_cadastro']
        if isinstance(data_cadastro, str):
            data_cadastro = datetime.datetime.strptime(data_cadastro[:10], '%Y-%m-%d')
        elif hasattr(data_cadastro, 'date'):
            data_cadastro = data_cadastro.date()
            data_cadastro = datetime.datetime.combine(data_cadastro, datetime.time())
        
        if data_cadastro >= data_corte:
            if marca_filtro == "Todas" or veiculo['marca'] == marca_filtro:
                veiculos_filtrados.append(veiculo)
    
    # Filtrar vendas
    vendas_filtradas = []
    for venda in vendas:
        data_venda = venda['data_venda']
        
        # ✅ CORREÇÃO: Processar data do PostgreSQL corretamente
        if hasattr(data_venda, 'strftime'):
            # Timestamp do PostgreSQL
            data_venda_dt = data_venda
        elif isinstance(data_venda, str):
            # String do SQLite
            data_venda_dt = datetime.datetime.strptime(data_venda[:10], '%Y-%m-%d')
        elif hasattr(data_venda, 'date'):
            # Date object
            data_venda_dt = datetime.datetime.combine(data_venda, datetime.time())
        else:
            continue
        
        if data_venda_dt >= data_corte:
            # ✅ CORREÇÃO: Usar .get() para evitar KeyError
            venda_marca = venda.get('marca') or venda.get('veiculo_marca')
            if marca_filtro == "Todas" or venda_marca == marca_filtro:
                vendas_filtradas.append(venda)

    
    # ANÁLISE 1: PERFORMANCE DE MARGENS POR MODELO
    st.markdown("#### 💰 Análise de Rentabilidade por Modelo")
    
    # Calcular margens por modelo
    modelos_lucro = {}
    for veiculo in veiculos_filtrados:
        if veiculo['status'] == 'Vendido':
            gastos_veiculo = db.get_gastos(veiculo['id'])
            total_gastos = sum(g['valor'] for g in gastos_veiculo)
            custo_total = veiculo['preco_entrada'] + total_gastos
            
            # Encontrar a venda correspondente
            venda_veiculo = next((v for v in vendas if v['veiculo_id'] == veiculo['id']), None)
            if venda_veiculo:
                lucro = venda_veiculo['valor_venda'] - custo_total
                margem = (lucro / custo_total * 100) if custo_total > 0 else 0
                
                modelo_key = f"{veiculo['marca']} {veiculo['modelo']}"
                if modelo_key not in modelos_lucro:
                    modelos_lucro[modelo_key] = {
                        'lucro_total': 0,
                        'vendas': 0,
                        'margem_media': 0,
                        'tempo_medio_estoque': 0
                    }
                
                modelos_lucro[modelo_key]['lucro_total'] += lucro
                modelos_lucro[modelo_key]['vendas'] += 1
    
    # Calcular margem média
    for modelo in modelos_lucro:
        if modelos_lucro[modelo]['vendas'] > 0:
            modelos_lucro[modelo]['margem_media'] = modelos_lucro[modelo]['lucro_total'] / modelos_lucro[modelo]['vendas']
    
    if modelos_lucro:
        # Gráfico de barras horizontais para margens por modelo
        modelos_ordenados = sorted(modelos_lucro.items(), key=lambda x: x[1]['margem_media'], reverse=True)[:10]
        
        fig = px.bar(
            x=[dados['margem_media'] for modelo, dados in modelos_ordenados],
            y=[modelo for modelo, dados in modelos_ordenados],
            orientation='h',
            title="Top 10 Modelos por Lucro Médio",
            color=[dados['margem_media'] for modelo, dados in modelos_ordenados],
            color_continuous_scale='RdYlGn',
            labels={'x': 'Lucro Médio por Venda (R$)', 'y': 'Modelo'}
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=500,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=False)
        )
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.plotly_chart(fig, use_container_width=True)
        
        with col_graf2:
            # Métricas de performance
            st.markdown("#### 🎯 KPIs de Performance")
            
            lucro_total_periodo = sum(v['valor_venda'] for v in vendas_filtradas) - sum(v['preco_entrada'] for v in veiculos_filtrados if v['status'] == 'Vendido')
            ticket_medio = sum(v['valor_venda'] for v in vendas_filtradas) / len(vendas_filtradas) if vendas_filtradas else 0
            veiculos_em_estoque = [v for v in veiculos_filtrados if v['status'] == 'Em estoque']
            giro_estoque = len(vendas_filtradas) / len(veiculos_em_estoque) if veiculos_em_estoque else 0
            
            col_kpi1, col_kpi2 = st.columns(2)
            with col_kpi1:
                st.metric("💰 Lucro no Período", f"R$ {lucro_total_periodo:,.0f}")
                st.metric("📦 Ticket Médio", f"R$ {ticket_medio:,.0f}")
            with col_kpi2:
                st.metric("🔄 Giro de Estoque", f"{giro_estoque:.1f}x")
                st.metric("🚗 Vendas/Mês", f"{len(vendas_filtradas)/max(1, (data_atual - data_corte).days/30):.1f}")
    
    # ANÁLISE 2: EFICIÊNCIA OPERACIONAL
    st.markdown("---")
    st.markdown("#### ⚡ Eficiência Operacional e Custos")
    
    col_eff1, col_eff2 = st.columns(2)
    
    with col_eff1:
        # Análise de custos por categoria
        gastos_categoria = {}
        for veiculo in veiculos_filtrados:
            gastos_veiculo = db.get_gastos(veiculo['id'])
            for gasto in gastos_veiculo:
                categoria = gasto['categoria'] or 'Outros'
                if categoria not in gastos_categoria:
                    gastos_categoria[categoria] = 0
                gastos_categoria[categoria] += gasto['valor']
        
        if gastos_categoria:
            # Treemap para visualização de custos
            categorias = list(gastos_categoria.keys())
            valores = list(gastos_categoria.values())
            
            fig = px.treemap(
                names=categorias,
                parents=[''] * len(categorias),
                values=valores,
                title="Distribuição de Custos por Categoria",
                color=valores,
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col_eff2:
        # Análise de tempo de estoque
        tempos_estoque = []
        modelos_tempo = {}
        
        for veiculo in veiculos_filtrados:
            if veiculo['status'] == 'Vendido':
                # ✅ CORREÇÃO: Lidar com Timestamp do PostgreSQL - PARA ANÁLISE
                data_cadastro = veiculo['data_cadastro']
                if isinstance(data_cadastro, str):
                    # Se for string (SQLite), converter
                    data_cadastro = datetime.datetime.strptime(data_cadastro[:10], '%Y-%m-%d')
                elif hasattr(data_cadastro, 'date'):
                    # Se for Timestamp (PostgreSQL), extrair a data
                    data_cadastro = data_cadastro.date()
                    data_cadastro = datetime.datetime.combine(data_cadastro, datetime.time())
                
                venda_veiculo = next((v for v in vendas if v['veiculo_id'] == veiculo['id']), None)
                if venda_veiculo:
                    # ✅ CORREÇÃO: Lidar com data_venda também
                    data_venda = venda_veiculo['data_venda']
                    if isinstance(data_venda, str):
                        data_venda = datetime.datetime.strptime(data_venda[:10], '%Y-%m-%d')
                    elif hasattr(data_venda, 'date'):
                        data_venda = data_venda.date()
                        data_venda = datetime.datetime.combine(data_venda, datetime.time())
                    
                    tempo_estoque = (data_venda - data_cadastro).days
                    tempos_estoque.append(tempo_estoque)
                    
                    modelo_key = f"{veiculo['marca']} {veiculo['modelo']}"
                    if modelo_key not in modelos_tempo:
                        modelos_tempo[modelo_key] = []
                    modelos_tempo[modelo_key].append(tempo_estoque)
        
        if tempos_estoque:
            # Calcular tempo médio por modelo
            tempo_medio_modelos = {modelo: sum(tempos)/len(tempos) for modelo, tempos in modelos_tempo.items()}
            modelos_rapidos = sorted(tempo_medio_modelos.items(), key=lambda x: x[1])[:8]
            
            fig = px.bar(
                x=[tempo for modelo, tempo in modelos_rapidos],
                y=[modelo for modelo, tempo in modelos_rapidos],
                orientation='h',
                title="Modelos com Menor Tempo no Estoque (dias)",
                color=[tempo for modelo, tempo in modelos_rapidos],
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ANÁLISE 3: TENDÊNCIAS E SAZONALIDADE
    st.markdown("---")
    st.markdown("#### 📈 Tendências e Previsões")
    
    # Análise de sazonalidade - CORRIGIDA PARA POSTGRESQL
    if vendas:
        vendas_por_mes = {}
        for venda in vendas:
            if venda.get('data_venda'):
                try:
                    # ✅ CORREÇÃO PARA POSTGRESQL: Processar Timestamp corretamente
                    data_venda = venda['data_venda']
                    
                    # Se for Timestamp do PostgreSQL
                    if hasattr(data_venda, 'strftime'):
                        mes_ano = data_venda.strftime("%Y-%m")
                    elif isinstance(data_venda, str):
                        # Se for string, tentar converter
                        data_venda = datetime.datetime.strptime(data_venda[:10], '%Y-%m-%d')
                        mes_ano = data_venda.strftime("%Y-%m")
                    else:
                        continue
                        
                    if mes_ano not in vendas_por_mes:
                        vendas_por_mes[mes_ano] = 0
                    vendas_por_mes[mes_ano] += venda['valor_venda']
                except Exception as e:
                    print(f"⚠️ Erro ao processar data da venda ({type(venda['data_venda'])}): {e}")
                    continue
    
        # Ordenar por data se houver dados
        if vendas_por_mes:
            meses_ordenados = sorted(vendas_por_mes.items())
            meses = [mes for mes, valor in meses_ordenados[-12:]]  # Últimos 12 meses
            valores = [valor for mes, valor in meses_ordenados[-12:]]
            
            if len(valores) > 1:
                col_trend1, col_trend2 = st.columns(2)
                
                with col_trend1:
                    # Gráfico de tendência
                    fig = px.line(
                        x=meses,
                        y=valores,
                        title="Evolução de Vendas (Últimos 12 meses)",
                        markers=True
                    )
                    
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        height=400,
                        xaxis_title="Mês",
                        yaxis_title="Valor de Vendas (R$)",
                        showlegend=False
                    )
                    
                    fig.update_traces(line=dict(color='#e88e1b', width=3))
                    
                    st.plotly_chart(fig, use_container_width=True)
            
                with col_trend2:
                    # Análise de preços médios
                    precos_por_marca = {}
                    for veiculo in veiculos_filtrados:
                        if veiculo['status'] == 'Vendido':
                            # ✅ CORREÇÃO: Lidar com Timestamp do PostgreSQL
                            data_cadastro = veiculo['data_cadastro']
                            if isinstance(data_cadastro, str):
                                data_cadastro = datetime.datetime.strptime(data_cadastro[:10], '%Y-%m-%d')
                            elif hasattr(data_cadastro, 'date'):
                                data_cadastro = data_cadastro.date()
                                data_cadastro = datetime.datetime.combine(data_cadastro, datetime.time())
                            
                            venda_veiculo = next((v for v in vendas if v['veiculo_id'] == veiculo['id']), None)
                            if venda_veiculo:
                                marca = veiculo['marca']
                                if marca not in precos_por_marca:
                                    precos_por_marca[marca] = []
                                precos_por_marca[marca].append(venda_veiculo['valor_venda'])
                
       
    # =============================================
    # ANÁLISES AVANÇADAS DE FINANCIAMENTOS
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div class="glass-card">
        <h2>🏦 Análise de Recebíveis e Financiamentos</h2>
        <p style="color: #a0a0a0;">Visão completa do seu fluxo de recebíveis e saúde financeira</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar dados de financiamentos
    financiamentos = db.get_financiamentos()
    parcelas = db.get_parcelas()
    
    # ✅ CORREÇÃO: Função para processar datas do PostgreSQL
    def processar_data_postgresql(data):
        """Processa data do PostgreSQL (pode ser string ou date object)"""
        if data is None:
            return None
        if isinstance(data, str):
            return datetime.datetime.strptime(data, '%Y-%m-%d').date()
        elif hasattr(data, 'date'):
            return data.date() if hasattr(data, 'date') else data
        return data

    # Cálculos para métricas - CORRIGIDOS PARA POSTGRESQL
    parcelas_pendentes = [p for p in parcelas if p['status'] == 'Pendente']
    
    # ✅ CORREÇÃO: Filtrar parcelas vencidas
    parcelas_vencidas = [p for p in parcelas_pendentes if p['data_vencimento'] and processar_data_postgresql(p['data_vencimento']) < datetime.datetime.now().date()]
    
    # ✅ CORREÇÃO: Filtrar parcelas deste mês  
    parcelas_este_mes = [p for p in parcelas_pendentes if p['data_vencimento'] and processar_data_postgresql(p['data_vencimento']).month == datetime.datetime.now().date().month]
    
    total_a_receber = sum(p['valor_parcela'] for p in parcelas_pendentes)
    total_vencido = sum(p['valor_parcela'] for p in parcelas_vencidas)
    total_este_mes = sum(p['valor_parcela'] for p in parcelas_este_mes)
    
    # Métricas de Financiamentos
    col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
    
    with col_fin1:
        st.metric(
            "📈 Financiamentos Ativos", 
            len([f for f in financiamentos if f['status'] == 'Ativo']),
            delta=f"{len(financiamentos)} total"
        )
    
    with col_fin2:
        st.metric(
            "⚠️ Parcelas Vencidas", 
            len(parcelas_vencidas),
            delta=f"R$ {total_vencido:,.0f}",
            delta_color="inverse"
        )
    
    with col_fin3:
        st.metric(
            "💰 Receber Este Mês", 
            f"R$ {total_este_mes:,.0f}",
            delta=f"{len(parcelas_este_mes)} parcelas"
        )
    
    with col_fin4:
        st.metric(
            "🏦 Total a Receber", 
            f"R$ {total_a_receber:,.0f}",
            delta=f"{len(parcelas_pendentes)} parcelas"
        )
    
    # Gráficos de Análise
    col_anal1, col_anal2 = st.columns(2)
    
    with col_anal1:
        st.markdown("""
        <div class="glass-card">
            <h4>📊 Distribuição de Parcelas por Status</h4>
        """, unsafe_allow_html=True)
        
        if parcelas:
            # Agrupar por status
            status_data = {}
            for parcela in parcelas:
                status = parcela['status']
                if status not in status_data:
                    status_data[status] = 0
                status_data[status] += parcela['valor_parcela']
            
            if status_data:
                fig = px.pie(
                    values=list(status_data.values()),
                    names=list(status_data.keys()),
                    title="",
                    color_discrete_sequence=['#27AE60', '#E74C3C', '#F39C12', '#3498DB']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Nenhuma parcela registrada")
        else:
            st.info("📊 Nenhuma parcela registrada")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_anal2:
        st.markdown("""
        <div class="glass-card">
            <h4>📈 Previsão de Recebíveis (Próximos 3 Meses)</h4>
        """, unsafe_allow_html=True)
        
        if parcelas_pendentes:
            # Calcular previsão para os próximos 3 meses
            meses_previsao = []
            valores_previsao = []
            
            for i in range(3):
                mes_data = datetime.datetime.now().date() + datetime.timedelta(days=30*i)
                mes_nome = mes_data.strftime("%b/%Y")
                
            # Linha ~2654-2659 - Previsão de recebíveis (CORRIGIDA):
            valor_mes = sum(
                p['valor_parcela'] for p in parcelas_pendentes 
                if p['data_vencimento'] and processar_data_postgresql(p['data_vencimento']).month == mes_data.month and
                processar_data_postgresql(p['data_vencimento']).year == mes_data.year
            )

                
            meses_previsao.append(mes_nome)
            valores_previsao.append(valor_mes)
            
            if any(valores_previsao):
                fig = px.bar(
                    x=meses_previsao,
                    y=valores_previsao,
                    title="",
                    color=valores_previsao,
                    color_continuous_scale='viridis'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400,
                    xaxis_title="Mês",
                    yaxis_title="Valor (R$)",
                    showlegend=False
                )
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📈 Nenhuma parcela prevista para os próximos meses")
        else:
            st.info("📈 Nenhuma parcela pendente")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Análise de Risco e Performance
    col_anal3, col_anal4 = st.columns(2)
    
    with col_anal3:
        st.markdown("""
        <div class="glass-card">
            <h4>⚡ Performance por Tipo de Financiamento</h4>
        """, unsafe_allow_html=True)
        
        if financiamentos:
            # Agrupar por tipo de financiamento
            tipo_data = {}
            for fin in financiamentos:
                tipo = fin['tipo_financiamento']
                if tipo not in tipo_data:
                    tipo_data[tipo] = {
                        'total': 0,
                        'pendente': 0,
                        'quantidade': 0
                    }
                tipo_data[tipo]['total'] += fin['valor_total']
                tipo_data[tipo]['pendente'] += fin['total_pendente'] or 0
                tipo_data[tipo]['quantidade'] += 1
            
            if tipo_data:
                # Criar DataFrame para o gráfico
                tipos = list(tipo_data.keys())
                totais = [tipo_data[t]['total'] for t in tipos]
                pendentes = [tipo_data[t]['pendente'] for t in tipos]
                
                fig = go.Figure(data=[
                    go.Bar(name='Total Contratado', x=tipos, y=totais, marker_color='#e88e1b'),
                    go.Bar(name='A Receber', x=tipos, y=pendentes, marker_color='#27AE60')
                ])
                
                fig.update_layout(
                    barmode='group',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400,
                    xaxis_title="Tipo de Financiamento",
                    yaxis_title="Valor (R$)",
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("⚡ Nenhum financiamento ativo")
        else:
            st.info("⚡ Nenhum financiamento cadastrado")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_anal4:
        st.markdown("""
        <div class="glass-card">
            <h4>🎯 Indicadores de Saúde Financeira</h4>
        """, unsafe_allow_html=True)
        
        # Calcular indicadores
        total_financiado = sum(f['valor_total'] for f in financiamentos if f['status'] == 'Ativo')
        taxa_recebimento = ((total_a_receber - total_vencido) / total_a_receber * 100) if total_a_receber > 0 else 100
        
        # Cards de indicadores
        st.metric("📦 Valor Total Financiado", f"R$ {total_financiado:,.2f}")
        st.metric("✅ Taxa de Recebimento", f"{taxa_recebimento:.1f}%")
        st.metric("⏰ Dias Médios de Atraso", 
                 f"{sum((datetime.datetime.now().date() - processar_data_postgresql(p['data_vencimento']).date()).days for p in parcelas_vencidas) / len(parcelas_vencidas) if parcelas_vencidas else 0:.1f}")
        st.metric("📋 Carteira Ativa", f"{len([f for f in financiamentos if f['status'] == 'Ativo'])} contratos")
        
        st.markdown("</div>", unsafe_allow_html=True)
with tab2:
    # GESTÃO DE VEÍCULOS
    st.markdown("""
    <div class="glass-card">
        <h2>🚗 Gestão de Veículos</h2>
        <p style="color: #a0a0a0;">Cadastro completo e gestão do seu estoque</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_veic1, col_veic2 = st.columns([1, 2])

    with col_veic1:
        st.markdown("#### ➕ Novo Veículo")
        with st.form("novo_veiculo_form", clear_on_submit=True):
            modelo = st.text_input("Modelo*", placeholder="Gol")
            marca = st.text_input("Marca*", placeholder="Volkswagen")
            ano = st.number_input("Ano*", min_value=1970, max_value=2030, value=2025)
            cor = st.selectbox("Cor*", ["Prata", "Preto", "Branco", "Vermelho", "Azul", "Cinza", "Verde", "Laranja"])
            st.markdown("#### 📄 Dados para Contrato")
            renavam = st.text_input("RENAVAM", placeholder="12345678901", key="renavam_input")
            chassi = st.text_input("Chassi", placeholder="9BWZZZ377VT004251")
            ano_fabricacao = st.number_input("Ano de Fabricação", min_value=1970, max_value=2030, value=2025)
            ano_modelo = st.number_input("Ano Modelo", min_value=1970, max_value=2030, value=2025)
            
            # ✅✅✅ SOLUÇÃO DEFINITIVA - Campo de preço BR
            preco_input = st.text_input(
                "Preço de Custo (R$)*", 
                placeholder="Ex: 50.000,00",
                help="Use ponto para milhares e vírgula para centavos"
            )
            
            # ✅ PRÉ-VISUALIZAÇÃO EM TEMPO REAL
            if preco_input:
                try:
                    # Tentar converter e mostrar prévia
                    preco_convertido = float(preco_input.replace('.', '').replace(',', '.'))
                    preco_formatado = f"R$ {preco_convertido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    st.info(f"💡 **Pré-visualização:** {preco_formatado}")
                except:
                    # Se não conseguir converter, mostra aviso
                    st.warning("⚠️ Digite o valor no formato correto: 50.000,00")
            
            margem_negociacao = st.slider("Margem para Negociação (%)", min_value=0, max_value=20, value=12,
                                        help="Percentual acrescido para negociação")
            
            # Calcular preço de venda automaticamente
            if preco_input:
                try:
                    preco_convertido = float(preco_input.replace('.', '').replace(',', '.'))
                    preco_venda_negociacao = preco_convertido * (1 + margem_negociacao/100)
                    preco_venda_formatado = f"R$ {preco_venda_negociacao:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    st.info(f"💰 **Preço para Negociação:** {preco_venda_formatado}")
                except:
                    st.error("❌ Valor inválido no preço de custo")
            
            fornecedor = st.text_input("Fornecedor*", placeholder="Nome do fornecedor")
            km = st.number_input("Quilometragem", value=0)
            placa = st.text_input("Placa", placeholder="ABC1D23")            
            combustivel = st.selectbox("Combustível", ["Gasolina", "Álcool", "Flex", "Diesel", "Elétrico"])
            cambio = st.selectbox("Câmbio", ["Automático", "Manual", "CVT"])
            portas = st.selectbox("Portas", [2, 4, 5])
            observacoes = st.text_area("Observações")
            foto_veiculo = st.file_uploader("Foto do Veículo", type=['jpg', 'jpeg', 'png'], 
                               help="Faça upload da foto principal do veículo")
            
            submitted = st.form_submit_button("Cadastrar Veículo", use_container_width=True)
            
            if submitted:
                if not prevenir_loop_submit():
                    st.stop()
                
                # ✅ VALIDAÇÃO DO PREÇO COM CONVERSÃO
                if not preco_input:
                    st.error("⚠️ Preço de custo é obrigatório!")
                else:
                    try:
                        # Converter formato BR para float
                        preco_entrada = float(preco_input.replace('.', '').replace(',', '.'))
                        
                        if preco_entrada <= 0:
                            st.error("⚠️ Preço de custo deve ser maior que zero!")
                        elif modelo and marca and fornecedor:
                            # Calcular preço de venda com margem
                            preco_venda_final = preco_entrada * (1 + margem_negociacao/100)
                            
                            novo_veiculo = {
                                'modelo': modelo, 'ano': ano, 'marca': marca, 'cor': cor,
                                'preco_entrada': preco_entrada, 
                                'preco_venda': preco_venda_final,
                                'margem_negociacao': margem_negociacao,
                                'fornecedor': fornecedor, 'km': km, 'placa': placa,
                                'chassi': chassi, 'combustivel': combustivel, 'cambio': cambio,
                                'portas': portas, 'observacoes': observacoes,
                                'renavam': renavam,
                                'ano_fabricacao': ano_fabricacao,
                                'ano_modelo': ano_modelo
                            }
                            
                            print("🔄 Tentando cadastrar veículo...")
                            veiculo_id = db.add_veiculo(novo_veiculo)
                            
                            if veiculo_id:
                                # Salvar foto se foi enviada
                                if foto_veiculo is not None:
                                    db.salvar_foto_veiculo(veiculo_id, foto_veiculo.getvalue())
                                
                                st.success("✅ Veículo cadastrado com sucesso!")
                                st.balloons()
                                resetar_formulario()
                            else:
                                st.error("❌ Erro ao cadastrar veículo. Verifique os logs.")
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios!")
                            
                    except ValueError:
                        st.error("❌ Formato de preço inválido! Use: 50.000,00 ou 50000,00")
    
    with col_veic2:
        st.markdown("#### 📋 Estoque Atual")
        
        # Filtros
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            filtro_status = st.selectbox("Status", ["Todos", "Em estoque", "Vendido", "Reservado"])
        with col_filtro2:
            filtro_marca = st.text_input("Filtrar por marca")
        
        # Lista de veículos
        veiculos = get_veiculos_cache(db, filtro_status if filtro_status != "Todos" else None)
        
        if filtro_marca:
            veiculos = [v for v in veiculos if filtro_marca.lower() in v['marca'].lower()]
        
        for veiculo in veiculos:
            # Criar uma chave única para o expander baseada no ID do veículo
            expander_key = f"expander_{veiculo['id']}"
            
            with st.expander(f"{veiculo['marca']} {veiculo['modelo']} - {veiculo['ano']} - {veiculo['cor']}", expanded=False):
                # Calcular gastos totais do veículo
                gastos_veiculo = db.get_gastos(veiculo['id'])
                total_gastos = sum(g['valor'] for g in gastos_veiculo)
                custo_total = veiculo['preco_entrada'] + total_gastos

                # Calcular margem atual
                margem_atual = ((veiculo['preco_venda'] - custo_total) / custo_total) * 100 if custo_total > 0 else 0

                # Exibir informações do veículo
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**Marca:** {veiculo['marca']}")
                    st.write(f"**Modelo:** {veiculo['modelo']}")
                    st.write(f"**Ano:** {veiculo['ano']}")
                with col_info2:
                    st.write(f"**Cor:** {veiculo['cor']}")
                    st.write(f"**KM:** {veiculo['km']:,}")
                    st.write(f"**Placa:** {veiculo['placa'] or 'Não informada'}")

                # Preços
                st.markdown("---")
                col_preco1, col_preco2 = st.columns(2)
                with col_preco1:
                    st.subheader("💰 Preço para Negociação")
                    st.markdown(f"<h2 style='color: #e88e1b; text-align: center;'>R$ {veiculo['preco_venda']:,.2f}</h2>", unsafe_allow_html=True)
                with col_preco2:
                    st.subheader("📊 Custo Total")
                    st.markdown(f"<h2 style='color: #a0a0a0; text-align: center;'>R$ {custo_total:,.2f}</h2>", unsafe_allow_html=True)

                # Margem
                if margem_atual >= 20:
                    st.success(f"**✅ Margem: +{margem_atual:.1f}%**")
                elif margem_atual >= 10:
                    st.warning(f"**⚠️ Margem: +{margem_atual:.1f}%**")
                else:
                    st.error(f"**❌ Margem: +{margem_atual:.1f}%**")

                # Detalhes do custo
                st.markdown("**📋 Detalhes do Custo:**")
                col_det1, col_det2, col_det3 = st.columns(3)
                with col_det1:
                    st.metric("Compra", f"R$ {veiculo['preco_entrada']:,.2f}")
                with col_det2:
                    st.metric("Gastos", f"R$ {total_gastos:,.2f}")
                with col_det3:
                    st.metric("Custo Total", f"R$ {custo_total:,.2f}")

                # Gastos detalhados
                if gastos_veiculo:
                    st.markdown("#### 💰 Gastos Detalhados")
                    for i, gasto in enumerate(gastos_veiculo):
                        # ✅ CORREÇÃO: Usar função auxiliar para data do gasto
                        data_gasto_formatada = formatar_data(gasto['data'])
                        
                        # Key única para cada gasto
                        gasto_key = f"gasto_{veiculo['id']}_{i}"
                        st.markdown(f"""
                        <div style="padding: 0.5rem; margin: 0.25rem 0; background: rgba(255,255,255,0.02); border-radius: 6px;">
                            <strong>{gasto['tipo_gasto']}</strong> - R$ {gasto['valor']:,.2f}
                            <div style="color: #a0a0a0; font-size: 0.8rem;">
                                {data_gasto_formatada} • {gasto['descricao']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Adicionar novo gasto - COM FORM CORRIGIDO
                st.markdown("#### ➕ Adicionar Gasto")
                
                # ✅ CONTROLE DE ESTADO PARA GASTOS
                gasto_form_key = f"gasto_form_{veiculo['id']}"
                if f"{gasto_form_key}_submitted" not in st.session_state:
                    st.session_state[f"{gasto_form_key}_submitted"] = False
                
                # Se o formulário foi submetido recentemente, mostrar apenas confirmação
                if st.session_state[f"{gasto_form_key}_submitted"]:
                    st.success("✅ Gasto adicionado com sucesso!")
                    
                    # Botão para adicionar outro gasto
                    if st.button("➕ Adicionar Outro Gasto", key=f"add_another_{veiculo['id']}"):
                        st.session_state[f"{gasto_form_key}_submitted"] = False
                        st.rerun()
                else:
                    with st.form(f"novo_gasto_form_{veiculo['id']}", clear_on_submit=True):
                        col_gasto1, col_gasto2, col_gasto3 = st.columns(3)
                        
                        with col_gasto1:
                            tipo_gasto = st.selectbox("Tipo de Gasto", [
                                "Pneus", "Manutenção", "Documentação", "Combustível", 
                                "Peças", "Lavagem", "Pintura", "Seguro", "IPVA", "Outros"
                            ], key=f"tipo_{veiculo['id']}")
                
                        with col_gasto2:
                            valor_gasto = st.number_input("Valor (R$)", min_value=0.0, value=0.0, step=10.0, key=f"valor_{veiculo['id']}")
                            
                        with col_gasto3:
                            data_gasto = st.date_input("Data", value=datetime.datetime.now(), key=f"data_{veiculo['id']}")
                        
                        descricao_gasto = st.text_input("Descrição", placeholder="Descrição do gasto", key=f"desc_{veiculo['id']}")
                        arquivo_nota = st.file_uploader("Anexar Nota Fiscal", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"arquivo_{veiculo['id']}")
                        
                        submitted_gasto = st.form_submit_button("💾 Adicionar Gasto", use_container_width=True)
                        
                        if submitted_gasto:
                            if not prevenir_loop_submit():
                                st.stop()
                                
                            if valor_gasto > 0:
                                gasto_data = {
                                    'veiculo_id': veiculo['id'],
                                    'tipo_gasto': tipo_gasto,
                                    'valor': valor_gasto,
                                    'data': data_gasto,
                                    'descricao': descricao_gasto,
                                    'categoria': tipo_gasto
                                }
                                success = db.add_gasto(gasto_data)
                                
                                # Salvar arquivo se anexado
                                if success and arquivo_nota is not None:
                                    documento_data = {
                                        'veiculo_id': veiculo['id'],
                                        'tipo_documento': 'Nota Fiscal',
                                        'nome_arquivo': arquivo_nota.name,
                                        'arquivo': arquivo_nota.getvalue(),
                                        'observacoes': f"Nota fiscal do gasto: {descricao_gasto}"
                                    }
                                    db.add_documento_financeiro(documento_data)
                                
                                if success:
                                    # ✅ CORREÇÃO: MARCAR COMO SUBMETIDO SEM st.rerun() IMEDIATO
                                    st.session_state[f"{gasto_form_key}_submitted"] = True
                                    forcar_atualizacao_gastos()
                                    resetar_formulario()
                                    
                                    # ✅ ATUALIZAÇÃO SEGURA: Usar success message que persiste
                                    st.success("✅ Gasto adicionado com sucesso! Os dados serão atualizados automaticamente.")
                                    
                            else:
                                st.error("❌ O valor do gasto deve ser maior que zero!")

                # Controles de status
                st.markdown("---")
                st.markdown("#### 🔄 Alterar Status")
                col_status1, col_status2, col_status3 = st.columns(3)  # ← MUDAR PARA 3 COLUNAS
                
                with col_status1:
                    status_options = ["Em estoque", "Vendido", "Reservado", "Financiado"]
                    novo_status = st.selectbox(
                        "Status do Veículo", 
                        status_options, 
                        index=status_options.index(veiculo['status']),
                        key=f"status_select_{veiculo['id']}"
                    )
                
                with col_status2:
                    if st.button("Atualizar Status", key=f"status_btn_{veiculo['id']}", use_container_width=True):
                        if novo_status != veiculo['status']:
                            success = db.update_veiculo_status(veiculo['id'], novo_status)
                            if success:
                                st.success("✅ Status atualizado!")
                                st.rerun()
                
                # ⬇️⬇️ NOVA COLUNA PARA EXCLUIR ⬇️⬇️
                with col_status3:
                    if veiculo['status'] != 'Vendido':
                        if st.button("🗑️ Excluir", key=f"delete_btn_{veiculo['id']}", use_container_width=True, type="secondary"):
                            # Para confirmar a exclusão
                            with st.container():
                                st.warning("⚠️ Tem certeza que deseja excluir este veículo?")
                                col_confirm1, col_confirm2 = st.columns(2)
                                with col_confirm1:
                                    if st.button("✅ Sim, excluir", key=f"confirm_yes_{veiculo['id']}", use_container_width=True):
                                        sucesso, mensagem = db.delete_veiculo(veiculo['id'])
                                        if sucesso:
                                            st.success("✅ " + mensagem)
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ " + mensagem)
                                with col_confirm2:
                                    if st.button("❌ Cancelar", key=f"confirm_no_{veiculo['id']}", use_container_width=True):
                                        st.rerun()
                    else:
                        st.info("📝 Vendido - não pode excluir")

with tab3:
    # ABA UNIFICADA VENDAS + FINANCIAMENTOS
    st.markdown("""
    <div class="glass-card">
        <h2>💰 Vendas & Financiamentos</h2>
        <p style="color: #a0a0a0;">Processo completo de vendas com financiamento integrado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sub-abas dentro da aba unificada
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🛒 Nova Venda", "📋 Histórico", "📅 Parcelas"])
    
    with sub_tab1:
        col_venda1, col_venda2 = st.columns(2)
                
        with col_venda1:
            st.markdown("#### 👤 Dados da Venda")
            veiculos_estoque = [v for v in db.get_veiculos() if v['status'] == 'Em estoque']
            
            if veiculos_estoque:
                veiculos_options = [f"{v['id']} - {v['marca']} {v['modelo']} ({v['ano']})" for v in veiculos_estoque]
                
                with st.form("venda_financiamento_form", clear_on_submit=True):
                    # Seleção do veículo
                    veiculo_selecionado = st.selectbox("Veículo*", veiculos_options)
                    
                    if veiculo_selecionado:
                        veiculo_id = int(veiculo_selecionado.split(" - ")[0])
                        veiculo = next((v for v in veiculos_estoque if v['id'] == veiculo_id), None)
                        
                        if veiculo:
                            # Calcular custos
                            gastos_veiculo = db.get_gastos(veiculo_id)
                            total_gastos = sum(g['valor'] for g in gastos_veiculo)
                            custo_total = veiculo['preco_entrada'] + total_gastos
                            
                            st.markdown(f"""
                            <div style="padding: 1rem; background: rgba(232, 142, 27, 0.1); border-radius: 8px; margin: 1rem 0;">
                                <strong>🚗 Veículo Selecionado:</strong><br>
                                <strong>{veiculo['marca']} {veiculo['modelo']} {veiculo['ano']} - {veiculo['cor']}</strong><br>
                                <small><strong>💰 Custo Total:</strong> R$ {custo_total:,.2f}</small><br>
                                <small><strong>💵 Preço Sugerido:</strong> R$ {veiculo['preco_venda']:,.2f}</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Dados do cliente
                            st.markdown("#### 👤 Dados do Comprador")
                            comprador_nome = st.text_input("Nome Completo*", placeholder="Maria Santos")
                            comprador_cpf = st.text_input("CPF*", placeholder="123.456.789-00")
                            comprador_endereco = st.text_area("Endereço", placeholder="Rua Exemplo, 123 - Cidade/UF")
                            comprador_telefone = st.text_input("Telefone", placeholder="(11) 99999-9999")
                            st.markdown("#### 📝 Dados para Contrato")
                            # Dados das testemunhas
                            col_test1, col_test2 = st.columns(2)
                            with col_test1:
                                testemunha1_nome = st.text_input("Testemunha 1 - Nome", placeholder="Nome completo")
                                testemunha1_cpf = st.text_input("Testemunha 1 - CPF", placeholder="000.000.000-00")
                            with col_test2:
                                testemunha2_nome = st.text_input("Testemunha 2 - Nome", placeholder="Nome completo") 
                                testemunha2_cpf = st.text_input("Testemunha 2 - CPF", placeholder="000.000.000-00")      
                            # Checklist do veículo
                            st.markdown("#### 🔍 Checklist do Veículo")
                            col_check1, col_check2 = st.columns(2)
                            with col_check1:
                                km_atual = st.number_input("Quilometragem Atual", value=veiculo['km'])
                                observacoes_checklist = st.text_area("Observações do Veículo", placeholder="Estado geral, avarias, etc.")
                            with col_check2:
                                avarias = st.text_area("Avarias Identificadas", placeholder="Descreva avarias se houver")
                            # Troca (opcional)
                            st.markdown("#### 🔄 Veículo em Troca (Opcional)")
                            tem_troca = st.checkbox("Há veículo em troca?")
                            troca_marca_modelo = ""
                            troca_placa = "" 
                            troca_ano = 0
                            troca_valor = 0.0
                            
                            if tem_troca:
                                col_troca1, col_troca2 = st.columns(2)
                                with col_troca1:
                                    troca_marca_modelo = st.text_input("Veículo trocado - Marca/Modelo", placeholder="Ford Ka 2020")
                                    troca_placa = st.text_input("Veículo trocado - Placa", placeholder="QUY4A64")
                                with col_troca2:
                                    troca_ano = st.number_input("Veículo trocado - Ano", min_value=1990, max_value=2024, value=2020)
                                    troca_valor = st.number_input("Valor da Troca (R$)", min_value=0.0, value=0.0)

                            # Dados do financiamento
                            st.markdown("#### 💳 Condições de Pagamento")
                            
                            col_cond1, col_cond2 = st.columns(2)
                            with col_cond1:
                                tipo_pagamento = st.selectbox("Forma de Pagamento*", 
                                    ["Financiamento", "Crédito Direto", "Cheques", "Cartão", "À Vista"])
                                valor_total = st.number_input("Valor Total da Venda (R$)*", 
                                    min_value=0.0, value=float(veiculo['preco_venda']), step=1000.0)
                            
                            with col_cond2:
                                if tipo_pagamento != "À Vista":
                                    valor_entrada = st.number_input("Valor de Entrada (R$)", 
                                        min_value=0.0, value=0.0, step=1000.0)
                                    num_parcelas = st.number_input("Número de Parcelas", 
                                        min_value=1, value=12, max_value=60)
                                else:
                                    valor_entrada = valor_total
                                    num_parcelas = 1
                            
                            # Cálculos automáticos
                            if tipo_pagamento != "À Vista" and num_parcelas > 1:
                                valor_financiado = valor_total - valor_entrada
                                valor_parcela = valor_financiado / num_parcelas
                                
                                st.markdown(f"""
                                <div style="padding: 1rem; background: rgba(39, 174, 96, 0.1); border-radius: 8px; margin: 1rem 0;">
                                    <strong>📊 Resumo do Financiamento:</strong><br>
                                    <small>Valor Financiado: R$ {valor_financiado:,.2f}</small><br>
                                    <small>Valor da Parcela: R$ {valor_parcela:,.2f}</small><br>
                                    <small>Total de Parcelas: {num_parcelas}x</small>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Cálculo de lucro
                            lucro_venda = valor_total - custo_total
                            margem_lucro = (lucro_venda / custo_total * 100) if custo_total > 0 else 0
                            
                            col_lucro1, col_lucro2 = st.columns(2)
                            with col_lucro1:
                                st.metric("💰 Lucro Estimado", f"R$ {lucro_venda:,.2f}")
                            with col_lucro2:
                                st.metric("📊 Margem", f"{margem_lucro:.1f}%")
                            
                            observacoes = st.text_area("Observações da Venda")
                            
                            submitted = st.form_submit_button("✅ Finalizar Venda", use_container_width=True)
                            
                            if submitted:
                                if not prevenir_loop_submit():
                                    st.stop()
                                    
                                if comprador_nome and comprador_cpf and valor_total > 0:
                                    # Registrar a venda
                                    venda_data = {
                                        'veiculo_id': veiculo_id,
                                        'comprador_nome': comprador_nome,
                                        'comprador_cpf': comprador_cpf,
                                        'comprador_endereco': comprador_endereco,
                                        'valor_venda': valor_total
                                    }
                                    success_venda = db.add_venda(venda_data)
                                    
                                    if success_venda and tipo_pagamento != "À Vista":
                                        # Registrar financiamento
                                        financiamento_data = {
                                            'veiculo_id': veiculo_id,
                                            'tipo_financiamento': tipo_pagamento,
                                            'valor_total': valor_total,
                                            'valor_entrada': valor_entrada,
                                            'num_parcelas': num_parcelas,
                                            'data_contrato': datetime.datetime.now().date(),
                                            'observacoes': f"Venda para {comprador_nome}. {observacoes}"
                                        }
                                        financiamento_id = db.add_financiamento(financiamento_data)
                                        
                                        if financiamento_id:
                                            st.success("🎉 Venda e financiamento registrados com sucesso!")
                                    else:
                                        st.success("🎉 Venda à vista registrada com sucesso!")
                                    
                                    # Registrar no fluxo de caixa
                                    fluxo_data = {
                                        'data': datetime.datetime.now().date(),
                                        'descricao': f'Venda - {veiculo["marca"]} {veiculo["modelo"]}',
                                        'tipo': 'Entrada',
                                        'categoria': 'Vendas',
                                        'valor': valor_entrada if tipo_pagamento != "À Vista" else valor_total,
                                        'veiculo_id': veiculo_id,
                                        'status': 'Concluído'
                                    }
                                    db.add_fluxo_caixa(fluxo_data)
                                    
                                    # Registrar contato do cliente
                                    contato_data = {
                                        'nome': comprador_nome,
                                        'telefone': comprador_telefone,
                                        'email': '',
                                        'tipo': 'Cliente',
                                        'veiculo_interesse': f"{veiculo['marca']} {veiculo['modelo']}",
                                        'data_contato': datetime.datetime.now().date(),
                                        'observacoes': f"Comprou veículo por R$ {valor_total:,.2f}. {observacoes}"
                                    }
                                    db.add_contato(contato_data)
                                    
                                    st.balloons()
                                    resetar_formulario()
                                    # Gerar contrato automático
                                    dados_contrato = {
                                        'comprador_nome': comprador_nome,
                                        'comprador_cpf': comprador_cpf,
                                        'comprador_endereco': comprador_endereco,
                                        'comprador_telefone': comprador_telefone,
                                        'veiculo_marca': veiculo['marca'],
                                        'veiculo_modelo': veiculo['modelo'],
                                        'veiculo_placa': veiculo['placa'],
                                        'veiculo_renavam': veiculo.get('renavam', ''),
                                        'veiculo_ano_fabricacao': veiculo.get('ano_fabricacao', veiculo['ano']),
                                        'veiculo_ano_modelo': veiculo.get('ano_modelo', veiculo['ano']),
                                        'veiculo_chassi': veiculo.get('chassi', ''),
                                        'valor_total': valor_total,
                                        'valor_entrada': valor_entrada,
                                        'num_parcelas': num_parcelas,
                                        'data_venda': datetime.datetime.now().strftime("%d/%m/%Y"),
                                        'km_atual': km_atual,
                                        'testemunha1_nome': testemunha1_nome,
                                        'testemunha1_cpf': testemunha1_cpf,
                                        'testemunha2_nome': testemunha2_nome,
                                        'testemunha2_cpf': testemunha2_cpf,
                                        'observacoes_checklist': observacoes_checklist,
                                        'avarias': avarias,
                                        'tem_troca': tem_troca,
                                        'troca_marca_modelo': troca_marca_modelo,
                                        'troca_placa': troca_placa,
                                        'troca_ano': troca_ano,
                                        'troca_valor': troca_valor
                                        
                                    }
                                    
                                    contrato_gerado = gerar_contrato_venda(dados_contrato)
                                    st.session_state.contrato_gerado = contrato_gerado
                                    st.session_state.contrato_nome = f"contrato_{veiculo['marca']}_{veiculo['modelo']}_{comprador_nome.replace(' ', '_')}.docx" 
                                else:
                                    st.error("❌ Preencha todos os campos obrigatórios!")
            else:
                st.info("📝 Não há veículos em estoque para venda.")
        if 'contrato_gerado' in st.session_state:
            st.markdown("---")
            st.markdown("#### 📄 Contrato Gerado - Faça o Download")
            
            st.download_button(
            label="📥 Baixar Contrato de Compra e Venda",
            data=st.session_state.contrato_gerado,
            file_name=st.session_state.contrato_nome,
            mime="text/html"  # ⬅️ Mude para HTML
        )
            
            with st.expander("👁️ Visualizar Contrato"):
                st.text_area("Prévia do Contrato", st.session_state.contrato_gerado, height=400, key="previa_contrato")                        
        with col_venda2:
            st.markdown("#### 📊 Resumo Financeiro")
            # Aqui pode mostrar cálculos detalhados, simulações, etc.
            st.info("💡 **Dica:** Preencha os dados à esquerda para ver o resumo financeiro completo aqui.")


    
    with sub_tab2:
        st.markdown("#### 📋 Histórico Completo de Vendas")
        
        vendas = db.get_vendas()
        financiamentos = db.get_financiamentos()
        
        # Combinar dados de vendas e financiamentos
        vendas_completas = []
        for venda in vendas:
            venda_completa = venda.copy()
            # Buscar financiamento correspondente
            financiamento = next((f for f in financiamentos if f['veiculo_id'] == venda['veiculo_id']), None)
            if financiamento:
                venda_completa['tipo_pagamento'] = financiamento['tipo_financiamento']
                venda_completa['num_parcelas'] = financiamento['num_parcelas']
                venda_completa['valor_entrada'] = financiamento['valor_entrada']
            else:
                venda_completa['tipo_pagamento'] = 'À Vista'
                venda_completa['num_parcelas'] = 1
                venda_completa['valor_entrada'] = venda['valor_venda']
            
            vendas_completas.append(venda_completa)
        
        for venda in vendas_completas[:15]:
            data_venda_formatada = formatar_data(venda.get('data_venda'))
            
            st.markdown(f"""
            <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(255,255,255,0.03); border-radius: 8px;">
                <div style="display: flex; justify-content: between; align-items: start;">
                    <div style="flex: 1;">
                        <strong>{venda.get('marca', 'N/A')} {venda.get('modelo', 'N/A')} ({venda.get('ano', 'N/A')})</strong>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">
                            👤 {venda.get('comprador_nome', 'N/A')} • {venda['tipo_pagamento']}
                        </div>
                        <div style="margin-top: 0.5rem;">
                            <span style="color: #27AE60; font-weight: bold;">R$ {venda.get('valor_venda', 0):,.2f}</span>
                            <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.8rem;">
                                {venda['num_parcelas']}x de R$ {(venda.get('valor_venda', 0) - venda.get('valor_entrada', 0)) / venda['num_parcelas']:,.2f}
                            </span>
                        </div>
                        <div style="color: #666; font-size: 0.7rem; margin-top: 0.5rem;">
                            {data_venda_formatada}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with sub_tab3:
        st.markdown("#### 📅 Gestão de Parcelas")
        
        # ✅ CORREÇÃO: Cálculo "Receber Este Mês" - Próximos 30 dias
        parcelas = db.get_parcelas()
        hoje = datetime.datetime.now().date()
        data_fim_mes = hoje + datetime.timedelta(days=30)
        
        parcelas_pendentes = [p for p in parcelas if p['status'] == 'Pendente']
        parcelas_vencidas = [p for p in parcelas_pendentes if p['data_vencimento'] and processar_data_postgresql(p['data_vencimento']) < hoje]
        parcelas_este_mes = [p for p in parcelas_pendentes if p['data_vencimento'] and processar_data_postgresql(p['data_vencimento']) <= data_fim_mes]
        
        # Métricas
        col_met1, col_met2, col_met3 = st.columns(3)
        with col_met1:
            st.metric("⏰ Vencidas", len(parcelas_vencidas))
        with col_met2:
            st.metric("💰 Este Mês", f"R$ {sum(p['valor_parcela'] for p in parcelas_este_mes):,.2f}")
        with col_met3:
            st.metric("🏦 Total Pendente", f"R$ {sum(p['valor_parcela'] for p in parcelas_pendentes):,.2f}")
        
        col_parc1, col_parc2 = st.columns(2)
        
        with col_parc1:
            st.markdown("##### ⏰ Parcelas Vencidas")
            
            for parcela in parcelas_vencidas[:10]:
                dias_vencido = (hoje - processar_data_postgresql(parcela['data_vencimento'])).days
                
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(231, 76, 60, 0.1); border-radius: 8px;">
                    <strong>{parcela['marca']} {parcela['modelo']}</strong>
                    <div style="color: #a0a0a0; font-size: 0.9rem;">
                        Parcela {parcela['numero_parcela']} • Vencida há {dias_vencido} dias
                    </div>
                    <div style="color: #E74C3C; font-weight: bold; margin-top: 0.5rem;">
                        R$ {parcela['valor_parcela']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_parc2:
            st.markdown("##### 📈 Próximas Parcelas (30 dias)")
            
            for parcela in parcelas_este_mes[:10]:
                dias_restantes = (processar_data_postgresql(parcela['data_vencimento']) - hoje).days
                
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(243, 156, 18, 0.1); border-radius: 8px;">
                    <strong>{parcela['marca']} {parcela['modelo']}</strong>
                    <div style="color: #a0a0a0; font-size: 0.9rem;">
                        Parcela {parcela['numero_parcela']} • {dias_restantes} dias
                    </div>
                    <div style="color: #F39C12; font-weight: bold; margin-top: 0.5rem;">
                        R$ {parcela['valor_parcela']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)      

with tab4:
    # DOCUMENTOS
    st.markdown("""
    <div class="glass-card">
        <h2>📄 Gestão de Documentos</h2>
        <p style="color: #a0a0a0;">Armazene todos os documentos dos veículos digitalmente</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_doc1, col_doc2 = st.columns(2)
    
    with col_doc1:
        st.markdown("#### 📤 Novo Documento")
        with st.form("novo_documento_form", clear_on_submit=True):
            veiculos_options = [f"{v['id']} - {v['marca']} {v['modelo']} ({v['ano']})" for v in db.get_veiculos()]
            veiculo_selecionado = st.selectbox("Veículo*", veiculos_options)
            
            nome_documento = st.text_input("Nome do Documento*", placeholder="Nota Fiscal de Compra")
            tipo_documento = st.selectbox("Tipo de Documento*", [
                "Nota Fiscal", "CRV", "CRLV", "Contrato", "Laudo", 
                "Foto", "Documento Pessoal", "Outros"
            ])
            
            arquivo = st.file_uploader("Arquivo*", type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])
            observacoes = st.text_area("Observações", placeholder="Observações sobre o documento...")
            
            submitted = st.form_submit_button("💾 Salvar Documento", use_container_width=True)
            if submitted:
                if not prevenir_loop_submit():
                    st.stop()
                    
                if veiculo_selecionado and nome_documento and arquivo:
                    documento_data = {
                        'veiculo_id': int(veiculo_selecionado.split(" - ")[0]),
                        'nome_documento': nome_documento,
                        'tipo_documento': tipo_documento,
                        'arquivo': arquivo.getvalue(),
                        'observacoes': observacoes
                    }
                    success = db.add_documento(documento_data)
                    if success:
                        st.success("✅ Documento salvo com sucesso!")
                        resetar_formulario()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
    
    with col_doc2:
        st.markdown("#### 📋 Documentos Salvos")
        
        documentos = db.get_documentos()
        
        if documentos:
            for doc in documentos[:8]:
                # ✅ CORREÇÃO: Usar função auxiliar para data
                data_upload_formatada = formatar_data(doc['data_upload'])
                
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(255,255,255,0.03); border-radius: 8px;">
                    <div style="display: flex; justify-content: between; align-items: start;">
                        <div style="flex: 1;">
                            <strong>{doc['nome_documento']}</strong>
                            <div style="color: #a0a0a0; font-size: 0.9rem;">
                                {doc['marca']} {doc['modelo']} • {doc['tipo_documento']}
                            </div>
                            <div style="color: #666; font-size: 0.8rem; margin-top: 0.5rem;">
                                {data_upload_formatada}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botão para download
                if st.button("📥 Download", key=f"down_{doc['id']}", use_container_width=True):
                    # Criar download do arquivo
                    st.download_button(
                        label="Baixar Arquivo",
                        data=doc['arquivo'],
                        file_name=f"{doc['nome_documento']}.{doc['tipo_documento'].lower()}",
                        mime="application/octet-stream",
                        key=f"dl_{doc['id']}"
                    )
        else:
            st.info("📝 Nenhum documento salvo ainda.")

with tab5:
    # FLUXO DE CAIXA COMPLETO
    st.markdown("""
    <div class="glass-card">
        <h2>💸 Fluxo de Caixa</h2>
        <p style="color: #a0a0a0;">Controle financeiro completo com gastos por veículo</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros de período
    col_filtro_fc1, col_filtro_fc2 = st.columns(2)
    with col_filtro_fc1:
        data_inicio = st.date_input("Data Início", value=datetime.datetime.now().replace(day=1))
    with col_filtro_fc2:
        data_fim = st.date_input("Data Fim", value=datetime.datetime.now())
    
    # Métricas do período
    fluxo_periodo = db.get_fluxo_caixa(data_inicio, data_fim)
    entradas = sum(f['valor'] for f in fluxo_periodo if f['tipo'] == 'Entrada')
    saidas = sum(f['valor'] for f in fluxo_periodo if f['tipo'] == 'Saída')
    saldo = entradas - saidas
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    with col_met1:
        st.metric("💰 Entradas", f"R$ {entradas:,.2f}")
    with col_met2:
        st.metric("💸 Saídas", f"R$ {saidas:,.2f}")
    with col_met3:
        st.metric("⚖️ Saldo", f"R$ {saldo:,.2f}", delta=f"R$ {saldo:,.2f}")
    with col_met4:
        st.metric("📊 Movimentações", len(fluxo_periodo))
    
    col_fc1, col_fc2 = st.columns(2)
    
    with col_fc1:
        st.markdown("#### ➕ Nova Movimentação")
        with st.form("nova_movimentacao_form", clear_on_submit=True):
            tipo = st.selectbox("Tipo*", ["Entrada", "Saída"])
            
            if tipo == "Saída":
                # Para saídas, permitir associar a veículo
                veiculos_options = ["Não associado"] + [f"{v['id']} - {v['marca']} {v['modelo']}" for v in db.get_veiculos()]
                veiculo_associado = st.selectbox("Associar a Veículo", veiculos_options)
                categoria = st.selectbox("Categoria*", [
                    "Pneus", "Manutenção", "Documentação", "Combustível", 
                    "Peças", "Lavagem", "Pintura", "Seguro", "IPVA", "Outros"
                ])
            else:
                veiculo_associado = "Não associado"
                categoria = st.selectbox("Categoria*", [
                    "Vendas", "Serviços", "Financiamento", "Outros"
                ])
            
            valor = st.number_input("Valor (R$)*", min_value=0.0, value=0.0)
            data_mov = st.date_input("Data*", value=datetime.datetime.now())
            descricao = st.text_input("Descrição*", placeholder="Descrição da movimentação")
            
            submitted = st.form_submit_button("💾 Registrar Movimentação", use_container_width=True)
            if submitted:
                if not prevenir_loop_submit():
                    st.stop()
                    
                if descricao and valor > 0:
                    fluxo_data = {
                        'data': data_mov,
                        'descricao': descricao,
                        'tipo': tipo,
                        'categoria': categoria,
                        'valor': valor,
                        'veiculo_id': int(veiculo_associado.split(" - ")[0]) if veiculo_associado != "Não associado" else None,
                        'status': 'Concluído'
                    }
                    success = db.add_fluxo_caixa(fluxo_data)
                    if success:
                        # Se for uma saída associada a veículo, registrar também na tabela de gastos
                        if tipo == "Saída" and veiculo_associado != "Não associado":
                            gasto_data = {
                                'veiculo_id': int(veiculo_associado.split(" - ")[0]),
                                'tipo_gasto': categoria,
                                'valor': valor,
                                'data': data_mov,
                                'descricao': descricao,
                                'categoria': categoria
                            }
                            db.add_gasto(gasto_data)
                        
                        st.success("✅ Movimentação registrada com sucesso!")
                        resetar_formulario()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
        
    with col_fc2:
        st.markdown("#### 📋 Últimas Movimentações")
        
        for mov in fluxo_periodo[:10]:
            cor = "#27AE60" if mov['tipo'] == 'Entrada' else "#E74C3C"
            veiculo_info = f" • {mov['marca']} {mov['modelo']}" if mov['marca'] else ""
            
            # ✅ CORREÇÃO: Usar função auxiliar para data
            data_mov_formatada = formatar_data(mov['data'])
            
            st.markdown(f"""
            <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(255,255,255,0.03); border-radius: 8px;">
                <div style="display: flex; justify-content: between; align-items: start;">
                    <div style="flex: 1;">
                        <strong>{mov['descricao']}</strong>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">
                            {mov['categoria']}{veiculo_info} • {data_mov_formatada}
                        </div>
                    </div>
                    <span style="color: {cor}; font-weight: bold;">
                        {'+' if mov['tipo'] == 'Entrada' else '-'} R$ {mov['valor']:,.2f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab6:
    # CONTATOS
    st.markdown("""
    <div class="glass-card">
        <h2>📞 Gestão de Contatos</h2>
        <p style="color: #a0a0a0;">CRM completo para acompanhamento de clientes</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_ctt1, col_ctt2 = st.columns(2)
    
    with col_ctt1:
        st.markdown("#### 👥 Novo Contato")
        with st.form("novo_contato_form", clear_on_submit=True):
            nome = st.text_input("Nome*", placeholder="João Silva")
            telefone = st.text_input("Telefone", placeholder="(11) 99999-9999")
            email = st.text_input("Email", placeholder="joao@email.com")
            tipo = st.selectbox("Tipo de Contato", ["Cliente", "Fornecedor", "Lead", "Vendedor", "Outros"])
            veiculo_interesse = st.text_input("Veículo de Interesse", placeholder="Honda Civic 2023")
            data_contato = st.date_input("Data do Contato", value=datetime.datetime.now())
            observacoes = st.text_area("Observações", placeholder="Anotações importantes...")
            
            submitted = st.form_submit_button("💾 Salvar Contato", use_container_width=True)
            if submitted:
                if not prevenir_loop_submit():
                    st.stop()
                    
                if nome:
                    contato_data = {
                        'nome': nome,
                        'telefone': telefone,
                        'email': email,
                        'tipo': tipo,
                        'veiculo_interesse': veiculo_interesse,
                        'data_contato': data_contato,
                        'observacoes': observacoes
                    }
                    success = db.add_contato(contato_data)
                    if success:
                        st.success("✅ Contato salvo com sucesso!")
                        resetar_formulario()
                else:
                    st.error("❌ Nome é obrigatório!")
        
    with col_ctt2:
        st.markdown("#### 📋 Lista de Contatos")
        
        contatos = db.get_contatos()
        
        for contato in contatos[:10]:
            # ✅ CORREÇÃO: Usar função auxiliar para data
            data_contato_formatada = formatar_data(contato['data_contato'])
            
            st.markdown(f"""
            <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(255,255,255,0.03); border-radius: 8px;">
                <div style="display: flex; justify-content: between; align-items: start;">
                    <div style="flex: 1;">
                        <strong>{contato['nome']}</strong>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">
                            {contato['tipo']} • {contato['telefone']}
                        </div>
                        <div style="color: #a0a0a0; font-size: 0.8rem; margin-top: 0.5rem;">
                            {contato['veiculo_interesse'] or 'Sem interesse específico'}
                        </div>
                        <div style="color: #666; font-size: 0.7rem; margin-top: 0.5rem;">
                            {data_contato_formatada}
                        </div>
                    </div>
                    <span style="background: #e88e1b; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem;">
                        {contato['status']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab7:
    st.markdown("""
    <div class="glass-card">
        <h2>⚙️ Configurações do Sistema</h2>
        <p style="color: #a0a0a0;">Personalize e gerencie o sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_config1, col_config2 = st.columns(2)
    
    with col_config1:
        st.markdown("#### 👤 Perfil do Usuário")
        st.markdown(f"""
        <div style="padding: 1.5rem; background: rgba(255,255,255,0.03); border-radius: 8px;">
            <p><strong>Nome:</strong> {usuario['nome']}</p>
            <p><strong>Usuário:</strong> {usuario['username']}</p>
            <p><strong>Email:</strong> {usuario['email'] or 'Não cadastrado'}</p>
            <p><strong>Nível de Acesso:</strong> {usuario['nivel_acesso']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_config2:
        st.markdown("#### 🚪 Sessão")
        if st.button("🔓 Sair do Sistema", use_container_width=True, type="secondary"):
            logout()
        
    # NOVA SEÇÃO DO PAPEL TIMBRADO
    st.markdown("---")
    seção_papel_timbrado()
     
    st.markdown("---")
    st.markdown("#### 🔐 Alterar Minha Senha")
    
    with st.form("alterar_senha_form", clear_on_submit=True):
        senha_atual = st.text_input("Senha Atual", type="password", 
                                   placeholder="Digite sua senha atual")
        nova_senha = st.text_input("Nova Senha", type="password",
                                  placeholder="Digite a nova senha (mín. 6 caracteres)")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password",
                                       placeholder="Digite novamente a nova senha")
        
        submitted_senha = st.form_submit_button("🔄 Alterar Senha", use_container_width=True)
        if submitted_senha:
            if not prevenir_loop_submit():
                st.stop()
                
            if senha_atual and nova_senha and confirmar_senha:
                # Verificar senha atual
                usuario_temp = db.verificar_login(usuario['username'], senha_atual)
                if usuario_temp:
                    if nova_senha == confirmar_senha:
                        if len(nova_senha) >= 6:
                            # Atualizar senha
                            conn = sqlite3.connect(db.db_path)
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE usuarios SET password_hash = ? WHERE id = ?
                            ''', (hash_password(nova_senha), usuario['id']))
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ Senha alterada com sucesso!")
                            st.info("🔒 Sua senha foi atualizada com segurança")
                            resetar_formulario()
                        else:
                            st.error("❌ A senha deve ter pelo menos 6 caracteres")
                    else:
                        st.error("❌ As novas senhas não coincidem")
                else:
                    st.error("❌ Senha atual incorreta")
            else:
                st.error("⚠️ Preencha todos os campos")

    

    '''st.markdown("---")
    st.markdown("#### 🗑️ Limpeza do Banco de Dados")
    
    # Usar session_state para controlar a confirmação
    if 'confirmar_limpeza' not in st.session_state:
        st.session_state.confirmar_limpeza = False
    
    if not st.session_state.confirmar_limpeza:
        if st.button("⚠️ LIMPAR TODOS OS DADOS", type="secondary", use_container_width=True):
            st.session_state.confirmar_limpeza = True
            st.rerun()
    else:
        st.warning("🚨 **ATENÇÃO:** Esta ação é IRREVERSÍVEL! Todos os dados serão perdidos!")
        
        col_conf1, col_conf2 = st.columns(2)
        with col_conf1:
            if st.button("✅ SIM, LIMPAR TUDO", type="primary", use_container_width=True):
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    
                    # Desativar foreign keys temporariamente
                    if os.getenv('DATABASE_URL'):
                        cursor.execute('SET session_replication_role = replica;')
                    else:
                        cursor.execute('PRAGMA foreign_keys = OFF;')
                    
                    # Limpar tabelas na ordem correta (evitando constraints)
                    tables = [
                        'parcelas', 'documentos_financeiros', 'financiamentos', 
                        'vendas', 'gastos', 'documentos', 'fluxo_caixa', 
                        'contatos', 'veiculos', 'logs_acesso'
                    ]
                    
                    for table in tables:
                        try:
                            if os.getenv('DATABASE_URL'):
                                cursor.execute(f'TRUNCATE TABLE {table} CASCADE;')
                            else:
                                cursor.execute(f'DELETE FROM {table};')
                            st.write(f"✅ {table} limpa")
                        except Exception as e:
                            st.write(f"⚠️ {table}: {e}")
                    
                    # Reativar foreign keys
                    if os.getenv('DATABASE_URL'):
                        cursor.execute('SET session_replication_role = DEFAULT;')
                    else:
                        cursor.execute('PRAGMA foreign_keys = ON;')
                    
                    conn.commit()
                    conn.close()
                    
                    st.success("🎉 Banco de dados limpo com sucesso!")
                    st.session_state.confirmar_limpeza = False
                    
                    # Forçar atualização dos caches
                    forcar_atualizacao_gastos()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao limpar banco: {e}")
        
        with col_conf2:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.session_state.confirmar_limpeza = False
                st.rerun()'''

# =============================================
# FOOTER PREMIUM
# =============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0a0; padding: 2rem;">
    <p style="margin: 0; font-size: 0.9rem; font-weight: 600; color: #e88e1b;"> Sistema de Gestão Automotiva</p>
    <p style="margin: 0; font-size: 0.8rem;">Soluções profissionais para o mercado automotivo ®</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.7rem; color: #666;">
        Powered by Júlio Aguiar
    </p>
</div>
""", unsafe_allow_html=True)
