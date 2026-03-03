
import streamlit as st

st.set_page_config(page_title="Calculadora de Ponto de Equilíbrio", layout="centered")

st.title("📊 Calculadora de Ponto de Equilíbrio")
st.write("Calcule o ponto de equilíbrio da sua empresa inserindo os dados abaixo.")

# Entradas do usuário
st.header("Dados da Empresa")

custos_fixos = st.number_input("Custos Fixos Totais (R$)", min_value=0.0, value=10000.0, step=100.0)
preco_venda_unitario = st.number_input("Preço de Venda por Unidade (R$)", min_value=0.0, value=50.0, step=1.0)
custo_variavel_unitario = st.number_input("Custo Variável por Unidade (R$)", min_value=0.0, value=20.0, step=1.0)

# Validação e cálculo
if preco_venda_unitario <= custo_variavel_unitario:
    st.error("O Preço de Venda por Unidade deve ser maior que o Custo Variável por Unidade para que haja lucro.")
else:
    margem_contribuicao_unitario = preco_venda_unitario - custo_variavel_unitario
    ponto_equilibrio_unidades = custos_fixos / margem_contribuicao_unitario
    ponto_equilibrio_receita = ponto_equilibrio_unidades * preco_venda_unitario

    st.header("Resultados")
    st.success(f"**Margem de Contribuição por Unidade:** R$ {margem_contribuicao_unitario:,.2f}")
    st.success(f"**Ponto de Equilíbrio em Unidades:** {ponto_equilibrio_unidades:,.2f} unidades")
    st.success(f"**Ponto de Equilíbrio em Receita:** R$ {ponto_equilibrio_receita:,.2f}")

    st.markdown("""
    ### Entendendo o Ponto de Equilíbrio
    O **Ponto de Equilíbrio** é o nível de vendas (em unidades ou receita) no qual a receita total é igual aos custos totais, resultando em lucro zero. 
    Atingir este ponto significa que a empresa cobriu todos os seus custos fixos e variáveis. Vendas acima deste ponto geram lucro, enquanto vendas abaixo resultam em prejuízo.
    """)

