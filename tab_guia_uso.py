import streamlit as st

def render_tab_guia_uso():
    """Renderiza a aba de Guia de Uso com instruções e explicação de cálculos"""
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📖 Guia de Uso - Gestão de Devolução Inteligente</div>', unsafe_allow_html=True)
    
    # ========== SEÇÃO 1: COMO COMEÇAR ==========
    with st.expander("🚀 Como Começar - Passo a Passo", expanded=True):
        st.markdown("""
        ### Passo 1️⃣: Baixar os Relatórios do Mercado Livre
        
        Para usar esta ferramenta, você precisa de **dois arquivos Excel** do Mercado Livre:
        
        #### 📊 Relatório de Vendas
        1. Acesse: **Vendas > Relatórios > Relatório de Vendas**
        2. Configure o período desejado
        3. Clique em **"Descarregar"** (formato Excel)
        4. Salve o arquivo como `vendas.xlsx`
        
        #### 📦 Relatório de Devoluções
        1. Acesse: **Devoluções > Relatório de Devoluções**
        2. Configure o mesmo período das vendas
        3. Clique em **"Descarregar"** (formato Excel)
        4. Salve o arquivo como `devolucoes.xlsx`
        
        ### Passo 2️⃣: Fazer Upload dos Arquivos
        
        1. Na **Sidebar** (esquerda), clique em **"📁 Upload de Dados"**
        2. Selecione o arquivo de **Vendas** (`vendas.xlsx`)
        3. Selecione o arquivo de **Devoluções** (`devolucoes.xlsx`)
        4. Clique no botão **"🚀 Processar"**
        5. Aguarde o processamento (pode levar alguns segundos)
        
        ### Passo 3️⃣: Explorar os Dados
        
        Após o processamento, você terá acesso a:
        - **Dashboard Principal**: Métricas gerais e gráficos
        - **Análise de Devoluções**: Motivos e padrões
        - **Análise de Anúncios**: Ferramenta de IA para otimizar seus anúncios
        """)
    
    # ========== SEÇÃO 2: ONDE ENCONTRAR OS RELATÓRIOS ==========
    with st.expander("🔍 Localizando os Relatórios no Mercado Livre"):
        st.markdown("""
        ### 📍 Localização Exata dos Relatórios
        
        #### Relatório de Vendas
        ```
        Painel do Vendedor
        └── Vendas
            └── Relatórios
                └── Relatório de Vendas ← AQUI
        ```
        
        #### Relatório de Devoluções
        ```
        Painel do Vendedor
        └── Devoluções
            └── Relatório de Devoluções ← AQUI
        ```
        
        ### ⚙️ Configurações Recomendadas
        
        - **Período**: Escolha um mês completo ou mais (quanto maior, melhor a análise)
        - **Formato**: Sempre em **Excel (.xlsx)**
        - **Colunas**: Mantenha as colunas padrão do Mercado Livre
        - **Idioma**: Português (BR)
        
        ### 💡 Dica Importante
        
        > Para análises mais precisas, recomendamos usar dados de **pelo menos 30 dias** de histórico. 
        > Isso garante uma quantidade significativa de devoluções para identificar padrões.
        """)
    
    # ========== SEÇÃO 3: EXPLICAÇÃO DOS CÁLCULOS ==========
    with st.expander("📐 Explicação dos Cálculos e Métricas"):
        st.markdown("""
        ### 1️⃣ Taxa de Devolução (%)
        
        **Fórmula:**
        ```
        Taxa de Devolução = (Total de Devoluções / Total de Vendas) × 100
        ```
        
        **O que significa:**
        - Percentual de vendas que resultaram em devolução
        - Quanto maior, mais problemas com seus produtos/anúncios
        - **Benchmark Mercado Livre**: ~3-5% é considerado bom
        
        **Exemplo:**
        - 100 vendas, 5 devoluções = 5% de taxa de devolução
        
        ---
        
        ### 2️⃣ Impacto Financeiro da Devolução (R$)
        
        **Fórmula:**
        ```
        Impacto Financeiro = Preço Médio × Total de Devoluções
        ```
        
        **O que significa:**
        - Quanto você deixou de ganhar com as devoluções
        - Não inclui custos de reembolso/logística (apenas perda de venda)
        - Ajuda a priorizar quais SKUs focar
        
        **Exemplo:**
        - Preço médio: R$ 100
        - 10 devoluções = R$ 1.000 de impacto
        
        ---
        
        ### 3️⃣ Motivos de Devolução
        
        **Categorias Analisadas:**
        - **Descrição não corresponde ao anúncio**: Problema de comunicação
        - **Produto com defeito**: Problema de qualidade
        - **Produto danificado na entrega**: Problema de logística
        - **Não é o produto que eu queria**: Problema de clareza/fotos
        - **Outros**: Motivos diversos
        
        **Interpretação:**
        - Se maioria é "Descrição não corresponde" → Revise seu anúncio
        - Se maioria é "Defeito" → Revise qualidade do produto
        - Se maioria é "Danificado" → Revise embalagem/logística
        
        ---
        
        ### 4️⃣ Análise por SKU (Produto)
        
        **Fórmula:**
        ```
        Taxa de Devolução por SKU = (Devoluções do SKU / Vendas do SKU) × 100
        ```
        
        **O que significa:**
        - Identifica quais produtos têm mais problemas
        - Prioriza ações corretivas nos produtos problemáticos
        - Ajuda a identificar produtos com qualidade inconsistente
        
        ---
        
        ### 5️⃣ Análise por Canal (Matriz vs Full)
        
        **Definições:**
        - **Matriz**: Produtos do seu próprio catálogo
        - **Full**: Produtos de outros vendedores (você apenas vende)
        
        **O que significa:**
        - Compara performance entre canais
        - Identifica se problemas vêm de qualidade (Matriz) ou logística (Full)
        
        ---
        
        ### 6️⃣ Análise por Publicidade (Ads)
        
        **Fórmula:**
        ```
        Taxa Ads vs Orgânico = Comparação de devoluções entre vendas pagas e orgânicas
        ```
        
        **O que significa:**
        - Identifica se anúncios pagos trazem clientes com mais devoluções
        - Pode indicar problema na segmentação de anúncios
        - Ajuda a otimizar ROI de publicidade
        
        ---
        
        ### 7️⃣ Simulação de Redução
        
        **Fórmula:**
        ```
        Impacto da Redução = Taxa Atual - Taxa Simulada
        Economia Potencial = Impacto Financeiro × (Redução em %)
        ```
        
        **O que significa:**
        - Mostra quanto você economizaria se reduzisse devoluções
        - Ajuda a priorizar ações com maior ROI
        - Exemplo: Reduzir de 5% para 3% economiza X% do impacto
        
        ---
        
        ### 📊 Indicadores de Saúde
        
        | Métrica | Excelente | Bom | Atenção | Crítico |
        |---------|-----------|-----|---------|---------|
        | Taxa de Devolução | < 2% | 2-5% | 5-10% | > 10% |
        | Produtos Problemáticos | 0-1 | 2-3 | 4-5 | > 5 |
        | Impacto Financeiro | < R$ 500 | R$ 500-2k | R$ 2k-5k | > R$ 5k |
        """)
    
    # ========== SEÇÃO 4: DICAS E BOAS PRÁTICAS ==========
    with st.expander("💡 Dicas e Boas Práticas"):
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
    
    # ========== SEÇÃO 5: SUPORTE ==========
    with st.expander("🆘 Suporte e Troubleshooting"):
        st.markdown("""
        ### ❓ Perguntas Frequentes
        
        **P: Os arquivos não estão sendo processados**
        - Verifique se os arquivos estão em formato Excel (.xlsx)
        - Certifique-se de que os nomes das colunas estão em português
        - Tente fazer download novamente dos relatórios
        
        **P: Os dados parecem incorretos**
        - Verifique se o período dos dois relatórios é o mesmo
        - Confirme que não há filtros aplicados nos relatórios
        - Tente com um período menor (ex: últimos 7 dias)
        
        **P: A ferramenta de IA não está funcionando**
        - Verifique sua conexão com a internet
        - Tente novamente em alguns minutos
        - Verifique se a chave de API está configurada
        
        **P: Posso usar dados de múltiplos períodos?**
        - Sim, mas combine os arquivos em um único Excel antes
        - Ou processe um período por vez e compare
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== RESUMO VISUAL ==========
    st.markdown("---")
    st.markdown("### 📋 Resumo Rápido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📥 Upload
        1. Baixe 2 arquivos
        2. Faça upload
        3. Clique processar
        """)
    
    with col2:
        st.markdown("""
        #### 📊 Análise
        1. Veja métricas
        2. Identifique problemas
        3. Priorize ações
        """)
    
    with col3:
        st.markdown("""
        #### 🚀 Otimização
        1. Implemente mudanças
        2. Monitore resultados
        3. Repita processo
        """)
    
    st.markdown("""
    ---
    **Dica Final:** Esta ferramenta é um complemento à sua análise. Combine os dados aqui com sua experiência 
    de vendedor para tomar as melhores decisões! 🎯
    """)
