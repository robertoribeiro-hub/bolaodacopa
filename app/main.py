import os
import sys
import subprocess
import streamlit as st
import shutil

@st.cache_resource
def instalar_navegadores_playwright():
    """
    Aciona o sistema operacional (Linux do Streamlit Cloud) para baixar 
    os motores do navegador em segundo plano de forma silenciosa.
    O uso do cache garante que este processo massivo ocorra apenas uma vez 
    durante o ciclo de vida do contêiner.
    """
    # Define um comando otimizado para baixar APENAS o Chromium, 
    # economizando espaço e tempo de inicialização.
    comando = ["playwright", "install", "chromium"]

    # Verifica se o binário/CLI do playwright está disponível no PATH
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

# Inicializa o injetor antes do render do dashboard
try:
    instalar_navegadores_playwright()
except Exception as e:
    st.warning(f"Falha ao tentar instalar navegadores do Playwright: {e}")

import os

# 1. Captura o caminho absoluto do diretório onde main.py está localizado (pasta 'app')
caminho_atual = os.path.dirname(os.path.abspath(__file__))

# 2. Navega um nível para cima para alcançar a raiz do projeto ('bolaodacopa')
caminho_raiz = os.path.abspath(os.path.join(caminho_atual, '..'))

# 3. Adiciona a raiz ao path do sistema caso ainda não esteja lá
if caminho_raiz not in sys.path:
    sys.path.append(caminho_raiz)

# 4. Agora as importações locais funcionarão normalmente
from config import settings
import streamlit as st

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
from config import settings
# Import de `scraper` feito tardiamente onde necessário para evitar
# ModuleNotFoundError se `playwright` não estiver instalado no ambiente.
from app.utils import statistics
from app import scheduler

@st.cache_resource
def iniciar_agendador():
    """
    Inicia a thread de agendamento automático em background.
    O cache garante que a thread seja criada apenas uma vez por instância do app.
    """
    return scheduler.start_scheduler()

# Inicia o agendador de sincronização automática
iniciar_agendador()

# Configuração da página Streamlit (layout wide e título premium)
st.set_page_config(page_title="🏆 Bolão é Nóis na Copa", page_icon="⚽", layout="wide")

# Estilização CSS Avançada (Responsiva, Limpa e Corrigida)
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
            content: "\\2630" !important;
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


