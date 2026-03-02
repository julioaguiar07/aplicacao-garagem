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
    page_title="Adm. Carmelo Multimarcas",
    page_icon="logo-icon.png",
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
            


def seção_gerador_stories():
    st.markdown("#### 📸 **Escolha a Foto**")
    
    foto_story = st.file_uploader(
        "📤 **Carregue qualquer foto para criar um story:**",
        type=['jpg', 'jpeg', 'png'],
        help="Foto vertical fica melhor para stories",
        key="foto_story_universal"
    )
    
    if foto_story is not None:
        # Carregar imagem
        image = Image.open(foto_story)
        width, height = image.size
        
        # Inicializar estado para posição vertical
        if 'vertical_pos' not in st.session_state:
            st.session_state.vertical_pos = 0.5  # 0.5 = centro
        
        # =============================================
        # CONTROLE VISUAL DE POSIÇÃO VERTICAL
        # =============================================
        st.markdown("#### 📐 **Ajuste a Posição**")
        
        # Explicação visual
        col_explain1, col_explain2, col_explain3 = st.columns([1, 2, 1])
        
        with col_explain2:
            st.markdown("""
            <div style="text-align: center; background: rgba(232, 142, 27, 0.1); 
                     padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #e88e1b;">⬆️ Arraste para cima/baixo ⬇️</h4>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">
                    Ajuste sutilmente para mostrar a melhor parte da foto
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Slider visual e sensível
        col_slider1, col_slider2, col_slider3 = st.columns([1, 3, 1])
        
        with col_slider2:
            # Slider com melhor sensibilidade
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            
            # Slider vertical personalizado
            vertical_pos = st.slider(
                "**Posição Vertical**",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.vertical_pos,
                step=0.01,  # Sensibilidade boa - nem muito pouco, nem muito
                format="",
                label_visibility="collapsed",
                key="vertical_slider_universal"
            )
            
            # Atualizar estado
            st.session_state.vertical_pos = vertical_pos
            
            # Indicador visual abaixo do slider
            pos_percent = int(vertical_pos * 100)
            indicator_color = "#27AE60" if 40 <= pos_percent <= 60 else "#F39C12"
            
            st.markdown(f"""
            <div style="text-align: center; margin-top: 10px;">
                <div style="display: inline-block; background: {indicator_color}; 
                     color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold;">
                    📍 Posição: {pos_percent}% {'' if 40 <= pos_percent <= 60 else '| '}
                    {'CENTRO' if 40 <= pos_percent <= 60 else 'AJUSTADO'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # =============================================
        # VISUALIZAÇÃO DO RECORTE 4:3 HORIZONTAL
        # =============================================
        st.markdown("---")
        st.markdown("#### 👁️ **Visualização do Recorte**")
        
        # Configurações do recorte 4:3 horizontal
        TARGET_RATIO = 4/3  # 4:3 horizontal
        AREA_LARGURA = 950  # Largura no template
        
        # Calcular recorte
        crop_width = min(width, int(height * TARGET_RATIO))
        crop_height = int(crop_width / TARGET_RATIO)
        
        # Se a foto for mais larga que a proporção 4:3
        if width > height * TARGET_RATIO:
            crop_width = int(height * TARGET_RATIO)
            crop_height = height
            left = (width - crop_width) // 2
            right = left + crop_width
            top = 0
            bottom = height
        else:
            # Foto mais alta - ajustar posição vertical
            left = 0
            right = width
            max_vertical_offset = max(0, height - crop_height)
            vertical_offset = int(max_vertical_offset * vertical_pos)
            top = min(vertical_offset, height - crop_height)
            bottom = top + crop_height
        
        # Criar visualização COMPACTA
        col_view1, col_view2, col_view3 = st.columns([1, 3, 1])
        
        with col_view2:  # Coluna central
            # Tamanho fixo e compacto para visualização
            preview_size = 350  # Menor que antes
            
            # Calcular proporção para visualização
            display_ratio = crop_width / crop_height
            if display_ratio > 1:
                preview_width = preview_size
                preview_height = int(preview_size / display_ratio)
            else:
                preview_height = preview_size
                preview_width = int(preview_size * display_ratio)
            
            # Fazer o recorte
            img_cropped = image.crop((left, top, right, bottom))
            
            # Redimensionar para visualização
            img_preview = img_cropped.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            
            # Adicionar borda sutil
            from PIL import ImageOps
            img_with_border = ImageOps.expand(img_preview, border=3, fill='#e88e1b')
            
            # Mostrar imagem compacta
            st.image(img_with_border, 
                    caption=f"Recorte 4:3 | {crop_width}x{crop_height}px",
                    use_column_width=False)
            
            # Mini indicador de qualidade
            coverage = (crop_width * crop_height) / (width * height) * 100
            
            if coverage > 60:
                quality_indicator = "✅ Ótima qualidade"
                quality_color = "#27AE60"
            elif coverage > 40:
                quality_indicator = "⚠️ Boa qualidade"
                quality_color = "#F39C12"
            else:
                quality_indicator = "📏 Pequena área"
                quality_color = "#E74C3C"
            
            st.markdown(f"""
            <div style="text-align: center; margin-top: 10px;">
                <div style="display: inline-block; background: rgba(0,0,0,0.05); 
                     padding: 8px 15px; border-radius: 10px; font-size: 0.9em;">
                    <span style="color: {quality_color}; font-weight: bold;">{quality_indicator}</span> | 
                    Área utilizada: <strong>{coverage:.1f}%</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # =============================================
        # PRÉ-VISUALIZAÇÃO NO TEMPLATE (COMPACTA)
        # =============================================
        st.markdown("---")
        st.markdown("#### 🎨 **Pré-visualização no Template**")
        
        try:
            # Carregar template
            template = Image.open("stories.png").convert('RGB')
            
            # Redimensionar para caber na área do template
            AREA_TEMPLATE_LARGURA = 950
            AREA_TEMPLATE_ALTURA = 1200
            AREA_TEMPLATE_POS_Y = 260
            
            # Calcular tamanho para template
            if crop_width / crop_height > AREA_TEMPLATE_LARGURA / AREA_TEMPLATE_ALTURA:
                nova_largura = AREA_TEMPLATE_LARGURA
                nova_altura = int(nova_largura * crop_height / crop_width)
            else:
                nova_altura = AREA_TEMPLATE_ALTURA
                nova_largura = int(nova_altura * crop_width / crop_height)
            
            img_for_template = img_cropped.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
            
            # Posicionar no template
            pos_x = (template.width - nova_largura) // 2
            pos_y = AREA_TEMPLATE_POS_Y + (AREA_TEMPLATE_ALTURA - nova_altura) // 2
            
            # Criar cópia e colar
            template_preview = template.copy()
            template_preview.paste(img_for_template, (pos_x, pos_y))
            
            # Mostrar em tamanho COMPACTO
            col_temp1, col_temp2, col_temp3 = st.columns([1, 3, 1])
            
            with col_temp2:
                # Redimensionar template para visualização compacta
                template_display_width = 300  # Muito menor
                template_display_height = int(template_display_width * template.height / template.width)
                template_display = template_preview.resize((template_display_width, template_display_height), Image.Resampling.LANCZOS)
                
                st.image(template_display, caption="Visualização do Story", use_column_width=False)
                
                # Campo para nome do arquivo
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                col_name1, col_name2 = st.columns([1, 1])
                with col_name1:
                    nome_personalizado = st.text_input(
                        "Nome do arquivo (opcional):",
                        placeholder="meu_story",
                        help="Deixe em branco para nome automático"
                    )
                
                with col_name2:
                    data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    if nome_personalizado:
                        nome_sugerido = f"{nome_personalizado}_{data_atual}.png"
                    else:
                        nome_sugerido = f"story_{data_atual}.png"
                    
                    st.info(f"📁 **Salvar como:** `{nome_sugerido}`")
                
                # Botão para gerar - CENTRALIZADO
                if st.button("✨ **GERAR STORY AGORA**", 
                           use_container_width=True, 
                           type="primary",
                           key="gerar_story_universal"):
                    
                    config_corte = {
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'proporcao': "4:3 Horizontal",
                        'foto_bytes': foto_story.getvalue(),
                        'posicao_vertical': vertical_pos
                    }
                    
                    nome_arquivo, erro = gerar_story_universal(
                        config_corte,
                        nome_personalizado if nome_personalizado else f"story_{data_atual}"
                    )
                    
                    if erro:
                        st.error(f"❌ Erro: {erro}")
                    else:
                        st.success("✅ Story gerado com sucesso!")
                        
                        # Mostrar e download em colunas
                        col_result1, col_result2 = st.columns(2)
                        
                        with col_result1:
                            # Mostrar resultado compacto
                            result_img = Image.open(nome_arquivo)
                            display_width = 250
                            display_height = int(display_width * result_img.height / result_img.width)
                            result_display = result_img.resize((display_width, display_height), Image.Resampling.LANCZOS)
                            st.image(result_display, caption="Story Pronto!")
                        
                        with col_result2:
                            with open(nome_arquivo, "rb") as file:
                                st.download_button(
                                    label="📥 **BAIXAR STORY**",
                                    data=file,
                                    file_name=os.path.basename(nome_arquivo),
                                    mime="image/png",
                                    use_container_width=True,
                                    type="primary"
                                )
        
        except Exception as e:
            st.error(f"❌ Erro ao carregar template: {e}")
    
    else:
        st.info("📸 **Carregue uma foto para começar a criar seu story**")

def gerar_story_universal(config_corte, nome_base="story"):
    """Gera story universal para qualquer foto"""
    try:
        # Carregar template
        try:
            template = Image.open("stories.png").convert('RGB')
        except:
            return None, "Template não encontrado"
        
        # Carregar e recortar foto
        image = Image.open(io.BytesIO(config_corte['foto_bytes']))
        img_cropped = image.crop(
            (config_corte['left'],
             config_corte['top'],
             config_corte['right'],
             config_corte['bottom'])
        )
        
        # Configurações do template
        AREA_LARGURA = 950
        AREA_ALTURA = 1200
        AREA_POS_Y = 325
        
        # Redimensionar para caber na área
        if img_cropped.width / img_cropped.height > AREA_LARGURA / AREA_ALTURA:
            nova_largura = AREA_LARGURA
            nova_altura = int(nova_largura * img_cropped.height / img_cropped.width)
        else:
            nova_altura = AREA_ALTURA
            nova_largura = int(nova_altura * img_cropped.width / img_cropped.height)
        
        img_final = img_cropped.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
        
        # Posicionar no template
        pos_x = (template.width - nova_largura) // 2
        pos_y = AREA_POS_Y + (AREA_ALTURA - nova_altura) // 2
        
        # Colar no template
        template.paste(img_final, (pos_x, pos_y))
        
        # Salvar com nome personalizado
        nome_arquivo = f"{nome_base}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        template.save(nome_arquivo, quality=95, format='PNG')
        
        return nome_arquivo, None
        
    except Exception as e:
        print(f"❌ Erro ao gerar story: {e}")
        return None, str(e)

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
        self.criar_coluna_foto()
        
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

    def salvar_foto_veiculo(self, veiculo_id, foto_bytes):
        """Salva foto do veículo de forma segura - VERSÃO CORRIGIDA"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ✅ CORREÇÃO: Verificar se a coluna 'foto' existe de forma mais robusta
            if os.getenv('DATABASE_URL'):
                # PostgreSQL - Verificar coluna
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'veiculos' AND column_name = 'foto'
                """)
                colunas = [col[0] for col in cursor.fetchall()]
            else:
                # SQLite - Verificar coluna
                cursor.execute("PRAGMA table_info(veiculos)")
                colunas = [col[1] for col in cursor.fetchall()]
            
            # Se a coluna não existir, adicionar
            if 'foto' not in colunas:
                print("🔄 Criando coluna 'foto' antes de salvar...")
                if os.getenv('DATABASE_URL'):
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN foto BYTEA')
                else:
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN foto BLOB')
                conn.commit()
                print("✅ Coluna 'foto' criada com sucesso!")
            
            # ✅ CORREÇÃO CRÍTICA: Verificar se o veículo existe antes de atualizar
            if os.getenv('DATABASE_URL'):
                cursor.execute('SELECT id FROM veiculos WHERE id = %s', (veiculo_id,))
            else:
                cursor.execute('SELECT id FROM veiculos WHERE id = ?', (veiculo_id,))
            
            veiculo_existe = cursor.fetchone()
            
            if not veiculo_existe:
                print(f"❌ Veículo ID {veiculo_id} não encontrado!")
                return False
            
            # ✅ CORREÇÃO: Agora salvar a foto com verificação de tamanho
            if foto_bytes and len(foto_bytes) > 0:
                print(f"📸 Salvando foto ({len(foto_bytes)} bytes) para veículo {veiculo_id}...")
                
                if os.getenv('DATABASE_URL'):
                    # ✅ PostgreSQL: Converter para psycopg2.Binary para BYTEA
                    cursor.execute('UPDATE veiculos SET foto = %s WHERE id = %s', (psycopg2.Binary(foto_bytes), veiculo_id))
                else:
                    # SQLite: manter como bytes
                    cursor.execute('UPDATE veiculos SET foto = ? WHERE id = ?', (foto_bytes, veiculo_id))
                
                conn.commit()
                print("✅ Foto salva com sucesso!")
                return True
            else:
                print("⚠️ Nenhum dado de foto para salvar")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao salvar foto: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def get_foto_veiculo(self, veiculo_id):
        """Busca a foto do veículo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if os.getenv('DATABASE_URL'):
                cursor.execute('SELECT foto FROM veiculos WHERE id = %s', (veiculo_id,))
            else:
                cursor.execute('SELECT foto FROM veiculos WHERE id = ?', (veiculo_id,))
            
            resultado = cursor.fetchone()
            return resultado[0] if resultado and resultado[0] else None
        except Exception as e:
            print(f"Erro ao buscar foto: {e}")
            return None
        finally:
            conn.close()
    
    def criar_coluna_foto(self):
        """Cria a coluna foto se não existir - VERSÃO MAIS ROBUSTA"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            print("🔍 Verificando coluna 'foto'...")
            
            # Verificar se a coluna 'foto' existe
            if os.getenv('DATABASE_URL'):
                # PostgreSQL
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'veiculos' AND column_name = 'foto'
                """)
                resultado = cursor.fetchall()
                colunas = [col[0] for col in resultado] if resultado else []
            else:
                # SQLite
                cursor.execute("PRAGMA table_info(veiculos)")
                resultado = cursor.fetchall()
                colunas = [col[1] for col in resultado] if resultado else []
            
            print(f"📊 Colunas encontradas: {colunas}")
            
            if 'foto' not in colunas:
                print("🔄 Criando coluna 'foto'...")
                if os.getenv('DATABASE_URL'):
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN foto BYTEA')
                    print("✅ Coluna 'foto' criada no PostgreSQL!")
                else:
                    cursor.execute('ALTER TABLE veiculos ADD COLUMN foto BLOB')
                    print("✅ Coluna 'foto' criada no SQLite!")
                conn.commit()
            else:
                print("✅ Coluna 'foto' já existe")
                
        except Exception as e:
            print(f"❌ Erro ao verificar/criar coluna foto: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()     

    # =============================================
    # MÉTODOS ORIGINAIS - ADAPTADOS PARA AMBOS OS BANCOS
    # =============================================
        
    def get_veiculos(self, filtro_status=None):
        """Busca veículos - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT 
                    v.id, v.modelo, v.ano, v.marca, v.cor, 
                    v.preco_entrada, v.preco_venda, v.fornecedor, 
                    v.km, v.placa, v.chassi, v.combustivel, 
                    v.cambio, v.portas, v.observacoes, 
                    v.data_cadastro, v.status,
                    COALESCE(v.margem_negociacao, 30) as margem_negociacao
                FROM veiculos v
            '''
            
            if filtro_status and filtro_status != 'Todos':
                query += f" WHERE v.status = '{filtro_status}'"
            
            query += ' ORDER BY v.data_cadastro DESC'
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            # Converter para dicionários
            veiculos = []
            for row in resultados:
                veiculo = dict(zip(colunas, row))
                veiculos.append(veiculo)
            
            return veiculos
            
        except Exception as e:
            print(f"❌ Erro ao buscar veículos: {e}")
            return []
        finally:
            conn.close()
    
    def add_veiculo(self, veiculo_data):
        """Adiciona veículo com tratamento robusto de erros"""
        print(f"🔍 DEBUG add_veiculo - Iniciando cadastro...")
        print(f"📦 Dados recebidos: {veiculo_data}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calcular preço de venda
        preco_venda = veiculo_data['preco_venda']
        margem = veiculo_data.get('margem_negociacao', 15)

        
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
        """Busca gastos - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT g.*, v.marca, v.modelo 
                FROM gastos g 
                LEFT JOIN veiculos v ON g.veiculo_id = v.id
            '''
            
            if veiculo_id:
                query += f' WHERE g.veiculo_id = {veiculo_id}'
            
            query += ' ORDER BY g.data DESC'
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            gastos = []
            for row in resultados:
                gasto = dict(zip(colunas, row))
                gastos.append(gasto)
            
            return gastos
            
        except Exception as e:
            print(f"❌ Erro ao buscar gastos: {e}")
            return []
        finally:
            conn.close()
    
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
        """Busca vendas - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            vendas = []
            for row in resultados:
                venda = dict(zip(colunas, row))
                vendas.append(venda)
            
            return vendas
            
        except Exception as e:
            print(f"❌ Erro ao buscar vendas: {e}")
            return []
        finally:
            conn.close()
    
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
        """Busca documentos - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT d.*, v.marca, v.modelo 
                FROM documentos d 
                LEFT JOIN veiculos v ON d.veiculo_id = v.id
            '''
            if veiculo_id:
                query += f' WHERE d.veiculo_id = {veiculo_id}'
            query += ' ORDER BY d.data_upload DESC'
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            documentos = []
            for row in resultados:
                documento = dict(zip(colunas, row))
                documentos.append(documento)
            
            return documentos
            
        except Exception as e:
            print(f"❌ Erro ao buscar documentos: {e}")
            return []
        finally:
            conn.close()
    
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
        """Busca fluxo de caixa - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            fluxo = []
            for row in resultados:
                item = dict(zip(colunas, row))
                fluxo.append(item)
            
            return fluxo
            
        except Exception as e:
            print(f"❌ Erro ao buscar fluxo de caixa: {e}")
            return []
        finally:
            conn.close()
    
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
        """Busca contatos - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM contatos ORDER BY data_contato DESC'
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            contatos = []
            for row in resultados:
                contato = dict(zip(colunas, row))
                contatos.append(contato)
            
            return contatos
            
        except Exception as e:
            print(f"❌ Erro ao buscar contatos: {e}")
            return []
        finally:
            conn.close()
    
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
        """Verifica login - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar se estamos usando PostgreSQL
        usando_postgres = os.getenv('DATABASE_URL') is not None
        
        print(f"🔐 MÉTODO verificar_login CHAMADO:")
        print(f"   Username: '{username}'")
        print(f"   Banco: {'PostgreSQL' if usando_postgres else 'SQLite'}")
        
        try:
            if usando_postgres:
                cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
            else:
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
        """Busca financiamentos - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            financiamentos = []
            for row in resultados:
                financiamento = dict(zip(colunas, row))
                financiamentos.append(financiamento)
            
            return financiamentos
            
        except Exception as e:
            print(f"❌ Erro ao buscar financiamentos: {e}")
            return []
        finally:
            conn.close()
            
    def get_parcelas(self, financiamento_id=None, status=None):
        """Busca parcelas - VERSÃO CORRIGIDA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
            
            cursor.execute(query)
            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            parcelas = []
            for row in resultados:
                parcela = dict(zip(colunas, row))
                parcelas.append(parcela)
            
            return parcelas
            
        except Exception as e:
            print(f"❌ Erro ao buscar parcelas: {e}")
            return []
        finally:
            conn.close()

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
            Gerenciamento Carmelo Multimarcas
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
    # =============================================
    # DASHBOARD CONSULTOR INTELIGENTE
    # =============================================
    st.markdown("""
    <div class="glass-card">
        <h2>📊 Painel Estratégico - 4 Perguntas em 10 Segundos</h2>
        <p style="color: #a0a0a0;">💰 Estou ganhando dinheiro? 🔍 Onde estou perdendo? ⏰ O que está parado? ⚡ O que fazer agora?</p>
    </div>
    """, unsafe_allow_html=True)

    # =============================================
    # FUNÇÕES AUXILIARES PARA O DASHBOARD
    # =============================================
    
    def calcular_metricas_periodo(dias=30):
        """Calcula métricas comparativas com período anterior"""
        hoje = datetime.datetime.now()
        data_inicio = hoje - datetime.timedelta(days=dias)
        data_anterior_inicio = data_inicio - datetime.timedelta(days=dias)
        
        # Buscar vendas do período atual e anterior
        todas_vendas = db.get_vendas()
        vendas_periodo = []
        vendas_anterior = []
        
        for venda in todas_vendas:
            data_venda = venda['data_venda']
            if hasattr(data_venda, 'date'):
                data_venda = data_venda.date()
            elif isinstance(data_venda, str):
                data_venda = datetime.datetime.strptime(data_venda[:10], '%Y-%m-%d').date()
            
            if data_inicio.date() <= data_venda <= hoje.date():
                vendas_periodo.append(venda)
            elif data_anterior_inicio.date() <= data_venda < data_inicio.date():
                vendas_anterior.append(venda)
        
        faturamento_atual = sum(v['valor_venda'] for v in vendas_periodo)
        faturamento_anterior = sum(v['valor_venda'] for v in vendas_anterior)
        
        # Calcular variação
        if faturamento_anterior > 0:
            variacao = ((faturamento_atual - faturamento_anterior) / faturamento_anterior) * 100
        else:
            variacao = 100 if faturamento_atual > 0 else 0
        
        return {
            'faturamento_atual': faturamento_atual,
            'faturamento_anterior': faturamento_anterior,
            'variacao': variacao,
            'qtd_vendas': len(vendas_periodo),
            'qtd_anterior': len(vendas_anterior)
        }

    def calcular_giro_estoque():
        """Calcula métricas de giro de estoque"""
        veiculos = db.get_veiculos()
        vendas = db.get_vendas()
        
        # Calcular tempo médio em estoque para vendidos
        tempos_estoque = []
        for venda in vendas:
            veiculo = next((v for v in veiculos if v['id'] == venda['veiculo_id']), None)
            if veiculo:
                data_cadastro = veiculo['data_cadastro']
                data_venda = venda['data_venda']
                
                # Converter datas
                if hasattr(data_cadastro, 'date'):
                    data_cadastro = data_cadastro.date()
                elif isinstance(data_cadastro, str):
                    data_cadastro = datetime.datetime.strptime(data_cadastro[:10], '%Y-%m-%d').date()
                
                if hasattr(data_venda, 'date'):
                    data_venda = data_venda.date()
                elif isinstance(data_venda, str):
                    data_venda = datetime.datetime.strptime(data_venda[:10], '%Y-%m-%d').date()
                
                dias = (data_venda - data_cadastro).days
                if dias > 0:
                    tempos_estoque.append(dias)
        
        tempo_medio = sum(tempos_estoque) / len(tempos_estoque) if tempos_estoque else 0
        
        # Classificar veículos atuais por tempo
        hoje = datetime.datetime.now().date()
        estoque_atual = [v for v in veiculos if v['status'] == 'Em estoque']
        
        faixas = {
            '0-30 dias': [],
            '31-60 dias': [],
            '61+ dias': []
        }
        
        for veiculo in estoque_atual:
            data_cadastro = veiculo['data_cadastro']
            if hasattr(data_cadastro, 'date'):
                data_cadastro = data_cadastro.date()
            elif isinstance(data_cadastro, str):
                data_cadastro = datetime.datetime.strptime(data_cadastro[:10], '%Y-%m-%d').date()
            
            dias_estoque = (hoje - data_cadastro).days
            
            if dias_estoque <= 30:
                faixas['0-30 dias'].append(veiculo)
            elif dias_estoque <= 60:
                faixas['31-60 dias'].append(veiculo)
            else:
                faixas['61+ dias'].append(veiculo)
        
        return {
            'tempo_medio': tempo_medio,
            'faixas': faixas,
            'total_estoque': len(estoque_atual)
        }

    def calcular_alarmes():
        """Gera alertas inteligentes"""
        veiculos = db.get_veiculos()
        vendas = db.get_vendas()
        gastos = db.get_gastos()
        metricas_periodo = calcular_metricas_periodo(30)
        
        alertas = []
        
        # Alerta 1: Veículos parados > 45 dias
        hoje = datetime.datetime.now().date()
        veiculos_parados = []
        capital_parado = 0
        
        for veiculo in [v for v in veiculos if v['status'] == 'Em estoque']:
            data_cadastro = veiculo['data_cadastro']
            if hasattr(data_cadastro, 'date'):
                data_cadastro = data_cadastro.date()
            elif isinstance(data_cadastro, str):
                data_cadastro = datetime.datetime.strptime(data_cadastro[:10], '%Y-%m-%d').date()
            
            dias = (hoje - data_cadastro).days
            if dias > 45:
                veiculos_parados.append(veiculo)
                capital_parado += veiculo['preco_entrada']
        
        if veiculos_parados:
            alertas.append({
                'tipo': 'critico',
                'icone': '⚠️',
                'mensagem': f"{len(veiculos_parados)} veículos acima de 45 dias em estoque (R$ {capital_parado:,.0f} em capital parado)"
            })
        
        # Alerta 2: Margem em queda
        dre = calcular_dre()
        if dre['lucro_liquido'] > 0:
            margem_atual = (dre['lucro_liquido'] / dre['receitas'] * 100) if dre['receitas'] > 0 else 0
            # Comparar com período anterior (simplificado)
            if margem_atual < 10:
                alertas.append({
                    'tipo': 'atencao',
                    'icone': '📉',
                    'mensagem': f"Margem em {margem_atual:.1f}% - abaixo da meta recomendada (15%)"
                })
        
        # Alerta 3: Queda de vendas
        if metricas_periodo['variacao'] < 0:
            alertas.append({
                'tipo': 'atencao',
                'icone': '⬇️',
                'mensagem': f"Vendas caíram {abs(metricas_periodo['variacao']):.1f}% vs período anterior"
            })
        
        # Alerta 4: Modelo de maior giro
        if vendas:
            modelos_vendas = {}
            for venda in vendas:
                modelo = f"{venda.get('marca', '')} {venda.get('modelo', '')}"
                if modelo not in modelos_vendas:
                    modelos_vendas[modelo] = 0
                modelos_vendas[modelo] += 1
            
            if modelos_vendas:
                top_modelo = max(modelos_vendas, key=modelos_vendas.get)
                alertas.append({
                    'tipo': 'positivo',
                    'icone': '🔥',
                    'mensagem': f"Modelo {top_modelo} é o de maior giro ({modelos_vendas[top_modelo]} vendas)"
                })
        
        return alertas

    def calcular_rentabilidade_inteligente():
        """Ranking de rentabilidade por modelo/marca"""
        veiculos = db.get_veiculos()
        vendas = db.get_vendas()
        gastos = db.get_gastos()
        
        modelos = {}
        marcas = {}
        
        for veiculo in veiculos:
            if veiculo['status'] == 'Vendido':
                # Calcular custo total
                gastos_veiculo = [g for g in gastos if g['veiculo_id'] == veiculo['id']]
                total_gastos = sum(g['valor'] for g in gastos_veiculo)
                custo_total = veiculo['preco_entrada'] + total_gastos
                
                # Buscar venda
                venda = next((v for v in vendas if v['veiculo_id'] == veiculo['id']), None)
                if venda:
                    lucro = venda['valor_venda'] - custo_total
                    margem = (lucro / custo_total * 100) if custo_total > 0 else 0
                    
                    # Por modelo
                    modelo_key = f"{veiculo['marca']} {veiculo['modelo']}"
                    if modelo_key not in modelos:
                        modelos[modelo_key] = {'lucro_total': 0, 'margens': [], 'qtd': 0}
                    modelos[modelo_key]['lucro_total'] += lucro
                    modelos[modelo_key]['margens'].append(margem)
                    modelos[modelo_key]['qtd'] += 1
                    
                    # Por marca
                    if veiculo['marca'] not in marcas:
                        marcas[veiculo['marca']] = {'lucro_total': 0, 'margens': [], 'qtd': 0}
                    marcas[veiculo['marca']]['lucro_total'] += lucro
                    marcas[veiculo['marca']]['margens'].append(margem)
                    marcas[veiculo['marca']]['qtd'] += 1
        
        # Calcular médias
        for modelo in modelos:
            modelos[modelo]['margem_media'] = sum(modelos[modelo]['margens']) / len(modelos[modelo]['margens'])
        
        for marca in marcas:
            marcas[marca]['margem_media'] = sum(marcas[marca]['margens']) / len(marcas[marca]['margens'])
        
        return {
            'modelos': modelos,
            'marcas': marcas
        }

    def gerar_recomendacoes():
        """Gera recomendações automáticas baseadas em dados"""
        recomendacoes = []
        rentabilidade = calcular_rentabilidade_inteligente()
        giro = calcular_giro_estoque()
        veiculos = db.get_veiculos()
        
        # Recomendação 1: Priorizar modelo de maior margem
        if rentabilidade['modelos']:
            top_modelo = max(rentabilidade['modelos'].items(), key=lambda x: x[1]['margem_media'])
            recomendacoes.append({
                'icone': '📢',
                'titulo': 'Priorizar anúncios',
                'descricao': f"Modelo {top_modelo[0]} tem melhor margem ({top_modelo[1]['margem_media']:.1f}%)"
            })
        
        # Recomendação 2: Reduzir preço de modelos lentos
        veiculos_lentos = giro['faixas']['61+ dias']
        if veiculos_lentos:
            valor_total_lentos = sum(v['preco_venda'] for v in veiculos_lentos)
            recomendacoes.append({
                'icone': '🏷️',
                'titulo': 'Acelerar giro',
                'descricao': f"Reduzir preço de {len(veiculos_lentos)} veículos parados (R$ {valor_total_lentos:,.0f})"
            })
        
        # Recomendação 3: Marca para investir
        if rentabilidade['marcas']:
            melhor_marca = max(rentabilidade['marcas'].items(), key=lambda x: x[1]['margem_media'])
            recomendacoes.append({
                'icone': '💎',
                'titulo': 'Foco em compras',
                'descricao': f"Marca {melhor_marca[0]} tem melhor histórico de margem ({melhor_marca[1]['margem_media']:.1f}%)"
            })
        
        # Recomendação 4: Revisar modelos ruins
        modelos_ruins = [m for m in rentabilidade['modelos'].items() if m[1]['margem_media'] < 5]
        if modelos_ruins:
            pior_modelo = min(rentabilidade['modelos'].items(), key=lambda x: x[1]['margem_media'])
            recomendacoes.append({
                'icone': '⚠️',
                'titulo': 'Revisar estratégia',
                'descricao': f"Modelo {pior_modelo[0]} com margem baixa ({pior_modelo[1]['margem_media']:.1f}%)"
            })
        
        return recomendacoes[:4]  # Top 4 recomendações

    def calcular_saude_financeira():
        """Calcula indicadores de saúde financeira"""
        financiamentos = db.get_financiamentos()
        parcelas = db.get_parcelas()
        
        hoje = datetime.datetime.now().date()
        
        def processar_data(data):
            if data is None:
                return hoje
            if hasattr(data, 'date'):
                return data.date()
            elif isinstance(data, str):
                return datetime.datetime.strptime(data[:10], '%Y-%m-%d').date()
            return data
        
        # Cálculos
        total_financiado = sum(f['valor_total'] for f in financiamentos if f['status'] == 'Ativo')
        carteira_ativa = len([f for f in financiamentos if f['status'] == 'Ativo'])
        
        parcelas_pendentes = [p for p in parcelas if p['status'] == 'Pendente']
        parcelas_vencidas = [p for p in parcelas_pendentes if processar_data(p['data_vencimento']) < hoje]
        
        total_pendente = sum(p['valor_parcela'] for p in parcelas_pendentes)
        total_vencido = sum(p['valor_parcela'] for p in parcelas_vencidas)
        
        taxa_inadimplencia = (total_vencido / total_pendente * 100) if total_pendente > 0 else 0
        
        # Dias médios de atraso
        dias_atraso = []
        for p in parcelas_vencidas:
            dias = (hoje - processar_data(p['data_vencimento'])).days
            dias_atraso.append(dias)
        
        dias_medio_atraso = sum(dias_atraso) / len(dias_atraso) if dias_atraso else 0
        
        # Previsão 3 meses
        previsao = []
        for i in range(1, 4):
            mes = hoje.replace(day=1) + datetime.timedelta(days=32*i)
            mes = mes.replace(day=1)
            
            valor_mes = sum(
                p['valor_parcela'] for p in parcelas_pendentes
                if processar_data(p['data_vencimento']).year == mes.year and
                processar_data(p['data_vencimento']).month == mes.month
            )
            previsao.append({
                'mes': mes.strftime('%b/%Y'),
                'valor': valor_mes
            })
        
        return {
            'total_financiado': total_financiado,
            'carteira_ativa': carteira_ativa,
            'taxa_inadimplencia': taxa_inadimplencia,
            'dias_medio_atraso': dias_medio_atraso,
            'previsao': previsao,
            'total_pendente': total_pendente
        }

    # =============================================
    # BUSCAR TODOS OS DADOS NECESSÁRIOS
    # =============================================
    
    veiculos = db.get_veiculos()
    vendas = db.get_vendas()
    dre = calcular_dre()
    stats = calcular_estatisticas_veiculos()
    metricas_periodo = calcular_metricas_periodo(30)
    giro = calcular_giro_estoque()
    alertas = calcular_alarmes()
    rentabilidade = calcular_rentabilidade_inteligente()
    recomendacoes = gerar_recomendacoes()
    saude = calcular_saude_financeira()

    # =============================================
    # BLOCO 1 – KPIs ESTRATÉGICOS (Topo da Página)
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin:0; color: #e88e1b;">📊 INDICADORES VITAIS</h3>
        <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.9rem;">vs período anterior</span>
    </div>
    """, unsafe_allow_html=True)

    # Linha 1 – Indicadores Vitais
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #a0a0a0;">🚗 Estoque</h4>
            <h2 style="font-size: 2rem;">{stats['veiculos_estoque']}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">veículos</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #a0a0a0;">📦 Vendas</h4>
            <h2 style="font-size: 2rem;">{stats['veiculos_vendidos']}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">realizadas</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #a0a0a0;">💰 Faturamento</h4>
            <h2 style="font-size: 2rem; color: #27AE60;">R$ {dre['receitas']:,.0f}</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">total</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # Lucro Líquido em destaque (MAIOR)
        cor_lucro = "#27AE60" if dre['lucro_liquido'] >= 0 else "#E74C3C"
        variacao = metricas_periodo['variacao']
        seta = "▲" if variacao >= 0 else "▼"
        cor_variacao = "#27AE60" if variacao >= 0 else "#E74C3C"
        
        st.markdown(f"""
        <div class="metric-card" style="border: 2px solid {cor_lucro};">
            <h4 style="color: #a0a0a0;">💎 LUCRO LÍQUIDO</h4>
            <h2 style="font-size: 2.5rem; color: {cor_lucro};">R$ {dre['lucro_liquido']:,.0f}</h2>
            <div style="display: flex; justify-content: center; align-items: center; gap: 0.5rem;">
                <span style="color: {cor_variacao}; font-weight: bold;">{seta} {abs(variacao):.1f}%</span>
                <span style="color: #a0a0a0; font-size: 0.8rem;">vs mês anterior</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        margem_geral = (dre['lucro_liquido'] / dre['receitas'] * 100) if dre['receitas'] > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #a0a0a0;">📊 Margem Geral</h4>
            <h2 style="font-size: 2rem;">{margem_geral:.1f}%</h2>
            <p style="color: #a0a0a0; font-size: 0.8rem;">sobre faturamento</p>
        </div>
        """, unsafe_allow_html=True)

    # =============================================
    # BLOCO 2 – ALERTAS INTELIGENTES
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin:0; color: #e88e1b;">🚨 ALERTAS INTELIGENTES</h3>
        <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.9rem;">O que merece sua atenção agora</span>
    </div>
    """, unsafe_allow_html=True)

    # Container para alertas
    st.markdown("""
    <style>
        .alerta-card {
            padding: 1.2rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            border-left: 6px solid;
            transition: all 0.3s ease;
        }
        .alerta-card:hover {
            transform: translateX(5px);
        }
        .alerta-critico { background: rgba(231, 76, 60, 0.1); border-left-color: #E74C3C; }
        .alerta-atencao { background: rgba(243, 156, 18, 0.1); border-left-color: #F39C12; }
        .alerta-positivo { background: rgba(39, 174, 96, 0.1); border-left-color: #27AE60; }
    </style>
    """, unsafe_allow_html=True)

    if alertas:
        for alerta in alertas:
            classe = f"alerta-{alerta['tipo']}"
            st.markdown(f"""
            <div class="alerta-card {classe}">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 2rem; margin-right: 1rem;">{alerta['icone']}</span>
                    <div>
                        <span style="font-size: 1.1rem;">{alerta['mensagem']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✨ Nenhum alerta crítico no momento. Tudo sob controle!")

    # =============================================
    # BLOCO 3 – GIRO DE ESTOQUE
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin:0; color: #e88e1b;">🔄 GIRO DE ESTOQUE</h3>
        <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.9rem;">Tempo é dinheiro</span>
    </div>
    """, unsafe_allow_html=True)

    col_giro1, col_giro2 = st.columns([1, 1])

    with col_giro1:
        st.markdown(f"""
        <div class="glass-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0;">⏱️ Tempo Médio em Estoque</h4>
            <h2 style="font-size: 3rem; color: #e88e1b;">{giro['tempo_medio']:.0f} dias</h2>
            <p style="color: #a0a0a0;">baseado nos últimos veículos vendidos</p>
        </div>
        """, unsafe_allow_html=True)

    with col_giro2:
        st.markdown("""
        <div class="glass-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0;">📊 Distribuição por Faixa</h4>
        """, unsafe_allow_html=True)
        
        # Gráfico de barras horizontal
        faixas = ['0–30 dias', '31–60 dias', '61+ dias']
        valores = [
            len(giro['faixas']['0-30 dias']),
            len(giro['faixas']['31-60 dias']),
            len(giro['faixas']['61+ dias'])
        ]
        cores = ['#27AE60', '#F39C12', '#E74C3C']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=faixas,
            x=valores,
            orientation='h',
            marker_color=cores,
            text=valores,
            textposition='auto',
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=200,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # =============================================
    # BLOCO 4 – RENTABILIDADE INTELIGENTE
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin:0; color: #e88e1b;">📈 RENTABILIDADE INTELIGENTE</h3>
        <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.9rem;">Onde ganhamos mais</span>
    </div>
    """, unsafe_allow_html=True)

    col_rent1, col_rent2, col_rent3 = st.columns([1, 1, 1])

    with col_rent1:
        st.markdown("""
        <div class="glass-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0;">🏆 Ranking por Modelo</h4>
        """, unsafe_allow_html=True)
        
        if rentabilidade['modelos']:
            top_modelos = sorted(rentabilidade['modelos'].items(), key=lambda x: x[1]['margem_media'], reverse=True)[:5]
            for i, (modelo, dados) in enumerate(top_modelos):
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <span>{i+1}. {modelo}</span>
                    <span style="color: #27AE60; font-weight: bold;">{dados['margem_media']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with col_rent2:
        st.markdown("""
        <div class="glass-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0;">🏅 Ranking por Marca</h4>
        """, unsafe_allow_html=True)
        
        if rentabilidade['marcas']:
            top_marcas = sorted(rentabilidade['marcas'].items(), key=lambda x: x[1]['margem_media'], reverse=True)[:5]
            for i, (marca, dados) in enumerate(top_marcas):
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <span>{i+1}. {marca}</span>
                    <span style="color: #27AE60; font-weight: bold;">{dados['margem_media']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with col_rent3:
        st.markdown("""
        <div class="glass-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0;">🎯 Destaques do Mês</h4>
        """, unsafe_allow_html=True)
        
        if rentabilidade['modelos']:
            melhor = max(rentabilidade['modelos'].items(), key=lambda x: x[1]['margem_media'])
            pior = min(rentabilidade['modelos'].items(), key=lambda x: x[1]['margem_media'])
            
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <p style="color: #27AE60; margin-bottom: 0.2rem;">✅ Melhor margem</p>
                <strong>{melhor[0]}</strong>
                <p style="color: #27AE60;">{melhor[1]['margem_media']:.1f}%</p>
            </div>
            <div>
                <p style="color: #E74C3C; margin-bottom: 0.2rem;">⚠️ Pior margem</p>
                <strong>{pior[0]}</strong>
                <p style="color: #E74C3C;">{pior[1]['margem_media']:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de simulação
            if st.button("💰 Simular preço ideal", use_container_width=True, key="simular_preco"):
                st.info("💡 Funcionalidade em desenvolvimento: Simulação de preços baseada em margem histórica")
        else:
            st.info("Dados insuficientes")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # =============================================
    # BLOCO 5 – RECOMENDAÇÕES AUTOMÁTICAS
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin:0; color: #e88e1b;">💡 RECOMENDAÇÕES AUTOMÁTICAS</h3>
        <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.9rem;">Insights baseados em dados</span>
    </div>
    """, unsafe_allow_html=True)

    if recomendacoes:
        cols = st.columns(len(recomendacoes))
        for i, rec in enumerate(recomendacoes):
            with cols[i]:
                st.markdown(f"""
                <div class="glass-card" style="padding: 1.5rem; height: 100%;">
                    <div style="font-size: 2rem; text-align: center;">{rec['icone']}</div>
                    <h4 style="text-align: center; margin: 0.5rem 0;">{rec['titulo']}</h4>
                    <p style="text-align: center; color: #a0a0a0;">{rec['descricao']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("📊 Continue usando o sistema para gerar recomendações personalizadas")

    # =============================================
    # BLOCO 7 – SAÚDE FINANCEIRA
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin:0; color: #e88e1b;">🏦 SAÚDE FINANCEIRA</h3>
        <span style="margin-left: 1rem; color: #a0a0a0; font-size: 0.9rem;">Recebíveis e inadimplência</span>
    </div>
    """, unsafe_allow_html=True)

    col_saude1, col_saude2, col_saude3, col_saude4 = st.columns(4)

    with col_saude1:
        st.metric("💰 Total Financiado", f"R$ {saude['total_financiado']:,.0f}")

    with col_saude2:
        st.metric("📋 Carteira Ativa", f"{saude['carteira_ativa']} contratos")

    with col_saude3:
        cor_inad = "#E74C3C" if saude['taxa_inadimplencia'] > 10 else "#27AE60"
        st.metric("⚠️ Inadimplência", f"{saude['taxa_inadimplencia']:.1f}%")

    with col_saude4:
        st.metric("⏰ Dias Médio Atraso", f"{saude['dias_medio_atraso']:.0f} dias")

    # Gráfico de previsão
    st.markdown("""
    <div class="glass-card" style="margin-top: 1rem; padding: 1.5rem;">
        <h4 style="margin-top: 0;">📅 Previsão de Recebíveis - Próximos 3 Meses</h4>
    """, unsafe_allow_html=True)

    if saude['previsao']:
        meses = [p['mes'] for p in saude['previsao']]
        valores = [p['valor'] for p in saude['previsao']]
        
        fig = px.bar(
            x=meses,
            y=valores,
            title="",
            color=valores,
            color_continuous_scale='viridis',
            labels={'x': 'Mês', 'y': 'Valor (R$)'}
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            showlegend=False
        )
        
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📈 Nenhum recebível previsto para os próximos meses")

    st.markdown("</div>", unsafe_allow_html=True)

    # =============================================
    # RESUMO EXECUTIVO
    # =============================================
    
    st.markdown("---")
    st.markdown("""
    <div class="glass-card" style="background: linear-gradient(135deg, rgba(232,142,27,0.1), rgba(255,255,255,0.05));">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin:0;">📋 Resumo Executivo</h4>
                <p style="color: #a0a0a0; margin:0;">Respondendo às 4 perguntas em 10 segundos:</p>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 1rem;">
            <div>
                <p style="color: #27AE60; margin-bottom: 0.2rem;">💰 Estou ganhando dinheiro?</p>
                <p style="color: white;">{dre['lucro_liquido']:,.0f} de lucro • {margem_geral:.1f}% de margem</p>
                
                <p style="color: #E74C3C; margin: 1rem 0 0.2rem 0;">🔍 Onde estou perdendo?</p>
                <p style="color: white;">{len(giro['faixas']['61+ dias'])} veículos parados • R$ {sum(v['preco_entrada'] for v in giro['faixas']['61+ dias']):,.0f} parado</p>
            </div>
            <div>
                <p style="color: #F39C12; margin-bottom: 0.2rem;">⏰ O que está parado?</p>
                <p style="color: white;">{giro['tempo_medio']:.0f} dias em média • {len(giro['faixas']['61+ dias'])} veículos com 61+ dias</p>
                
                <p style="color: #3498DB; margin: 1rem 0 0.2rem 0;">⚡ O que fazer agora?</p>
                <p style="color: white;">{recomendacoes[0]['descricao'] if recomendacoes else "Sistema coletando dados para recomendações"}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pequeno espaço no final
    st.markdown("<br>", unsafe_allow_html=True)
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
            # Dados básicos
            modelo = st.text_input("Modelo*", placeholder="Gol")
            marca = st.text_input("Marca*", placeholder="Volkswagen")
            cor = st.selectbox("Cor*", ["Prata", "Preto", "Branco", "Vermelho", "Azul", "Cinza", "Verde", "Laranja"])
            
            # ANOS - lado a lado
            st.markdown("#### 📅 Anos")
            col_ano1, col_ano2 = st.columns(2)
            with col_ano1:
                ano = st.number_input("Ano*", min_value=1970, max_value=2030, value=2025,
                                    help="Ano do modelo (geralmente igual ao de fabricação)")
            with col_ano2:
                ano_fabricacao = st.number_input("Ano de Fabricação", min_value=1970, max_value=2030, value=2025,
                                               help="Ano em que o veículo foi efetivamente fabricado")
            
            # Dados para contrato
            st.markdown("#### 📄 Dados para Contrato")
            col_doc1, col_doc2 = st.columns(2)
            with col_doc1:
                renavam = st.text_input("RENAVAM", placeholder="12345678901", key="renavam_input")
            with col_doc2:
                chassi = st.text_input("Chassi", placeholder="9BWZZZ377VT004251")
            
            # =============================================
            # SISTEMA DE PREÇOS COM NEGOCIAÇÃO
            # =============================================
            st.markdown("#### 💰 Sistema de Preços")
            
            # 1. PREÇO DE CUSTO (PISO)
            col_custo1, col_custo2 = st.columns([3, 1])
            with col_custo1:
                preco_custo_input = st.text_input(
                    "Preço de Custo (R$)*", 
                    placeholder="Ex: 50.000,00",
                    help="Valor que você pagou pelo veículo (piso mínimo)",
                    key="preco_custo"
                )
            with col_custo2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("💰 **PISO**")
            
            # 2. PREÇO PARA NEGOCIAÇÃO
            col_negociacao1, col_negociacao2 = st.columns([3, 1])
            with col_negociacao1:
                preco_negociacao_input = st.text_input(
                    "Preço para Negociação (R$)*", 
                    placeholder="Ex: 65.000,00",
                    help="Valor anunciado - ponto de partida para negociação",
                    key="preco_negociacao"
                )
            with col_negociacao2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("🏷️ **ANUNCIADO**")
            
            # 3. MARGEM PARA NEGOCIAÇÃO (campo numérico)
            col_margem1, col_margem2 = st.columns([3, 1])
            with col_margem1:
                margem_negociacao = st.number_input(
                    "Margem para Negociação (%)*",
                    min_value=0.0,
                    max_value=100.0,
                    value=15.0,
                    step=0.5,
                    format="%.1f",
                    help="Percentual de desconto máximo que pode ser concedido"
                )
            with col_margem2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("🎯 **MARGEM**")
            
            # =============================================
            # CÁLCULOS EM TEMPO REAL
            # =============================================
            
            # Função para converter preço BR para float
            def converter_preco_para_float(preco_str):
                """Converte formato brasileiro para float"""
                if not preco_str:
                    return None
                try:
                    # Remove R$, espaços e pontos de milhar
                    preco_limpo = preco_str.replace('R$', '').replace(' ', '').strip()
                    
                    # Verifica formato
                    if ',' in preco_limpo and '.' in preco_limpo:
                        # Formato: 50.000,00
                        preco_limpo = preco_limpo.replace('.', '').replace(',', '.')
                    elif ',' in preco_limpo:
                        # Formato: 50000,00
                        preco_limpo = preco_limpo.replace(',', '.')
                    
                    return float(preco_limpo)
                except:
                    return None
            
            # Converter preços
            preco_custo_float = converter_preco_para_float(preco_custo_input)
            preco_negociacao_float = converter_preco_para_float(preco_negociacao_input)
            
            # Container para resultados
            if preco_custo_float and preco_negociacao_float:
                st.markdown("---")
                st.markdown("#### 📊 Resultados dos Cálculos")
                
                # Calcular margem real
                margem_real = ((preco_negociacao_float - preco_custo_float) / preco_custo_float * 100)
                
                # Calcular preço mínimo (com margem de desconto aplicada)
                preco_minimo = preco_negociacao_float * (1 - margem_negociacao/100)
                
                # Calcular lucro potencial mínimo
                lucro_minimo = preco_minimo - preco_custo_float
                
                # Mostrar métricas
                col_res1, col_res2 = st.columns(2)
                
                with col_res1:
                    # Margem real do preço anunciado
                    st.metric(
                        "📈 Margem no Anúncio",
                        f"{margem_real:.1f}%",
                        help="Margem entre preço anunciado e custo"
                    )
                    
                    # Preço mínimo
                    st.metric(
                        "💰 Preço Mínimo",
                        f"R$ {preco_minimo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        delta=f"-{margem_negociacao:.1f}%",
                        delta_color="inverse",
                        help="Menor valor que pode ser aceito na negociação"
                    )
                
                with col_res2:
                    # Margem de negociação permitida
                    st.metric(
                        "🎯 Margem de Negociação",
                        f"{margem_negociacao:.1f}%",
                        help="Desconto máximo que pode ser concedido"
                    )
                    
                    # Lucro mínimo garantido
                    cor_lucro = "normal" if lucro_minimo > 0 else "inverse"
                    st.metric(
                        "💵 Lucro Mínimo",
                        f"R$ {lucro_minimo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        delta_color=cor_lucro,
                        help="Lucro garantido mesmo com desconto máximo"
                    )
                
                # Barra de visualização
                st.markdown("#### 📊 Visualização da Faixa de Preços")
                
                # Calcular valores para a barra
                faixa_custo = preco_custo_float
                faixa_minimo = preco_minimo
                faixa_negociacao = preco_negociacao_float
                
                # Encontrar máximo para escala
                faixa_max = max(faixa_custo, faixa_minimo, faixa_negociacao) * 1.1
                
                # Criar visualização
                fig = go.Figure()
                
                # Adicionar barra de custo
                fig.add_trace(go.Indicator(
                    mode="number+gauge",
                    value=faixa_custo,
                    title={'text': "💰 Custo"},
                    domain={'x': [0.25, 1], 'y': [0.7, 1]},
                    gauge={
                        'shape': "bullet",
                        'axis': {'range': [0, faixa_max]},
                        'bar': {'color': "#E74C3C", 'thickness': 0.8},
                        'steps': [
                            {'range': [0, faixa_custo], 'color': "rgba(231, 76, 60, 0.2)"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 2},
                            'thickness': 0.75,
                            'value': faixa_custo
                        }
                    }
                ))
                
                # Adicionar barra de preço mínimo
                fig.add_trace(go.Indicator(
                    mode="number+gauge",
                    value=faixa_minimo,
                    title={'text': "🎯 Mínimo"},
                    domain={'x': [0.25, 1], 'y': [0.4, 0.7]},
                    gauge={
                        'shape': "bullet",
                        'axis': {'range': [0, faixa_max]},
                        'bar': {'color': "#F39C12", 'thickness': 0.8},
                        'steps': [
                            {'range': [0, faixa_minimo], 'color': "rgba(243, 156, 18, 0.2)"}
                        ],
                        'threshold': {
                            'line': {'color': "orange", 'width': 2},
                            'thickness': 0.75,
                            'value': faixa_minimo
                        }
                    }
                ))
                
                # Adicionar barra de preço anunciado
                fig.add_trace(go.Indicator(
                    mode="number+gauge",
                    value=faixa_negociacao,
                    title={'text': "🏷️ Anunciado"},
                    domain={'x': [0.25, 1], 'y': [0.1, 0.4]},
                    gauge={
                        'shape': "bullet",
                        'axis': {'range': [0, faixa_max]},
                        'bar': {'color': "#27AE60", 'thickness': 0.8},
                        'steps': [
                            {'range': [0, faixa_negociacao], 'color': "rgba(39, 174, 96, 0.2)"}
                        ],
                        'threshold': {
                            'line': {'color': "green", 'width': 2},
                            'thickness': 0.75,
                            'value': faixa_negociacao
                        }
                    }
                ))
                
                fig.update_layout(
                    height=250,
                    margin={'t': 20, 'b': 20, 'l': 20, 'r': 20},
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': 'white'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Legenda
                col_leg1, col_leg2, col_leg3 = st.columns(3)
                with col_leg1:
                    st.markdown("""
                    <div style="background: rgba(231, 76, 60, 0.2); padding: 8px; border-radius: 6px; text-align: center;">
                        <small><strong>💰 CUSTO</strong><br>Valor pago</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_leg2:
                    st.markdown("""
                    <div style="background: rgba(243, 156, 18, 0.2); padding: 8px; border-radius: 6px; text-align: center;">
                        <small><strong>🎯 MÍNIMO</strong><br>Com desconto máximo</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_leg3:
                    st.markdown("""
                    <div style="background: rgba(39, 174, 96, 0.2); padding: 8px; border-radius: 6px; text-align: center;">
                        <small><strong>🏷️ ANUNCIADO</strong><br>Ponto de partida</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # =============================================
            # CAMPOS RESTANTES DO FORMULÁRIO
            # =============================================
            
            fornecedor = st.text_input("Fornecedor*", placeholder="Nome do fornecedor")
            km = st.number_input("Quilometragem", value=0)
            placa = st.text_input("Placa", placeholder="ABC1D23")            
            combustivel = st.selectbox("Combustível", ["Gasolina", "Álcool", "Flex", "Diesel", "Elétrico"])
            cambio = st.selectbox("Câmbio", ["Automático", "Manual", "CVT"])
            portas = st.selectbox("Portas", [2, 4, 5])
            observacoes = st.text_area("Observações")
            
            # Campo de foto do veículo
            st.markdown("#### 📸 Foto do Veículo")
            foto_veiculo = st.file_uploader(
                "Faça upload da foto principal do veículo", 
                type=['jpg', 'jpeg', 'png'],
                help="Selecione uma imagem clara do veículo"
            )
            
            # Mostrar prévia da foto
            if foto_veiculo is not None:
                image = Image.open(foto_veiculo)
                st.image(image, caption="Prévia da Foto", width=300)
            
            # BOTÃO DE SUBMIT DO FORMULÁRIO
            submitted = st.form_submit_button("Cadastrar Veículo", use_container_width=True)
            
            if submitted:
                if not prevenir_loop_submit():
                    st.stop()
                
                # Validação dos campos obrigatórios
                campos_obrigatorios = [
                    ("Modelo", modelo),
                    ("Marca", marca),
                    ("Ano", ano),
                    ("Preço de Custo", preco_custo_input),
                    ("Preço para Negociação", preco_negociacao_input),
                    ("Fornecedor", fornecedor)
                ]
                
                campos_faltando = [nome for nome, valor in campos_obrigatorios if not valor]
                
                if campos_faltando:
                    st.error(f"❌ Campos obrigatórios faltando: {', '.join(campos_faltando)}")
                else:
                    try:
                        # Converter preços
                        preco_custo = converter_preco_para_float(preco_custo_input)
                        preco_negociacao = converter_preco_para_float(preco_negociacao_input)
                        
                        if preco_custo is None or preco_negociacao is None:
                            st.error("❌ Formato de preço inválido! Use: 50.000,00 ou 50000,00")
                        elif preco_custo <= 0 or preco_negociacao <= 0:
                            st.error("⚠️ Os preços devem ser maiores que zero!")
                        elif preco_negociacao <= preco_custo:
                            st.error("❌ O preço para negociação deve ser maior que o preço de custo!")
                        else:
                            # Verificar se margem de negociação é viável
                            preco_minimo_calculado = preco_negociacao * (1 - margem_negociacao/100)
                            
                            if preco_minimo_calculado < preco_custo:
                                st.warning(f"⚠️ Atenção: Com {margem_negociacao}% de desconto, o preço mínimo (R$ {preco_minimo_calculado:,.2f}) fica abaixo do custo!")
                                if not st.checkbox("✅ Confirmar cadastro mesmo assim"):
                                    st.stop()
                            
                            # Preparar dados para salvar
                            novo_veiculo = {
                                'modelo': modelo, 
                                'ano': ano, 
                                'marca': marca, 
                                'cor': cor,
                                'preco_entrada': preco_custo,  # Salva como preço de custo
                                'preco_venda': preco_negociacao,  # Salva como preço para negociação
                                'margem_negociacao': margem_negociacao,  # Margem de desconto permitida
                                'fornecedor': fornecedor, 
                                'km': km, 
                                'placa': placa,
                                'chassi': chassi, 
                                'renavam': renavam,
                                'combustivel': combustivel, 
                                'cambio': cambio,
                                'portas': portas, 
                                'observacoes': observacoes,
                                'ano_fabricacao': ano_fabricacao  # Mantemos apenas este
                            }
                            
                            print("🔄 Tentando cadastrar veículo...")
                            veiculo_id = db.add_veiculo(novo_veiculo)
                            
                            if veiculo_id:
                                # Salvar foto se fornecida
                                if foto_veiculo is not None:
                                    try:
                                        if len(foto_veiculo.getvalue()) > 5 * 1024 * 1024:
                                            st.warning("⚠️ Foto muito grande (máximo 5MB).")
                                        else:
                                            success_foto = db.salvar_foto_veiculo(veiculo_id, foto_veiculo.getvalue())
                                            if success_foto:
                                                st.success("✅ Foto salva com sucesso!")
                                            else:
                                                st.warning("⚠️ Veículo cadastrado, mas erro ao salvar foto")
                                    except Exception as e:
                                        st.warning(f"⚠️ Veículo cadastrado, mas erro na foto: {str(e)}")
                                
                                st.success("✅ Veículo cadastrado com sucesso!")
                                st.balloons()
                                resetar_formulario()
                            else:
                                st.error("❌ Erro ao cadastrar veículo. Verifique os logs.")
                                
                    except ValueError as e:
                        st.error(f"❌ Erro na conversão de preços: {e}")
                    except Exception as e:
                        st.error(f"❌ Erro inesperado: {str(e)}")
    
    with col_veic2:
        # =============================================
        # LISTA DE VEÍCULOS EM ESTOQUE (INALTERADA)
        # =============================================
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

                # Calcular margem atual (baseada no preço de negociação atual)
                margem_atual = ((veiculo['preco_venda'] - custo_total) / custo_total) * 100 if custo_total > 0 else 0

                # Exibir informações do veículo
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**Marca:** {veiculo['marca']}")
                    st.write(f"**Modelo:** {veiculo['modelo']}")
                    st.write(f"**Ano:** {veiculo['ano']}")
                    if 'ano_fabricacao' in veiculo and veiculo['ano_fabricacao'] != veiculo['ano']:
                        st.write(f"**Fabricação:** {veiculo['ano_fabricacao']}")
                with col_info2:
                    st.write(f"**Cor:** {veiculo['cor']}")
                    st.write(f"**KM:** {veiculo['km']:,}")
                    st.write(f"**Placa:** {veiculo['placa'] or 'Não informada'}")

                # Preços - AGORA MOSTRANDO OS 3 NÍVEIS
                st.markdown("---")
                st.markdown("#### 💰 Sistema de Preços")
                
                # Recuperar margem de negociação do banco
                margem_negociacao_veiculo = veiculo.get('margem_negociacao', 15)
                preco_minimo_veiculo = veiculo['preco_venda'] * (1 - margem_negociacao_veiculo/100)
                
                col_preco1, col_preco2, col_preco3 = st.columns(3)
                with col_preco1:
                    st.markdown("**💰 Custo Total**")
                    st.markdown(f"<h3 style='color: #a0a0a0; text-align: center;'>R$ {custo_total:,.2f}</h3>", unsafe_allow_html=True)
                    st.caption(f"Compra: R$ {veiculo['preco_entrada']:,.2f}")
                    st.caption(f"Gastos: R$ {total_gastos:,.2f}")
                
                with col_preco2:
                    st.markdown("**🎯 Preço Mínimo**")
                    st.markdown(f"<h3 style='color: #F39C12; text-align: center;'>R$ {preco_minimo_veiculo:,.2f}</h3>", unsafe_allow_html=True)
                    st.caption(f"Margem: {margem_negociacao_veiculo}%")
                
                with col_preco3:
                    st.markdown("**🏷️ Anunciado**")
                    st.markdown(f"<h3 style='color: #27AE60; text-align: center;'>R$ {veiculo['preco_venda']:,.2f}</h3>", unsafe_allow_html=True)
                    st.caption("Ponto de partida")

                # Margem real
                margem_real = ((veiculo['preco_venda'] - custo_total) / custo_total * 100) if custo_total > 0 else 0
                if margem_real >= 20:
                    st.success(f"**✅ Margem Real: +{margem_real:.1f}%**")
                elif margem_real >= 10:
                    st.warning(f"**⚠️ Margem Real: +{margem_real:.1f}%**")
                else:
                    st.error(f"**❌ Margem Real: +{margem_real:.1f}%**")

                # Gastos detalhados (código existente continua igual)
                if gastos_veiculo:
                    st.markdown("#### 💰 Gastos Detalhados")
                    for i, gasto in enumerate(gastos_veiculo):
                        data_gasto_formatada = formatar_data(gasto['data'])
                        
                        gasto_key = f"gasto_{veiculo['id']}_{i}"
                        st.markdown(f"""
                        <div style="padding: 0.5rem; margin: 0.25rem 0; background: rgba(255,255,255,0.02); border-radius: 6px;">
                            <strong>{gasto['tipo_gasto']}</strong> - R$ {gasto['valor']:,.2f}
                            <div style="color: #a0a0a0; font-size: 0.8rem;">
                                {data_gasto_formatada} • {gasto['descricao']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Adicionar novo gasto (código existente continua igual)
                st.markdown("#### ➕ Adicionar Gasto")
                
                gasto_form_key = f"gasto_form_{veiculo['id']}"
                if f"{gasto_form_key}_submitted" not in st.session_state:
                    st.session_state[f"{gasto_form_key}_submitted"] = False
                
                if st.session_state[f"{gasto_form_key}_submitted"]:
                    st.success("✅ Gasto adicionado com sucesso!")
                    
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
                                    st.session_state[f"{gasto_form_key}_submitted"] = True
                                    forcar_atualizacao_gastos()
                                    resetar_formulario()
                                    
                                    st.success("✅ Gasto adicionado com sucesso! Os dados serão atualizados automaticamente.")
                                    
                            else:
                                st.error("❌ O valor do gasto deve ser maior que zero!")

                # Controles de status (código existente continua igual)
                st.markdown("---")
                st.markdown("#### 🔄 Alterar Status")
                col_status1, col_status2, col_status3 = st.columns(3)
                
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
                
                with col_status3:
                    if veiculo['status'] != 'Vendido':
                        if st.button("🗑️ Excluir", key=f"delete_btn_{veiculo['id']}", use_container_width=True, type="secondary"):
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
        
    # SEÇÃO DO PAPEL TIMBRADO
    st.markdown("---")
    seção_papel_timbrado()

    # SEÇÃO: GERADOR DE STORIES
    st.markdown("---")
    seção_gerador_stories()
    
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
