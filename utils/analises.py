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
    
    # CORRECAO: O Mercado Livre retorna valores NEGATIVOS para devoluções e cancelamentos.
    # Filtrar apenas devoluções com valor != 0 (devoluções reais)
    # Isso evita contar pedidos que aparecem no arquivo de devoluções mas não foram realmente devolvidos
    todas_dev = todas_dev[todas_dev[col_valor] != 0]
    
    agg_dict = {col_valor: 'max'}  # 'max' em vez de 'sum' para evitar duplicatas no relatório de devoluções
    if 'Forma de entrega' in todas_dev.columns:
        agg_dict['Forma de entrega'] = 'first'
    
    dev_agg = todas_dev.groupby('N.º de venda').agg(agg_dict).reset_index()
    
    # Merge vendas com devoluções
    # CORREÇÃO: Usar right join para garantir que TODAS as devoluções reais sejam incluídas,
    # mesmo que o pedido não esteja no arquivo de vendas (pode ocorrer por janelas de tempo diferentes)
    df_merged = pd.merge(vendas_periodo, dev_agg, on='N.º de venda', how='outer', suffixes=('', '_dev'))
    
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
    
    # Uma devolução só conta se a venda NÃO foi cancelada E se o valor de reembolso é != 0
    # (O filtro já foi aplicado em todas_dev, então se col_valor != 0, é uma devolução real)
    # Usar abs() porque o ML retorna valores negativos
    df_merged['tem_dev'] = (df_merged[col_valor] != 0) & (~df_merged['is_cancelada'])
        
    # Converter valores negativos para positivos (padrão do ML)
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0).abs()
    
    # Se valor_dev é 0 mas tem devolução (pode ocorrer se o filtro falhar ou em casos específicos), usar receita do produto
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in df_merged.columns: df_merged[col_receita] = 0.0
    
    # Garantir que valor_dev é sempre positivo
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged[col_receita].abs()
    
    # Agrupar por forma de entrega
    col_forma = 'Forma de entrega' if 'Forma de entrega' in df_merged.columns else None
    if not col_forma:
        return pd.DataFrame()
        
    # CORREÇÃO: Se a forma de entrega for nula tanto na venda quanto na devolução, 
    # mas o pedido for uma devolução real, vamos tentar identificar o canal (Matriz/Full)
    # para não perder a informação na tabela.
    df_merged[col_forma] = df_merged[col_forma].fillna(df_merged['Forma de entrega_dev'])
    
    # Limpar espaços em branco nas formas de entrega ANTES de agrupar
    if df_merged[col_forma].dtype == 'object':
        df_merged[col_forma] = df_merged[col_forma].str.strip()
    
    df_merged[col_forma] = df_merged[col_forma].fillna('Outros').replace(['', ' '], 'Outros')
    
    # Agrupar métricas principais
    res = df_merged.groupby(col_forma).agg(
        Vendas=('N.º de venda', 'nunique'),
        Cancelados=('is_cancelada', 'sum'),
        Impacto=('valor_dev', 'sum'),
        Devoluções=('tem_dev', 'sum')
    ).reset_index()
    
    # CORREÇÃO: Se o Vendas for menor que Devoluções (pode ocorrer devido ao outer join),
    # ajustar Vendas para ser no mínimo Devoluções + Cancelados para manter a lógica da tabela
    res['Vendas'] = res[['Vendas', 'Devoluções', 'Cancelados']].apply(lambda x: max(x['Vendas'], x['Devoluções'] + x['Cancelados']), axis=1)
    
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
        
    # CORRECAO: Verificar se valor é != 0 (não apenas notna) porque ML retorna valores negativos
    df_merged['tem_dev'] = (df_merged[col_valor] != 0) & (~df_merged['is_cancelada'])
    # Converter para positivo
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0).abs()
    
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in df_merged.columns: df_merged[col_receita] = 0.0
    
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged[col_receita].abs()
    
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
    if todas_dev.empty or 'N.º de venda' not in todas_dev.columns:
        return garantir_colunas_app(pd.DataFrame())
    
    # Remover duplicatas por pedido (evita contar o mesmo pedido múltiplas vezes)
    todas_dev = todas_dev.drop_duplicates(subset=['N.º de venda'])
    
    # CORRECAO: Filtrar devoluções com valor != 0 (não > 0) porque ML retorna valores negativos
    todas_dev_validas = todas_dev[todas_dev[col_valor] != 0].copy()
    
    # Merge vendas com devoluções
    df_merged = pd.merge(vendas_periodo, todas_dev_validas[['N.º de venda', col_valor]], on='N.º de venda', how='left')
    
    # Identificar cancelamentos
    df_merged['is_cancelada'] = False
    if 'Estado' in df_merged.columns:
        df_merged['is_cancelada'] = df_merged['Estado'].astype(str).str.lower().str.contains('cancelad|anulad', na=False)
    
    # Garantir que col_valor existe
    if col_valor not in df_merged.columns:
        df_merged[col_valor] = 0.0
    
    # Uma devolução conta se valor != 0 e venda não foi cancelada
    df_merged['tem_dev'] = (df_merged[col_valor] != 0) & (~df_merged['is_cancelada'])
    # Converter para positivo
    df_merged['valor_dev'] = df_merged[col_valor].fillna(0).abs()
    
    col_receita = 'Receita por produtos (BRL)'
    if col_receita not in df_merged.columns: df_merged[col_receita] = 0.0
    
    df_merged.loc[(df_merged['tem_dev']) & (df_merged['valor_dev'] == 0), 'valor_dev'] = df_merged[col_receita].abs()
    
    # Agrupar por SKU/Produto
    if agrupar_por in df_merged.columns:
        res = df_merged.groupby(agrupar_por).agg(
            Vendas=('N.º de venda', 'count'),
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
            res['Impacto_Acum'] = res['Impacto'].cumsum()
            res['Impacto_Pct'] = (res['Impacto_Acum'] / impacto_total * 100).round(1)
            
            res['Classe'] = res['Impacto_Pct'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            res = res.drop(['Impacto_Acum', 'Impacto_Pct'], axis=1)
        
        res = res.sort_values('Impacto', ascending=False)
        
        if limit:
            res = res.head(limit)
        
        return garantir_colunas_app(res), None
    
    return garantir_colunas_app(pd.DataFrame()), None

def simular_reducao(skus_data, percentual_reducao):
    """Simula redução de devoluções."""
    if skus_data.empty:
        return pd.DataFrame()
    
    resultado = skus_data.copy()
    
    if 'Dev.' in resultado.columns and 'Impacto' in resultado.columns:
        # Reduzir devoluções pelo percentual
        reducao_dev = (resultado['Dev.'] * percentual_reducao / 100).astype(int)
        resultado['Dev. Reduzido'] = resultado['Dev.'] - reducao_dev
        
        # Recalcular impacto
        resultado['Impacto Reduzido'] = resultado['Impacto'] * (1 - percentual_reducao / 100)
        
        # Recalcular taxa
        if 'Vendas' in resultado.columns:
            resultado['Taxa Reduzida'] = (resultado['Dev. Reduzido'] / resultado['Vendas'] * 100).round(1)
    
    return resultado

def calcular_qualidade_arquivo(data):
    """Calcula qualidade do arquivo de dados."""
    vendas = data.get('vendas', pd.DataFrame())
    matriz = data.get('matriz', pd.DataFrame())
    full = data.get('full', pd.DataFrame())
    
    if vendas.empty:
        return {'qualidade': 0, 'avisos': ['Nenhum dado de vendas encontrado']}
    
    avisos = []
    pontos = 100
    
    # Verificar colunas essenciais
    colunas_essenciais = ['N.º de venda', 'Data da venda', 'Receita por produtos (BRL)']
    for col in colunas_essenciais:
        if col not in vendas.columns:
            avisos.append(f'Coluna ausente: {col}')
            pontos -= 10
    
    # Verificar dados faltantes
    if 'Data da venda' in vendas.columns:
        pct_faltante = vendas['Data da venda'].isna().sum() / len(vendas) * 100
        if pct_faltante > 10:
            avisos.append(f'{pct_faltante:.1f}% de datas faltando')
            pontos -= 5
    
    # Verificar se há devoluções
    todas_dev = pd.concat([matriz, full], ignore_index=True) if not matriz.empty or not full.empty else pd.DataFrame()
    if todas_dev.empty:
        avisos.append('Nenhum dado de devoluções encontrado')
        pontos -= 20
    
    return {
        'qualidade': max(0, pontos),
        'avisos': avisos,
        'total_vendas': len(vendas),
        'total_devolucoes': len(todas_dev)
    }
