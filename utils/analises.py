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

def _agrupar_vendas_por_pedido(vendas_periodo):
    """
    Para Shopee: agrupa linhas por pedido único para evitar duplicatas por múltiplos itens.
    Para ML: retorna o DataFrame original.
    """
    plataforma = vendas_periodo['Plataforma'].iloc[0] if not vendas_periodo.empty and 'Plataforma' in vendas_periodo.columns else 'ML'
    
    if plataforma == 'Shopee' and 'N.º de venda' in vendas_periodo.columns:
        # Agrupar por pedido: somar receita de produtos, usar primeiro valor para demais colunas
        agg_dict = {}
        if 'Receita por produtos (BRL)' in vendas_periodo.columns:
            agg_dict['Receita por produtos (BRL)'] = 'sum'
        if 'Receita por envio (BRL)' in vendas_periodo.columns:
            agg_dict['Receita por envio (BRL)'] = 'first'
        if 'Estado' in vendas_periodo.columns:
            agg_dict['Estado'] = 'first'
        if 'Forma de entrega' in vendas_periodo.columns:
            agg_dict['Forma de entrega'] = 'first'
        if 'Venda por publicidade' in vendas_periodo.columns:
            agg_dict['Venda por publicidade'] = 'first'
        if 'SKU' in vendas_periodo.columns:
            agg_dict['SKU'] = 'first'
        if 'Título do anúncio' in vendas_periodo.columns:
            agg_dict['Título do anúncio'] = 'first'
        if 'Plataforma' in vendas_periodo.columns:
            agg_dict['Plataforma'] = 'first'
        if 'Data da venda' in vendas_periodo.columns:
            agg_dict['Data da venda'] = 'first'
        
        if agg_dict:
            return vendas_periodo.groupby('N.º de venda').agg(agg_dict).reset_index()
    
    return vendas_periodo

