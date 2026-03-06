import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.parser import processar_arquivos
from utils.metricas import calcular_metricas, calcular_qualidade_arquivo
from utils.export import exportar_xlsx
from utils.analises import analisar_frete, analisar_motivos, analisar_ads, analisar_skus, simular_reducao
from utils.formatacao import formatar_brl, formatar_percentual, formatar_pct_direto, formatar_numero, formatar_risco

# Configuração da página
st.set_page_config(
    page_title="Dashboard Vendas x Devoluções",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    /* Estilo dos Cartões de Métricas */
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e6e9ef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        flex: 1;
        position: relative;
        min-height: 100px;
    }
    .metric-label {
        color: #6e7787;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #1a1d23;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .metric-subvalue {
        color: #9ba3af;
        font-size: 0.75rem;
        margin-top: 2px;
    }
    .metric-icon {
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.8rem;
        color: #d1d5db;
    }
    
    /* Estilo das Seções de Gráficos */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e6e9ef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .chart-title {
        color: #1a1d23;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 20px;
    }
    
    /* Estilo do Cabeçalho de Filtros */
    .filter-header {
        background-color: white;
        padding: 15px 25px;
        border-radius: 10px;
        border: 1px solid #e6e9ef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def render_metric_card(label, value, subvalue, icon):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subvalue">{subvalue}</div>
            <div class="metric-icon">{icon}</div>
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# Função de filtragem global dos dados
# ─────────────────────────────────────────────────────────
def aplicar_filtros(data, janela, canal, somente_ads, top10_skus):
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

    # 4) Filtro TOP 10 SKUs (filtra vendas apenas dos 10 SKUs com mais devoluções)
    if top10_skus:
        todas_dev = pd.concat([matriz, full], ignore_index=True)
        if len(todas_dev) > 0 and 'N.º de venda' in todas_dev.columns and 'SKU' in vendas.columns:
            # Mapear devoluções para SKUs via vendas
            dev_nums = set(todas_dev['N.º de venda'].astype(str).unique())
            vendas_com_dev = vendas[vendas['N.º de venda'].astype(str).isin(dev_nums)]
            if 'SKU' in vendas_com_dev.columns:
                top_skus = vendas_com_dev['SKU'].value_counts().head(10).index.tolist()
                vendas = vendas[vendas['SKU'].isin(top_skus)]
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

# Sidebar
st.sidebar.title("📊 Menu")
st.sidebar.markdown("---")

# ─────────────────────────────────────────────────────────
# PÁGINA DE UPLOAD
# ─────────────────────────────────────────────────────────
if st.session_state.processed_data is None:
    st.title("📊 Dashboard Vendas x Devoluções")
    st.markdown("Análise automática de Vendas e Devoluções do Mercado Livre (BR)")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 Relatório de Vendas")
        file_vendas = st.file_uploader("Selecione o arquivo de Vendas", type=['xlsx'], key='vendas')
    with col2:
        st.subheader("📁 Relatório de Devoluções")
        file_devolucoes = st.file_uploader("Selecione o arquivo de Devoluções", type=['xlsx'], key='devolucoes')
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Processar", use_container_width=True, type="primary"):
            if file_vendas and file_devolucoes:
                with st.spinner("Processando arquivos..."):
                    try:
                        data = processar_arquivos(file_vendas, file_devolucoes)
                        st.session_state.processed_data = data
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar: {str(e)}")
            else:
                st.warning("Por favor, selecione ambos os arquivos")
    
    with col2:
        if st.button("📋 Carregar Exemplo", use_container_width=True):
            with st.spinner("Carregando exemplo..."):
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
                        st.warning("Arquivos de exemplo não encontrados")
                except Exception as e:
                    st.error(f"Erro ao carregar exemplo: {str(e)}")

# ─────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────
else:
    data_raw = st.session_state.processed_data
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Dashboard de Análise")
    with col2:
        if st.button("← Voltar", use_container_width=True):
            st.session_state.processed_data = None
            st.rerun()
    
    # ─────────────────────────────────────────────────────
    # CABEÇALHO GLOBAL DE FILTROS
    # ─────────────────────────────────────────────────────
    st.markdown('<div class="filter-header">', unsafe_allow_html=True)
    
    fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1, 1])
    
    with fc1:
        janela_opcoes = {'30 dias': 30, '60 dias': 60, '90 dias': 90, '120 dias': 120, '150 dias': 150, '180 dias': 180}
        janela_label = st.selectbox("Janela", list(janela_opcoes.keys()), index=5, key="filtro_janela")
        janela_global = janela_opcoes[janela_label]
    
    with fc2:
        canal_global = st.selectbox("Canal", ["Todos", "Matriz", "Full"], index=0, key="filtro_canal")
    
    with fc3:
        somente_ads_global = st.toggle("Somente Ads", value=False, key="filtro_ads")
    
    with fc4:
        top10_skus_global = st.toggle("Top 10 SKUs", value=False, key="filtro_top10")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Aplicar filtros globais
    data = aplicar_filtros(data_raw, janela_global, canal_global, somente_ads_global, top10_skus_global)
    
    # Garantir DataFrames válidos para funções
    df_matriz = data['matriz'] if data['matriz'] is not None else pd.DataFrame()
    df_full = data['full'] if data['full'] is not None else pd.DataFrame()
    
    st.markdown("---")
    
    # ─────────────────────────────────────────────────────
    # ABAS
    # ─────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📈 Resumo", "🎯 Janelas", "📦 Matriz/Full", "🚚 Frete", 
        "🔍 Motivos", "📢 Ads", "📊 SKUs", "🎮 Simulador"
    ])
    
    # ─── TAB 1: RESUMO ───
    with tab1:
        metricas = calcular_metricas(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            render_metric_card("VENDAS", formatar_numero(metricas['vendas']), f"{formatar_numero(metricas['unidades'])} un.", "🛒")
        with c2:
            render_metric_card("FATURAMENTO", formatar_brl(metricas['faturamento_produtos']), f"Total: {formatar_brl(metricas['faturamento_total'])}", "💲")
        with c3:
            render_metric_card("DEVOLUÇÕES", formatar_numero(metricas['devolucoes_vendas']), f"Taxa: {formatar_percentual(metricas['taxa_devolucao'])}", "🔄")
        with c4:
            render_metric_card("FAT. DEVOLUÇÕES", formatar_brl(metricas['faturamento_devolucoes']), "", "📉")
        with c5:
            render_metric_card("PERDA TOTAL", formatar_brl(metricas['perda_total']), "", "⚠️")
        with c6:
            render_metric_card("PERDA PARCIAL", formatar_brl(metricas['perda_parcial']), "", "📦")
            
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
            st.markdown('<div class="chart-title">Top 5 SKUs por Devoluções</div>', unsafe_allow_html=True)
            
            df_skus_top, _ = analisar_skus(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global, 5)
            
            if not df_skus_top.empty:
                df_skus_top = df_skus_top.sort_values('Dev.', ascending=True)
                fig_bar = go.Figure(go.Bar(
                    x=df_skus_top['Dev.'], y=df_skus_top['SKU'],
                    orientation='h', marker_color='#f59e0b'
                ))
                fig_bar.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0), height=300,
                    xaxis=dict(showgrid=True, gridcolor='#f3f4f6'),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sem dados de SKUs para exibir")
            st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 2: JANELAS ───
    with tab2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Evolução por Janela de Tempo</div>', unsafe_allow_html=True)
        
        janelas_list = [30, 60, 90, 120, 150, 180]
        # Filtrar janelas até a janela global selecionada
        janelas_list = [j for j in janelas_list if j <= janela_global]
        janelas_data_raw = []
        
        for janela in janelas_list:
            # Usar data_raw para recalcular por janela, mas aplicar canal/ads/top10
            d_temp = aplicar_filtros(data_raw, janela, canal_global, somente_ads_global, top10_skus_global)
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
            title='',
            xaxis=dict(title='Período', showgrid=True, gridcolor='#e5e7eb'),
            yaxis=dict(title='Vendas / Devoluções', showgrid=True, gridcolor='#e5e7eb', side='left'),
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
                'Imp. Saud.': formatar_brl(0),
                'Crit.': row['Criticas'],
                'Imp. Crit.': formatar_brl(0),
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
            st.markdown('<div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #1a1d23;">Matriz</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Devoluções</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_numero(metricas_matriz['devolucoes_vendas'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Taxa</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_percentual(metricas_matriz['taxa_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Impacto</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_brl(metricas_matriz['impacto_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                # Calcular Top 10 concentração para Matriz
                df_skus_m, total_dev_m = analisar_skus(data['vendas'], data['matriz'], None, data['max_date'], janela_global)
                top10_m = (df_skus_m.sort_values('Dev.', ascending=False).head(10)['Dev.'].sum() / total_dev_m * 100) if total_dev_m > 0 and len(df_skus_m) > 0 else 0
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Top 10 Conc.</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_pct_direto(top10_m)}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_full:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #1a1d23;">Full</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Devoluções</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_numero(metricas_full['devolucoes_vendas'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Taxa</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_percentual(metricas_full['taxa_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Impacto</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_brl(metricas_full['impacto_devolucao'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                df_skus_f, total_dev_f = analisar_skus(data['vendas'], None, data['full'], data['max_date'], janela_global)
                top10_f = (df_skus_f.sort_values('Dev.', ascending=False).head(10)['Dev.'].sum() / total_dev_f * 100) if total_dev_f > 0 and len(df_skus_f) > 0 else 0
                st.markdown(f"""
                    <div style="padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                        <div style="color: #9ba3af; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Top 10 Conc.</div>
                        <div style="color: #1a1d23; font-size: 1.8rem; font-weight: 700;">{formatar_pct_direto(top10_f)}</div>
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
        st.subheader("🚚 Análise de Frete e Forma de Entrega")
        df_frete = analisar_frete(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        if len(df_frete) > 0:
            df_frete_display = df_frete.copy()
            df_frete_display['Vendas'] = df_frete_display['Vendas'].apply(lambda x: formatar_numero(x))
            df_frete_display['Taxa (%)'] = df_frete_display['Taxa (%)'].apply(lambda x: formatar_pct_direto(x))
            df_frete_display['Impacto (R$)'] = df_frete_display['Impacto (R$)'].apply(lambda x: formatar_brl(x))
            st.dataframe(df_frete_display, use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados disponíveis")

    # ─── TAB 5: MOTIVOS ───
    with tab5:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Distribuição de Motivos</div>', unsafe_allow_html=True)
        
        df_motivos = analisar_motivos(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        
        if len(df_motivos) > 0:
            df_motivos_sorted = df_motivos.sort_values('Quantidade', ascending=True)
            fig = go.Figure(go.Bar(
                x=df_motivos_sorted['Quantidade'], y=df_motivos_sorted['Motivo'],
                orientation='h', marker_color='#f59e0b',
                text=df_motivos_sorted['Quantidade'], textposition='outside'
            ))
            fig.update_layout(
                title='',
                xaxis=dict(title='Quantidade', showgrid=True, gridcolor='#e5e7eb'),
                yaxis=dict(title=''), height=400, margin=dict(l=250, r=50)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados disponíveis")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        col_search, col_empty = st.columns([1, 4])
        with col_search:
            search_motivo = st.text_input("Buscar motivo...", "")
        
        if len(df_motivos) > 0:
            if search_motivo:
                df_motivos_filtered = df_motivos[df_motivos['Motivo'].str.contains(search_motivo, case=False, na=False)]
            else:
                df_motivos_filtered = df_motivos
            
            df_motivos_display = df_motivos_filtered.copy()
            df_motivos_display['%'] = df_motivos_display['Percentual (%)'].apply(lambda x: formatar_pct_direto(x))
            df_motivos_display = df_motivos_display[['Motivo', 'Quantidade', '%']]
            st.dataframe(df_motivos_display, use_container_width=True, hide_index=True)
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
            render_metric_card("VENDAS ADS", formatar_numero(ads_vendas), "", "📣")
        with c2:
            render_metric_card("DEV. ADS", formatar_numero(ads_dev), "", "📉")
        with c3:
            render_metric_card("TAXA ADS", formatar_pct_direto(ads_taxa), "", "🎯")
        with c4:
            render_metric_card("IMPACTO ADS", formatar_brl(ads_impacto), "", "📉")
        with c5:
            render_metric_card("FAT. ADS", formatar_brl(ads_fat), "", "💲")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Ads vs Orgânico</div>', unsafe_allow_html=True)
        
        col_pub, col_org = st.columns(2)
        with col_pub:
            st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="color: #3b82f6; font-size: 1rem; font-weight: 700; margin-bottom: 15px;">Publicidade</div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                        <span style="color: #1a1d23; font-weight: 500;">Vendas</span>
                        <span style="color: #1a1d23; font-weight: 600;">{formatar_numero(ads_vendas)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                        <span style="color: #1a1d23; font-weight: 500;">Devoluções</span>
                        <span style="color: #1a1d23; font-weight: 600;">{formatar_numero(ads_dev)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                        <span style="color: #1a1d23; font-weight: 500;">Taxa</span>
                        <span style="color: #1a1d23; font-weight: 600;">{formatar_pct_direto(ads_taxa)}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col_org:
            st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="color: #3b82f6; font-size: 1rem; font-weight: 700; margin-bottom: 15px;">Orgânico</div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                        <span style="color: #1a1d23; font-weight: 500;">Vendas</span>
                        <span style="color: #1a1d23; font-weight: 600;">{formatar_numero(org_vendas)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                        <span style="color: #1a1d23; font-weight: 500;">Devoluções</span>
                        <span style="color: #1a1d23; font-weight: 600;">{formatar_numero(org_dev)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                        <span style="color: #1a1d23; font-weight: 500;">Taxa</span>
                        <span style="color: #1a1d23; font-weight: 600;">{formatar_pct_direto(org_taxa)}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── TAB 7: SKUS ───
    with tab7:
        df_skus_all, total_dev_skus = analisar_skus(data['vendas'], data['matriz'], data['full'], data['max_date'], janela_global)
        
        total_skus_com_dev = len(df_skus_all)
        if total_dev_skus > 0 and len(df_skus_all) > 0:
            df_sorted_vol = df_skus_all.sort_values('Dev.', ascending=False)
            top10_conc = (df_sorted_vol.head(10)['Dev.'].sum() / total_dev_skus * 100)
            top20_conc = (df_sorted_vol.head(20)['Dev.'].sum() / total_dev_skus * 100)
        else:
            top10_conc = top20_conc = 0
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">Top 10 concentração</div>
                    <div class="metric-value" style="font-size: 2rem;">{formatar_pct_direto(top10_conc)}</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">Top 20 concentração</div>
                    <div class="metric-value" style="font-size: 2rem;">{formatar_pct_direto(top20_conc)}</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">SKUs com devolução</div>
                    <div class="metric-value" style="font-size: 2rem;">{total_skus_com_dev}</div>
                </div>
            """, unsafe_allow_html=True)
        
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
                return df_display[['SKU', 'Vendas', 'Dev.', 'Taxa', 'Impacto', 'Reemb.', 'Custo Dev.', 'Risco', 'Classe']]
            
            with sub_tab1:
                df_vol = df_skus_all.sort_values('Dev.', ascending=False).head(20)
                st.dataframe(formatar_df_skus(df_vol), use_container_width=True, hide_index=True)
            with sub_tab2:
                df_taxa = df_skus_all[(df_skus_all['Taxa'] >= 20) & (df_skus_all['Vendas'] >= 5)].sort_values('Taxa', ascending=False)
                if len(df_taxa) > 0:
                    st.dataframe(formatar_df_skus(df_taxa), use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum SKU com taxa ≥ 20% e pelo menos 5 vendas")
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
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Simulador de Impacto</div>', unsafe_allow_html=True)
        
        max_slider = int(taxa_atual) if taxa_atual > 0 else 10
        reducao_pp = st.slider("Redução desejada (pp)", 0, max_slider, min(1, max_slider), key="sim_reducao_pp")
        
        st.markdown(f"""
            <div style="color: #6e7787; font-size: 0.85rem; margin-top: -10px; margin-bottom: 10px;">
                Redução desejada: <strong style="color: #1a1d23;">{reducao_pp}pp</strong>
            </div>
            <div style="color: #6e7787; font-size: 0.85rem;">
                Perda média por devolução: <strong style="color: #1a1d23;">{formatar_brl(perda_media)}</strong>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        nova_taxa = max(taxa_atual - reducao_pp, 0)
        diff_pp = taxa_atual - nova_taxa
        vendas_totais = metricas_sim['vendas']
        dev_evitadas = int((diff_pp / 100) * vendas_totais) if vendas_totais > 0 else 0
        dinheiro_recuperado = dev_evitadas * perda_media
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("TAXA ATUAL", formatar_pct_direto(taxa_atual), "", "🎯")
        with c2:
            render_metric_card("NOVA TAXA", formatar_pct_direto(nova_taxa), f"-{reducao_pp}pp", "📈")
        with c3:
            render_metric_card("DINHEIRO RECUPERADO", formatar_brl(dinheiro_recuperado), f"{formatar_numero(dev_evitadas)} devoluções evitadas", "📋")
    
    # ─── EXPORT ───
    st.markdown("---")
    if st.button("📥 Exportar Relatório XLSX", use_container_width=True, type="primary"):
        try:
            xlsx_file = exportar_xlsx(data)
            st.download_button(
                label="⬇️ Clique aqui para baixar",
                data=xlsx_file,
                file_name=f"Relatorio_Vendas_Devolucoes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao exportar: {str(e)}")
