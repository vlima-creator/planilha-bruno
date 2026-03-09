import pandas as pd
from datetime import datetime, timedelta

def classificar_estado(estado, plataforma='ML'):
    """Classifica devolução baseado no estado e plataforma"""
    if pd.isna(estado):
        return 'Neutra'
    
    estado_lower = str(estado).lower()
    
    if plataforma == 'Shopee':
        # Shopee Status: 'Reembolso Concluído', 'Aprovada', 'Em devolução', etc.
        # Na Shopee, 'concluído' ou 'aprovada' geralmente significa que o reembolso foi feito.
        # Se o produto voltou, é saudável. Se não voltou ou foi perda total do valor, é crítica.
        if 'reembolso concluído' in estado_lower or 'concluído' in estado_lower or 'aprovada' in estado_lower:
            return 'Saudável'
        if 'disputa' in estado_lower or 'rejeitado' in estado_lower or 'cancelado' in estado_lower:
            return 'Crítica'
        return 'Neutra'
    else:
        # ML: Saudável: produto foi devolvido e aceito
        if ('colocamos o produto à venda novamente' in estado_lower or 
            'devolvemos o produto ao comprador' in estado_lower or
            'reembolsamos o dinheiro' in estado_lower or
            'devolução finalizada' in estado_lower):
            return 'Saudável'
        
        # ML: Crítica: devolução problemática ou cancelada
        if ('cancelada' in estado_lower or 
            'mediação' in estado_lower or
            'reclamação' in estado_lower or
            'revisão' in estado_lower or
            'te demos o dinheiro' in estado_lower):
            return 'Crítica'
        
        # ML: Neutra: em processo
        return 'Neutra'

