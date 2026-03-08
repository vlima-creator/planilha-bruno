import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
from utils.parser import processar_arquivos
from utils.metricas import calcular_metricas, calcular_qualidade_arquivo
from utils.export import exportar_xlsx
from utils.analises import analisar_frete, analisar_motivos, analisar_ads, analisar_skus, simular_reducao
from utils.formatacao import formatar_brl, formatar_percentual, formatar_pct_direto, formatar_numero, formatar_risco
from utils.analise_anuncios import processar_analise_completa
from tab_analise_anuncios import render_tab_analise_anuncios
from tab_guia_uso import render_tab_guia_uso

# Configuração da página
st.set_page_config(
    page_title="Devoluções Inteligentes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Devoluções Inteligentes")
st.markdown("**Recupere sua rentabilidade identificando custos ocultos e vazamentos financeiros nas suas devoluções nos Marketplaces.**")
st.markdown("**Análise 100% segura: seus dados nunca saem do seu computador.**")

# CSS customizado
st.markdown("""
    <style>
    /* Configurações Globais */
    .main {
        background-color: #000000;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #000000;
    }

    /* Estilo dos Cartões de Métricas (Glass Effect) */
    .metric-card {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        flex: 1;
        position: relative;
        min-height: 110px;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(82, 121, 111, 0.5);
        background-color: rgba(82, 121, 111, 0.15);
        transform: translateY(-3px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .metric-label {
        color: #888888;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.7rem;
        font-weight: 700;
    }
    .metric-subvalue {
        color: #888888;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .metric-icon {
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
    }
    
    .icon-container {
        width: 45px;
        height: 45px;
        background-color: #000000;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .icon-svg {
        width: 24px;
        height: 24px;
        fill: #ffffff;
    }

    /* Estilo das Seções de Gráficos (Glass Effect) */
    .chart-container {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        margin-bottom: 25px;
        transition: all 0.3s ease;
    }
    .chart-container:hover {
        border-color: rgba(82, 121, 111, 0.5);
        box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.9);
    }
    .chart-title {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 20px;
    }
    
    /* Estilo do Cabecalho de Filtros */
    .filter-header {
        background-color: rgba(255, 255, 255, 0.02);
        padding: 20px 30px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 25px;
    }
    
    /* Estilo do Simulador */
    .simulator-box {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .simulator-box:hover {
        border-color: #3b82f6;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
    }
    
    .simulator-bar-container {
        display: flex;
        gap: 0;
        height: 24px;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    
    .simulator-bar-yellow {
        background-color: #ffd700;
        height: 100%;
        border-radius: 4px 0 0 4px;
        transition: width 0.1s ease;
    }
    
    .simulator-bar-dark {
        background-color: #4a4a4a;
        height: 100%;
        flex: 1;
        border-radius: 0 4px 4px 0;
    }
    
    /* Ajustes para Sidebar */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] .stMarkdown h3 {
        color: #f8fafc;
    }
    
    /* Estilo para os botões */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        background-color: rgba(82, 121, 111, 0.2) !important;
        color: #ffffff !important;
        border: 1px solid rgba(82, 121, 111, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: rgba(82, 121, 111, 0.4) !important;
        border-color: rgba(82, 121, 111, 0.8) !important;
        transform: scale(1.02);
    }
    
    /* Estilo para o uploader na sidebar */
    [data-testid="stSidebar"] .stFileUploader {
        padding: 15px;
        background-color: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        border: 1px dashed rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }

    /* Estilização das Abas (Tabs) - Liquid Glass Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        width: 100%;
        padding: 10px 0;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        background-color: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
        color: #888888;
        font-weight: 600;
        padding: 10px 25px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
        flex: 1;
        min-width: 150px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(82, 121, 111, 0.3) !important;
        color: #ffffff !important;
        border-color: rgba(82, 121, 111, 0.6) !important;
        box-shadow: 0 4px 15px rgba(82, 121, 111, 0.2);
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.1);
    }

    /* Inputs e Selects */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: rgba(255, 255, 255, 0.02) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

def render_icon_svg(icon_name, color="#ffffff"):
    # Dicionário de caminhos SVG para os ícones
    icons = {
        "vendas": '<path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>',
        "cancelados": '<path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/>',
        "devolucoes": '<path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/>',
        "faturamento": '<path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/>',
        "perda_parcial": '<path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-5 10H9v-2h6v2zm0-4H9v-2h6v2z"/>',
        "perda_total": '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>',
        "guia": '<path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z"/>',
        "resumo": '<path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>',
        "janelas": '<path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>',
        "matriz_full": '<path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-5 14H9v-2h6v2zm0-4H9v-2h6v2z"/>',
        "frete": '<path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>',
        "motivos": '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>',
        "ads": '<path d="M20 2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 16H6v-2h12v2zm0-4H6v-2h12v2zm0-4H6V8h12v2z"/>',
        "anuncios": '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5-9h10v2H7z"/>',
        "simulador": '<path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>',
        "ia": '<path d="M21 10.12h-6.78l2.74-2.82c-2.73-2.7-7.15-2.8-9.88-.1-2.73 2.71-2.73 7.08 0 9.79s7.15 2.71 9.88 0C18.32 15.65 19 14.08 19 12.1h2c0 1.98-.88 4.55-2.64 6.29-3.51 3.48-9.21 3.48-12.72 0-3.5-3.47-3.51-9.11 0-12.58s9.21-3.47 12.72 0L21 3v7.12zM12.5 8v4.25l3.5 2.08-.75 1.23-4.25-2.5V8h1.5z"/>',
        "config": '<path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.21.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>',
        "rocket": '<path d="M13.13 22.19L11.5 18.35c-.74.14-1.49.18-2.25.13l-1.63 3.71c-.13.29-.42.48-.74.48-.44 0-.8-.36-.8-.8 0-.08.01-.16.03-.23l1.49-3.39c-1.23-.48-2.33-1.24-3.24-2.24l-3.39 1.49c-.07.03-.15.05-.23.05-.44 0-.8-.36-.8-.8 0-.32.19-.61.48-.74l3.71-1.63c-.05-.76-.01-1.51.13-2.25L.41 10.87c-.29-.13-.48-.42-.48-.74 0-.44.36-.8.8-.8.08 0 .16.01.23.03l3.39 1.49c.48-1.23 1.24-2.33 2.24-3.24L5.1 4.22c-.03-.07-.05-.15-.05-.23 0-.44.36-.8.8-.8.32 0 .61.19.74.48l1.63 3.71c.76-.05 1.51-.01 2.25.13L12.1 1.41c.13-.29.42-.48.74-.48.44 0 .8.36.8.8 0 .08-.01.16-.03.23l-1.49 3.39c1.23.48 2.33 1.24 3.24 2.24l3.39-1.49c.07-.03.15-.05.23-.05.44 0 .8.36.8.8 0 .32-.19.61-.48.74l-3.71 1.63c.05.76.01 1.51-.13 2.25l3.71 1.63c.29.13.48.42.48.74 0 .44-.36.8-.8.8-.08 0-.16-.01-.23-.03l-3.39-1.49c-.48 1.23-1.24 2.33-2.24 3.24l1.49 3.39c.03.07.05.15.05.23 0 .44-.36.8-.8.8-.32 0-.61-.19-.74-.48l-1.63-3.71c-.76.05-1.51.01-2.25-.13l-1.63 3.71c-.13.29-.42.48-.74.48-.44 0-.8-.36-.8-.8 0-.08.01-.16.03-.23l1.49-3.39c-1.23-.48-2.33-1.24-3.24-2.24L1.41 13.13c-.29-.13-.48-.42-.48-.74 0-.44.36-.8.8-.8.08 0 .16.01.23.03l3.39 1.49c.48-1.23 1.24-2.33 2.24-3.24l-1.49-3.39c-.03-.07-.05-.15-.05-.23 0-.44.36-.8.8-.8.32 0 .61.19.74.48l1.63 3.71c.76-.05 1.51-.01 2.25.13l1.63-3.71c.13-.29.42-.48.74-.48.44 0 .8.36.8.8 0 .08-.01.16-.03.23l-1.49 3.39c1.23.48 2.33 1.24 3.24 2.24l3.39-1.49c.07.03.15.05.23.05.44 0 .8.36.8.8 0 .32-.19.61-.48.74l-3.71 1.63c.05.76.01 1.51-.13 2.25l3.71 1.63c.29.13.48.42.48.74 0 .44-.36.8-.8.8-.08 0-.16-.01-.23-.03l-3.39-1.49c-.48 1.23-1.24 2.33-2.24 3.24l1.49 3.39c.03.07.05.15.05.23 0 .44-.36.8-.8.8-.32 0-.61-.19-.74-.48l-1.63-3.71c-.76.05-1.51.01-2.25-.13z"/>',
        "search": '<path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>',
        "rule": '<path d="M10.5 5h3v3h-3V5zM10.5 10h3v3h-3v-3zM10.5 15h3v3h-3v-3zM5.5 5h3v3h-3V5zM5.5 10h3v3h-3v-3zM5.5 15h3v3h-3v-3zM15.5 5h3v3h-3V5zM15.5 10h3v3h-3v-3zM15.5 15h3v3h-3v-3z"/>',
        "lightbulb": '<path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6C7.8 12.16 7 10.63 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z"/>'
    }
    path = icons.get(icon_name, "")
    return f"""
        <div class="icon-container">
            <svg class="icon-svg" viewBox="0 0 24 24" style="fill: {color};">
                {path}
            </svg>
        </div>
    """

def render_metric_card(label, value, subvalue, icon_name):
    icon_html = render_icon_svg(icon_name)
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subvalue">{subvalue}</div>
            <div class="metric-icon">{icon_html}</div>
        </div>
    """, unsafe_allow_html=True)