# Função para carregar os dados das planilhas Excel
@st.cache_data(ttl=5)
def load_data():
    membros = pd.DataFrame(columns=["nome", "arroba"])
    historico = pd.DataFrame(columns=[
        "data_hora", "coleta_id", "participante", "arroba", "posicao", "pontos",
        "placar_exato", "gols_vencedor", "saldo_gols", "gols_perdedor", "vencedor_certo", "sem_pontos"
    ])
    palpites = pd.DataFrame(columns=[
        "coleta_id", "partida_id", "mandante", "visitante",
        "placar_real_m", "placar_real_v",
        "participante", "arroba",
        "palpite_m", "palpite_v", "categoria"
    ])
    
    if settings.MEMBROS_EXCEL.exists():
        try:
            membros = pd.read_excel(settings.MEMBROS_EXCEL)
        except Exception as e:
            st.error(f"Erro ao ler membros.xlsx: {e}")
            
    if settings.HISTORICO_EXCEL.exists():
        try:
            historico = pd.read_excel(settings.HISTORICO_EXCEL)
            if not historico.empty:
                historico["data_hora"] = pd.to_datetime(historico["data_hora"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                for col in ["placar_exato", "gols_vencedor", "saldo_gols", "gols_perdedor", "vencedor_certo", "sem_pontos"]:
                    if col not in historico.columns:
                        historico[col] = 0
                    else:
                        historico[col] = historico[col].fillna(0).astype(int)
        except Exception as e:
            st.error(f"Erro ao ler historico.xlsx: {e}")
    
    if settings.PALPITES_EXCEL.exists():
        try:
            palpites = pd.read_excel(settings.PALPITES_EXCEL)
        except Exception as e:
            st.error(f"Erro ao ler palpites.xlsx: {e}")
            
    return membros, historico, palpites


# Renderiza cabeçalho principal elegante e compacto
st.markdown("""
<div class="header-container">
    <div class="header-title-box">
        <h1 class="header-title">🏆 COPA DO MUNDO 2026</h1>
        <div class="header-subtitle">Bolão é Nóis na Copa — Central de Inteligência</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Carrega os dados
df_membros, df_historico, df_palpites = load_data()

# Configuração da barra lateral (Sidebar)
st.sidebar.markdown("<h3 style='margin:0; padding:10px 0;'>⚽ Navegação</h3>", unsafe_allow_html=True)

# Controle da aba oculta de Admin
admin_expander = st.sidebar.expander("🔐 Configurações do Sistema")
admin_key = admin_expander.text_input("Chave do Admin", type="password")

is_admin_authenticated = (admin_key == "vaibrasa")

navigation_options = ["📊 Ranking Atual", "👤 Evolução Individual", "⚡ Estatísticas", "💎 Pérolas"]
if is_admin_authenticated:
    navigation_options.append("⚙️ Administração")

aba_selecionada = st.sidebar.radio("Selecione a Tela", navigation_options, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Conexão DaCopa:** `Online ✅` ")
if df_historico.empty:
    st.sidebar.warning("Banco de dados local vazio. Faça uma coleta no Painel Admin.")

if aba_selecionada == "📊 Ranking Atual":
    st.markdown("<div class='section-title'>Classificação Geral da Copa</div>", unsafe_allow_html=True)
    
    if df_historico.empty:
        st.info("Nenhum dado cadastrado. Atualize o bolão no Painel Admin.")
    else:
        ultimo_coleta_id = df_historico["coleta_id"].iloc[-1]
        df_ranking = df_historico[df_historico["coleta_id"] == ultimo_coleta_id].copy()
        df_ranking = df_ranking.sort_values(by="posicao")
        
        df_exibicao = df_ranking[[
            "posicao", "participante", "arroba", "pontos", 
            "placar_exato", "gols_vencedor", "saldo_gols", 
            "gols_perdedor", "vencedor_certo", "sem_pontos"
        ]].rename(columns={
            "posicao": "Posição",
            "participante": "Participante",
            "arroba": "Usuário (@)",
            "pontos": "Pontuação",
            "placar_exato": "🎯 Placar Exato (25 pts)",
            "gols_vencedor": "⚽ Gols Vencedor (18 pts)",
            "saldo_gols": "⚖️ Saldo Gols (15 pts)",
            "gols_perdedor": "📉 Gols Perdedor (12 pts)",
            "vencedor_certo": "🏆 Vencedor Certo (10 pts)",
            "sem_pontos": "❌ Sem Pontos (0 pts)"
        })
        
        def medalha(pos):
            if pos == 1: return "🥇 1º"
            if pos == 2: return "🥈 2º"
            if pos == 3: return "🥉 3º"
            if pos == 4: return "🎖️ 4º"
            if pos == 5: return "🎖️ 5º"
            return f"🏃 {pos}º"
            
        df_exibicao["Posição"] = df_exibicao["Posição"].apply(medalha)
        
        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True,
            height=780
        )


elif aba_selecionada == "👤 Evolução Individual":
    st.markdown("<div class='section-title'>Análise de Desempenho Individual</div>", unsafe_allow_html=True)
    
    if df_historico.empty:
        st.info("Nenhum dado cadastrado.")
    else:
        df_diario = df_historico.copy()
        df_diario["data"] = pd.to_datetime(df_diario["data_hora"]).dt.date
        
        from datetime import date
        data_inicio = date(2026, 6, 11)
        df_diario["dia_copa"] = df_diario["data"].apply(lambda d: (d - data_inicio).days + 1)
        
        df_diario = df_diario.sort_values(by="data_hora")
        df_diario_grouped = df_diario.groupby(["participante", "arroba", "dia_copa"]).last().reset_index()
        
        lista_participantes = sorted(df_diario_grouped["participante"].unique())
        
        c_title, c_selects = st.columns([1.5, 2.5])
        with c_title:
            st.markdown("<p style='margin-top:5px; color:#64748b;'>Selecione o participante principal e escolha se deseja comparar com outro.</p>", unsafe_allow_html=True)
            comparar = st.checkbox("Comparar com outro participante", key="chk_comparar")
        
        participante_comp = None
        arroba_comp = None
        
        with c_selects:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                participante_selecionado = st.selectbox("Participante Principal:", lista_participantes)
            with col_sel2:
                if comparar:
                    lista_comparar = [p for p in lista_participantes if p != participante_selecionado]
                    participante_comp = st.selectbox("Comparar com:", lista_comparar)
            
        arroba_selecionado = df_diario_grouped[df_diario_grouped["participante"] == participante_selecionado]["arroba"].iloc[0]
        
        ind_stats = statistics.calculate_individual_statistics(df_diario_grouped, arroba_selecionado)
        
        if not comparar:
            st.markdown(f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 15px;">
                <div class="metric-card" style="border-left-color: #1e3a8a;">
                    <div class="metric-label">📌 Posição Atual</div>
                    <div class="metric-value">{ind_stats['posicao_atual']}º</div>
                </div>
                <div class="metric-card" style="border-left-color: #16a34a;">
                    <div class="metric-label">⭐ Melhor Posição</div>
                    <div class="metric-value">{ind_stats['melhor_posicao']}º</div>
                </div>
                <div class="metric-card" style="border-left-color: #ef4444;">
                    <div class="metric-label">⚠️ Pior Posição</div>
                    <div class="metric-value">{ind_stats['pior_posicao']}º</div>
                </div>
                <div class="metric-card" style="border-left-color: #94a3b8;">
                    <div class="metric-label">📊 Média de Posição</div>
                    <div class="metric-value">{ind_stats['media_posicao']}º</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if participante_comp:
                arroba_comp = df_diario_grouped[df_diario_grouped["participante"] == participante_comp]["arroba"].iloc[0]
                ind_stats_comp = statistics.calculate_individual_statistics(df_diario_grouped, arroba_comp)
                
                col_card1, col_card2 = st.columns(2)
                with col_card1:
                    st.markdown(f"<p style='margin: 0 0 5px 0; font-weight:bold; color:#15803d;'>👤 {participante_selecionado}</p>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px;">
                        <div class="metric-card" style="border-left-color: #1e3a8a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📌 Posição Atual</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['posicao_atual']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #16a34a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⭐ Melhor Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['melhor_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #ef4444; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⚠️ Pior Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['pior_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #94a3b8; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📊 Média Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['media_posicao']}º</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_card2:
                    st.markdown(f"<p style='margin: 0 0 5px 0; font-weight:bold; color:#1e3a8a;'>👤 {participante_comp}</p>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px;">
                        <div class="metric-card" style="border-left-color: #1e3a8a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📌 Posição Atual</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['posicao_atual']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #16a34a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⭐ Melhor Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['melhor_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #ef4444; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⚠️ Pior Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['pior_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #94a3b8; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📊 Média Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['media_posicao']}º</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
        df_ind1 = df_diario_grouped[df_diario_grouped["arroba"] == arroba_selecionado].copy()
        if comparar and arroba_comp:
            df_ind2 = df_diario_grouped[df_diario_grouped["arroba"] == arroba_comp].copy()
            df_plot = pd.concat([df_ind1, df_ind2], ignore_index=True)
        else:
            df_plot = df_ind1
            
        if not df_plot.empty:
            fig_rank = px.line(
                df_plot,
                x="dia_copa",
                y="posicao",
                color="participante",
                markers=True,
                title="Evolução de Ranking",
                labels={"dia_copa": "Dia da Copa", "posicao": "Posição", "participante": "Participante"}
            )
            
            fig_rank.update_yaxes(range=[21.5, 0.5], tickmode="linear", tick0=1, dtick=1)
            fig_rank.update_xaxes(range=[0.5, 39.5], tickmode="linear", tick0=1, dtick=1)
            
            fig_rank.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#e2e8f0"),
                xaxis=dict(gridcolor="#e2e8f0"),
                font=dict(family="Outfit, sans-serif", size=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    title_text=None
                )
            )
            
            if not comparar:
                fig_rank.update_traces(line_color="#15803d", marker=dict(size=6, color="#eab308"))
            else:
                fig_rank.update_traces(marker=dict(size=6))
                
            st.plotly_chart(fig_rank, use_container_width=True)


elif aba_selecionada == "⚡ Estatísticas":
    st.markdown("<div class='section-title'>Estatísticas e Recordes do Bolão</div>", unsafe_allow_html=True)
    
    if df_historico.empty:
        st.info("Nenhum dado cadastrado.")
    else:
        global_stats = statistics.calculate_global_statistics(df_historico)
        
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown("<h4 style='margin-top:0;'>👑 Recordistas da Competição</h4>", unsafe_allow_html=True)
            
            subida = global_stats["maior_subida"]
            queda = global_stats["maior_queda"]
            seq = global_stats["melhor_sequencia"]
            pontos = global_stats["melhor_pontuacao"]
            cons = global_stats["mais_consistente"]
            pe_rec = global_stats["mais_placares_exatos"]
            sp_rec = global_stats["mais_sem_pontos"]
            
            st.markdown(f"""
            <div style="display:flex; flex-direction:column; gap:8px;">
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #22c55e; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">📈 Maior Subida:</strong> {subida['participante']} 
                    <span style="color:#16a34a; font-weight:bold; float:right;">+{subida['valor']} pos</span>
                </div>
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #ef4444; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">📉 Maior Queda:</strong> {queda['participante']} 
                    <span style="color:#dc2626; font-weight:bold; float:right;">-{queda['valor']} pos</span>
                </div>
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #3b82f6; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">🔥 Melhor Sequência:</strong> {seq['participante']} 
                    <span style="color:#2563eb; font-weight:bold; float:right;">{seq['valor']} acertos</span>
                </div>
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #eab308; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">⭐ Melhor Pontuação:</strong> {pontos['participante']} 
                    <span style="color:#ca8a04; font-weight:bold; float:right;">{pontos['valor']} pts</span>
                </div>
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #64748b; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">🎯 Mais Consistente:</strong> {cons['participante']} 
                    <span style="color:#475569; font-weight:bold; float:right;">Desvio Padrão: {cons['desvio']}</span>
                </div>
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #16a34a; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">🎯 Mais Placares Exatos:</strong> {pe_rec['participante']} 
                    <span style="color:#16a34a; font-weight:bold; float:right;">{pe_rec['valor']} acertos</span>
                </div>
                <div style="background:#ffffff; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #dc2626; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">❌ Pé-Frio (Sem Pontos):</strong> {sp_rec['participante']} 
                    <span style="color:#dc2626; font-weight:bold; float:right;">{sp_rec['valor']} erros</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_right:
            st.markdown("<h4 style='margin-top:0;'>🥇 Dias na Liderança</h4>", unsafe_allow_html=True)
            
            dias = global_stats["dias_lideranca"]
            if not dias:
                st.info("Nenhum participante assumiu a liderança (1º lugar) até o momento.")
            else:
                df_dias = pd.DataFrame(dias).rename(columns={
                    "participante": "Participante",
                    "arroba": "Usuário (@)",
                    "coleta_id": "Dias na Liderança"
                })
                st.dataframe(df_dias, use_container_width=True, hide_index=True, height=250)


elif aba_selecionada == "⚙️ Administração" and is_admin_authenticated:
    st.markdown("<div class='section-title'>Painel Administrativo do Bolão</div>", unsafe_allow_html=True)

    # ── STATUS DO AGENDADOR AUTOMÁTICO ──────────────────────────────────────
    sched_status = scheduler.get_status()

    ultima_exec = sched_status.get("ultima_execucao_auto")
    ultima_sucesso = sched_status.get("ultima_execucao_sucesso")
    em_execucao = sched_status.get("em_execucao", False)
    proxima = sched_status.get("proxima_execucao", "—")
    horario_gatilho = sched_status.get("horario_disparado", "—")

    if ultima_exec:
        ultima_exec_str = ultima_exec.strftime("%d/%m/%Y às %H:%M:%S")
        icone_sucesso = "✅" if ultima_sucesso else "❌"
        ultima_label = f"{icone_sucesso} {ultima_exec_str} (gatilho: {horario_gatilho} BRT)"
    else:
        ultima_label = "Nenhuma execução automática desde que o app foi iniciado."

    status_cor = "#f59e0b" if em_execucao else "#16a34a"
    status_txt = "⏳ Sincronizando agora..." if em_execucao else "✅ Aguardando próximo horário"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; border: 1px solid #334155;">
        <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 8px;">🤖 Agendador Automático</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
            <div>
                <div style="color: #64748b; font-size: 0.75rem; margin-bottom: 2px;">Status</div>
                <div style="color: {status_cor}; font-weight: 700; font-size: 0.95rem;">{status_txt}</div>
            </div>
            <div>
                <div style="color: #64748b; font-size: 0.75rem; margin-bottom: 2px;">Última Execução Automática</div>
                <div style="color: #f8fafc; font-weight: 600; font-size: 0.85rem;">{ultima_label}</div>
            </div>
            <div>
                <div style="color: #64748b; font-size: 0.75rem; margin-bottom: 2px;">Próximo Horário (BRT)</div>
                <div style="color: #eab308; font-weight: 700; font-size: 1.1rem;">🕐 {proxima}</div>
            </div>
        </div>
        <div style="margin-top: 10px; color: #475569; font-size: 0.75rem;">
            Horários programados (BRT): {' · '.join(sorted(scheduler.HORARIOS_AGENDADOS))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([1, 2])
    
    with col_btn:
        st.markdown("<h4 style='margin-top:0;'>Coletas Manuais</h4>", unsafe_allow_html=True)
        
        if st.button("🔄 Sincronizar Tudo (Membros + Ranking + Palpites)", use_container_width=True):
            with st.spinner("Conectando ao DaCopa via Playwright..."):
                st.info("Iniciando sincronização completa de membros, classificação e palpites detalhados...")
                try:
                    from collectors import scraper
                except Exception as e:
                    st.error(
                        "Não foi possível carregar o módulo de coleta (Playwright ausente).\n"
                        "Instale as dependências: `pip install -r requirements.txt` e execute `playwright install chromium`.\n"
                        f"Erro: {e}"
                    )
                    success = False

                try:
                    success = scraper.run_coleta_completa()
                except Exception as e:
                    st.error(f"Erro durante a coleta: {e}")
                    success = False

                if success:
                    st.success("Dados reais sincronizados e gravados no Excel com sucesso! 🎉")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Ocorreu uma falha durante a sincronização. Verifique os logs.")
                    
        st.markdown("---")
        st.markdown("**Status do Excel**")
        st.write(f"📁 `membros.xlsx`: {'Sim' if settings.MEMBROS_EXCEL.exists() else 'Não'}")
        st.write(f"📁 `historico.xlsx`: {'Sim' if settings.HISTORICO_EXCEL.exists() else 'Não'}")
                    
    with col_info:
        st.markdown("<h4 style='margin-top:0;'>Últimos Registros do Sistema (Logs)</h4>", unsafe_allow_html=True)
        
        log_file = Path(settings.LOG_COLLECTOR_FILE)
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                    ultimas_linhas = linhas[-12:] if len(linhas) > 12 else linhas
                    st.code("".join(ultimas_linhas), language="text")
            except Exception as e:
                st.error(f"Erro ao ler arquivo de logs: {e}")
        else:
            st.info("Nenhum log gerado no momento.")


# ─────────────────────────────────────────────────
# TELA: PÉROLAS DO BOLÃO
# ─────────────────────────────────────────────────
elif aba_selecionada == "💎 Pérolas":
    st.markdown("""
    <style>
    .perola-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        border: 1px solid rgba(255,255,255,0.08);
        transition: transform 0.2s;
        position: relative;
        overflow: hidden;
    }
    .perola-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .perola-card-visionario::before   { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
    .perola-card-nostradamus::before  { background: linear-gradient(90deg, #f59e0b, #eab308); }
    .perola-card-ousado::before       { background: linear-gradient(90deg, #f59e0b, #ef4444); }
    .perola-card-maria::before        { background: linear-gradient(90deg, #a78bfa, #ec4899); }
    .perola-card-retr::before         { background: linear-gradient(90deg, #10b981, #06b6d4); }
    .perola-card-futebolarte::before  { background: linear-gradient(90deg, #f97316, #eab308); }
    .perola-card-zicado::before       { background: linear-gradient(90deg, #f97316, #dc2626); }
    .perola-card-pefrio::before       { background: linear-gradient(90deg, #64748b, #475569); }
    .perola-card-golfinho::before     { background: linear-gradient(90deg, #3b82f6, #0ea5e9); }
    .perola-card-rocha::before        { background: linear-gradient(90deg, #78716c, #57534e); }
    .perola-card-diplomata::before    { background: linear-gradient(90deg, #14b8a6, #0d9488); }
    .perola-card-arroz::before        { background: linear-gradient(90deg, #84cc16, #65a30d); }
    .perola-emoji  { font-size: 3rem; margin-bottom: 8px; display: block; }
    .perola-titulo { font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em;
                     text-transform: uppercase; margin-bottom: 4px; opacity: 0.7; }
    .perola-nome   { font-size: 1.6rem; font-weight: 800; margin: 4px 0; }
    .perola-arroba { font-size: 0.9rem; opacity: 0.6; }
    .perola-valor  { font-size: 1.2rem; font-weight: 600; margin-top: 8px;
                     background: rgba(255,255,255,0.1); border-radius: 8px;
                     padding: 4px 12px; display: inline-block; }
    .perola-desc   { font-size: 0.82rem; opacity: 0.55; margin-top: 10px;
                     font-style: italic; line-height: 1.4; }
    .perola-placares { margin-top: 10px; font-size: 0.8rem; opacity: 0.7;
                       background: rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 12px; }
    .perola-placares-item { margin: 2px 0; }
    .perola-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 14px; padding: 16px 24px; color: white;
        margin-bottom: 20px; text-align: center;
        border: 1px solid rgba(255,255,255,0.06);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Banner do título
    st.markdown("""
    <div class="perola-banner">
        <div style="font-size:2.2rem; font-weight:900; letter-spacing:0.04em;">💎 Pérolas do Bolão</div>
        <div style="opacity:0.6; margin-top:4px; font-size:0.95rem;">
            Os apelidos que o bolão deu a cada palpiteiro
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if df_palpites.empty:
        st.info("ℹ️ Dados de palpites individuais ainda não coletados. Acesse o **Painel de Administração** e clique em **Atualizar Agora** para coletar os palpites de cada participante.")
    else:
        # ── Função auxiliar de renderização de ranking ─────────────────────────
        def render_top3(lista, unidade, emoji_medalhas=None):
            if emoji_medalhas is None:
                emoji_medalhas = ["🥇", "🥈", "🥉"]
            if not lista:
                return "<div style='opacity:0.6; padding: 10px 0;'>Nenhum participante qualificado.</div>"
            html = '<div style="margin-top: 16px;">'
            for i, p in enumerate(lista):
                medalha = emoji_medalhas[i] if i < len(emoji_medalhas) else "🏅"
                font_size = "1.2rem" if i == 0 else "1.1rem"
                val_padding = "4px 12px" if i == 0 else "2px 8px"
                val_font = "1.1rem" if i == 0 else "1.0rem"
                html += (
                    f'<div style="display: flex; justify-content: space-between; align-items: center; '
                    f'margin-bottom: 8px; background: rgba(255,255,255,0.04); padding: 8px 12px; '
                    f'border-radius: 8px; border-left: 3px solid rgba(255,255,255,0.2);">'
                )
                html += (
                    f'<div><span style="font-size: {font_size};">{medalha}</span> '
                    f'<strong style="font-size: {font_size};">{p["participante"]}</strong> '
                    f'<span style="font-size:0.8rem; opacity:0.7;">{p["arroba"]}</span></div>'
                )
                html += (
                    f'<div class="perola-valor" style="margin-top: 0; padding: {val_padding}; '
                    f'font-size: {val_font};">{p["valor"]} '
                    f'<span style="font-size: 0.7em; opacity:0.8;">{unidade}</span></div>'
                )
                html += '</div>'
                # Destaque de placares extras para o 1º colocado
                if i == 0 and p.get("placares"):
                    items = "".join(
                        f'<div class="perola-placares-item">⚽ {pl}</div>' for pl in p["placares"]
                    )
                    html += f'<div class="perola-placares" style="margin-bottom: 12px; margin-top: -4px;">{items}</div>'
                # Destaque de info extra genérica (ex: placar favorito para Arroz com Feijão)
                if i == 0 and p.get("info_extra"):
                    html += (
                        f'<div class="perola-placares" style="margin-bottom: 12px; margin-top: -4px;">'
                        f'<div class="perola-placares-item">🔁 {p["info_extra"]}</div></div>'
                    )
            html += '</div>'
            return html

        # ── Configura e calcula as Pérolas ─────────────────────────────────────
        perolas = statistics.calculate_perolas(df_palpites, df_historico)

        # ── CONFIGURAÇÃO DAS PÉROLAS ────────────────────────────────────────────
        # Cada entrada define: chave nos dados, classe CSS, emoji, título, descrição, unidade
        PEROLAS_CONFIG = [
            # Linha 1
            {
                "chave": "visionario",
                "css": "perola-card-visionario",
                "emoji": "🔮",
                "titulo": "Visionário",
                "desc": "Acertou resultados improváveis que mais ninguém conseguiu cravar.",
                "unidade": "palpite(s) único(s)"
            },
            {
                "chave": "nostradamus",
                "css": "perola-card-nostradamus",
                "emoji": "🌟",
                "titulo": "Nostradamus",
                "desc": "Quando ele fala, a FIFA escuta.",
                "unidade": "placar(es) exato(s)"
            },
            # Linha 2
            {
                "chave": "ousado",
                "css": "perola-card-ousado",
                "emoji": "🦅",
                "titulo": "Ousadia e Alegria",
                "desc": "Apostou sozinho, sem mais ninguém com o mesmo placar. O mais ousado e criativo do grupo!",
                "unidade": "palpite(s)"
            },
            {
                "chave": "maria",
                "css": "perola-card-maria",
                "emoji": "🐑",
                "titulo": "Maria vai com as outras",
                "desc": "Mais vezes apostou o mesmo placar que a maioria do grupo. Segurança em números!",
                "unidade": "vez(es)"
            },
            # Linha 3
            {
                "chave": "retranqueiro",
                "css": "perola-card-retr",
                "emoji": "🧱",
                "titulo": "Retranqueiro",
                "desc": "Apostou menos gols que qualquer outro participante. Amor pelo 0x0!",
                "unidade": "gol(s)"
            },
            {
                "chave": "futebol_arte",
                "css": "perola-card-futebolarte",
                "emoji": "🎨",
                "titulo": "Futebol Arte",
                "desc": "Apostou mais gols que qualquer outro participante. O negócio é sacudir a roseira!",
                "unidade": "gol(s)"
            },
            # Linha 4
            {
                "chave": "zicado",
                "css": "perola-card-zicado",
                "emoji": "🤦",
                "titulo": "Zicado",
                "desc": "Mais vezes errou o placar por apenas um gol de diferença no total. Quase lá... mas não!",
                "unidade": "vez(es)"
            },
            {
                "chave": "pe_frio",
                "css": "perola-card-pefrio",
                "emoji": "🥶",
                "titulo": "Pé Frio",
                "desc": "Uma máquina de errar! Mais vezes não marcou ponto algum na rodada.",
                "unidade": "rodada(s) zerada(s)"
            },
            # Linha 5
            {
                "chave": "golfinho",
                "css": "perola-card-golfinho",
                "emoji": "🐬",
                "titulo": "Golfinho",
                "desc": "Participantes que mais alternaram posições ao longo do tempo. Sobe e desce sem parar!",
                "unidade": "posições movidas"
            },
            {
                "chave": "rocha",
                "css": "perola-card-rocha",
                "emoji": "🪨",
                "titulo": "Rocha",
                "desc": "Nem sobe, nem desce. A estabilidade em pessoa.",
                "unidade": "mudança(s) de posição"
            },
            # Linha 6
            {
                "chave": "diplomata",
                "css": "perola-card-diplomata",
                "emoji": "🤝",
                "titulo": "Diplomata",
                "desc": "Para ele, todo mundo merece um pontinho. O Rei do empate!",
                "unidade": "empate(s) apostado(s)"
            },
            {
                "chave": "arroz_feijao",
                "css": "perola-card-arroz",
                "emoji": "🍚",
                "titulo": "Arroz com Feijão",
                "desc": "Não inventa moda. Sempre o mesmo padrão.",
                "unidade": "placar(es) distinto(s)"
            },
        ]

        # ── Renderização em pares de colunas ────────────────────────────────────
        for i in range(0, len(PEROLAS_CONFIG), 2):
            cols = st.columns(2)
            for j, cfg in enumerate(PEROLAS_CONFIG[i:i+2]):
                dados = perolas.get(cfg["chave"], [])
                with cols[j]:
                    st.markdown(f"""
<div class="perola-card {cfg['css']}">
    <span class="perola-emoji">{cfg['emoji']}</span>
    <div class="perola-titulo">{cfg['titulo']}</div>
    <div class="perola-desc">{cfg['desc']}</div>
{render_top3(dados, cfg['unidade'])}
</div>
""", unsafe_allow_html=True)

        # ── Tabela de detalhes dos palpites ─────────────────────────────────────
        st.markdown("---")
        st.markdown("<div class='section-title'>📋 Detalhe dos Palpites Coletados</div>", unsafe_allow_html=True)
        
        ultimo_coleta = df_palpites["coleta_id"].iloc[-1]
        df_detalhe = df_palpites[df_palpites["coleta_id"] == ultimo_coleta].copy()
        df_detalhe["Jogo"] = df_detalhe["mandante"] + " x " + df_detalhe["visitante"]
        df_detalhe["Placar Real"] = df_detalhe["placar_real_m"].astype(str) + " x " + df_detalhe["placar_real_v"].astype(str)
        df_detalhe["Palpite"] = df_detalhe["palpite_m"].astype(str) + " x " + df_detalhe["palpite_v"].astype(str)
        df_detalhe = df_detalhe[["participante", "arroba", "Jogo", "Placar Real", "Palpite", "categoria"]]
        df_detalhe.columns = ["Participante", "Arroba", "Jogo", "Placar Real", "Palpite", "Categoria"]
        st.dataframe(df_detalhe, use_container_width=True, height=400)
