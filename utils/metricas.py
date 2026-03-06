import pandas as pd
from datetime import datetime, timedelta

def classificar_estado(estado, plataforma='ML'):
    """Classifica devolução baseado no estado e plataforma"""
    if pd.isna(estado):
        return 'Neutra'
    
    estado_lower = str(estado).lower()
    
    if plataforma == 'Shopee':
        # Shopee Status: 'Reembolso Concluído', 'Devolução Pendente', etc.
        if 'reembolso concluído' in estado_lower or 'concluído' in estado_lower:
            return 'Saudável' # Assumindo que o processo foi finalizado
        if 'disputa' in estado_lower or 'rejeitado' in estado_lower:
            return 'Crítica'
        return 'Neutra'
    else:
        # ML: Saudável: produto foi devolvido e aceito
        if ('colocamos o produto à venda novamente' in estado_lower or 
            'devolvemos o produto ao comprador' in estado_lower or
            'reembolsamos o dinheiro' in estado_lower):
            return 'Saudável'
        
        # ML: Crítica: devolução problemática ou cancelada
        if ('cancelada' in estado_lower or 
            'mediação' in estado_lower or
            'reclamação' in estado_lower or
            'revisão' in estado_lower):
            return 'Crítica'
        
        # ML: Neutra: em processo
        return 'Neutra'

def calcular_metricas(vendas, matriz, full, max_date, dias_atras):
    """
    Calcula métricas para um período específico.
    """
    if matriz is None:
        matriz = pd.DataFrame()
    if full is None:
        full = pd.DataFrame()
    
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
    
    # Calcular métricas
    vendas_totais = len(vendas_periodo)
    unidades_totais = 0
    if 'Unidades' in vendas_periodo.columns:
        unidades_totais = int(vendas_periodo['Unidades'].fillna(0).sum())
    else:
        unidades_totais = vendas_totais
    
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
        # Faturamento: somar receita de produtos + receita de envio
        receita_prod = venda.get('Receita por produtos (BRL)', 0)
        receita_env = venda.get('Receita por envio (BRL)', 0)
        if pd.isna(receita_prod): receita_prod = 0.0
        if pd.isna(receita_env): receita_env = 0.0
        receita_prod = float(receita_prod)
        receita_env = float(receita_env)
        
        faturamento_produtos += receita_prod
        faturamento_total += receita_prod + receita_env
        
        # Verificar se esta venda tem devolução
        num_venda = str(venda.get('N.º de venda', ''))
        
        if num_venda in dev_map:
            venda_com_devolucao.add(num_venda)
            
            # Faturamento de Devoluções = receita dos produtos que foram devolvidos
            faturamento_devolucoes += receita_prod
            
            for dev in dev_map[num_venda]:
                # Impacto real: usar 'Cancelamentos e reembolsos (BRL)'
                reembolso = dev.get('Cancelamentos e reembolsos (BRL)', None)
                if reembolso is None or pd.isna(reembolso):
                    reembolso = 0.0
                reembolso = float(reembolso)
                
                # Se reembolso é 0, usar receita do produto como fallback
                if reembolso == 0:
                    reembolso = receita_prod
                
                # Perda Parcial = Tarifas de envio + Tarifa de venda e impostos
                tarifas_envio = dev.get('Tarifas de envio (BRL)', 0)
                if pd.isna(tarifas_envio): tarifas_envio = 0.0
                tarifas_envio = float(tarifas_envio)
                
                tarifa_venda = dev.get('Tarifa de venda e impostos (BRL)', 0)
                if pd.isna(tarifa_venda): tarifa_venda = 0.0
                tarifa_venda = float(tarifa_venda)
                
                # Perda parcial é a soma dos custos (já vêm negativos no ML)
                perda_parcial_item = abs(tarifas_envio) + abs(tarifa_venda)
                
                # Lógica de perda total baseada na classificação
                classe = classificar_estado(dev.get('Estado'), plataforma)
                if classe == 'Saudável':
                    saudaveis += 1
                    perda_total_item = perda_parcial_item
                elif classe == 'Crítica':
                    criticas += 1
                    perda_total_item = abs(reembolso) + perda_parcial_item
                else:
                    neutras += 1
                    perda_total_item = perda_parcial_item
                
                impacto_devolucao += abs(reembolso)
                perda_total += perda_total_item
                perda_parcial += perda_parcial_item
    
    # Contagem de devoluções = número de vendas que tiveram devolução
    devolucoes_count = len(venda_com_devolucao)
    taxa_devolucao = devolucoes_count / vendas_totais if vendas_totais > 0 else 0
    
    return {
        'vendas': vendas_totais,
        'unidades': unidades_totais,
        'faturamento_produtos': faturamento_produtos,
        'faturamento_total': faturamento_total,
        'devolucoes_vendas': devolucoes_count,
        'taxa_devolucao': taxa_devolucao,
        'faturamento_devolucoes': faturamento_devolucoes,
        'impacto_devolucao': -abs(impacto_devolucao),
        'perda_total': -abs(perda_total),
        'perda_parcial': -abs(perda_parcial),
        'saudaveis': saudaveis,
        'criticas': criticas,
        'neutras': neutras,
        'plataforma': plataforma
    }

def calcular_qualidade_arquivo(data):
    """Calcula qualidade dos arquivos"""
    vendas = data['vendas']
    matriz = data['matriz']
    full = data['full']
    
    if matriz is None: matriz = pd.DataFrame()
    if full is None: full = pd.DataFrame()
    
    # Qualidade Vendas
    sem_numero = vendas['N.º de venda'].isna().sum() if 'N.º de venda' in vendas.columns else 0
    sem_data = vendas['Data da venda'].isna().sum() if 'Data da venda' in vendas.columns else 0
    sem_receita = vendas['Receita por produtos (BRL)'].isna().sum() if 'Receita por produtos (BRL)' in vendas.columns else 0
    sem_sku = vendas['SKU'].isna().sum() if 'SKU' in vendas.columns else 0
    
    # Qualidade Devoluções
    sem_estado_matriz = matriz['Estado'].isna().sum() if len(matriz) > 0 and 'Estado' in matriz.columns else 0
    sem_motivo_matriz = matriz['Motivo do resultado'].isna().sum() if len(matriz) > 0 and 'Motivo do resultado' in matriz.columns else 0
    
    sem_estado_full = full['Estado'].isna().sum() if len(full) > 0 and 'Estado' in full.columns else 0
    sem_motivo_full = full['Motivo do resultado'].isna().sum() if len(full) > 0 and 'Motivo do resultado' in full.columns else 0
    
    return {
        'vendas': {
            'sem_numero_venda_pct': (sem_numero / len(vendas) * 100) if len(vendas) > 0 else 0,
            'sem_data_pct': (sem_data / len(vendas) * 100) if len(vendas) > 0 else 0,
            'sem_receita_pct': (sem_receita / len(vendas) * 100) if len(vendas) > 0 else 0,
            'sem_sku_pct': (sem_sku / len(vendas) * 100) if len(vendas) > 0 else 0,
        },
        'matriz': {
            'sem_estado_pct': (sem_estado_matriz / len(matriz) * 100) if len(matriz) > 0 else 0,
            'sem_motivo_pct': (sem_motivo_matriz / len(matriz) * 100) if len(matriz) > 0 else 0,
        },
        'full': {
            'sem_estado_pct': (sem_estado_full / len(full) * 100) if len(full) > 0 else 0,
            'sem_motivo_pct': (sem_motivo_full / len(full) * 100) if len(full) > 0 else 0,
        },
        'custo_logistico_ausente': False
    }
