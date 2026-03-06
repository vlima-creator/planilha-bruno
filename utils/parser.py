import pandas as pd
from datetime import datetime
import re
import os

MESES_PT = {
    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
    'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
}

def parse_date_pt_br(date_str):
    """Converte data no formato PT-BR para datetime"""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    
    # Formato ML: "24 de fevereiro de 2026 22:51 hs."
    pattern = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\s+(\d{2}):(\d{2})'
    match = re.search(pattern, date_str, re.IGNORECASE)
    
    if match:
        dia, mes_str, ano, hora, minuto = match.groups()
        mes = MESES_PT.get(mes_str.lower())
        if mes:
            try:
                return datetime(int(ano), mes, int(dia), int(hora), int(minuto))
            except:
                pass

    # Formato Shopee: "2026-02-27 11:42" ou "2026-02-27"
    try:
        return pd.to_datetime(date_str)
    except:
        return None

def limpar_valor_shopee(valor):
    """Limpa strings de valores da Shopee (ex: 'R$38,23' -> 38.23)"""
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    valor_str = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(valor_str)
    except:
        return 0.0

def detectar_plataforma(df):
    """Detecta se o DataFrame é do Mercado Livre ou Shopee"""
    cols = df.columns.tolist()
    if 'N.º de venda' in cols or 'Receita por produtos (BRL)' in cols:
        return 'ML'
    if 'ID do pedido' in cols or 'ID da Devolução' in cols:
        return 'Shopee'
    return 'Desconhecida'

def ler_vendas(file):
    """Lê arquivo de Vendas (ML ou Shopee)"""
    try:
        # Tentar ler para detectar plataforma
        # Para Shopee .all, a aba é 'orders'
        # Para ML, a aba é 'Vendas BR' e começa na linha 6
        
        xls = pd.ExcelFile(file)
        plataforma = 'ML'
        header_row = 5
        sheet_name = None

        if 'orders' in xls.sheet_names:
            plataforma = 'Shopee'
            header_row = 0
            sheet_name = 'orders'
        elif 'Vendas BR' in xls.sheet_names:
            plataforma = 'ML'
            header_row = 5
            sheet_name = 'Vendas BR'
        else:
            # Tentar ler a primeira aba
            sheet_name = xls.sheet_names[0]
            test_df = pd.read_excel(file, sheet_name=sheet_name, nrows=10)
            plataforma = detectar_plataforma(test_df)
            if plataforma == 'Shopee':
                header_row = 0
            else:
                header_row = 5

        df = pd.read_excel(file, sheet_name=sheet_name, header=header_row)
        df = df.dropna(how='all')
        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

        if plataforma == 'Shopee':
            # Mapear colunas Shopee para o padrão do App (ou manter originais e tratar nas métricas)
            # Para manter a lógica do app, vamos criar colunas equivalentes onde possível
            df['Data da venda'] = pd.to_datetime(df['Data de criação do pedido'], errors='coerce')
            df['N.º de venda'] = df['ID do pedido'].astype(str)
            df['SKU'] = df['Número de referência SKU'].fillna(df['Nº de referência do SKU principal'])
            df['Título do anúncio'] = df['Nome do Produto']
            df['Unidades'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(1)
            
            # Valores financeiros Shopee
            df['Receita por produtos (BRL)'] = df['Preço acordado'].apply(limpar_valor_shopee) * df['Unidades']
            df['Receita por envio (BRL)'] = df['Taxa de envio pagas pelo comprador'].apply(limpar_valor_shopee)
            
            # Venda por publicidade na Shopee? (Não tem essa info direta no Order.all)
            df['Venda por publicidade'] = 'Não'
            
            # Canal na Shopee (Padrão)
            df['Forma de entrega'] = df['Método de envio']
            
        else: # ML
            if 'Data da venda' in df.columns:
                df['Data da venda'] = df['Data da venda'].apply(parse_date_pt_br)
            
            # Converter números ML
            for col in df.columns:
                if isinstance(col, str) and ('BRL' in col or 'Receita' in col or 'Custo' in col or 'Taxa' in col):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['Plataforma'] = plataforma
        return df
    
    except Exception as e:
        raise Exception(f"Erro ao ler vendas: {str(e)}")

def ler_devolucoes(file):
    """Lê arquivo de Devoluções (ML ou Shopee)"""
    try:
        xls = pd.ExcelFile(file)
        
        # Detectar se é Shopee (geralmente tem ID da Devolução)
        is_shopee = False
        if 'Sheet1' in xls.sheet_names:
            test_df = pd.read_excel(file, sheet_name='Sheet1', nrows=5)
            if 'ID da Devolução' in test_df.columns:
                is_shopee = True

        if is_shopee:
            df = pd.read_excel(file, sheet_name='Sheet1')
            df = df.dropna(how='all')
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
            
            # Mapear para o padrão
            df['N.º de venda'] = df['ID do pedido'].astype(str)
            df['Data da venda'] = pd.to_datetime(df['Data de criação do pedido'], errors='coerce')
            df['Estado'] = df['Status da Devolução / Reembolso']
            df['Motivo do resultado'] = df['Motivo da Devolução']
            
            # Tentar capturar forma de entrega se disponível no relatório de devoluções
            # Na Shopee, às vezes o relatório de devolução tem o canal de envio
            if 'Método de envio' in df.columns:
                df['Forma de entrega'] = df['Método de envio']
            
            # Valores financeiros Shopee
            df['Cancelamentos e reembolsos (BRL)'] = df['Quantia total de reembolsos'].apply(limpar_valor_shopee)
            df['Tarifas de envio (BRL)'] = 0.0 # Shopee não detalha isso aqui
            df['Tarifa de venda e impostos (BRL)'] = 0.0
            
            df['Plataforma'] = 'Shopee'
            return df, None # Retorna como 'matriz', 'full' como None
            
        else: # ML
            matriz = None
            full = None
            for sheet in xls.sheet_names:
                sheet_lower = sheet.lower()
                df = pd.read_excel(file, sheet_name=sheet, header=5)
                df = df.dropna(how='all')
                df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
                
                if 'Data da venda' in df.columns:
                    df['Data da venda'] = df['Data da venda'].apply(parse_date_pt_br)
                
                for col in df.columns:
                    if isinstance(col, str) and ('BRL' in col or 'Receita' in col or 'Custo' in col or 'Taxa' in col):
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                df['Plataforma'] = 'ML'
                if 'matriz' in sheet_lower:
                    matriz = df
                elif 'full' in sheet_lower:
                    full = df
            
            return matriz, full
    
    except Exception as e:
        raise Exception(f"Erro ao ler devoluções: {str(e)}")

def processar_arquivos(file_vendas, file_devolucoes):
    """Processa ambos os arquivos"""
    vendas = ler_vendas(file_vendas)
    matriz, full = ler_devolucoes(file_devolucoes)
    
    # Data máxima
    if 'Data da venda' in vendas.columns:
        max_date = vendas['Data da venda'].max()
        if pd.isna(max_date):
            max_date = datetime.now()
    else:
        max_date = datetime.now()
    
    plataforma = vendas['Plataforma'].iloc[0] if not vendas.empty else 'ML'
    
    return {
        'vendas': vendas,
        'matriz': matriz,
        'full': full,
        'max_date': max_date,
        'total_vendas': len(vendas),
        'total_matriz': len(matriz) if matriz is not None else 0,
        'total_full': len(full) if full is not None else 0,
        'plataforma': plataforma
    }
