import streamlit as st
from datetime import datetime
from utils.analise_anuncios import processar_analise_completa
from utils.export_anuncio_pdf import gerar_pdf_analise_anuncio

def render_tab_analise_anuncios():
    """Renderiza a aba de Análise de Anúncios com IA"""
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Análise Inteligente de Anúncios com IA</div>', unsafe_allow_html=True)
    
    # Seção de configuração
    st.markdown("### ⚙️ Configuração")
    
    url_anuncio = st.text_input(
        "Cole o link do anúncio (Mercado Livre ou similar)",
        placeholder="https://www.mercadolivre.com.br/...",
        key="url_anuncio_input"
    )
    
    # Prompt de análise em um expander
    prompt_padrao = """Prompt de Análise de Anúncios - Mercado Livre (V.2.0)
Analise o anúncio do Mercado Livre que enviarei abaixo e entregue a resposta rigorosamente nas seções seguintes.

⚠️ Regra importante sobre catálogo
Se este for um anúncio de catálogo, sinalize isso logo no início da resposta e NÃO sugira alterações em campos travados (como título ou ficha técnica padrão). Foque apenas em melhorias permitidas (preço, atacado, promoções, logística, reputação, conteúdo complementar, etc.).

1. Diagnóstico de RELEVÂNCIA NA BUSCA (Relevância Direta)
Liste o que está prejudicando a exposição orgânica em:
- Título: (Análise de palavras-chave e uso de caracteres).
- Categoria: (Se está na árvore de categoria correta).
- Atributos/Ficha Técnica: (Campos vazios ou preenchidos incorretamente).
- Variações: (Uso correto de cores, tamanhos ou voltagem).
- Compliance/Políticas: (Infrações que podem causar queda de exposição).

2. Diagnóstico de CONVERSÃO (Relevância Indireta)
Liste o que impede o clique de virar venda em:
- Preço e Promoções: (Competitividade).
- Entrega/Logística: (Uso de Full, Flex ou prazos abusivos).
- Reputação e Reviews: (Impacto das avaliações e termômetro do vendedor).
- Fotos e Vídeos: (Qualidade visual, fundo branco, proporção e presença de vídeos/clips).
- Clareza da Oferta: (Descrição, quebra de objeções e perguntas frequentes).

3. Top 10 Melhorias Prioritárias
Uma lista numerada do 1 ao 10 (em ordem de prioridade), contendo:
- O que fazer: Ação objetiva.
- Por quê: Justificativa estratégica.
- Impacto: (Busca, Conversão ou Ambos).

4. Sugestão de TÍTULOS e Análise de Curva
Para cada sugestão abaixo, avalie primeiro a curva do anúncio:
Critério de Decisão: Se o anúncio já possui vendas constantes e histórico relevante (Anúncio Quente), a orientação deve ser NÃO ALTERAR O TÍTULO e sim criar um NOVO ANÚNCIO (CLONE) com a nova sugestão para evitar a perda de indexação. Se o anúncio tem poucas vendas ou está estagnado (Anúncio Frio), a orientação deve ser a ALTERAÇÃO DIRETA no título atual.
Sugira:
- Título Principal Otimizado (Até 60 caracteres).
- Variação Genérica (Foco em termos amplos).
- Variação Cauda Longa (Foco em especificidade).
- Variação Benefício (Foco em dor/solução).

5. Preço, Atacado e Promoções
- Preço de Atacado: Avalie se o ticket médio e público permitem atacado. Sugira faixas (Ex: 3un, 5un) e descontos coerentes.
- Promoções: Verifique se há "Central de Promoções" ativa e qual o melhor formato (Oferta do Dia, Relâmpago ou Leve mais por menos). Alerte sobre a margem para não depender apenas de desconto.

6. Checklist Final
Um checklist de até 10 itens no formato [ ] ação com os pontos cruciais para revisão antes da publicação/atualização."""
    
    with st.expander("📝 Prompt de Análise (Customizável)"):
        prompt_usuario = st.text_area(
            "Prompt de Análise",
            value=prompt_padrao,
            height=350,
            key="prompt_usuario_input"
        )
    
    # Se o expander não foi aberto, usar o prompt padrão
    if 'prompt_usuario_input' not in st.session_state:
        prompt_usuario = prompt_padrao
    else:
        prompt_usuario = st.session_state.get('prompt_usuario_input', prompt_padrao)
    
    # Botão de análise
    st.markdown("### 🚀 Executar Análise")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        btn_analisar = st.button("🔍 Analisar Anúncio", use_container_width=True, type="primary")
    with col2:
        btn_limpar = st.button("🗑️ Limpar", use_container_width=True)
    
    if btn_limpar:
        st.rerun()
    
    # Executar análise
    if btn_analisar:
        if not url_anuncio:
            st.error("❌ Por favor, cole um link válido do anúncio.")
        else:
            # Usar o prompt do session_state se foi customizado, senão usar o padrão
            prompt_final = st.session_state.get('prompt_usuario_input', prompt_padrao)
            
            with st.spinner("⏳ Analisando anúncio... Isso pode levar alguns segundos."):
                try:
                    resultado = processar_analise_completa(url_anuncio, prompt_final)
                    
                    if resultado['status'] == 'erro':
                        st.error(f"❌ Erro ao processar: {resultado.get('mensagem', 'Erro desconhecido')}")
                    else:
                        # Exibir análise da IA em um container destacado
                        st.markdown("---")
                        st.markdown("### 🤖 Análise da IA")
                        
                        with st.container(border=True):
                            st.markdown(resultado['analise_ia'])
                        
                        # Adicionar informações de quando foi gerada
                        st.markdown(f"*Análise gerada em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*")
                        
                        # Botão para gerar PDF
                        st.markdown("---")
                        st.markdown("### 📥 Exportar Relatório")
                        
                        try:
                            # Gerar PDF
                            pdf_bytes = gerar_pdf_analise_anuncio(
                                dados_anuncio=resultado['dados_extraidos'],
                                analise_ia=resultado['analise_ia'],
                                url=url_anuncio
                            )
                            
                            # Botão de download
                            st.download_button(
                                label="📄 Baixar Relatório em PDF",
                                data=pdf_bytes,
                                file_name=f"analise_anuncio_{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                type="primary"
                            )
                            
                            st.success("✅ PDF pronto para download! Clique no botão acima para baixar o relatório completo.")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar PDF: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Erro durante a análise: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Dicas de uso
    with st.expander("💡 Dicas de Uso"):
        st.markdown("""
        - **Link:** Funciona com anúncios do Mercado Livre, Amazon e outras plataformas
        - **Prompt:** O prompt padrão (V.2.0) está otimizado para análise profunda de anúncios do Mercado Livre
        - **Customização:** Você pode editar o prompt no expander "Prompt de Análise" para adaptar às suas necessidades
        - **PDF:** Você pode exportar a análise completa em PDF para compartilhar ou arquivar
        - **Histórico:** Você pode manter múltiplas análises abertas em abas diferentes do navegador para comparação
        """)
