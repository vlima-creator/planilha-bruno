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
    
    col_frete = 'Custo de frete a cargo do vendedor (BRL)'
    col_valor_dev = 'Cancelamentos e reembolsos (BRL)'
    col_entrega = 'Forma de entrega'
    
    # Garantir colunas básicas
    if col_frete not in vendas_periodo.columns:
        vendas_periodo[col_frete] = 0.0
    
    # Tratar Forma de entrega em branco
    if col_entrega not in vendas_periodo.columns:
        vendas_periodo[col_entrega] = 'Não informado'
    else:
        vendas_periodo[col_entrega] = vendas_periodo[col_entrega].fillna('Não informado').replace('', 'Não informado').replace(' ', 'Não informado')
        
    if col_valor_dev not in todas_dev.columns:
        todas_dev[col_valor_dev] = 0.0
        
    # Identificar cancelamentos (vendas que têm status de cancelado no relatório de vendas)
    if 'is_cancelado' not in vendas_periodo.columns:
        if 'Estado' in vendas_periodo.columns:
            vendas_periodo['is_cancelado'] = vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelada', na=False)
        else:
            vendas_periodo['is_cancelado'] = False

    # Devoluções: Vendas que aparecem no relatório de devoluções e NÃO são cancelamentos
    # Deduplicação de devoluções antes do merge
    todas_dev_unicas = todas_dev.drop_duplicates(subset=['N.º de venda']).copy()
    
    # Cruzar vendas com devoluções únicas
    df_merged = pd.merge(vendas_periodo, todas_dev_unicas[['N.º de venda', col_valor_dev]], on='N.º de venda', how='left', suffixes=('', '_dev'))
    
    # Identificar coluna de valor após merge
    col_valor_final = col_valor_dev if col_valor_dev in df_merged.columns else f"{col_valor_dev}_dev"
    
    # Uma venda é considerada devolução se estiver no relatório de devoluções E não for cancelada
    df_merged['no_relatorio_dev'] = df_merged[col_valor_final].notna()
    df_merged['is_devolucao'] = df_merged['no_relatorio_dev'] & (~df_merged['is_cancelado'])
    df_merged['valor_dev'] = df_merged[col_valor_final].fillna(0).abs()
    
    # Agrupar por Forma de Entrega
    res = df_merged.groupby(col_entrega).agg(
        Vendas=('N.º de venda', 'count'),
        Cancelados=('is_cancelado', 'sum'),
        Devoluções=('is_devolucao', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    # Renomear coluna de agrupamento para 'Forma de Entrega'
    res = res.rename(columns={col_entrega: 'Forma de Entrega'})
    
    res['Taxa (%)'] = (res['Devoluções'] / res['Vendas'] * 100).round(1).fillna(0)
    
    # Renomear para o que o app.py espera na exibição
    res = res.rename(columns={'Impacto': 'Impacto (R$)'})
    
    # Garantir ordem das colunas para o display
    cols_ordem = ['Forma de Entrega', 'Vendas', 'Cancelados', 'Devoluções', 'Taxa (%)', 'Impacto (R$)']
    for col in cols_ordem:
        if col not in res.columns:
            res[col] = 0
            
    return res[cols_ordem]

def analisar_motivos(vendas, matriz, full, max_date, dias_atras):
    """Análise qualitativa de motivos de devolução com suporte a SKU e Produto."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    # ML usa 'Motivo', Shopee usa 'Motivo do resultado' (mapeado no parser)
    col_motivo = 'Motivo' if 'Motivo' in todas_dev.columns else ('Motivo do resultado' if 'Motivo do resultado' in todas_dev.columns else None)
    
    if not col_motivo or todas_dev.empty:
        return pd.DataFrame()
        
    # Tentar trazer SKU e Produto das vendas para as devoluções
    if 'N.º de venda' in todas_dev.columns and 'N.º de venda' in vendas_periodo.columns:
        cols_vendas = ['N.º de venda']
        if 'SKU' in vendas_periodo.columns: cols_vendas.append('SKU')
        if 'Título do anúncio' in vendas_periodo.columns: cols_vendas.append('Título do anúncio')
        
        vendas_subset = vendas_periodo[cols_vendas].drop_duplicates(subset=['N.º de venda'])
        todas_dev = pd.merge(todas_dev, vendas_subset, on='N.º de venda', how='left')

    # Garantir que as colunas existam para não quebrar o agrupamento posterior
    if 'SKU' not in todas_dev.columns: todas_dev['SKU'] = 'Não informado'
    if 'Título do anúncio' not in todas_dev.columns: todas_dev['Título do anúncio'] = 'Não informado'
    
    # Renomear coluna de motivo para padrão 'Motivo'
    if col_motivo != 'Motivo':
        todas_dev = todas_dev.rename(columns={col_motivo: 'Motivo'})
    
    # Agrupar mantendo SKU e Produto se possível (usando o primeiro encontrado para cada motivo)
    # Mas o ideal é retornar os dados brutos de devolução para o app filtrar
    return todas_dev

def analisar_ads(vendas, matriz, full, max_date, dias_atras):
    """Análise de impacto de devoluções em campanhas de Ads."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    col_ads = 'Venda por publicidade'
    col_valor_dev = 'Cancelamentos e reembolsos (BRL)'
    col_receita = 'Preço unitário (BRL)'
    
    if col_ads not in vendas_periodo.columns:
        vendas_periodo[col_ads] = 'Não'
    if col_receita not in vendas_periodo.columns:
        vendas_periodo[col_receita] = 0.0
        
    # Cruzar com devoluções únicas
    todas_dev_unicas = todas_dev.drop_duplicates(subset=['N.º de venda']).copy()
    df_merged = pd.merge(vendas_periodo, todas_dev_unicas[['N.º de venda', col_valor_dev]], on='N.º de venda', how='left', suffixes=('', '_dev'))
    col_valor_final = col_valor_dev if col_valor_dev in df_merged.columns else f"{col_valor_dev}_dev"
    
    # Identificar cancelamentos
    if 'is_cancelado' not in df_merged.columns:
        if 'Estado' in df_merged.columns:
            df_merged['is_cancelado'] = df_merged['Estado'].astype(str).str.lower().str.contains('cancelada', na=False)
        else:
            df_merged['is_cancelado'] = False

    df_merged['no_relatorio_dev'] = df_merged[col_valor_final].notna()
    df_merged['is_devolucao'] = df_merged['no_relatorio_dev'] & (~df_merged['is_cancelado'])
    df_merged['valor_dev'] = df_merged[col_valor_final].fillna(0).abs()
    df_merged['Tipo'] = df_merged[col_ads].apply(lambda x: 'Com Publicidade' if x == 'Sim' else 'Orgânico')
    
    # Agrupar por Tipo (Ads vs Orgânico)
    res = df_merged.groupby('Tipo').agg(
        Vendas=('N.º de venda', 'count'),
        Cancelados=('is_cancelado', 'sum'),
        Devoluções=('is_devolucao', 'sum'),
        Impacto=('valor_dev', 'sum'),
        Receita=(col_receita, 'sum')
    ).reset_index()
    
    res['Taxa (%)'] = (res['Devoluções'] / res['Vendas'] * 100).round(1).fillna(0)
    res = res.rename(columns={'Impacto': 'Impacto (R$)', 'Receita': 'Receita (R$)'})
    
    return res

def analisar_skus(vendas, matriz, full, max_date, dias_atras, limit=None, agrupar_por='SKU'):
    """Análise por SKU ou Produto."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    if agrupar_por not in vendas_periodo.columns:
        agrupar_por = 'SKU' if 'SKU' in vendas_periodo.columns else (vendas_periodo.columns[0] if not vendas_periodo.empty else 'SKU')
        
    col_valor = 'Cancelamentos e reembolsos (BRL)'
    if col_valor not in todas_dev.columns: 
        todas_dev[col_valor] = 0.0
    
    def garantir_colunas_app(df):
        cols_esperadas = {
            'Vendas': 0, 'Dev.': 0, 'Taxa': 0.0, 'Impacto': 0.0, 'Reemb.': 0.0,
            'Custo Dev.': 0.0, 'Risco': 0.0, 'Classe': 'C', 'Dev': 0
        }
        for col, val in cols_esperadas.items():
            if col not in df.columns:
                df[col] = val
        return df

    if todas_dev.empty or 'N.º de venda' not in todas_dev.columns:
        return garantir_colunas_app(pd.DataFrame()), 0
    
    # Identificar cancelamentos no relatório de vendas
    if 'is_cancelado' not in vendas_periodo.columns:
        if 'Estado' in vendas_periodo.columns:
            vendas_periodo['is_cancelado'] = vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelada', na=False)
        else:
            vendas_periodo['is_cancelado'] = False

    todas_dev_unicas = todas_dev.drop_duplicates(subset=['N.º de venda']).copy()
    
    df_merged = pd.merge(vendas_periodo, todas_dev_unicas[['N.º de venda', col_valor]], on='N.º de venda', how='left', suffixes=('', '_dev'))
    col_valor_final = col_valor if col_valor in df_merged.columns else f"{col_valor}_dev"
    
    df_merged['no_relatorio_dev'] = df_merged[col_valor_final].notna()
    df_merged['is_devolucao'] = df_merged['no_relatorio_dev'] & (~df_merged['is_cancelado'])
    df_merged['valor_dev'] = df_merged[col_valor_final].fillna(0).abs()
    df_merged['Dev'] = df_merged['is_devolucao'].astype(int)
    
    if agrupar_por in df_merged.columns:
        res = df_merged.groupby(agrupar_por).agg(
            Vendas=('N.º de venda', 'count'),
            Dev=('Dev', 'sum'),
            **{'Dev.': ('is_devolucao', 'sum')}
        ).reset_index()
        
        impacto_por_sku = df_merged.groupby(agrupar_por)['valor_dev'].sum()
        reemb_por_sku = df_merged.groupby(agrupar_por)[col_valor_final].sum().abs()
        
        res['Impacto'] = res[agrupar_por].map(impacto_por_sku)
        res['Reemb.'] = res[agrupar_por].map(reemb_por_sku)
        res['Taxa'] = (res['Dev.'] / res['Vendas'] * 100).round(1)
        res['Custo Dev.'] = 0.0
        res['Risco'] = (res['Impacto'] / res['Vendas']).round(2)
        
        if len(res) > 0:
            res = res.sort_values('Impacto', ascending=False)
            impacto_total = res['Impacto'].sum()
            if impacto_total > 0:
                res['Impacto_Acum'] = res['Impacto'].cumsum()
                res['Impacto_Pct'] = (res['Impacto_Acum'] / impacto_total * 100)
                res['Classe'] = res['Impacto_Pct'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                res = res.drop(['Impacto_Acum', 'Impacto_Pct'], axis=1)
            else:
                res['Classe'] = 'C'
        
        if limit:
            res = res.head(limit)
        
        total_dev = res['Dev'].sum()
        return garantir_colunas_app(res), total_dev
    
    return garantir_colunas_app(pd.DataFrame()), 0

def simular_reducao(skus_data, percentual_reducao):
    """Simula redução de devoluções."""
    if skus_data.empty:
        return pd.DataFrame()
    resultado = skus_data.copy()
    if 'Dev.' in resultado.columns and 'Impacto' in resultado.columns:
        resultado['Dev._Simulado'] = (resultado['Dev.'] * (1 - percentual_reducao / 100)).round(0)
        resultado['Impacto_Simulado'] = (resultado['Impacto'] * (1 - percentual_reducao / 100)).round(2)
        resultado['Economia'] = (resultado['Impacto'] - resultado['Impacto_Simulado']).round(2)
    return resultado
