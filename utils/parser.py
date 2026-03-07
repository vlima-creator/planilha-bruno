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
            df['Data da venda'] = pd.to_datetime(df['Data de criação do pedido'], errors='coerce')
            df['N.º de venda'] = df['ID do pedido'].astype(str)
            df['SKU'] = df['Número de referência SKU'].fillna(df['Nº de referência do SKU principal'])
            df['Título do anúncio'] = df['Nome do Produto']
            df['Unidades'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(1)
            df['Receita por produtos (BRL)'] = df['Subtotal do produto'].apply(limpar_valor_shopee)
            df['Receita por envio (BRL)'] = df['Taxa de envio pagas pelo comprador'].apply(limpar_valor_shopee)
            df['Venda por publicidade'] = 'Não'
            if 'Status do pedido' in df.columns:
                df['Estado'] = df['Status do pedido']
            
            if 'Método de envio' in df.columns and 'Opção de envio' in df.columns:
                df['Forma de entrega'] = df.apply(
                    lambda x: f"{x['Método de envio']} ({x['Opção de envio']})" 
                    if pd.notna(x['Método de envio']) and pd.notna(x['Opção de envio']) 
                    else (x['Método de envio'] if pd.notna(x['Método de envio']) else x['Opção de envio']), 
                    axis=1
                )
            else:
                df['Forma de entrega'] = df.get('Método de envio', 'Não informado')
            
        else: # ML
            if 'Data da venda' in df.columns:
                df['Data da venda'] = df['Data da venda'].apply(parse_date_pt_br)
            
            # Tratar Forma de entrega em branco
            if 'Forma de entrega' in df.columns:
                df['Forma de entrega'] = df['Forma de entrega'].fillna('Não informado').replace('', 'Não informado').replace(' ', 'Não informado')
            else:
                df['Forma de entrega'] = 'Não informado'

            # Identificar Cancelamentos ML
            if 'Estado' in df.columns:
                df['is_cancelado'] = df['Estado'].astype(str).str.lower().str.contains('cancelada', na=False)
            else:
                df['is_cancelado'] = False

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
        is_shopee = False
        if 'Sheet1' in xls.sheet_names:
            test_df = pd.read_excel(file, sheet_name='Sheet1', nrows=5)
            if 'ID da Devolução' in test_df.columns:
                is_shopee = True

        if is_shopee:
            df = pd.read_excel(file, sheet_name='Sheet1')
            df = df.dropna(how='all')
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
            df['N.º de venda'] = df['ID do pedido'].astype(str)
            df['Data da venda'] = pd.to_datetime(df['Data de criação do pedido'], errors='coerce')
            df['Estado'] = df['Status da Devolução / Reembolso']
            df['Motivo do resultado'] = df['Motivo da Devolução']
            df['is_reembolso'] = df['Estado'].astype(str).str.lower().str.contains('reembolso|concluído|aceito|aprovad', na=False)
            df['Cancelamentos e reembolsos (BRL)'] = df['Quantia total de reembolsos'].apply(limpar_valor_shopee)
            df['Plataforma'] = 'Shopee'
            return df, None
            
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
                
                if 'Cancelamentos e reembolsos (BRL)' in df.columns:
                    df['Cancelamentos e reembolsos (BRL)'] = df['Cancelamentos e reembolsos (BRL)'].abs()
                
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
