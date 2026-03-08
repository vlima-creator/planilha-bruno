"""
Módulo para exportar análises de anúncios para PDF
Versão polida com design profissional e amigável
Utiliza fpdf2 com suporte completo a Unicode (DejaVu Sans)
"""

from fpdf import FPDF
from io import BytesIO
from datetime import datetime
from typing import Dict, Any
import os

class PDFRelatorioAnuncio(FPDF):
    """Classe customizada para gerar PDF de análise de anúncios com design profissional"""
    
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=18)
        
        # Tentar carregar fonte Unicode (DejaVu Sans) para evitar erros de codificação
        # Caminhos comuns em sistemas Linux (Ubuntu)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "utils/fonts/DejaVuSans.ttf" # Fallback local se existir
        ]
        
        font_bold_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "utils/fonts/DejaVuSans-Bold.ttf"
        ]
        
        self.unicode_font = False
        
        # Tentar carregar a fonte regular
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.add_font("DejaVu", "", path)
                    self.unicode_font = True
                    break
                except:
                    continue
        
        # Tentar carregar a fonte negrito
        for path in font_bold_paths:
            if os.path.exists(path):
                try:
                    self.add_font("DejaVu", "B", path)
                    break
                except:
                    continue
        
        # Definir fonte inicial
        if self.unicode_font:
            self.set_font("DejaVu", "", 10)
        else:
            self.set_font("Helvetica", "", 10)
            
    def header(self):
        """Cabeçalho do PDF com design profissional"""
        if self.page_no() == 1:
            # Fundo azul no topo apenas na primeira página
            self.set_fill_color(31, 78, 120)
            self.rect(0, 0, 210, 45, 'F')
            
            # Título principal
            font_name = "DejaVu" if self.unicode_font else "Helvetica"
            self.set_font(font_name, "B", 26)
            self.set_text_color(255, 255, 255)
            self.set_xy(18, 12)
            self.cell(0, 12, "Relatório de Análise", ln=True)
            
            # Subtítulo
            self.set_font(font_name, "", 11)
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
            font_name = "DejaVu" if self.unicode_font else "Helvetica"
            self.set_font(font_name, "B", 10)
            self.set_text_color(255, 255, 255)
            self.set_xy(18, 4)
            self.cell(0, 7, "Relatório de Análise - Inteligência Artificial", ln=True)
            self.set_text_color(0, 0, 0)
            self.set_y(25)
        
    def footer(self):
        """Rodapé do PDF"""
        self.set_y(-18)
        font_name = "DejaVu" if self.unicode_font else "Helvetica"
        self.set_font(font_name, "", 8)
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
        
        font_name = "DejaVu" if self.unicode_font else "Helvetica"
        self.set_font(font_name, "B", 12)
        self.set_text_color(31, 78, 120)
        self.set_xy(22, self.get_y() + 1)
        self.cell(0, 8, titulo.upper(), ln=True)
        
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def info_row(self, label: str, value: str):
        """Cria uma linha de informação estilizada"""
        if not value or value.strip() == "" or value.lower() == "não extraído" or value.lower() == "n/a":
            return
            
        font_name = "DejaVu" if self.unicode_font else "Helvetica"
        self.set_font(font_name, "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(35, 7, f"{label}:", ln=False)
        
        self.set_font(font_name, "", 10)
        self.set_text_color(0, 0, 0)
        
        # Quebrar valor se muito longo
        value_limpo = str(value)
        
        # Se for URL, tratar de forma especial
        if label.upper() == "URL":
            self.set_text_color(31, 78, 120)
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
        font_name = "DejaVu" if pdf.unicode_font else "Helvetica"
        pdf.set_font(font_name, "B", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 7, "Descrição do Produto:", ln=True)
        
        pdf.set_font(font_name, "", 9)
        pdf.set_text_color(30, 30, 30)
        desc = str(dados_anuncio.get('descricao'))[:500]
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
    font_name = "DejaVu" if pdf.unicode_font else "Helvetica"
    
    for linha in linhas_analise:
        linha_strip = linha.strip()
        
        if not linha_strip:
            pdf.ln(2)
            continue
        
        # Detectar títulos de seção (## ou 1. Título)
        if linha.startswith('##') or (linha_strip and linha_strip[0].isdigit() and '. ' in linha_strip[:4] and len(linha_strip) < 100):
            pdf.ln(2)
            if pdf.get_y() > 250:
                pdf.add_page()
                
            pdf.set_font(font_name, "B", 11)
            pdf.set_text_color(31, 78, 120)
            titulo_secao = linha_strip.lstrip('#').strip()
            pdf.cell(0, 8, titulo_secao, ln=True)
            
            pdf.set_draw_color(31, 78, 120)
            pdf.set_line_width(0.3)
            pdf.line(18, pdf.get_y(), 60, pdf.get_y())
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
        
        # Detectar subtítulos (###)
        elif linha.startswith('###'):
            pdf.ln(1)
            pdf.set_font(font_name, "B", 10)
            pdf.set_text_color(50, 100, 150)
            pdf.cell(0, 7, f"  > {linha_strip.lstrip('#').strip()}", ln=True)
            pdf.set_text_color(0, 0, 0)
        
        # Detectar listas
        elif linha_strip.startswith('-') or linha_strip.startswith('*') or linha_strip.startswith('[ ]') or linha_strip.startswith('[x]'):
            pdf.set_font(font_name, "", 9)
            pdf.set_text_color(40, 40, 40)
            
            marcador = "•"
            texto_item = linha_strip.lstrip('-* ').strip()
            if linha_strip.startswith('['):
                marcador = "□" if '[ ]' in linha_strip else "▣"
                texto_item = linha_strip[3:].strip()
                
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
            pdf.set_font(font_name, "", 9)
            pdf.set_text_color(0, 0, 0)
            linhas_quebradas = quebrar_texto(linha_strip, 85)
            for linha_quebrada in linhas_quebradas:
                pdf.cell(0, 5, linha_quebrada, ln=True)
    
    # ========== RODAPÉ FINAL ==========
    pdf.ln(10)
    if pdf.get_y() > 260:
        pdf.add_page()
        
    pdf.set_font(font_name, "I", 8)
    pdf.set_text_color(128, 128, 128)
    
    rodape = "Este relatório foi gerado automaticamente pela ferramenta de Análise Inteligente de Anúncios. As recomendações são baseadas em algoritmos de IA e devem ser validadas conforme o contexto do seu negócio."
    linhas_rodape = quebrar_texto(rodape, 95)
    for linha in linhas_rodape:
        pdf.cell(0, 4, linha, ln=True, align="C")
    
    # Gerar PDF
    pdf_bytes = pdf.output()
    return BytesIO(pdf_bytes)
