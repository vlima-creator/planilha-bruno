"""
Módulo para exportar análises de anúncios para PDF
Versão polida com design profissional e amigável
Utiliza fpdf2 para suporte completo a Unicode
"""

from fpdf import FPDF
from io import BytesIO
from datetime import datetime
from typing import Dict, Any
import re

class PDFRelatorioAnuncio(FPDF):
    """Classe customizada para gerar PDF de análise de anúncios com design profissional"""
    
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=18)
        
    def header(self):
        """Cabeçalho do PDF com design profissional"""
        if self.page_no() == 1:
            # Fundo azul no topo apenas na primeira página
            self.set_fill_color(31, 78, 120)
            self.rect(0, 0, 210, 45, 'F')
            
            # Título principal
            self.set_font("Helvetica", "B", 26)
            self.set_text_color(255, 255, 255)
            self.set_xy(18, 12)
            self.cell(0, 12, "Relatório de Análise", ln=True)
            
            # Subtítulo
            self.set_font("Helvetica", "", 11)
            self.set_text_color(200, 220, 240)
            self.set_xy(18, 26)
            self.cell(0, 8, "Análise Estratégica de Anúncios com Inteligência Artificial", ln=True)
            
            # Voltar para cor normal e dar espaço
            self.set_text_color(0, 0, 0)
            self.set_y(50)
        else:
            # Cabeçalho simplificado para as demais páginas
            self.set_fill_color(31, 78, 120)
            self.rect(0, 0, 210, 15, 'F')
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(255, 255, 255)
            self.set_xy(18, 4)
            self.cell(0, 7, "Relatório de Análise - Inteligência Artificial", ln=True)
            self.set_text_color(0, 0, 0)
            self.set_y(25)
        
    def footer(self):
        """Rodapé do PDF"""
        self.set_y(-18)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(128, 128, 128)
        
        # Linha separadora
        self.set_draw_color(200, 200, 200)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(2)
        
        # Conteúdo do rodapé
        self.cell(0, 4, f"Página {self.page_no()}", align="L")
        self.set_x(120)
        self.cell(0, 4, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="R")

    def section_header(self, titulo: str):
        """Cria um cabeçalho de seção com design atraente"""
        self.ln(4)
        # Fundo azul claro para a seção
        self.set_fill_color(235, 240, 250)
        self.rect(18, self.get_y(), 174, 10, 'F')
        
        # Borda lateral esquerda azul escura
        self.set_fill_color(31, 78, 120)
        self.rect(18, self.get_y(), 2, 10, 'F')
        
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(31, 78, 120)
        self.set_xy(22, self.get_y() + 1)
        self.cell(0, 8, limpar_texto_pdf(titulo.upper()), ln=True)
        
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def info_row(self, label: str, value: str):
        """Cria uma linha de informação estilizada"""
        if not value or value.strip() == "" or value.lower() == "não extraído" or value.lower() == "n/a":
            return
            
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(35, 7, f"{limpar_texto_pdf(label)}:", ln=False)
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        
        # Quebrar valor se muito longo
        value_limpo = limpar_texto_pdf(str(value))
        
        # Se for URL, tratar de forma especial para não quebrar o layout
        if label.upper() == "URL":
            self.set_text_color(31, 78, 120)
            # Limitar tamanho visual da URL mas manter funcional se possível
            display_url = value_limpo if len(value_limpo) <= 85 else value_limpo[:82] + "..."
            self.cell(0, 7, display_url, ln=True, link=value)
        else:
            linhas = quebrar_texto(value_limpo, 75)
            for i, linha in enumerate(linhas):
                if i == 0:
                    self.cell(0, 7, linha, ln=True)
                else:
                    self.cell(35, 7, "", ln=False)
                    self.cell(0, 7, linha, ln=True)
        
        self.ln(1)

def limpar_texto_pdf(texto: str) -> str:
    """Limpa o texto para ser compatível com PDF, removendo caracteres problemáticos"""
    if not texto:
        return ""
    
    texto = str(texto)
    
    # Remover marcadores de markdown comuns
    texto = texto.replace('**', '').replace('##', '').replace('###', '')
    texto = texto.replace('`', '').replace('*', '')
    
    # Substituir caracteres especiais comuns por equivalentes seguros
    substituicoes = {
        '\u201c': '"', '\u201d': '"',  # Aspas curvas
        '\u2018': "'", '\u2019': "'",  # Aspas simples
        '\u2013': '-', '\u2014': '-',  # Travessões
        '\u2026': '...',               # Reticências
        '\u2022': '*',                 # Bullet
        '\u25ba': '>',                 # Seta
        '\u2705': 'OK',                # Checkmark emoji
        '\u274c': 'X',                 # Cross emoji
        '\u26a0': '!',                 # Warning emoji
        '\ud83d\udca1': '!',           # Light bulb
        '\ud83d\ude80': '>',           # Rocket
        '\ud83d\udccb': '-',           # Clipboard
        '\ud83d\udce6': '-',           # Package
        '\ud83d\udcb0': '$',           # Money bag
        '\ud83d\udcca': '-',           # Chart
        '\ud83d\udc4d': 'OK',          # Thumbs up
    }
    
    for char_problema, char_seguro in substituicoes.items():
        texto = texto.replace(char_problema, char_seguro)
    
    # Remover qualquer outro caractere que não seja Latin-1 (que a fonte Helvetica suporta)
    # Isso remove emojis e outros símbolos especiais que a IA possa ter gerado
    texto_latin1 = ""
    for char in texto:
        try:
            char.encode('latin-1')
            texto_latin1 += char
        except UnicodeEncodeError:
            # Se não puder codificar em latin-1, ignoramos o caractere ou substituímos por algo neutro
            continue
            
    return texto_latin1

