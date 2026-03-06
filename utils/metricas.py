import pandas as pd
from datetime import datetime, timedelta

def classificar_estado(estado, plataforma='ML'):
    """Classifica devolução baseado no estado e plataforma"""
    if pd.isna(estado):
        return 'Neutra'
    
    estado_lower = str(estado).lower()
    
    if plataforma == 'Shopee':
        # Shopee Status: 'Reembolso Concluído', 'Aprovada', 'Em devolução', etc.
        if 'aprovad' in estado_lower or 'reembolso concluído' in estado_lower or 'concluído' in estado_lower:
            return 'Saudável'
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
    Para Shopee: conta pedidos únicos (não linhas), evitando inflação por múltiplos itens.
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
    
    # Para Shopee: agrupar por pedido único para evitar duplicatas por múltiplos itens
    if plataforma == 'Shopee' and 'N.º de venda' in vendas_periodo.columns:
        # Identificar pedidos cancelados (por pedido único)
        vendas_por_pedido = vendas_periodo.groupby('N.º de venda').agg(
            Estado=('Estado', 'first'),
            receita_prod=('Receita por produtos (BRL)', 'sum'),
            receita_env=('Receita por envio (BRL)', 'first'),
        ).reset_index()
        
        vendas_totais = len(vendas_por_pedido)
        vendas_canceladas_count = vendas_por_pedido['Estado'].astype(str).str.lower().str.contains('cancelad|anulad', na=False).sum()
        
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
        
        for _, venda in vendas_por_pedido.iterrows():
            estado_venda = str(venda.get('Estado', '')).lower()
            is_cancelada = 'cancelad' in estado_venda or 'anulad' in estado_venda
            
            if is_cancelada:
                continue
            
            receita_prod = float(venda.get('receita_prod', 0) or 0)
            receita_env = float(venda.get('receita_env', 0) or 0)
            
            faturamento_produtos += receita_prod
            faturamento_total += receita_prod + receita_env
            
            num_venda = str(venda.get('N.º de venda', ''))
            
            if num_venda in dev_map:
                # Para Shopee: usar apenas o primeiro registro de devolução por pedido
                # (evitar duplicatas no relatório de devoluções)
                devs_pedido = dev_map[num_venda]
                
                # Verificar se há devolução válida
                tem_dev_valida = False
                for dev in devs_pedido:
                    if pd.notna(dev.get('ID_Devolucao')) or dev.get('is_reembolso', False):
                        tem_dev_valida = True
                        break
                
                # Se não há ID de devolução mas existe no mapa, ainda é uma devolução
                if not tem_dev_valida and len(devs_pedido) > 0:
                    tem_dev_valida = True
                
                if tem_dev_valida:
                    venda_com_devolucao.add(num_venda)
                
                # Processar apenas o PRIMEIRO registro de devolução por pedido (evitar duplicatas)
                dev = devs_pedido[0]
                
                reembolso = dev.get('Cancelamentos e reembolsos (BRL)', None)
                if reembolso is None or pd.isna(reembolso):
                    reembolso = 0.0
                reembolso = abs(float(reembolso))
                
                if reembolso == 0:
                    reembolso = receita_prod
                
                faturamento_devolucoes += reembolso
                
                # Perda Parcial para Shopee:
                # = Reembolso ao comprador - Renda do pedido (o que o vendedor recebeu) - Compensação da Shopee
                # Representa o custo real que o vendedor arca (taxas, frete, etc.)
                val_o = float(dev.get('Shopee_Col_O', 0.0) or 0.0)  # Renda do pedido
                val_r = float(dev.get('Shopee_Col_R', 0.0) or 0.0)  # Valor de compensação
                
                # Perda Parcial = o que o vendedor perde em taxas/custos (não recupera)
                perda_parcial_item = max(0.0, reembolso - val_o - val_r)
                
                classe = classificar_estado(dev.get('Estado'), plataforma)
                if classe == 'Saudável':
                    saudaveis += 1
                    # Produto devolvido: perda é apenas as taxas não recuperadas
                    perda_total_item = perda_parcial_item
                elif classe == 'Crítica':
                    criticas += 1
                    # Produto perdido: perda total = reembolso + custos não recuperados
                    perda_total_item = reembolso + perda_parcial_item
                else:
                    neutras += 1
                    perda_total_item = perda_parcial_item
                
                impacto_devolucao += reembolso
                perda_total += perda_total_item
                perda_parcial += perda_parcial_item
        
        devolucoes_count = len(venda_com_devolucao)
        vendas_liquidas = vendas_totais - vendas_canceladas_count - devolucoes_count
        vendas_enviadas = vendas_totais - vendas_canceladas_count
        taxa_devolucao = devolucoes_count / vendas_enviadas if vendas_enviadas > 0 else 0
        
        # Unidades totais (soma real de todas as linhas não canceladas)
        vendas_nao_cancel = vendas_periodo[~vendas_periodo['Estado'].astype(str).str.lower().str.contains('cancelad|anulad', na=False)]
        unidades_totais = int(vendas_nao_cancel['Unidades'].fillna(0).sum()) if 'Unidades' in vendas_nao_cancel.columns else vendas_totais
        
    else:
        # Lógica original para ML (linha a linha)
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
        vendas_canceladas_count = 0
        
        for _, venda in vendas_periodo.iterrows():
            estado_venda = str(venda.get('Estado', '')).lower()
            is_cancelada = 'cancelad' in estado_venda or 'anulad' in estado_venda
            
            if is_cancelada:
                vendas_canceladas_count += 1
                continue
                
            receita_prod = venda.get('Receita por produtos (BRL)', 0)
            receita_env = venda.get('Receita por envio (BRL)', 0)
            if pd.isna(receita_prod): receita_prod = 0.0
            if pd.isna(receita_env): receita_env = 0.0
            receita_prod = float(receita_prod)
            receita_env = float(receita_env)
            
            faturamento_produtos += receita_prod
            faturamento_total += receita_prod + receita_env
            
            num_venda = str(venda.get('N.º de venda', ''))
            
            if num_venda in dev_map:
                tem_dev_valida = True
                
                if tem_dev_valida:
                    venda_com_devolucao.add(num_venda)
                
                for dev in dev_map[num_venda]:
                    reembolso = dev.get('Cancelamentos e reembolsos (BRL)', None)
                    if reembolso is None or pd.isna(reembolso):
                        reembolso = 0.0
                    reembolso = abs(float(reembolso))
                    
                    if reembolso == 0:
                        reembolso = receita_prod
                    
                    faturamento_devolucoes += reembolso
                    
                    tarifas_envio = dev.get('Tarifas de envio (BRL)', 0)
                    if pd.isna(tarifas_envio): tarifas_envio = 0.0
                    tarifas_envio = float(tarifas_envio)
                    
                    tarifa_venda = dev.get('Tarifa de venda e impostos (BRL)', 0)
                    if pd.isna(tarifa_venda): tarifa_venda = 0.0
                    tarifa_venda = float(tarifa_venda)
                    
                    perda_parcial_item = abs(tarifas_envio) + abs(tarifa_venda)
                    
                    # Lógica ML original
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
        vendas_liquidas = vendas_totais - vendas_canceladas_count - devolucoes_count
        vendas_enviadas = vendas_totais - vendas_canceladas_count
        taxa_devolucao = devolucoes_count / vendas_enviadas if vendas_enviadas > 0 else 0
    
    return {
        'vendas': vendas_totais,
        'vendas_canceladas': vendas_canceladas_count,
        'vendas_liquidas': vendas_liquidas,
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
