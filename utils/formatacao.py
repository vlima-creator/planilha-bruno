"""
Módulo de formatação padronizada para o Dashboard.

Padrões:
- BRL: R$ 132.715,54  (ponto para milhar, vírgula para decimal)
- BRL negativo: -R$ 132.715,54
- Percentual: 21.1%   (ponto para decimal, 1 casa)
- Número: 7.857       (ponto para milhar)
"""

def formatar_brl(valor):
    """
    Formata valor monetário no padrão BRL: R$ 132.715,54
    Valores negativos: -R$ 132.715,54
    """
    if valor is None or (isinstance(valor, float) and valor != valor):  # NaN check
        return "R$ 0,00"
    
    try:
        valor = float(valor)
        negativo = valor < 0
        valor_abs = abs(valor)
        # Formatar com separador de milhares (.) e decimal (,)
        formatado = f"{valor_abs:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if negativo:
            return f"-R$ {formatado}"
        return f"R$ {formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def formatar_percentual(valor, casas_decimais=1):
    """
    Formata percentual para padrão: 21.1%
    
    Se o valor estiver entre -1 e 1 (exclusive 0), multiplica por 100.
    Se o valor já estiver >= 1 ou <= -1, assume que já está em percentual.
    """
    if valor is None or (isinstance(valor, float) and valor != valor):  # NaN check
        return "0.0%"
    
    try:
        valor = float(valor)
        
        # Se valor está entre -1 e 1 (e não é 0), converter para percentual
        if -1 < valor < 1 and valor != 0:
            valor = valor * 100
        
        formato = f"{{:.{casas_decimais}f}}"
        return formato.format(valor) + "%"
    except (ValueError, TypeError):
        return "0.0%"


def formatar_pct_direto(valor, casas_decimais=1):
    """
    Formata percentual SEM conversão automática.
    Recebe valor já em percentual (ex: 21.1, não 0.211).
    Ideal para valores que já foram calculados como percentual.
    """
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "0.0%"
    
    try:
        valor = float(valor)
        formato = f"{{:.{casas_decimais}f}}"
        return formato.format(valor) + "%"
    except (ValueError, TypeError):
        return "0.0%"


def formatar_numero(valor, casas_decimais=0):
    """
    Formata número com ponto como separador de milhar: 7.857
    """
    if valor is None or (isinstance(valor, float) and valor != valor):  # NaN check
        return "0"
    
    try:
        valor = float(valor)
        if casas_decimais == 0:
            return f"{int(valor):,}".replace(",", ".")
        else:
            formato = f"{{:,.{casas_decimais}f}}"
            return formato.format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0"


def formatar_risco(valor):
    """
    Formata score de risco com ponto como separador de milhar: 185.801
    """
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "0"
    
    try:
        valor = float(valor)
        return f"{int(round(valor)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"


# Testes
if __name__ == "__main__":
    print("TESTES DE FORMATAÇÃO")
    print("=" * 60)
    
    # Testes BRL
    print("\nTestes BRL:")
    print(f"  1234.56 -> {formatar_brl(1234.56)}")             # R$ 1.234,56
    print(f"  132715.54 -> {formatar_brl(132715.54)}")         # R$ 132.715,54
    print(f"  -238500.00 -> {formatar_brl(-238500.00)}")       # -R$ 238.500,00
    print(f"  0 -> {formatar_brl(0)}")                         # R$ 0,00
    print(f"  -52446.24 -> {formatar_brl(-52446.24)}")         # -R$ 52.446,24
    
    # Testes Percentual (com auto-conversão)
    print("\nTestes Percentual (auto-conversão):")
    print(f"  0.082 -> {formatar_percentual(0.082)}")          # 8.2%
    print(f"  0.211 -> {formatar_percentual(0.211)}")          # 21.1%
    
    # Testes Percentual direto
    print("\nTestes Percentual (direto):")
    print(f"  8.2 -> {formatar_pct_direto(8.2)}")             # 8.2%
    print(f"  21.1 -> {formatar_pct_direto(21.1)}")           # 21.1%
    
    # Testes Número
    print("\nTestes Número:")
    print(f"  7857 -> {formatar_numero(7857)}")                # 7.857
    print(f"  641 -> {formatar_numero(641)}")                  # 641
    
    # Testes Risco
    print("\nTestes Risco:")
    print(f"  185801.5 -> {formatar_risco(185801.5)}")         # 185.802
    print(f"  15004.3 -> {formatar_risco(15004.3)}")           # 15.004
