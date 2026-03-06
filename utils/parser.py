import pandas as pd
from datetime import datetime
import re

MESES_PT = {
    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
    'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
}

def parse_date_pt_br(date_str):
    """Converte data no formato PT-BR para datetime"""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    
    # Formato: "24 de fevereiro de 2026 22:51 hs."
    pattern = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\s+(\d{2}):(\d{2})'
    match = re.search(pattern, date_str, re.IGNORECASE)
    
    if not match:
        return None
    
    dia, mes_str, ano, hora, minuto = match.groups()
    mes = MESES_PT.get(mes_str.lower())
    
    if not mes:
        return None
    
    try:
        return datetime(int(ano), mes, int(dia), int(hora), int(minuto))
    except:
        return None

def ler_vendas(file):
    """Lê arquivo de Vendas do Mercado Livre"""
    try:
        # Ler com cabeçalho na linha 6 (índice 5)
        df = pd.read_excel(file, sheet_name='Vendas BR', header=5)
        
        # Remover linhas vazias
        df = df.dropna(how='all')
        
        # Limpar nomes de colunas
        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
        
        # Converter datas
        if 'Data da venda' in df.columns:
            df['Data da venda'] = df['Data da venda'].apply(parse_date_pt_br)
        
        # Converter números
        for col in df.columns:
            if isinstance(col, str) and ('BRL' in col or 'Receita' in col or 'Custo' in col or 'Taxa' in col):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    except Exception as e:
        raise Exception(f"Erro ao ler vendas: {str(e)}")

def ler_devolucoes(file):
    """Lê arquivo de Devoluções do Mercado Livre"""
    try:
        xls = pd.ExcelFile(file)
        
        matriz = None
        full = None
        
        # Procurar pelas abas
        for sheet in xls.sheet_names:
            sheet_lower = sheet.lower()
            
            # Ler com cabeçalho na linha 6 (índice 5)
            df = pd.read_excel(file, sheet_name=sheet, header=5)
            df = df.dropna(how='all')
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
            
            # Converter datas
            if 'Data da venda' in df.columns:
                df['Data da venda'] = df['Data da venda'].apply(parse_date_pt_br)
            
            # Converter números
            for col in df.columns:
                if isinstance(col, str) and ('BRL' in col or 'Receita' in col or 'Custo' in col or 'Taxa' in col):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
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
    
    return {
        'vendas': vendas,
        'matriz': matriz,
        'full': full,
        'max_date': max_date,
        'total_vendas': len(vendas),
        'total_matriz': len(matriz) if matriz is not None else 0,
        'total_full': len(full) if full is not None else 0,
    }
