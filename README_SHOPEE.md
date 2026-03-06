# 📊 Gestão de Devolução Inteligente (ML & Shopee)

Este dashboard foi atualizado para suportar tanto o **Mercado Livre** quanto a **Shopee**, permitindo uma análise profunda de vendas e devoluções em ambas as plataformas com a mesma interface intuitiva.

## 🚀 Novidades na Versão Shopee

- **Detecção Automática:** O sistema identifica se o arquivo é do Mercado Livre ou da Shopee assim que você faz o upload.
- **Mapeamento de Dados:** Os relatórios da Shopee (`Order.all`, `Order.cancelled` e `Order.return_refund`) são processados para extrair SKUs, motivos de devolução e impacto financeiro.
- **Cálculo de Reembolso Corrigido:** Implementada lógica para ler corretamente os valores de reembolso da Shopee.
- **Performance Otimizada:** Refatoração do motor de processamento para ser até 10x mais rápido em grandes volumes de dados.

## 📁 Como usar com a Shopee

Para uma análise completa, faça o upload dos seguintes arquivos na barra lateral:

1.  **Relatório de Vendas:** Use o arquivo `Order.all.YYYYMMDD_YYYYMMDD.xlsx` (exportado de Central do Vendedor > Meus Pedidos).
2.  **Relatório de Devoluções:** Use o arquivo `Order.return_refund.YYYYMMDD_YYYYMMDD.xls` (exportado de Central do Vendedor > Devoluções).

## 🛠️ Correções Técnicas Realizadas

- **Bug Financeiro:** Corrigido o uso de colunas erradas no Mercado Livre que causavam erro no cálculo de lucro/perda.
- **Exportação XLSX:** Corrigido o erro `KeyError` que impedia a geração de relatórios Excel.
- **Limpeza:** Removidos arquivos residuais de React/TypeScript que poluíam o repositório.

---
*Desenvolvido para otimizar sua operação de e-commerce.*
