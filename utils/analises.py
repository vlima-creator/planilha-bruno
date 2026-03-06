import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analisar_frete(vendas, matriz, full, max_date, dias_atras):
    """Análise de frete e forma de entrega."""
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    vendas_periodo = vendas.copy()
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    
    if vendas_periodo.empty:
        return pd.DataFrame()

    # Agrupar devoluções por pedido
    dev_agg = todas_dev.groupby('N.º de venda').agg({
        'Cancelamentos e reembolsos (BRL)': 'sum'
    }).reset_index()
    
    # Merge vendas com devoluções
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].notna()
    df_merged['valor_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].fillna(0)
    
    # Se valor_dev é 0 mas tem devolução, usar receita do produto
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged['Receita por produtos (BRL)']
    
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
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    vendas_periodo = vendas.copy()
    if 'Venda por publicidade' not in vendas_periodo.columns:
        return pd.DataFrame()
        
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    dev_agg = todas_dev.groupby('N.º de venda').agg({'Cancelamentos e reembolsos (BRL)': 'sum'}).reset_index()
    
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].notna()
    df_merged['valor_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].fillna(0)
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged['Receita por produtos (BRL)']
    
    df_merged['Tipo'] = df_merged['Venda por publicidade'].apply(lambda x: 'Com Publicidade' if str(x).lower() == 'sim' else 'Orgânico')
    
    res = df_merged.groupby('Tipo').agg(
        Vendas=('N.º de venda', 'count'),
        Devoluções=('tem_dev', 'sum'),
        Receita=('Receita por produtos (BRL)', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    res['Taxa (%)'] = (res['Devoluções'] / res['Vendas'] * 100).round(1)
    res['Receita (R$)'] = res['Receita'].round(2)
    res['Impacto (R$)'] = (-res['Impacto']).round(2)
    
    return res

def analisar_skus(vendas, matriz, full, max_date, dias_atras, limit=None, agrupar_por='SKU'):
    """Análise por SKU ou Produto."""
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    vendas_periodo = vendas.copy()
    if agrupar_por not in vendas_periodo.columns:
        # Fallback se a coluna não existir
        agrupar_por = 'SKU' if 'SKU' in vendas_periodo.columns else vendas_periodo.columns[0]
        
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    dev_agg = todas_dev.groupby('N.º de venda').agg({'Cancelamentos e reembolsos (BRL)': 'sum'}).reset_index()
    
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].notna()
    df_merged['valor_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].fillna(0)
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged['Receita por produtos (BRL)']
    
    res = df_merged.groupby(agrupar_por).agg(
        Vendas=('N.º de venda', 'count'),
        Dev=('tem_dev', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    res['Taxa'] = (res['Dev'] / res['Vendas'] * 100).round(1)
    res['Impacto'] = (-res['Impacto']).round(2)
    
    res = res.sort_values('Dev', ascending=False)
    if limit:
        res = res.head(limit)
        
    return res, res['Dev'].sum()

def simular_reducao(vendas, matriz, full, max_date, dias_atras, reducao_pct):
    """Simula redução de devoluções."""
    # Simplesmente calcula o impacto atual e aplica a redução
    # Para ser mais preciso, deveria vir das métricas calculadas
    # Mas como o app chama essa função, vamos replicar a lógica mínima
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
