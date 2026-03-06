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
        # Se for Shopee, podemos ter múltiplas entradas para o mesmo pedido no relatório de devoluções
        # Vamos garantir que cada devolução única seja processada
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
    vendas_canceladas_count = 0
    
    for _, venda in vendas_periodo.iterrows():
        # Identificar se a venda foi cancelada
        estado_venda = str(venda.get('Estado', '')).lower()
        is_cancelada = 'cancelad' in estado_venda or 'anulad' in estado_venda
        
        if is_cancelada:
            vendas_canceladas_count += 1
            continue # Ignorar vendas canceladas para faturamento e devoluções
            
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
            # Para Shopee, verificar se a devolução é válida (não é apenas um registro de cancelamento)
            tem_dev_valida = False
            if plataforma == 'Shopee':
                for dev in dev_map[num_venda]:
                    # Se tem ID de devolução ou status de reembolso, é uma devolução real
                    if pd.notna(dev.get('ID_Devolucao')) or dev.get('is_reembolso', False):
                        tem_dev_valida = True
                        break
            else:
                tem_dev_valida = True # Para ML, assumimos que se está no mapa, é devolução
            
            if tem_dev_valida:
                venda_com_devolucao.add(num_venda)
            
            # Faturamento de Devoluções = receita dos produtos que foram devolvidos
            # No ML, o valor de 'Cancelamentos e reembolsos (BRL)' já representa o valor estornado do produto
            
            for dev in dev_map[num_venda]:
                # Impacto real: usar 'Cancelamentos e reembolsos (BRL)'
                reembolso = dev.get('Cancelamentos e reembolsos (BRL)', None)
                if reembolso is None or pd.isna(reembolso):
                    reembolso = 0.0
                reembolso = abs(float(reembolso))
                
                # Se reembolso é 0, usar receita do produto como fallback
                if reembolso == 0:
                    reembolso = receita_prod
                
                # Adicionar ao faturamento de devoluções (valor bruto do produto devolvido)
                faturamento_devolucoes += reembolso
                
                # Perda Parcial = Tarifas de envio + Tarifa de venda e impostos
                # No ML, essas tarifas vêm negativas. Queremos o custo absoluto.
                tarifas_envio = dev.get('Tarifas de envio (BRL)', 0)
                if pd.isna(tarifas_envio): tarifas_envio = 0.0
                tarifas_envio = float(tarifas_envio)
                
                tarifa_venda = dev.get('Tarifa de venda e impostos (BRL)', 0)
                if pd.isna(tarifa_venda): tarifa_venda = 0.0
                tarifa_venda = float(tarifa_venda)
                
                # Perda parcial é a soma dos custos logísticos e taxas que não são recuperados
                perda_parcial_item = abs(tarifas_envio) + abs(tarifa_venda)
                
                # Se for Shopee, usar colunas O e R para perdas se disponíveis
                if plataforma == 'Shopee':
                    val_o = dev.get('Shopee_Col_O', 0.0)
                    val_r = dev.get('Shopee_Col_R', 0.0)
                    
                    if val_o > 0 or val_r > 0:
                        perda_parcial_item = float(val_o)
                        perda_total_item = float(val_r)
                    else:
                        classe = classificar_estado(dev.get('Estado'), plataforma)
                        if classe == 'Saudável':
                            perda_total_item = perda_parcial_item
                        else:
                            perda_total_item = reembolso + perda_parcial_item
                else:
                    # Lógica ML original
                    classe = classificar_estado(dev.get('Estado'), plataforma)
                    if classe == 'Saudável':
                        saudaveis += 1
                        # Se saudável, o produto volta ao estoque, a perda é apenas a logística/taxas
                        perda_total_item = perda_parcial_item
                    elif classe == 'Crítica':
                        criticas += 1
                        # Se crítica, o produto é perdido, a perda é o valor do produto + logística/taxas
                        perda_total_item = reembolso + perda_parcial_item
                    else:
                        neutras += 1
                        perda_total_item = perda_parcial_item
                
                # Incrementar contadores de classe para Shopee se não foi feito acima
                if plataforma == 'Shopee':
                    classe = classificar_estado(dev.get('Estado'), plataforma)
                    if classe == 'Saudável': saudaveis += 1
                    elif classe == 'Crítica': criticas += 1
                    else: neutras += 1
                
                impacto_devolucao += reembolso
                perda_total += perda_total_item
                perda_parcial += perda_parcial_item
    
    # Contagem de devoluções = número de vendas que tiveram devolução
    devolucoes_count = len(venda_com_devolucao)
    
    # Vendas Líquidas = Vendas Totais - Canceladas
    vendas_liquidas = vendas_totais - vendas_canceladas_count
    taxa_devolucao = devolucoes_count / vendas_liquidas if vendas_liquidas > 0 else 0
    
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