# Exportar para session_state para ser usado em outros módulos
st.session_state['render_icon_svg'] = render_icon_svg

# ─────────────────────────────────────────────────────────
# Função de filtragem global dos dados
# ─────────────────────────────────────────────────────────
def aplicar_filtros(data, janela, canal, somente_ads, top10_skus, agrupar_por='SKU'):
    """
    Aplica os filtros globais do cabeçalho sobre os dados brutos.
    Retorna um dicionário com os mesmos campos de 'data', mas filtrados.
    """
    vendas = data['vendas'].copy()
    matriz = data['matriz'].copy() if data['matriz'] is not None else pd.DataFrame()
    full = data['full'].copy() if data['full'] is not None else pd.DataFrame()
    max_date = data['max_date']

    # 1) Filtro de JANELA (período)
    data_limite = max_date - timedelta(days=janela)
    if 'Data da venda' in vendas.columns:
        vendas = vendas[vendas['Data da venda'] >= data_limite]
    if 'Data da venda' in matriz.columns and len(matriz) > 0:
        matriz = matriz[matriz['Data da venda'] >= data_limite]
    if 'Data da venda' in full.columns and len(full) > 0:
        full = full[full['Data da venda'] >= data_limite]

    # 2) Filtro de CANAL
    if canal == 'Matriz':
        full = pd.DataFrame()
    elif canal == 'Full':
        matriz = pd.DataFrame()
    # 'Todos' mantém ambos

    # 3) Filtro SOMENTE ADS
    if somente_ads:
        if 'Venda por publicidade' in vendas.columns:
            vendas = vendas[vendas['Venda por publicidade'] == 'Sim']

    # 4) Filtro TOP 10 (filtra vendas apenas dos 10 itens com mais devoluções)
    if top10_skus:
        todas_dev = pd.concat([matriz, full], ignore_index=True)
        col_id = agrupar_por if agrupar_por in vendas.columns else 'SKU'
        
        if len(todas_dev) > 0 and 'N.º de venda' in todas_dev.columns and col_id in vendas.columns:
            # Mapear devoluções para itens via vendas
            dev_nums = set(todas_dev['N.º de venda'].astype(str).unique())
            vendas_com_dev = vendas[vendas['N.º de venda'].astype(str).isin(dev_nums)]
            
            if col_id in vendas_com_dev.columns:
                top_items = vendas_com_dev[col_id].value_counts().head(10).index.tolist()
                vendas = vendas[vendas[col_id].isin(top_items)]
                # Filtrar devoluções para manter apenas as relacionadas às vendas filtradas
                vendas_nums = set(vendas['N.º de venda'].astype(str).unique())
                if len(matriz) > 0 and 'N.º de venda' in matriz.columns:
                    matriz = matriz[matriz['N.º de venda'].astype(str).isin(vendas_nums)]
                if len(full) > 0 and 'N.º de venda' in full.columns:
                    full = full[full['N.º de venda'].astype(str).isin(vendas_nums)]

    return {
        'vendas': vendas,
        'matriz': matriz if len(matriz) > 0 else None,
        'full': full if len(full) > 0 else None,
        'max_date': max_date,
        'total_vendas': len(vendas),
        'total_matriz': len(matriz) if len(matriz) > 0 else 0,
        'total_full': len(full) if len(full) > 0 else 0,
    }

