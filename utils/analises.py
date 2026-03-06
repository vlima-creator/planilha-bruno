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
    
    if plataforma == 'Shopee' and 'N.º de pedido' in vendas_periodo.columns:
        # Renomear para padronizar com ML se necessário
        if 'N.º de venda' not in vendas_periodo.columns:
            vendas_periodo['N.º de venda'] = vendas_periodo['N.º de pedido']
            
        # Agrupar por pedido
        res = vendas_periodo.groupby('N.º de venda').agg({
            'Data': 'first',
            'Preço unitário (BRL)': 'sum',
            'Custo de frete a cargo do vendedor (BRL)': 'sum',
            'Comissão e outras tarifas (BRL)': 'sum',
            'Plataforma': 'first',
            'Anúncio': 'first',
            'SKU': 'first'
        }).reset_index()
        return res
    return vendas_periodo

def analisar_frete(vendas, matriz, full, max_date, dias_atras):
    """Análise de frete e custos logísticos."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    # Calcular custos de frete
    frete_total = vendas_periodo['Custo de frete a cargo do vendedor (BRL)'].sum()
    
    # Cruzar com devoluções para ver frete perdido
    df_merged = pd.merge(vendas_periodo, todas_dev[['N.º de venda', 'Cancelamentos e reembolsos (BRL)']], on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged['Cancelamentos e reembolsos (BRL)'].notna()
    
    frete_perdido = df_merged[df_merged['tem_dev']]['Custo de frete a cargo do vendedor (BRL)'].sum()
    
    return {
        'frete_total': frete_total,
        'frete_perdido': frete_perdido,
        'impacto_frete': (frete_perdido / frete_total * 100) if frete_total > 0 else 0
    }

def analisar_motivos(matriz, full):
    """Análise qualitativa de motivos de devolução."""
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    
    if 'Motivo' not in todas_dev.columns:
        return pd.DataFrame()
        
    res = todas_dev.groupby('Motivo').size().reset_index(name='Qtd')
    res = res.sort_values('Qtd', ascending=False)
    res['Pct'] = (res['Qtd'] / res['Qtd'].sum() * 100).round(1)
    
    return res

def analisar_ads(vendas, matriz, full, ads_data):
    """Análise de impacto de devoluções em campanhas de Ads."""
    # Placeholder para futura implementação
    return {
        'acos_real': 0.0,
        'roas_real': 0.0,
        'perda_investimento': 0.0
    }

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
    if todas_dev.empty or 'N.º de venda' not in todas_dev.columns:
        return garantir_colunas_app(pd.DataFrame()), 0
    
    # Remover duplicatas por pedido (evita contar o mesmo pedido múltiplas vezes)
    todas_dev = todas_dev.drop_duplicates(subset=['N.º de venda'])
    
    # CORRECAO: Filtrar devoluções com valor != 0 (não > 0) porque ML retorna valores negativos
    todas_dev_validas = todas_dev[todas_dev[col_valor] != 0].copy()
    
    # Merge vendas com devoluções
    df_merged = pd.merge(vendas_periodo, todas_dev_validas[['N.º de venda', col_valor]], on='N.º de venda', how='left')
    df_merged['tem_dev'] = df_merged[col_valor].notna()
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0).abs()
    
    # Adicionar coluna 'Dev' para compatibilidade com a linha 661 do app.py
    df_merged['Dev'] = df_merged['tem_dev'].astype(int)
    
    # Agrupar por SKU/Produto
    if agrupar_por in df_merged.columns:
        res = df_merged.groupby(agrupar_por).agg(
            Vendas=('N.º de venda', 'count'),
            Dev=('Dev', 'sum'),
            **{'Dev.': ('tem_dev', 'sum')}
        ).reset_index()
        
        res['Taxa'] = (res['Dev.'] / res['Vendas'] * 100).round(1)
        res['Impacto'] = df_merged.groupby(agrupar_por)['valor_dev'].sum().values
        res['Reemb.'] = df_merged.groupby(agrupar_por)[col_valor].sum().abs().values
        res['Custo Dev.'] = 0.0  # Placeholder
        res['Risco'] = (res['Impacto'] / res['Vendas']).round(2)
        
        # Classificação ABC por impacto
        if len(res) > 0:
            impacto_total = res['Impacto'].sum()
            if impacto_total > 0:
                res['Impacto_Acum'] = res['Impacto'].cumsum()
                res['Impacto_Pct'] = (res['Impacto_Acum'] / impacto_total * 100).round(1)
                res['Classe'] = res['Impacto_Pct'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                res = res.drop(['Impacto_Acum', 'Impacto_Pct'], axis=1)
            else:
                res['Classe'] = 'C'
        
        res = res.sort_values('Impacto', ascending=False)
        
        if limit:
            res = res.head(limit)
        
        # Total de devoluções únicas (baseado na soma da coluna Dev do agrupamento)
        total_dev = res['Dev'].sum()
        
        return garantir_colunas_app(res), total_dev
    
    return garantir_colunas_app(pd.DataFrame()), 0

def simular_reducao(skus_data, percentual_reducao):
    """Simula redução de devoluções."""
    if skus_data.empty:
        return pd.DataFrame()
    
    resultado = skus_data.copy()
    
    if 'Dev.' in resultado.columns and 'Impacto' in resultado.columns:
        # Reduzir devoluções pelo percentual
        resultado['Dev._Simulado'] = (resultado['Dev.'] * (1 - percentual_reducao / 100)).round(0)
        resultado['Impacto_Simulado'] = (resultado['Impacto'] * (1 - percentual_reducao / 100)).round(2)
        resultado['Economia'] = (resultado['Impacto'] - resultado['Impacto_Simulado']).round(2)
        
    return resultado
