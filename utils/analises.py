import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def preparar_dados_analise(vendas, matriz, full):
    """Função auxiliar para preparar e validar dados antes da análise."""
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    vendas_periodo = vendas.copy()
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    
    # Padronizar N.º de venda para string e remover espaços para garantir o merge
    if 'N.º de venda' in vendas_periodo.columns:
        vendas_periodo['N.º de venda'] = vendas_periodo['N.º de venda'].astype(str).str.strip()
    if 'N.º de venda' in todas_dev.columns:
        todas_dev['N.º de venda'] = todas_dev['N.º de venda'].astype(str).str.strip()

    return vendas_periodo, todas_dev

def analisar_frete(vendas, matriz, full, max_date, dias_atras):
    """Análise de frete e forma de entrega alinhada com as métricas globais."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    col_frete = 'Custo de frete a cargo do vendedor (BRL)'
    col_valor_dev = 'Cancelamentos e reembolsos (BRL)'
    col_entrega = 'Forma de entrega'
    
    # Garantir colunas básicas
    if col_frete not in vendas_periodo.columns:
        vendas_periodo[col_frete] = 0.0
    
    # Tratar Forma de entrega
    if col_entrega not in vendas_periodo.columns:
        vendas_periodo[col_entrega] = 'Não informado'
    else:
        vendas_periodo[col_entrega] = vendas_periodo[col_entrega].fillna('Não informado').replace('', 'Não informado').replace(' ', 'Não informado')
        
    # Identificar cancelamentos no relatório de vendas
    if 'is_cancelado' not in vendas_periodo.columns:
        if 'Estado' in vendas_periodo.columns:
            vendas_periodo['is_cancelado'] = vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelada', na=False)
        else:
            vendas_periodo['is_cancelado'] = False

    # Criar um set de IDs de venda que estão no relatório de devoluções para busca rápida
    dev_ids = set()
    if not todas_dev.empty and 'N.º de venda' in todas_dev.columns:
        dev_ids = set(todas_dev['N.º de venda'].unique())

    # Uma venda é devolução se: (ID está no relatório de devoluções) E (NÃO é cancelada no relatório de vendas)
    vendas_periodo['is_devolucao'] = vendas_periodo.apply(
        lambda x: (x['N.º de venda'] in dev_ids) and (not x['is_cancelado']), axis=1
    )
    
    # Para o impacto financeiro, precisamos do valor do reembolso
    # Vamos criar um mapeamento de ID de venda -> Valor de reembolso (soma se houver múltiplos itens)
    impacto_map = {}
    if not todas_dev.empty and 'N.º de venda' in todas_dev.columns:
        val_col = col_valor_dev if col_valor_dev in todas_dev.columns else (todas_dev.columns[0]) # fallback
        # Garantir que é numérico e absoluto
        todas_dev['valor_temp'] = pd.to_numeric(todas_dev[val_col], errors='coerce').fillna(0).abs()
        impacto_map = todas_dev.groupby('N.º de venda')['valor_temp'].sum().to_dict()

    vendas_periodo['valor_dev'] = vendas_periodo.apply(
        lambda x: impacto_map.get(x['N.º de venda'], 0.0) if x['is_devolucao'] else 0.0, axis=1
    )
    
    # Agrupar por Forma de Entrega
    res = vendas_periodo.groupby(col_entrega).agg(
        Vendas=('N.º de venda', 'count'),
        Cancelados=('is_cancelado', 'sum'),
        Devoluções=('is_devolucao', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    res = res.rename(columns={col_entrega: 'Forma de Entrega', 'Impacto': 'Impacto (R$)'})
    
    # Taxa de devolução baseada em vendas enviadas (Vendas - Cancelados)
    res['Taxa (%)'] = res.apply(
        lambda x: (x['Devoluções'] / (x['Vendas'] - x['Cancelados']) * 100) if (x['Vendas'] - x['Cancelados']) > 0 else 0,
        axis=1
    ).round(1)
    
    cols_ordem = ['Forma de Entrega', 'Vendas', 'Cancelados', 'Devoluções', 'Taxa (%)', 'Impacto (R$)']
    return res[cols_ordem]

def analisar_motivos(vendas, matriz, full, max_date, dias_atras):
    """Análise qualitativa de motivos de devolução."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    col_motivo = None
    # Priorizar 'Motivo do resultado' pois contém o motivo real preenchido pelo vendedor/comprador
    # 'Estado' geralmente contém o status logístico da devolução
    for col in ['Motivo do resultado', 'Motivo', 'Resultado', 'Estado']:
        if col in todas_dev.columns:
            # Verificar se a coluna não está vazia ou apenas com espaços
            if todas_dev[col].astype(str).str.strip().replace('', np.nan).notna().any():
                col_motivo = col
                break
    
    # Se não encontrou nenhuma com dados, usa a primeira disponível
    if not col_motivo:
        for col in ['Motivo do resultado', 'Motivo', 'Resultado', 'Estado']:
            if col in todas_dev.columns:
                col_motivo = col
                break
    
    if not col_motivo or todas_dev.empty:
        return pd.DataFrame()
        
    if col_motivo != 'Motivo':
        if 'Motivo' in todas_dev.columns:
            todas_dev = todas_dev.rename(columns={'Motivo': 'Motivo Original'})
        todas_dev = todas_dev.rename(columns={col_motivo: 'Motivo'})

    # Cruzar com SKUs das vendas
    if 'N.º de venda' in todas_dev.columns and 'N.º de venda' in vendas_periodo.columns:
        vendas_subset = vendas_periodo[['N.º de venda', 'SKU', 'Título do anúncio']].drop_duplicates(subset=['N.º de venda'])
        todas_dev = pd.merge(todas_dev, vendas_subset, on='N.º de venda', how='left')

    for col in ['SKU', 'Título do anúncio', 'Motivo']:
        if col not in todas_dev.columns: todas_dev[col] = 'Não informado'
        else: todas_dev[col] = todas_dev[col].fillna('Não informado').replace(r'^\s*$', 'Não informado', regex=True)
    
    return todas_dev