# ─────────────────────────────────────────────────────────
# Inicializar session state
# ─────────────────────────────────────────────────────────
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

# ─────────────────────────────────────────────────────────
# SIDEBAR - UPLOAD E CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Gestão de Devolução Inteligente")
    st.markdown("---")
    
    # Ícone para Upload de Dados
    icon_upload = render_icon_svg("guia", color="#ffffff").replace("\n", "")
    st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">{icon_upload} <h3 style="margin: 0; font-size: 1.2rem;">Upload de Dados</h3></div>', unsafe_allow_html=True)
    
    file_vendas = st.file_uploader("Relatório de Vendas", type=['xlsx'], key='vendas', help="Arraste o arquivo .xlsx de vendas (ML ou Shopee)")
    file_devolucoes = st.file_uploader("Relatório de Devoluções", type=['xlsx', 'xls'], key='devolucoes', help="Arraste o arquivo de devoluções (ML ou Shopee)")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_processar = st.button("Processar", use_container_width=True, type="primary")
    with col_btn2:
        btn_exemplo = st.button("Exemplo", use_container_width=True)
        
    if btn_processar:
        if file_vendas and file_devolucoes:
            with st.spinner("Processando..."):
                try:
                    data = processar_arquivos(file_vendas, file_devolucoes)
                    st.session_state.processed_data = data
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        else:
            st.warning("Selecione os dois arquivos")
            
    if btn_exemplo:
        with st.spinner("Carregando..."):
            try:
                import os
                example_dir = "public/examples"
                if os.path.exists(f"{example_dir}/vendas_exemplo.xlsx") and os.path.exists(f"{example_dir}/devolucoes_exemplo.xlsx"):
                    with open(f"{example_dir}/vendas_exemplo.xlsx", 'rb') as f1:
                        with open(f"{example_dir}/devolucoes_exemplo.xlsx", 'rb') as f2:
                            data = processar_arquivos(f1, f2)
                            st.session_state.processed_data = data
                            st.rerun()
                else:
                    st.warning("Exemplos não encontrados")
            except Exception as e:
                st.error(f"Erro: {str(e)}")

    if st.session_state.processed_data is not None:
        st.markdown("---")
        plataforma = st.session_state.processed_data.get('plataforma', 'ML')
        st.success(f"Plataforma Ativa: **{plataforma}**")
        
        st.markdown("---")
        # Ícone para Configurações
        icon_config = render_icon_svg("config", color="#ffffff").replace("\n", "")
        st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">{icon_config} <h3 style="margin: 0; font-size: 1.2rem;">Configurações</h3></div>', unsafe_allow_html=True)
        visualizacao = st.radio(
            "Visualizar por:",
            ["SKU", "Nome do Produto"],
            index=0,
            key="config_visualizacao",
            help="Altera como os produtos são agrupados nas tabelas e gráficos"
        )
        
        st.markdown("---")
        if st.button("Limpar Dados", use_container_width=True):
            st.session_state.processed_data = None
            st.rerun()

