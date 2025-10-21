import streamlit as st
import hashlib
from database import db
import hashlib
import secrets
import hmac

def check_auth():
    """Verifica se o usuário está autenticado"""
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    
    return st.session_state.autenticado

def login_page():
    """Página de login"""
    st.markdown("""
    <div class="main-header fade-in">
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" style="height: 60px; margin-right: 15px;">
            <div style="text-align: left;">
                <h1 style="margin:0; font-size: 2.5rem; font-weight: 700; letter-spacing: -0.5px;">Canal Automotivo</h1>
                <p style="margin:0; font-size: 1.1rem; opacity: 0.9; font-weight: 400;">Sistema de Gestão</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card" style="max-width: 400px; margin: 2rem auto;">
        <h2 style="text-align: center; color: #1760D0; margin-bottom: 2rem;">Acesso ao Sistema</h2>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        
        submitted = st.form_submit_button("Entrar", use_container_width=True)
        
        if submitted:
            if username and password:
                usuario = db.verificar_login(username, password)
                if usuario:
                    st.session_state.autenticado = True
                    st.session_state.usuario = usuario
                    st.success(f"Bem-vindo, {usuario['nome']}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")
            else:
                st.error("Preencha todos os campos!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Credenciais de exemplo (remover em produção)
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #6C757D;">
        <p><strong>Credenciais de teste:</strong></p>
        <p>Usuário: <code>admin</code> | Senha: <code>admin123</code></p>
    </div>
    """, unsafe_allow_html=True)

def logout():
    """Realiza logout"""
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.rerun()


def hash_password(password):
    """VERSÃO SIMPLIFICADA - retorna senha em texto puro"""
    print(f"🔐 HASH: Retornando senha em texto: '{password}'")
    return password  # Texto puro temporariamente

def verify_password(stored_password, provided_password):
    """VERSÃO SIMPLIFICADA - comparação direta"""
    print(f"🔐 VERIFICAÇÃO: '{stored_password}' vs '{provided_password}'")
    resultado = stored_password == provided_password
    print(f"🔐 RESULTADO: {resultado}")
    return resultado  # Comparação direta
