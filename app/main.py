import os
import sys
import subprocess
import shutil

import streamlit as st

st.set_page_config(page_title="🏆 Bolão - Copa do Mundo", page_icon="⚽", layout="wide")

MISSING_DEPENDENCIES = []
try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None
    MISSING_DEPENDENCIES.append("pandas")

try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None
    MISSING_DEPENDENCIES.append("plotly")

@st.cache_resource
def instalar_navegadores_playwright():
    """
    Aciona o sistema operacional (Linux do Streamlit Cloud) para baixar 
    os motores do navegador em segundo plano de forma silenciosa.
    O uso do cache garante que este processo massivo ocorra apenas uma vez 
    durante o ciclo de vida do contêiner.
    """
    comando = ["playwright", "install", "chromium"]

    if shutil.which("playwright") is None:
        st.warning("Playwright CLI não encontrado: instalação dos navegadores foi ignorada.")
        return False

    try:
        subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as erro:
        stderr = erro.stderr.decode() if erro.stderr else str(erro)
        st.error(f"Erro Crítico de Infraestrutura: Falha na injeção do Playwright. Detalhes: {stderr}")
        return False
    except FileNotFoundError:
        st.warning("Comando 'playwright' não foi encontrado no sistema; pulei a instalação.")
        return False

if MISSING_DEPENDENCIES:
    st.error(
        "Dependências faltando no ambiente: " + ", ".join(MISSING_DEPENDENCIES) + "."
    )
    st.info("Execute `pip install -r requirements.txt` no ambiente de deploy e reinicie a aplicação.")
    st.stop()

try:
    instalar_navegadores_playwright()
except Exception as e:
    st.warning(f"Falha ao tentar instalar navegadores do Playwright: {e}")

caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz = os.path.abspath(os.path.join(caminho_atual, '..'))
if caminho_raiz not in sys.path:
    sys.path.append(caminho_raiz)

from config import settings
from pathlib import Path
from app import scheduler
from app.utils.data_loader import load_data
from app.views import administracao, evolucao_individual, estatisticas, perolas, ranking, tabelas
from app import live_listener

@st.cache_resource
def iniciar_agendador():
    """
    Inicia a thread de agendamento automático em background.
    O cache garante que a thread seja criada apenas uma vez por instância do app.
    """
    return scheduler.start_scheduler()

iniciar_agendador()


@st.cache_resource
def iniciar_live_listener():
    """Inicia o listener que atualiza `live_matches.json` em background."""
    return live_listener.start_live_listener()


iniciar_live_listener()