def quebrar_texto(texto: str, max_chars: int = 80) -> list:
    """Quebra o texto em linhas com número máximo de caracteres"""
    if not texto:
        return [""]
    
    linhas = []
    paragrafos = texto.split('\n')
    
    for parágrafo in paragrafos:
        if not parágrafo.strip():
            linhas.append("")
            continue
            
        palavras = parágrafo.split()
        linha_atual = ""
        
        for palavra in palavras:
            if len(linha_atual) + len(palavra) + 1 <= max_chars:
                linha_atual += (" " if linha_atual else "") + palavra
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra
        
        if linha_atual:
            linhas.append(linha_atual)
            
    return linhas

def gerar_pdf_analise_anuncio(dados_anuncio: Dict[str, Any], analise_ia: str, url: str) -> BytesIO:
    """
    Gera um PDF profissional com a análise completa do anúncio.
    """
    
    pdf = PDFRelatorioAnuncio()
    pdf.add_page()
    
    # ========== SEÇÃO 1: INFORMAÇÕES DO ANÚNCIO ==========
    pdf.section_header("Informações do Anúncio")
    
    # Só mostrar campos que não estão vazios
    campos = [
        ("Título", dados_anuncio.get('titulo')),
        ("Preço", dados_anuncio.get('preco')),
        ("Vendedor", dados_anuncio.get('vendedor')),
        ("Avaliações", dados_anuncio.get('avaliacoes'))
    ]
    
    for label, valor in campos:
        if valor and str(valor).strip() and str(valor).lower() not in ["não extraído", "n/a", ""]:
            pdf.info_row(label, str(valor))
            
    # URL sempre mostramos
    pdf.info_row("URL", url)
    
    if dados_anuncio.get('descricao') and str(dados_anuncio.get('descricao')).strip():
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 7, "Descrição do Produto:", ln=True)
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        desc = limpar_texto_pdf(str(dados_anuncio.get('descricao')))[:500]
        if len(str(dados_anuncio.get('descricao'))) > 500:
            desc += "..."
            
        linhas_desc = quebrar_texto(desc, 85)
        for linha in linhas_desc:
            pdf.cell(0, 5, linha, ln=True)
    
    pdf.ln(5)
    
    # ========== SEÇÃO 2: ANÁLISE DETALHADA ==========
    if pdf.get_y() > 150:
        pdf.add_page()
        
    pdf.section_header("Análise Detalhada da IA")
    
    # Processar análise linha por linha
    linhas_analise = analise_ia.split('\n')
    
    for linha in linhas_analise:
        linha_limpa = limpar_texto_pdf(linha.strip())
        
        if not linha_limpa:
            pdf.ln(2)
            continue
        
        # Detectar títulos de seção (## ou 1. Título)
        if linha.startswith('##') or (linha_limpa and linha_limpa[0].isdigit() and '. ' in linha_limpa[:4] and len(linha_limpa) < 100):
            pdf.ln(2)
            if pdf.get_y() > 250:
                pdf.add_page()
                
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(31, 78, 120)
            titulo_secao = linha_limpa.lstrip('#').strip()
            pdf.cell(0, 8, titulo_secao, ln=True)
            
            pdf.set_draw_color(31, 78, 120)
            pdf.set_line_width(0.3)
            pdf.line(18, pdf.get_y(), 60, pdf.get_y())
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
        
        # Detectar subtítulos (###)
        elif linha.startswith('###'):
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(50, 100, 150)
            pdf.cell(0, 7, f"  > {linha_limpa.lstrip('#').strip()}", ln=True)
            pdf.set_text_color(0, 0, 0)
        
        # Detectar listas
        elif linha_limpa.startswith('-') or linha_limpa.startswith('*') or linha_limpa.startswith('[ ]') or linha_limpa.startswith('[x]'):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(40, 40, 40)
            
            marcador = "•"
            texto_item = linha_limpa.lstrip('-* ').strip()
            if linha_limpa.startswith('['):
                marcador = "□" if '[ ]' in linha_limpa else "▣"
                texto_item = linha_limpa[3:].strip()
                
            linhas_quebradas = quebrar_texto(texto_item, 80)
            for i, linha_quebrada in enumerate(linhas_quebradas):
                if i == 0:
                    pdf.cell(8, 6, f"  {marcador}", ln=False)
                    pdf.cell(0, 6, linha_quebrada, ln=True)
                else:
                    pdf.cell(8, 6, "", ln=False)
                    pdf.cell(0, 6, linha_quebrada, ln=True)
        
        # Texto normal
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            linhas_quebradas = quebrar_texto(linha_limpa, 85)
            for linha_quebrada in linhas_quebradas:
                pdf.cell(0, 5, linha_quebrada, ln=True)
    
    # ========== RODAPÉ FINAL ==========
    pdf.ln(10)
    if pdf.get_y() > 260:
        pdf.add_page()
        
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    
    rodape = "Este relatório foi gerado automaticamente pela ferramenta de Análise Inteligente de Anúncios. As recomendações são baseadas em algoritmos de IA e devem ser validadas conforme o contexto do seu negócio."
    linhas_rodape = quebrar_texto(limpar_texto_pdf(rodape), 95)
    for linha in linhas_rodape:
        pdf.cell(0, 4, linha, ln=True, align="C")
    
    # Gerar PDF
    pdf_bytes = pdf.output()
    return BytesIO(pdf_bytes)