def analisar_frete(vendas, matriz, full, max_date, dias_atras):
    """Análise de frete e forma de entrega."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    if vendas_periodo.empty:
        return pd.DataFrame()

    # Para Shopee: agrupar por pedido único antes da análise
    vendas_periodo = _agrupar_vendas_por_pedido(vendas_periodo)

    # Agrupar devoluções por pedido (sem duplicatas), capturando forma de entrega se existir
    col_valor = 'Cancelamentos e reembolsos (BRL)'
    if col_valor not in todas_dev.columns: todas_dev[col_valor] = 0.0
    
    agg_dict = {col_valor: 'max'}  # 'max' em vez de 'sum' para evitar duplicatas no relatório de devoluções
    if 'Forma de entrega' in todas_dev.columns:
        agg_dict['Forma de entrega'] = 'first'
    
    dev_agg = todas_dev.groupby('N.º de venda').agg(agg_dict).reset_index()
    
    # Merge vendas com devoluções
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left', suffixes=('', '_dev'))
    
    # Identificar Cancelamentos
    df_merged['is_cancelada'] = False
    if 'Estado' in df_merged.columns:
        df_merged['is_cancelada'] = df_merged['Estado'].astype(str).str.lower().str.contains('cancelad|anulad', na=False)
    
    # Se a forma de entrega não estiver na venda mas estiver na devolução, preencher
    if 'Forma de entrega_dev' in df_merged.columns:
        df_merged['Forma de entrega'] = df_merged['Forma de entrega'].fillna(df_merged['Forma de entrega_dev'])
    
    # Garantir que col_valor existe após o merge
    if col_valor not in df_merged.columns:
        df_merged[col_valor] = 0.0
    
    # Uma devolução só conta se a venda NÃO foi cancelada
    df_merged['tem_dev'] = (df_merged[col_valor].notna()) & (~df_merged['is_cancelada'])
        
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
        Vendas=('N.º de venda', 'nunique'),
        Cancelados=('is_cancelada', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    # Contar devoluções por forma de entrega (apenas pedidos únicos com devolução)
    dev_por_forma = {}
    for forma in df_merged[col_forma].unique():
        df_forma = df_merged[df_merged[col_forma] == forma]
        pedidos_com_dev = df_forma[df_forma['tem_dev']]['N.º de venda'].nunique()
        dev_por_forma[forma] = pedidos_com_dev
    
    res['Devoluções'] = res[col_forma].map(dev_por_forma).fillna(0).astype(int)
    
    # Vendas Líquidas (Vendas Totais - Cancelados - Devoluções)
    res['Vendas Líquidas'] = res['Vendas'] - res['Cancelados'] - res['Devoluções']
    
    # Taxa de devolução: (Devoluções / (Vendas - Cancelados)) * 100
    res['Vendas Enviadas'] = res['Vendas'] - res['Cancelados']
    res['Taxa (%)'] = (res['Devoluções'] / res['Vendas Enviadas'] * 100).fillna(0).round(1)
    res['Impacto (R$)'] = res['Impacto'].round(2)
    res = res.rename(columns={col_forma: 'Forma de Entrega'})
    
    # Selecionar apenas as colunas relevantes para exibição
    res = res[['Forma de Entrega', 'Vendas', 'Cancelados', 'Devoluções', 'Vendas Líquidas', 'Taxa (%)', 'Impacto (R$)']]
    
    return res

def analisar_motivos(vendas=None, matriz=None, full=None, max_date=None, dias_atras=0):
    """Análise de motivos de devolução."""
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    
    if todas_dev.empty:
        return pd.DataFrame()
    
    # Remover duplicatas por pedido para evitar contagem dupla
    if 'N.º de venda' in todas_dev.columns:
        todas_dev = todas_dev.drop_duplicates(subset=['N.º de venda'])
        
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
    
    # Para Shopee: agrupar por pedido único
    vendas_periodo = _agrupar_vendas_por_pedido(vendas_periodo)
        
    col_valor = 'Cancelamentos e reembolsos (BRL)'
    if col_valor not in todas_dev.columns: todas_dev[col_valor] = 0.0
    
    # Usar 'max' para evitar duplicatas no relatório de devoluções
    dev_agg = todas_dev.groupby('N.º de venda').agg({col_valor: 'max'}).reset_index()
    
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    # Identificar cancelamentos
    df_merged['is_cancelada'] = False
    if 'Estado' in df_merged.columns:
        df_merged['is_cancelada'] = df_merged['Estado'].astype(str).str.lower().str.contains('cancelad|anulad', na=False)
    
    # Garantir que col_valor existe após o merge
    if col_valor not in df_merged.columns:
        df_merged[col_valor] = 0.0
        
    df_merged['tem_dev'] = (df_merged[col_valor].notna()) & (~df_merged['is_cancelada'])
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
    res['Impacto (R$)'] = res['Impacto'].round(2)
    
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

    # Para devoluções: usar 'max' para evitar duplicatas por múltiplos itens no mesmo pedido
    # Verificar se col_valor existe em todas_dev antes de agrupar
    if col_valor not in todas_dev.columns:
        # Se não houver devoluções, retornar vendas sem devoluções
        if not vendas_periodo.empty and agrupar_por in vendas_periodo.columns:
            res = vendas_periodo.groupby(agrupar_por).agg(
                Vendas=('N.º de venda', 'count')
            ).reset_index()
            res = garantir_colunas_app(res)
            res = res.sort_values('Vendas', ascending=False)
            if limit: res = res.head(limit)
            return res, 0
        return garantir_colunas_app(pd.DataFrame(columns=[agrupar_por])), 0
    
    dev_agg = todas_dev.groupby('N.º de venda').agg({col_valor: 'max'}).reset_index()
    
    if 'N.º de venda' not in vendas_periodo.columns:
        return garantir_colunas_app(pd.DataFrame(columns=[agrupar_por])), 0

    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='left')
    # Identificar cancelamentos
    df_merged['is_cancelada'] = False
    if 'Estado' in df_merged.columns:
        df_merged['is_cancelada'] = df_merged['Estado'].astype(str).str.lower().str.contains('cancelad|anulad', na=False)
    
    # Garantir que col_valor existe após o merge
    if col_valor not in df_merged.columns:
        df_merged[col_valor] = 0.0
        
    df_merged['tem_dev'] = (df_merged[col_valor].notna()) & (~df_merged['is_cancelada'])
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
    res['Impacto'] = res['Impacto_val'].round(2)
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