def analisar_ads(vendas, matriz, full, max_date, dias_atras):
    """Análise de Ads alinhada com métricas globais."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    col_ads = 'Venda por publicidade'
    # Tentar encontrar a coluna de receita correta (ML ou Shopee)
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in vendas_periodo.columns:
        col_receita = 'Subtotal do produto' # Shopee fallback
    if col_receita not in vendas_periodo.columns:
        col_receita = 'Preço unitário (BRL)' # Outro fallback
    
    if col_ads not in vendas_periodo.columns: vendas_periodo[col_ads] = 'Não'
    
    # Garantir que a coluna de receita seja numérica
    if col_receita in vendas_periodo.columns:
        vendas_periodo[col_receita] = pd.to_numeric(vendas_periodo[col_receita], errors='coerce').fillna(0.0)
    else:
        vendas_periodo[col_receita] = 0.0
        
    dev_ids = set(todas_dev['N.º de venda'].unique()) if not todas_dev.empty else set()
    
    if 'is_cancelado' not in vendas_periodo.columns:
        vendas_periodo['is_cancelado'] = vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelada', na=False) if 'Estado' in vendas_periodo.columns else False

    vendas_periodo['is_devolucao'] = vendas_periodo.apply(lambda x: (x['N.º de venda'] in dev_ids) and (not x['is_cancelado']), axis=1)
    
    impacto_map = {}
    if not todas_dev.empty:
        # Priorizar coluna de reembolso já identificada como correta
        val_col = 'Cancelamentos e reembolsos (BRL)'
        if val_col not in todas_dev.columns:
            # Fallback para Shopee ou outras colunas de valor
            val_col = 'Quantia total de reembolsos' if 'Quantia total de reembolsos' in todas_dev.columns else todas_dev.columns[0]
            
        todas_dev['valor_temp'] = pd.to_numeric(todas_dev[val_col], errors='coerce').fillna(0).abs()
        impacto_map = todas_dev.groupby('N.º de venda')['valor_temp'].sum().to_dict()

    vendas_periodo['valor_dev'] = vendas_periodo.apply(lambda x: impacto_map.get(x['N.º de venda'], 0.0) if x['is_devolucao'] else 0.0, axis=1)
    
    # Criar coluna de receita efetiva (apenas para vendas não canceladas)
    vendas_periodo['receita_efetiva'] = vendas_periodo.apply(lambda x: x[col_receita] if not x['is_cancelado'] else 0.0, axis=1)
    
    vendas_periodo['Tipo'] = vendas_periodo[col_ads].apply(lambda x: 'Com Publicidade' if x == 'Sim' else 'Orgânico')
    
    res = vendas_periodo.groupby('Tipo').agg(
        Vendas=('N.º de venda', 'count'),
        Cancelados=('is_cancelado', 'sum'),
        Devoluções=('is_devolucao', 'sum'),
        Impacto=('valor_dev', 'sum'),
        Receita=('receita_efetiva', 'sum')
    ).reset_index()
    
    res['Taxa (%)'] = res.apply(lambda x: (x['Devoluções'] / (x['Vendas'] - x['Cancelados']) * 100) if (x['Vendas'] - x['Cancelados']) > 0 else 0, axis=1).round(1)
    return res.rename(columns={'Impacto': 'Impacto (R$)', 'Receita': 'Receita (R$)'})

def analisar_skus(vendas, matriz, full, max_date, dias_atras, limit=None, agrupar_por='SKU'):
    """Análise por SKU alinhada com métricas globais."""
    vendas_periodo, todas_dev = preparar_dados_analise(vendas, matriz, full)
    
    if agrupar_por not in vendas_periodo.columns:
        agrupar_por = 'SKU' if 'SKU' in vendas_periodo.columns else (vendas_periodo.columns[0] if not vendas_periodo.empty else 'SKU')
    
    dev_ids = set(todas_dev['N.º de venda'].unique()) if not todas_dev.empty else set()
    
    if 'is_cancelado' not in vendas_periodo.columns:
        vendas_periodo['is_cancelado'] = vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelada', na=False) if 'Estado' in vendas_periodo.columns else False

    vendas_periodo['is_devolucao'] = vendas_periodo.apply(lambda x: (x['N.º de venda'] in dev_ids) and (not x['is_cancelado']), axis=1)
    
    impacto_map = {}
    if not todas_dev.empty:
        val_col = 'Cancelamentos e reembolsos (BRL)' if 'Cancelamentos e reembolsos (BRL)' in todas_dev.columns else todas_dev.columns[0]
        todas_dev['valor_temp'] = pd.to_numeric(todas_dev[val_col], errors='coerce').fillna(0).abs()
        impacto_map = todas_dev.groupby('N.º de venda')['valor_temp'].sum().to_dict()

    vendas_periodo['valor_dev'] = vendas_periodo.apply(lambda x: impacto_map.get(x['N.º de venda'], 0.0) if x['is_devolucao'] else 0.0, axis=1)
    
    res = vendas_periodo.groupby(agrupar_por).agg(
        Vendas=('N.º de venda', 'count'),
        Cancelados=('is_cancelado', 'sum'),
        Devoluções=('is_devolucao', 'sum'),
        Impacto=('valor_dev', 'sum')
    ).reset_index()
    
    res['Taxa'] = res.apply(lambda x: (x['Devoluções'] / (x['Vendas'] - x['Cancelados']) * 100) if (x['Vendas'] - x['Cancelados']) > 0 else 0, axis=1).round(1)
    res['Risco'] = (res['Impacto'] / res['Vendas']).round(2)
    res['Dev'] = res['Devoluções']
    res['Dev.'] = res['Devoluções']
    res['Reemb.'] = res['Impacto']
    res['Custo Dev.'] = 0.0
    
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
    
    if limit: res = res.head(limit)
    return res, res['Devoluções'].sum()

def simular_reducao(skus_data, percentual_reducao):
    """Simula redução de devoluções."""
    if skus_data.empty: return pd.DataFrame()
    resultado = skus_data.copy()
    if 'Dev.' in resultado.columns and 'Impacto' in resultado.columns:
        resultado['Dev._Simulado'] = (resultado['Dev.'] * (1 - percentual_reducao / 100)).round(0)
        resultado['Impacto_Simulado'] = (resultado['Impacto'] * (1 - percentual_reducao / 100)).round(2)
        resultado['Economia'] = (resultado['Impacto'] - resultado['Impacto_Simulado']).round(2)
    return resultado