st.markdown("""
<style>
    /* ========================================== */
    /* CONFIGURAÇÕES GLOBAIS E TIPOGRAFIA         */
    /* ========================================== */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc !important; 
    }

    /* ========================================== */
    /* 1. LIMPEZA SEGURA DA INTERFACE DA NUVEM    */
    /* ========================================== */
    .stDeployButton,
    [data-testid="stToolbarActionButton"],
    .viewerBadge_container__1QSob,
    .viewerBadge_link__1S137,
    #viewerBadge_container__1QSob {
        display: none !important;
        visibility: hidden !important;
    }

    /* ========================================== */
    /* 2. COMPORTAMENTO DESKTOP (Monitores e PCs) */
    /* ========================================== */
    @media (min-width: 769px) {
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        .block-container {
            padding-top: 2.5rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 2.5% !important;
            padding-right: 2.5% !important;
            max-width: 96% !important;
        }
    }

    /* ========================================== */
    /* 3. COMPORTAMENTO MOBILE (Celulares)        */
    /* ========================================== */
    @media (max-width: 768px) {
        header[data-testid="stHeader"] {
            background-color: #0f172a !important; 
            z-index: 999998 !important; 
        }

        [data-testid="collapsedControl"] svg,
        button[kind="header"] svg {
            display: none !important;
        }

        [data-testid="collapsedControl"]::before,
        button[kind="header"]::before {
            content: "\2630" !important;
            color: #ffffff !important;
            font-size: 1.8rem !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 40px !important;
            height: 40px !important;
        }

        header[data-testid="stHeader"] * {
            color: #ffffff !important;
        }

        .block-container {
            padding-top: 4.5rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 3% !important;
            padding-right: 3% !important;
            max-width: 100% !important;
        }

        .modebar, .modebar-container, .modebar-btn, .plotly .modebar {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
    }

    /* ========================================== */
    /* ESTILIZAÇÃO GERAL DOS COMPONENTES INTERNOS */
    /* ========================================== */
    div[data-testid="stVerticalBlock"] { gap: 0.7rem !important; }
    
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #14532d 100%);
        padding: 16px 24px;
        border-radius: 12px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-bottom: 3px solid #eab308;
    }
    
    .header-title-box { text-align: left; }
    
    .header-title {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
        letter-spacing: 0.5px;
        color: #ffffff !important;
    }
    
    .header-subtitle { font-size: 0.9rem; margin-top: 2px; color: #eab308; font-weight: 500; }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid #334155;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p { color: #f8fafc !important; }
    
    .metric-card {
        background: #ffffff;
        padding: 12px 16px !important;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0;
        border-left: 5px solid #16a34a;
        text-align: left;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08); }
    .metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px; }
    .metric-value { font-size: 1.35rem; font-weight: 800; color: #0f172a; }
    
    .podium-1st { border-left-color: #eab308 !important; }
    .podium-2nd { border-left-color: #94a3b8 !important; }
    .podium-3rd { border-left-color: #b45309 !important; }
    
    .section-title { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin-top: 10px; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; }
    div[data-testid="stCodeBlock"], div[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# Renderiza cabeçalho principal elegante e compacto
st.markdown("""
<div class="header-container">
    <div class="header-title-box">
        <h1 class="header-title">🏆 COPA DO MUNDO 2026</h1>
        <div class="header-subtitle">A diversão do seu bolão é aqui</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Carrega os dados

df_membros, df_historico, df_palpites, live_matches = load_data()
missing_dacopa_env = settings.missing_dacopa_env_vars()

# Configuração da barra lateral (Sidebar)
st.sidebar.markdown("<h3 style='margin:0; padding:10px 0;'>⚽ Navegação</h3>", unsafe_allow_html=True)

admin_expander = st.sidebar.expander("🔐 Configurações do Sistema")
admin_key = admin_expander.text_input("Chave do Admin", type="password")

is_admin_authenticated = (admin_key == "vaibrasa")

navigation_options = ["📊 Ranking Atual", "📋 Tabelas", "👤 Evolução Individual", "⚡ Estatísticas", "💎 Pérolas"]
if is_admin_authenticated:
    navigation_options.append("⚙️ Administração")

aba_selecionada = st.sidebar.radio("Selecione a Tela", navigation_options, label_visibility="collapsed")

st.sidebar.markdown("---")
conexao_status = "Configuração pendente ⚠️" if missing_dacopa_env else "Online ✅"
st.sidebar.markdown(f"**Conexão DaCopa:** `{conexao_status}` ")
if missing_dacopa_env:
    st.sidebar.warning("Faltando no .env: " + ", ".join(missing_dacopa_env))
if df_historico.empty:
    st.sidebar.warning("Banco de dados local vazio. Faça uma coleta no Painel Admin.")

if aba_selecionada == "📊 Ranking Atual":
    ranking.render(df_historico, df_palpites, live_matches)
elif aba_selecionada == "📋 Tabelas":
    tabelas.render(df_historico)
elif aba_selecionada == "👤 Evolução Individual":
    evolucao_individual.render(df_historico)
elif aba_selecionada == "⚡ Estatísticas":
    estatisticas.render(df_historico)
elif aba_selecionada == "⚙️ Administração" and is_admin_authenticated:
    administracao.render(missing_dacopa_env)
elif aba_selecionada == "💎 Pérolas":
    perolas.render(df_palpites, df_historico)
