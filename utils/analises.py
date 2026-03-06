import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def preparar_dados_analise(vendas, matriz, full):
    """Função auxiliar para preparar e validar dados antes da análise."""
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    vendas_periodo = vendas.copy()
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    
    # Verificar se temos as colunas mínimas para cruzamento
    tem_id_venda = 'N.º de venda' in vendas_periodo.columns and 'N.º de venda' in todas_dev.columns
    
    if not tem_id_venda or todas_dev.empty:
        # Se não puder cruzar, criar colunas vazias para não quebrar o merge
        if 'N.º de venda' not in todas_dev.columns:
            todas_dev['N.º de venda'] = None
        if 'Cancelamentos e reembolsos (BRL)' not in todas_dev.columns:
            todas_dev['Cancelamentos e reembolsos (BRL)'] = 0.0
            
    return vendas_periodo, todas_dev

def analisar_frete(vendas, matriz, full, max_date, dias_atras):
    """Análise de frete e forma de entrega."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    if vendas_periodo.empty:
        return pd.DataFrame()

    # Agrupar devoluções por pedido
    col_valor = 'Cancelamentos e reembolsos (BRL)'
    if col_valor not in todas_dev.columns: todas_dev[col_valor] = 0.0
    
    dev_agg = todas_dev.groupby('N.º de venda').agg({
        col_valor: 'sum'
    }).reset_index()
    
    # Merge vendas com devoluções
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged[col_valor].notna()
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0)
    
    # Se valor_dev é 0 mas tem devolução, usar receita do produto
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in df_merged.columns: df_merged[col_receita] = 0.0
    
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged[col_receita]
    
    # Agrupar por forma de entrega
    col_forma = 'Forma de entrega' if 'Forma de entrega' in df_merged.columns else None
    if not col_forma:
        return pd.DataFrame()
        
    df_merged[col_forma] = df_merged[col_forma].fillna('Outros').replace(['', ' '], 'Outros')
    
    res = df_merged.groupby(col_forma).agg(
        Vendas=('N.º de venda', 'count'),
        Devoluções=('tem_dev', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    res['Taxa (%)'] = (res['Devoluções'] / res['Vendas'] * 100).round(1)
    res['Impacto (R$)'] = (-res['Impacto']).round(2)
    res = res.rename(columns={col_forma: 'Forma de Entrega'})
    
    return res

def analisar_motivos(vendas=None, matriz=None, full=None, max_date=None, dias_atras=0):
    """Análise de motivos de devolução."""
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    
    if todas_dev.empty:
        return pd.DataFrame()
        
    col_motivo = 'Motivo do resultado' if 'Motivo do resultado' in todas_dev.columns else None
    if not col_motivo:
        return pd.DataFrame()
        
    motivos = todas_dev[col_motivo].fillna('Não informado').value_counts()
    total = motivos.sum()
    
    motivos_data = []
    for motivo, count in motivos.items():
        motivos_data.append({
            'Motivo': str(motivo)[:50],
            'Quantidade': int(count),
            'Percentual (%)': round((count / total * 100), 1) if total > 0 else 0,
        })
    
    return pd.DataFrame(motivos_data)

def analisar_ads(vendas, matriz, full, max_date, dias_atras):
    """Análise de publicidade."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    if 'Venda por publicidade' not in vendas_periodo.columns:
        return pd.DataFrame()
        
    col_valor = 'Cancelamentos e reembolsos (BRL)'
    if col_valor not in todas_dev.columns: todas_dev[col_valor] = 0.0
    
    dev_agg = todas_dev.groupby('N.º de venda').agg({col_valor: 'sum'}).reset_index()
    
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged[col_valor].notna()
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0)
    
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in df_merged.columns: df_merged[col_receita] = 0.0
    
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged[col_receita]
    
    df_merged['Tipo'] = df_merged['Venda por publicidade'].apply(lambda x: 'Com Publicidade' if str(x).lower() == 'sim' else 'Orgânico')
    
    res = df_merged.groupby('Tipo').agg(
        Vendas=('N.º de venda', 'count'),
        Devoluções=('tem_dev', 'sum'),
        Receita=(col_receita, 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    res['Taxa (%)'] = (res['Devoluções'] / res['Vendas'] * 100).round(1)
    res['Receita (R$)'] = res['Receita'].round(2)
    res['Impacto (R$)'] = (-res['Impacto']).round(2)
    
    return res

def analisar_skus(vendas, matriz, full, max_date, dias_atras, limit=None, agrupar_por='SKU'):
    """Análise por SKU ou Produto."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    if agrupar_por not in vendas_periodo.columns:
        # Fallback se a coluna não existir
        agrupar_por = 'SKU' if 'SKU' in vendas_periodo.columns else (vendas_periodo.columns[0] if not vendas_periodo.empty else 'SKU')
        
    col_valor = 'Cancelamentos e reembolsos (BRL)'
    if col_valor not in todas_dev.columns: todas_dev[col_valor] = 0.0
    
    # Função para garantir todas as colunas que o app.py espera
    def garantir_colunas_app(df):
        cols_esperadas = {
            'Vendas': 0,
            'Dev.': 0,
            'Taxa': 0.0,
            'Impacto': 0.0,
            'Reemb.': 0.0,
            'Custo Dev.': 0.0,
            'Risco': 0.0,
            'Classe': 'C',
            'Dev': 0 # Fallback para uso interno se necessário
        }
        for col, val in cols_esperadas.items():
            if col not in df.columns:
                df[col] = val
        return df

    # Se todas_dev estiver vazio ou não tiver ID de venda, retornamos algo vazio mas estruturado
    if 'N.º de venda' not in todas_dev.columns or todas_dev.empty:
        if not vendas_periodo.empty and agrupar_por in vendas_periodo.columns:
            res = vendas_periodo.groupby(agrupar_por).agg(
                Vendas=('N.º de venda', 'count')
            ).reset_index()
            res = garantir_colunas_app(res)
            res = res.sort_values('Vendas', ascending=False)
            if limit: res = res.head(limit)
            return res, 0
        return garantir_colunas_app(pd.DataFrame(columns=[agrupar_por])), 0

    dev_agg = todas_dev.groupby('N.º de venda').agg({col_valor: 'sum'}).reset_index()
    
    if 'N.º de venda' not in vendas_periodo.columns:
        return garantir_colunas_app(pd.DataFrame(columns=[agrupar_por])), 0

    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged[col_valor].notna()
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0)
    
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in df_merged.columns: df_merged[col_receita] = 0.0
    
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged[col_receita]
    
    res = df_merged.groupby(agrupar_por).agg(
        Vendas=('N.º de venda', 'count'),
        Dev_count=('tem_dev', 'sum'),
        Impacto_val=('valor_dev', 'sum')
    ).reset_index()
    
    # Mapear para nomes esperados pelo app.py
    res['Dev.'] = res['Dev_count']
    res['Dev'] = res['Dev_count'] # Manter compatibilidade interna se houver
    res['Impacto'] = (-res['Impacto_val']).round(2)
    res['Taxa'] = (res['Dev.'] / res['Vendas'] * 100).round(1)
    
    # Colunas adicionais para evitar erros no formatar_df_skus do app.py
    res = garantir_colunas_app(res)
    
    # Lógica de Risco simples para não vir zerado
    res['Risco'] = (res['Taxa'] * res['Vendas'] / 100).round(1)
    
    res = res.sort_values('Dev.', ascending=False)
    if limit:
        res = res.head(limit)
        
    return res, res['Dev.'].sum()

def simular_reducao(vendas, matriz, full, max_date, dias_atras, reducao_pct):
    """Simula redução de devoluções."""
    from .metricas import calcular_metricas
    m = calcular_metricas(vendas, matriz, full, max_date, dias_atras)
    
    impacto_atual = abs(m['perda_total'])
    economia = impacto_atual * (reducao_pct / 100)
    novo_impacto = impacto_atual - economia
    
    return {
        'impacto_atual': -impacto_atual,
        'economia': economia,
        'novo_impacto': -novo_impacto
    }