def calcular_metricas(vendas, matriz, full, max_date, dias_atras):
    """
    Calcula métricas para um período específico.
    Garante que cancelamentos e devoluções sejam contados separadamente.
    """
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    vendas_periodo = vendas.copy()
    plataforma = vendas_periodo['Plataforma'].iloc[0] if not vendas_periodo.empty else 'ML'
    
    # Criar mapa de devoluções indexado por N.º de venda
    todas_dev = pd.concat([matriz, full], ignore_index=True)
    dev_map = {}
    
    if len(todas_dev) > 0 and 'N.º de venda' in todas_dev.columns:
        for _, row in todas_dev.iterrows():
            num_venda = str(row['N.º de venda'])
            if num_venda not in dev_map:
                dev_map[num_venda] = []
            dev_map[num_venda].append(row)
    
    vendas_totais = len(vendas_periodo)
    
    # Identificar cancelamentos no relatório de vendas
    if 'is_cancelado' not in vendas_periodo.columns:
        if 'Estado' in vendas_periodo.columns:
            vendas_periodo['is_cancelado'] = vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelada', na=False)
        else:
            vendas_periodo['is_cancelado'] = False
            
    vendas_canceladas_count = vendas_periodo['is_cancelado'].sum()
    
    faturamento_produtos = 0.0
    faturamento_total = 0.0
    faturamento_devolucoes = 0.0
    impacto_devolucao = 0.0
    perda_total = 0.0
    perda_parcial = 0.0
    saudaveis = 0
    criticas = 0
    neutras = 0
    
    venda_com_devolucao = set()
    
    for _, venda in vendas_periodo.iterrows():
        is_cancelada = venda.get('is_cancelado', False)
        
        if is_cancelada:
            continue
            
        receita_prod = float(venda.get('Receita por produtos (BRL)', 0) or 0)
        receita_env = float(venda.get('Receita por envio (BRL)', 0) or 0)
        
        faturamento_produtos += receita_prod
        faturamento_total += receita_prod + receita_env
        
        num_venda = str(venda.get('N.º de venda', ''))
        
        if num_venda in dev_map:
            # É uma devolução (venda enviada mas que gerou devolução/reembolso)
            venda_com_devolucao.add(num_venda)
            
            for dev in dev_map[num_venda]:
                # CORREÇÃO: Usar coluna correta de reembolso
                reembolso = dev.get('Cancelamentos e reembolsos (BRL)', None)
                if reembolso is None or pd.isna(reembolso):
                    reembolso = 0.0
                reembolso = abs(float(reembolso))
                
                faturamento_devolucoes += reembolso
                
                # Custos logísticos
                if plataforma == 'Shopee':
                    # Na Shopee, os custos logísticos podem vir de colunas diferentes
                    # Usamos os nomes de colunas padrão da Shopee se disponíveis
                    custo_envio_devolucao = float(dev.get('Taxa de envio pagas pelo comprador', 0) or 0)
                    # Outras tarifas que podem ser descontadas na devolução
                    tarifa_venda = float(dev.get('Taxas de transação', 0) or 0) + float(dev.get('Comissão', 0) or 0)
                    perda_parcial_item = abs(custo_envio_devolucao) + abs(tarifa_venda)
                else:
                    # ML
                    # 'Custo de envio com base nas medidas e peso declarados' é o custo do frete pago pelo vendedor na devolução
                    custo_envio_devolucao = float(dev.get('Custo de envio com base nas medidas e peso declarados', 0) or 0)
                    tarifa_venda = float(dev.get('Tarifa de venda e impostos (BRL)', 0) or 0)
                    perda_parcial_item = abs(custo_envio_devolucao) + abs(tarifa_venda)
                
                classe = classificar_estado(dev.get('Estado'), plataforma)
                if classe == 'Saudável':
                    saudaveis += 1
                    perda_total_item = perda_parcial_item
                elif classe == 'Crítica':
                    criticas += 1
                    perda_total_item = reembolso + perda_parcial_item
                else:
                    neutras += 1
                    perda_total_item = perda_parcial_item
                
                impacto_devolucao += reembolso
                perda_total += perda_total_item
                perda_parcial += perda_parcial_item
                
    devolucoes_count = len(venda_com_devolucao)
    vendas_enviadas = vendas_totais - vendas_canceladas_count
    taxa_devolucao = devolucoes_count / vendas_enviadas if vendas_enviadas > 0 else 0
    
    unidades_totais = int(vendas_periodo[~vendas_periodo['is_cancelado']]['Unidades'].fillna(0).sum()) if 'Unidades' in vendas_periodo.columns else (vendas_totais - vendas_canceladas_count)
    
    return {
        'vendas': vendas_totais,
        'vendas_canceladas': vendas_canceladas_count,
        'unidades': unidades_totais,
        'faturamento_produtos': faturamento_produtos,
        'faturamento_total': faturamento_total,
        'devolucoes_vendas': devolucoes_count,
        'taxa_devolucao': taxa_devolucao,
        'faturamento_devolucoes': faturamento_devolucoes,
        'impacto_devolucao': impacto_devolucao,
        'perda_total': perda_total,
        'perda_parcial': perda_parcial,
        'saudaveis': saudaveis,
        'criticas': criticas,
        'neutras': neutras,
        'plataforma': plataforma
    }

def calcular_qualidade_arquivo(data):
    """Calcula qualidade do arquivo com as chaves esperadas pelo export.py"""
    vendas = data['vendas']
    matriz = data['matriz'] if data['matriz'] is not None else pd.DataFrame()
    full = data['full'] if data['full'] is not None else pd.DataFrame()
    
    def get_stats(df):
        if df.empty:
            return {
                'sem_sku_pct': 0,
                'sem_data_pct': 0,
                'sem_numero_venda_pct': 0,
                'sem_motivo_pct': 0,
                'sem_estado_pct': 0
            }
        
        total = len(df)
        return {
            'sem_sku_pct': (df['SKU'].isna().sum() / total * 100) if 'SKU' in df.columns else 100,
            'sem_data_pct': (df['Data da venda'].isna().sum() / total * 100) if 'Data da venda' in df.columns else 100,
            'sem_numero_venda_pct': (df['N.º de venda'].isna().sum() / total * 100) if 'N.º de venda' in df.columns else 100,
            'sem_motivo_pct': (df['Motivo'].isna().sum() / total * 100) if 'Motivo' in df.columns else (
                (df['Motivo do resultado'].isna().sum() / total * 100) if 'Motivo do resultado' in df.columns else 0
            ),
            'sem_estado_pct': (df['Estado'].isna().sum() / total * 100) if 'Estado' in df.columns else 0
        }

    return {
        'vendas': get_stats(vendas),
        'matriz': get_stats(matriz),
        'full': get_stats(full)
    }
