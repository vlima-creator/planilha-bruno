import streamlit as st

def render_tab_guia_uso():
    """Renderiza a aba de Guia de Uso com instruções e explicação de cálculos em seções expansíveis"""
    
    st.markdown("<div class=\"chart-container\">", unsafe_allow_html=True)
    st.markdown("<div class=\"chart-title\">Guia de Uso - Gestão de Devolução Inteligente</div>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────────────────
    # SEÇÃO 1: COMO COMEÇAR
    # ─────────────────────────────────────────────────────────
    with st.expander("🚀 Como Começar - Passo a Passo", expanded=False):
        st.markdown("""
        ### Passo 1️⃣: Baixar os Relatórios

        Para usar esta ferramenta, você precisa de **dois arquivos Excel** de cada plataforma (Mercado Livre ou Shopee):

        #### 📊 Relatório de Vendas (Mercado Livre)
        1. Acesse: **Vendas > Relatórios > Relatório de Vendas**
        2. Configure o período desejado
        3. Clique em **"Descarregar"** (formato Excel)
        4. Salve o arquivo como `vendas.xlsx`

        #### 📦 Relatório de Devoluções (Mercado Livre)
        1. Acesse: **Devoluções > Relatório de Devoluções**
        2. Configure o mesmo período das vendas
        3. Clique em **"Descarregar"** (formato Excel)
        4. Salve o arquivo como `devolucoes.xlsx`

        #### 🛍️ Relatório de Pedidos (Shopee)
        1. Acesse: **Central do Vendedor > Pedidos > Meus Pedidos**
        2. Clique em **"Exportar"** e selecione o período desejado.
        3. Baixe o arquivo `Order.all.YYYYMMDD_YYYYMMDD.xlsx`.

        #### ↩️ Relatório de Devoluções/Reembolsos (Shopee)
        1. Acesse: **Central do Vendedor > Devolução/Reembolso > Todos**
        2. Clique em **"Exportar"** e selecione o período desejado.
        3. Baixe o arquivo `Order.return_refund.YYYYMMDD_YYYYMMDD_part_1_of_1.xls`.

        ### Passo 2️⃣: Fazer Upload dos Arquivos

        1. Na **Sidebar** (esquerda), clique em **"📁 Upload de Dados"**
        2. Selecione o arquivo de **Vendas** (ou Pedidos da Shopee)
        3. Selecione o arquivo de **Devoluções** (ou Devoluções/Reembolsos da Shopee)
        4. Clique no botão **"🚀 Processar"**
        5. Aguarde o processamento (pode levar alguns segundos)

        ### Passo 3️⃣: Explorar os Dados

        Após o processamento, você terá acesso a:
        - **Dashboard Principal**: Métricas gerais e gráficos
        - **Análise de Devoluções**: Motivos e padrões
        - **Análise de Anúncios**: Ferramenta de IA para otimizar seus anúncios
        """)

    # ─────────────────────────────────────────────────────────
    # SEÇÃO 2: LOCALIZANDO OS RELATÓRIOS
    # ─────────────────────────────────────────────────────────
    with st.expander("🔍 Localizando os Relatórios", expanded=False):
        st.markdown("""
        ### 📍 Localização Exata dos Relatórios

        #### Mercado Livre
        ```
        Painel do Vendedor
        └── Vendas
            └── Relatórios
                └── Relatório de Vendas ← AQUI

        Painel do Vendedor
        └── Devoluções
            └── Relatório de Devoluções ← AQUI
        ```

        #### Shopee
        ```
        Central do Vendedor
        └── Pedidos
            └── Meus Pedidos → Exportar ← AQUI

        Central do Vendedor
        └── Devolução/Reembolso
            └── Todos → Exportar ← AQUI
        ```

        ### ⚙️ Configurações Recomendadas

        - **Período**: Escolha um mês completo ou mais (quanto maior, melhor a análise)
        - **Formato**: Sempre em **Excel (.xlsx ou .xls)**
        - **Colunas**: Mantenha as colunas padrão da plataforma
        - **Idioma**: Português (BR)

        ### 💡 Dica Importante

        > Para análises mais precisas, recomendamos usar dados de **pelo menos 30 dias** de histórico. Isso garante uma quantidade significativa de devoluções para identificar padrões.
        """)

    # ─────────────────────────────────────────────────────────
    # SEÇÃO 3: EXPLICAÇÃO DOS CÁLCULOS E MÉTRICAS
    # ─────────────────────────────────────────────────────────
    with st.expander("📐 Explicação dos Cálculos e Métricas", expanded=False):
        st.markdown("""
        Esta seção detalha o significado e a forma de cálculo de cada indicador apresentado no dashboard, garantindo total transparência e compreensão dos dados.

        ### 1️⃣ Vendas Totais
        - **Significado**: Representa o número total de pedidos únicos registrados no período, antes de qualquer cancelamento ou devolução.
        - **Cálculo**: Contagem de IDs de pedidos únicos no relatório de vendas.

        ### 2️⃣ Vendas Canceladas
        - **Significado**: Número de pedidos únicos que foram cancelados e, portanto, não foram concluídos. Estes pedidos não geram faturamento nem são considerados para a taxa de devolução.
        - **Cálculo**: Contagem de IDs de pedidos únicos com status de cancelamento no relatório de vendas.

        ### 3️⃣ Unidades Vendidas
        - **Significado**: O total de unidades de produtos vendidas em pedidos não cancelados.
        - **Cálculo**: Soma da coluna 'Unidades' para todos os pedidos não cancelados.

        ### 4️⃣ Faturamento por Produtos
        - **Significado**: A receita bruta gerada apenas pela venda dos produtos, excluindo o valor do frete.
        - **Cálculo**: Soma da coluna 'Receita por produtos (BRL)' (Mercado Livre) ou 'Subtotal do produto' (Shopee) para todos os pedidos não cancelados.

        ### 5️⃣ Faturamento Total
        - **Significado**: A receita bruta total, incluindo o valor dos produtos e o valor do frete pago pelo comprador.
        - **Cálculo**: `Faturamento por Produtos + Receita por Envio`

        ### 6️⃣ Devoluções
        - **Significado**: O número de pedidos únicos que tiveram algum tipo de devolução ou reembolso processado no período.
        - **Cálculo**: Contagem de IDs de pedidos únicos presentes no relatório de devoluções que também estão no relatório de vendas do período.

        ### 7️⃣ Taxa de Devolução (%)
        - **Significado**: O percentual de vendas efetivamente enviadas que resultaram em uma devolução. É um indicador chave da qualidade do produto, anúncio ou processo logístico.
        - **Cálculo**: `(Devoluções (pedidos únicos) / (Vendas Totais (pedidos únicos) - Vendas Canceladas (pedidos únicos))) × 100`

        ### 8️⃣ Faturamento de Devoluções
        - **Significado**: O valor total dos produtos que foram devidos e reembolsados aos compradores.
        - **Cálculo**: Soma da coluna 'Cancelamentos e reembolsos (BRL)' (Mercado Livre) ou 'Quantia total de reembolsos' (Shopee) para todas as devoluções únicas.

        ### 9️⃣ Impacto de Devolução
        - **Significado**: O valor financeiro total que representa o reembolso pago ao comprador devido às devoluções. Este valor é o que o vendedor "perde" diretamente com o estorno.
        - **Cálculo**: Soma da coluna 'Cancelamentos e reembolsos (BRL)' (Mercado Livre) ou 'Quantia total de reembolsos' (Shopee) para todas as devoluções únicas.

        ### 1️⃣0️⃣ Perda Parcial
        - **Significado**: Representa os custos que o vendedor não consegue recuperar em uma devolução, mesmo que o produto retorne ao estoque ou haja compensação. Inclui taxas de envio não reembolsáveis, tarifas de venda e, para Shopee, a diferença entre o reembolso e o que o vendedor recebeu/compensação.
        - **Cálculo (Mercado Livre)**: `Soma das tarifas de envio não recuperadas + Soma das tarifas de venda e impostos não recuperadas`
        - **Cálculo (Shopee)**: `Soma de (Quantia total de reembolsos - Renda do pedido - Valor de compensação)` para cada devolução única, considerando apenas valores positivos.

        ### 1️⃣1️⃣ Perda Total
        - **Significado**: O custo total de uma devolução para o vendedor. Inclui a perda do valor do produto (se não recuperado) mais a perda parcial (custos não recuperáveis).
        - **Cálculo**: Se a devolução é classificada como 'Crítica' (produto perdido), `Perda Total = Impacto de Devolução + Perda Parcial`. Se 'Saudável' (produto recuperado), `Perda Total = Perda Parcial`.

        ### 1️⃣2️⃣ Devoluções Saudáveis
        - **Significado**: Número de devoluções onde o produto foi recuperado ou o processo foi concluído sem maiores problemas para o vendedor (ex: produto voltou ao estoque).
        - **Cálculo**: Contagem de devoluções únicas classificadas como 'Saudável' com base no status da devolução.

        ### 1️⃣3️⃣ Devoluções Críticas
        - **Significado**: Número de devoluções problemáticas, onde o produto foi perdido, danificado ou o processo resultou em uma disputa desfavorável ao vendedor.
        - **Cálculo**: Contagem de devoluções únicas classificadas como 'Crítica' com base no status da devolução.

        ### 1️⃣4️⃣ Devoluções Neutras
        - **Significado**: Número de devoluções que estão em processo ou cujo status não permite uma classificação clara como 'Saudável' ou 'Crítica'.
        - **Cálculo**: Contagem de devoluções únicas classificadas como 'Neutra' com base no status da devolução.

        ---

        ### 📊 Indicadores de Saúde

        | Métrica | Excelente | Bom | Atenção | Crítico |
        |---------|-----------|-----|---------|---------|
        | Taxa de Devolução | < 2% | 2-5% | 5-10% | > 10% |
        | Produtos Problemáticos | 0-1 | 2-3 | 4-5 | > 5 |
        | Impacto Financeiro | < R$ 500 | R$ 500-2k | R$ 2k-5k | > R$ 5k |
        """)

    # ─────────────────────────────────────────────────────────
    # SEÇÃO 4: DICAS E BOAS PRÁTICAS
    # ─────────────────────────────────────────────────────────
    with st.expander("💡 Dicas e Boas Práticas", expanded=False):
        st.markdown("""
        ### ✅ Boas Práticas para Reduzir Devoluções

        #### 1. Melhore a Descrição do Anúncio
        - Seja específico e detalhado
        - Use fotos de alta qualidade com fundo branco
        - Inclua medidas e especificações técnicas
        - Responda perguntas frequentes na descrição

        #### 2. Otimize Fotos e Vídeos
        - Mínimo 3 fotos em boa qualidade
        - Primeira foto deve mostrar o produto completo
        - Inclua fotos de detalhes e comparação de tamanho
        - Considere adicionar vídeos/clips (aumenta confiança)

        #### 3. Revise Preço e Competitividade
        - Compare com concorrentes
        - Não precisa ser o mais barato
        - Considere promoções estratégicas
        - Use atacado para aumentar ticket médio

        #### 4. Melhore Logística
        - Use Full (Mercado Livre entrega) quando possível
        - Se usar própria logística, embale bem
        - Avalie prazos de entrega
        - Considere frete grátis para aumentar conversão

        #### 5. Monitore Reputação
        - Responda comentários rapidamente
        - Mantenha termômetro verde (>95%)
        - Atenda bem o cliente pós-venda
        - Solicite avaliações positivas

        #### 6. Analise Regularmente
        - Revise dados semanalmente
        - Identifique padrões de devolução
        - Teste mudanças e meça impacto
        - Documente o que funciona

        ### 🎯 Prioridades de Ação

        1. **Semana 1**: Identifique os 3 produtos com mais devoluções
        2. **Semana 2**: Melhore descrição e fotos desses produtos
        3. **Semana 3**: Revise preço e competitividade
        4. **Semana 4**: Monitore resultados e ajuste

        ### ⚠️ Armadilhas Comuns

        - ❌ Não atualizar anúncios regularmente
        - ❌ Usar fotos de baixa qualidade
        - ❌ Descrição muito genérica
        - ❌ Preço muito acima da concorrência
        - ❌ Não responder perguntas dos clientes
        - ❌ Embalagem inadequada
        """)

    st.markdown("---")
    st.markdown("**Dica Final:** Esta ferramenta é um complemento à sua análise. Combine os dados aqui com sua experiência de vendedor para tomar as melhores decisões! 🎯")
    
    st.markdown("</div>", unsafe_allow_html=True)