# ─────────────────────────────────────────────────────────
# CONTEÚDO PRINCIPAL
# ─────────────────────────────────────────────────────────
if st.session_state.processed_data is None:
    # Definir valores padrão para evitar erros de escopo
    visualizacao = "SKU"
    agrupar_por = "SKU"
    
    # Título com ícone personalizado
    icon_dash = render_icon_svg("resumo", color="#ffffff").replace("\n", "")
    st.markdown(f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">{icon_dash} <h1 style="margin: 0;">Dashboard Vendas x Devoluções</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Bem-vindo! 
    Para começar a análise, utilize a **barra lateral à esquerda** para carregar seus relatórios do Mercado Livre.
    
    **Arquivos necessários:**
    1.  **Relatório de Vendas** (.xlsx)
    2.  **Relatório de Devoluções** (.xlsx)
    
    *Dica: Você também pode clicar em 'Exemplo' na barra lateral para visualizar como o dashboard funciona.*
    """)
    
    # Ilustração ou cards informativos
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Análise de Canais**\n\nCompare o desempenho entre Matriz e Full.")
    with c2:
        st.info("**Motivos de Devolução**\n\nIdentifique os principais gargalos da sua operação.")
    with c3:
        st.info("**Impacto Financeiro**\n\nVisualize o quanto as devoluções afetam seu lucro.")

else:
    data_raw = st.session_state.processed_data
    
    # Recuperar configuração da sidebar ou usar padrão
    visualizacao = st.session_state.get('config_visualizacao', 'SKU')
    agrupar_por = 'SKU' if visualizacao == "SKU" else 'Título do anúncio'
    
    # Título com ícone personalizado
    icon_dash = render_icon_svg("resumo", color="#ffffff").replace("\n", "")
    st.markdown(f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">{icon_dash} <h1 style="margin: 0;">Dashboard de Análise</h1></div>', unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────────────
    # CABEÇALHO GLOBAL DE FILTROS
    # ─────────────────────────────────────────────────────
    st.markdown('<div class="filter-header">', unsafe_allow_html=True)
    
    fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1, 1])
    
    with fc1:
        janela_opcoes = {'7 dias': 7, '15 dias': 15, '30 dias': 30, '60 dias': 60, '90 dias': 90, '120 dias': 120, '150 dias': 150, '180 dias': 180}
        janela_label = st.selectbox("Janela", list(janela_opcoes.keys()), index=2, key="filtro_janela")
        janela_global = janela_opcoes[janela_label]
    
    with fc2:
        canal_global = st.selectbox("Canal", ["Todos", "Matriz", "Full"], index=0, key="filtro_canal")
    
    with fc3:
        somente_ads_global = st.toggle("Somente Ads", value=False, key="filtro_ads")
    
    with fc4:
        top10_skus_global = st.toggle(f"Top 10 {visualizacao}s", value=False, key="filtro_top10")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Aplicar filtros globais
    data = aplicar_filtros(data_raw, janela_global, canal_global, somente_ads_global, top10_skus_global, agrupar_por=agrupar_por)
    
    # Garantir DataFrames válidos para funções
    df_matriz = data['matriz'] if data['matriz'] is not None else pd.DataFrame()
    df_full = data['full'] if data['full'] is not None else pd.DataFrame()
    
    st.markdown("---")
    
    # ─────────────────────────────────────────────────────
    # ABAS
    # ─────────────────────────────────────────────────────
    # Definir ícones e cores para as abas
    tab_icons = {
        "guia": "guia", "resumo": "resumo", "janelas": "janelas", 
        "matriz_full": "matriz_full", "frete": "frete", "motivos": "motivos", 
        "ads": "ads", "anuncios": "anuncios", "simulador": "simulador", "ia": "ia"
    }
    
    # Injetar CSS para os ícones das abas
    tab_styles = ""
    inactive_color = "#a0a0a0"
    active_color = "#ffffff"
    
    for i, (key, icon) in enumerate(tab_icons.items()):
        icon_svg_inactive = render_icon_svg(icon, color=inactive_color)
        icon_svg_active = render_icon_svg(icon, color=active_color)
        
        # Escapar as aspas simples para o CSS
        icon_svg_inactive = icon_svg_inactive.replace("'", '"').replace("\n", "")
        icon_svg_active = icon_svg_active.replace("'", '"').replace("\n", "")
        
        tab_styles += f"""
        .stTabs [data-baseweb="tab"]:nth-child({i+1})::before {{
            content: '';
            display: inline-block;
            margin-right: 10px;
            zoom: 0.7;
        }}
        .stTabs [data-baseweb="tab"]:nth-child({i+1})::before {{
            content: url('data:image/svg+xml;utf8,{icon_svg_inactive}');
        }}
        .stTabs [data-baseweb="tab"]:nth-child({i+1})[aria-selected="true"]::before {{
            content: url('data:image/svg+xml;utf8,{icon_svg_active}');
        }}
        """
    
    st.markdown(f"<style>{tab_styles}</style>", unsafe_allow_html=True)

    tab_guia, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "Guia de Uso", "Resumo", "Janelas", "Matriz/Full", "Frete", 
        "Motivos", "Ads", "Anúncios", "Simulador", "IA Análise"
    ])
    
    # ─── TAB GUIA: GUIA DE USO ───
    with tab_guia:
        render_tab_guia_uso()
    
    # ─── TAB 1: RESUMO ───
    with tab1:
        metricas = calcular_metricas(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            render_metric_card("VENDAS TOTAIS", formatar_numero(metricas['vendas']), "Total de pedidos", "vendas")
        with c2:
            render_metric_card("CANCELADOS", formatar_numero(metricas['vendas_canceladas']), "Vendas não concluídas", "cancelados")
        with c3:
            render_metric_card("DEVOLUÇÕES", formatar_numero(metricas['devolucoes_vendas']), f"Taxa: {formatar_percentual(metricas['taxa_devolucao'])}", "devolucoes")
        with c4:
            render_metric_card("FAT. DEVOLUÇÕES", formatar_brl(metricas['faturamento_devolucoes']), "", "faturamento")
        with c5:
            render_metric_card("PERDA PARCIAL", formatar_brl(metricas['perda_parcial']), "", "perda_parcial")
        with c6:
            render_metric_card("PERDA TOTAL", formatar_brl(metricas['perda_total']), "", "perda_total")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Classificação das Devoluções</div>', unsafe_allow_html=True)
            
            labels = ['Saudável', 'Crítica', 'Neutra']
            values = [metricas['saudaveis'], metricas['criticas'], metricas['neutras']]
            colors = ['#3b82f6', '#ef4444', '#10b981']
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=labels, values=values, hole=.6,
                marker=dict(colors=colors),
                textinfo='label+percent' if sum(values) > 0 else 'none'
            )])
            fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_right:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown(f'<div class="chart-title">Top 5 {visualizacao}s por Devoluções</div>', unsafe_allow_html=True)
            
            df_skus_top, _ = analisar_skus(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global, limit=5, agrupar_por=agrupar_por)
            
            if not df_skus_top.empty:
                # Garantir que a coluna de agrupamento existe no DataFrame retornado
                col_y = agrupar_por if agrupar_por in df_skus_top.columns else df_skus_top.columns[0]
                
                df_skus_top = df_skus_top.sort_values('Dev', ascending=True)
                fig_bar = go.Figure(go.Bar(
                    x=df_skus_top['Dev'], y=df_skus_top[col_y],
                    orientation='h', marker_color='#f59e0b'
                ))
                fig_bar.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=0, b=0, l=0, r=0), height=300,
                    xaxis=dict(showgrid=True, gridcolor='#334155'),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info(f"Sem dados de {visualizacao}s para exibir")
            st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 2: JANELAS ───
    with tab2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Evolução por Janela de Tempo</div>', unsafe_allow_html=True)
        
        # Definir janelas de tempo fixas para garantir consistência no gráfico
        janelas_list = [7, 15, 30, 60, 90, 120, 150, 180]
            
        # Filtrar janelas até a janela global selecionada
        janelas_list = [j for j in janelas_list if j <= janela_global]
        
        # Garantir que a janela global atual esteja sempre na lista (caso seja um valor customizado)
        if janela_global not in janelas_list:
            janelas_list.append(janela_global)
            
        # Inverter a ordem para começar do maior para o menor (ex: 180d -> 7d)
        janelas_list.sort(reverse=True)
            
        janelas_data_raw = []
        
        for janela in janelas_list:
            # Usar data_raw para recalcular por janela, mas aplicar canal/ads/top10
            d_temp = aplicar_filtros(data_raw, janela, canal_global, somente_ads_global, top10_skus_global, agrupar_por=agrupar_por)
            m = calcular_metricas(d_temp['vendas'], d_temp['matriz'], d_temp['full'], d_temp['max_date'], janela)
            janelas_data_raw.append({
                'Período': f'{janela}d',
                'Período_num': janela,
                'Vendas': m['vendas'],
                'Devoluções': m['devolucoes_vendas'],
                'Taxa': m['taxa_devolucao'] * 100,
                'Faturamento': m['faturamento_total'],
                'Faturamento_Dev': m['faturamento_devolucoes'],
                'Perda_Total': m['perda_total'],
                'Perda_Parcial': m['perda_parcial'],
                'Saudaveis': m['saudaveis'],
                'Criticas': m['criticas'],
            })
        
        df_janelas_raw = pd.DataFrame(janelas_data_raw)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_janelas_raw['Período'], y=df_janelas_raw['Vendas'],
            mode='lines+markers', name='Vendas',
            line=dict(color='#3b82f6', width=2), marker=dict(size=6), yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=df_janelas_raw['Período'], y=df_janelas_raw['Devoluções'],
            mode='lines+markers', name='Devoluções',
            line=dict(color='#f59e0b', width=2), marker=dict(size=6), yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=df_janelas_raw['Período'], y=df_janelas_raw['Taxa'],
            mode='lines+markers', name='Taxa (%)',
            line=dict(color='#ef4444', width=2), marker=dict(size=6), yaxis='y2'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title='',
            xaxis=dict(title='Período', showgrid=True, gridcolor='#334155'),
            yaxis=dict(title='Vendas / Devoluções', showgrid=True, gridcolor='#334155', side='left'),
            yaxis2=dict(title='Taxa (%)', overlaying='y', side='right'),
            hovermode='x unified', height=400, margin=dict(r=80),
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tabela Consolidada
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Tabela Consolidada</div>', unsafe_allow_html=True)
        
        tabela_data = []
        for _, row in df_janelas_raw.iterrows():
            tabela_data.append({
                'Dias': row['Período_num'],
                'Vendas': formatar_numero(row['Vendas']),
                'Fat. Prod.': formatar_brl(row['Faturamento']),
                'Dev.': row['Devoluções'],
                'Taxa': formatar_pct_direto(row['Taxa']),
                'Fat. Dev.': formatar_brl(row['Faturamento_Dev']),
                'Perda Total': formatar_brl(row['Perda_Total']),
                'Perda Parcial': formatar_brl(row['Perda_Parcial']),
                'Saud.': row['Saudaveis'],
                'Crit.': row['Criticas'],
            })
        
        df_tabela = pd.DataFrame(tabela_data)
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 3: MATRIZ/FULL ───
    with tab3:
        metricas_matriz = calcular_metricas(data['vendas'], data['matriz'], None, data['max_date'], janela_global)
        metricas_full = calcular_metricas(data['vendas'], None, data['full'], data['max_date'], janela_global)
        
        col_matriz, col_full = st.columns(2)
        
        with col_matriz:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #f8fafc;">Matriz</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Devoluções</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_numero(metricas_matriz['devolucoes_vendas'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Taxa</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_percentual(metricas_matriz['taxa_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Impacto</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_brl(metricas_matriz['impacto_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                # Calcular Top 10 concentração para Matriz
                df_skus_m, total_dev_m = analisar_skus(data['vendas'], data['matriz'], None, data['max_date'], janela_global, agrupar_por=agrupar_por)
                top10_m = (df_skus_m.sort_values('Dev', ascending=False).head(10)['Dev'].sum() / total_dev_m * 100) if total_dev_m > 0 and len(df_skus_m) > 0 else 0
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Top 10 Conc.</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_pct_direto(top10_m)}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_full:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #f8fafc;">Full</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Devoluções</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_numero(metricas_full['devolucoes_vendas'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Taxa</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_percentual(metricas_full['taxa_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Impacto</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_brl(metricas_full['impacto_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                df_skus_f, total_dev_f = analisar_skus(data['vendas'], None, data['full'], data['max_date'], janela_global, agrupar_por=agrupar_por)
                top10_f = (df_skus_f.sort_values('Dev', ascending=False).head(10)['Dev'].sum() / total_dev_f * 100) if total_dev_f > 0 and len(df_skus_f) > 0 else 0
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #334155; border-radius: 8px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Top 10 Conc.</div>
                        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 700;">{formatar_pct_direto(top10_f)}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico Comparativo
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Comparativo</div>', unsafe_allow_html=True)
        
        total_matriz = metricas_matriz['devolucoes_vendas']
        total_full = metricas_full['devolucoes_vendas']
        impacto_matriz = abs(metricas_matriz['impacto_devolucao'])
        impacto_full = abs(metricas_full['impacto_devolucao'])
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['Matriz', 'Full'], y=[total_matriz, total_full], name='Devoluções', marker_color='#3b82f6', yaxis='y1'))
        fig.add_trace(go.Bar(x=['Matriz', 'Full'], y=[impacto_matriz, impacto_full], name='Impacto (R$)', marker_color='#ef4444', yaxis='y2'))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group', title='',
            xaxis=dict(title='Canal'),
            yaxis=dict(title='Devoluções', side='left'),
            yaxis2=dict(title='Impacto (R$)', overlaying='y', side='right'),
            hovermode='x unified', height=400,
            legend=dict(x=0.5, y=1.0, orientation='h', xanchor='center', yanchor='top'),
            margin=dict(r=80)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 4: FRETE ───
    with tab4:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Análise de Frete e Forma de Entrega</div>', unsafe_allow_html=True)
        df_frete = analisar_frete(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        if len(df_frete) > 0:
            df_frete_display = df_frete.copy()
            # Formatar todas as colunas numéricas
            df_frete_display['Vendas'] = df_frete_display['Vendas'].astype(int).apply(lambda x: formatar_numero(x))
            df_frete_display['Cancelados'] = df_frete_display['Cancelados'].astype(int).apply(lambda x: formatar_numero(x))
            df_frete_display['Devoluções'] = df_frete_display['Devoluções'].astype(int).apply(lambda x: formatar_numero(x))
            df_frete_display['Taxa (%)'] = df_frete_display['Taxa (%)'].apply(lambda x: formatar_pct_direto(x))
            df_frete_display['Impacto (R$)'] = df_frete_display['Impacto (R$)'].apply(lambda x: formatar_brl(x))
            st.dataframe(df_frete_display, use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados disponíveis")
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 5: MOTIVOS ───
    with tab5:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Filtros de Devolução</div>', unsafe_allow_html=True)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            search_motivo = st.text_input("Buscar por Motivo...", "")
        with col_s2:
            search_sku = st.text_input("Buscar por SKU...", "")
        with col_s3:
            search_produto = st.text_input("Buscar por Produto...", "")
            
        df_dev_raw = analisar_motivos(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        
        if not df_dev_raw.empty:
            # Aplicar filtros de busca
            df_filtered = df_dev_raw.copy()
            if search_motivo:
                df_filtered = df_filtered[df_filtered['Motivo'].str.contains(search_motivo, case=False, na=False)]
            if search_sku:
                df_filtered = df_filtered[df_filtered['SKU'].str.contains(search_sku, case=False, na=False)]
            if search_produto:
                df_filtered = df_filtered[df_filtered['Título do anúncio'].str.contains(search_produto, case=False, na=False)]
            
            # 1. Gráfico de Motivos (Baseado nos dados filtrados)
            st.markdown("---")
            st.markdown('<div class="chart-title">Distribuição de Motivos (Filtrado)</div>', unsafe_allow_html=True)
            
            df_motivos_agg = df_filtered.groupby('Motivo').size().reset_index(name='Quantidade')
            total_devs = df_motivos_agg['Quantidade'].sum()
            df_motivos_agg['%'] = (df_motivos_agg['Quantidade'] / total_devs * 100).round(1)
            df_motivos_agg = df_motivos_agg.sort_values('Quantidade', ascending=True)
            
            if not df_motivos_agg.empty:
                # Criar texto para as barras com Quantidade e %
                bar_text = [f"{q} ({p}%)" for q, p in zip(df_motivos_agg['Quantidade'], df_motivos_agg['%'])]
                
                fig = go.Figure(go.Bar(
                    x=df_motivos_agg['Quantidade'], y=df_motivos_agg['Motivo'],
                    orientation='h', marker_color='#f59e0b',
                    text=bar_text, textposition='outside'
                ))
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title='Quantidade', showgrid=True, gridcolor='#334155'),
                    yaxis=dict(title=''), height=max(300, len(df_motivos_agg) * 30), margin=dict(l=250, r=50)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum motivo encontrado com os filtros aplicados.")

            # 2. Tabela Resumo por Motivo
            st.markdown("---")
            st.markdown('<div class="chart-title">Resumo por Motivo</div>', unsafe_allow_html=True)
            
            df_resumo = df_motivos_agg.sort_values('Quantidade', ascending=False).copy()
            df_resumo['%'] = df_resumo['%'].apply(lambda x: f"{x}%")
            st.dataframe(df_resumo[['Motivo', 'Quantidade', '%']], use_container_width=True, hide_index=True)
            
        else:
            st.info("Sem dados de devolução disponíveis para o período selecionado.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 6: ADS ───
    with tab6:
        df_ads = analisar_ads(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        
        ads_vendas = ads_dev = 0
        ads_taxa = ads_impacto = ads_fat = 0.0
        org_vendas = org_dev = 0
        org_taxa = 0.0
        
        if len(df_ads) > 0:
            for _, row in df_ads.iterrows():
                if 'Com Publicidade' in str(row.get('Tipo', '')):
                    ads_vendas = int(row.get('Vendas', 0))
                    ads_dev = int(row.get('Devoluções', 0))
                    ads_taxa = float(row.get('Taxa (%)', 0))
                    ads_impacto = float(row.get('Impacto (R$)', 0))
                    ads_fat = float(row.get('Receita (R$)', 0))
                elif 'Orgânico' in str(row.get('Tipo', '')):
                    org_vendas = int(row.get('Vendas', 0))
                    org_dev = int(row.get('Devoluções', 0))
                    org_taxa = float(row.get('Taxa (%)', 0))
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_metric_card("VENDAS ADS", formatar_numero(ads_vendas), "Total de pedidos", "ads")
        with c2:
            render_metric_card("DEV. ADS", formatar_numero(ads_dev), "Pedidos devolvidos", "devolucoes")
        with c3:
            render_metric_card("TAXA ADS", formatar_pct_direto(ads_taxa), "Percentual de dev.", "ia")
        with c4:
            render_metric_card("IMPACTO ADS", formatar_brl(ads_impacto), "Custo de devolução", "faturamento")
        with c5:
            render_metric_card("FAT. ADS", formatar_brl(ads_fat), "Receita de produtos", "faturamento")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Ads vs Orgânico</div>', unsafe_allow_html=True)
        
        col_pub, col_org = st.columns(2)
        with col_pub:
            st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="color: #3b82f6; font-size: 1rem; font-weight: 700; margin-bottom: 15px;">Publicidade</div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #475569;">
                        <span style="color: #f8fafc; font-weight: 500;">Vendas</span>
                        <span style="color: #f8fafc; font-weight: 600;">{formatar_numero(ads_vendas)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #475569;">
                        <span style="color: #f8fafc; font-weight: 500;">Devoluções</span>
                        <span style="color: #f8fafc; font-weight: 600;">{formatar_numero(ads_dev)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                        <span style="color: #f8fafc; font-weight: 500;">Taxa</span>
                        <span style="color: #f8fafc; font-weight: 600;">{formatar_pct_direto(ads_taxa)}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col_org:
            st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="color: #3b82f6; font-size: 1rem; font-weight: 700; margin-bottom: 15px;">Orgânico</div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #475569;">
                        <span style="color: #f8fafc; font-weight: 500;">Vendas</span>
                        <span style="color: #f8fafc; font-weight: 600;">{formatar_numero(org_vendas)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #475569;">
                        <span style="color: #f8fafc; font-weight: 500;">Devoluções</span>
                        <span style="color: #f8fafc; font-weight: 600;">{formatar_numero(org_dev)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                        <span style="color: #f8fafc; font-weight: 500;">Taxa</span>
                        <span style="color: #f8fafc; font-weight: 600;">{formatar_pct_direto(org_taxa)}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 7: ANÚNCIOS ───
    with tab7:
        df_skus_all, total_dev_skus = analisar_skus(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global, agrupar_por=agrupar_por)
        
        total_skus_com_dev = len(df_skus_all)
        if total_dev_skus > 0 and len(df_skus_all) > 0:
            df_sorted_vol = df_skus_all.sort_values('Dev.', ascending=False)
            top10_conc = (df_sorted_vol.head(10)['Dev.'].sum() / total_dev_skus * 100)
            top20_conc = (df_sorted_vol.head(20)['Dev.'].sum() / total_dev_skus * 100)
        else:
            top10_conc = top20_conc = 0
        
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("TOP 10 CONCENTRAÇÃO", formatar_pct_direto(top10_conc), "Volume de devoluções", "ia")
        with c2:
            render_metric_card("TOP 20 CONCENTRAÇÃO", formatar_pct_direto(top20_conc), "Volume de devoluções", "ia")
        with c3:
            render_metric_card(f"{visualizacao.upper()}S COM DEV.", formatar_numero(total_skus_com_dev), "Total no período", "anuncios")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if len(df_skus_all) > 0:
            sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
                "Top Volume", "Top Taxa (≥20)", "Top Perda", "Top Risco", "Todos"
            ])
            
            def formatar_df_skus(df):
                df_display = df.copy()
                df_display['Taxa'] = df_display['Taxa'].apply(lambda x: formatar_pct_direto(x))
                df_display['Impacto'] = df_display['Impacto'].apply(lambda x: formatar_brl(x))
                df_display['Reemb.'] = df_display['Reemb.'].apply(lambda x: formatar_brl(x))
                df_display['Custo Dev.'] = df_display['Custo Dev.'].apply(lambda x: formatar_brl(x))
                df_display['Risco'] = df_display['Risco'].apply(lambda x: formatar_risco(x))
                
                # Garantir que a coluna de agrupamento existe
                col_id = agrupar_por if agrupar_por in df_display.columns else df_display.columns[0]
                
                return df_display[[col_id, 'Vendas', 'Dev.', 'Taxa', 'Impacto', 'Reemb.', 'Custo Dev.', 'Risco', 'Classe']]
            
            with sub_tab1:
                df_vol = df_skus_all.sort_values('Dev.', ascending=False).head(20)
                st.dataframe(formatar_df_skus(df_vol), use_container_width=True, hide_index=True)
            with sub_tab2:
                df_taxa = df_skus_all[(df_skus_all['Taxa'] >= 20) & (df_skus_all['Vendas'] >= 5)].sort_values('Taxa', ascending=False)
                if len(df_taxa) > 0:
                    st.dataframe(formatar_df_skus(df_taxa), use_container_width=True, hide_index=True)
                else:
                    st.info(f"Nenhum {visualizacao} com taxa ≥ 20% e pelo menos 5 vendas")
            with sub_tab3:
                df_perda = df_skus_all.sort_values('Impacto', ascending=True).head(20)
                st.dataframe(formatar_df_skus(df_perda), use_container_width=True, hide_index=True)
            with sub_tab4:
                df_risco = df_skus_all.sort_values('Risco', ascending=False).head(20)
                st.dataframe(formatar_df_skus(df_risco), use_container_width=True, hide_index=True)
            with sub_tab5:
                st.dataframe(formatar_df_skus(df_skus_all), use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados disponíveis")

    # ─── TAB 8: SIMULADOR ───
    with tab8:
        metricas_sim = calcular_metricas(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        taxa_atual = metricas_sim['taxa_devolucao'] * 100
        total_dev = metricas_sim['devolucoes_vendas']
        impacto_total = abs(metricas_sim['impacto_devolucao'])
        perda_media = (impacto_total / total_dev) if total_dev > 0 else 0
        
        st.markdown('<div class="simulator-box">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-top: 0; margin-bottom: 15px;">Simulador de Reducao de Devolucoes</h4>', unsafe_allow_html=True)
        
        max_slider = int(taxa_atual) if taxa_atual > 0 else 10
        reducao_pct = st.slider("Reducao desejada (%)", 0, max_slider, min(1, max_slider), key="sim_reducao_pct")
        st.markdown('</div>', unsafe_allow_html=True)
        
        nova_taxa = max(taxa_atual - reducao_pct, 0)
        vendas_totais = metricas_sim['vendas']
        dev_evitadas = int((reducao_pct / 100) * vendas_totais) if vendas_totais > 0 else 0
        dinheiro_recuperado = dev_evitadas * perda_media
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("DEVOLUÇÕES SIMULADAS", formatar_numero(dev_evitadas), f"Antes: {formatar_numero(int(total_dev))}", "devolucoes")
        with c2:
            render_metric_card("PERDA SIMULADA", formatar_brl(dinheiro_recuperado), f"Antes: {formatar_brl(impacto_total)}", "faturamento")
        with c3:
            render_metric_card("ECONOMIA ESTIMADA", formatar_brl(dinheiro_recuperado), "Redução de perda", "ia")
    
    # ─── TAB 9: IA ANÁLISE DE ANÚNCIOS ───
    with tab9:
        render_tab_analise_anuncios()
    
    # ─── EXPORT ───
    st.markdown("---")
    if st.button("Exportar Relatório XLSX", use_container_width=True, type="primary"):
        try:
            xlsx_file = exportar_xlsx(data)
            st.download_button(
                label="Clique aqui para baixar",
                data=xlsx_file,
                file_name=f"Relatorio_Vendas_Devolucoes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao exportar: {str(e)}")

# ─── RODAPÉ ───
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 0.8rem;
        z-index: 999;
    }
    </style>
    <div class="footer">
        © Desenvolvido por Vinicius Lima / CNPJ: 47.192.694/0001-70
    </div>
""", unsafe_allow_html=True)
