# Dashboard Vendas x Devoluções

Dashboard Streamlit profissional para análise de vendas e devoluções do Mercado Livre (BR) com upload de arquivos Excel, processamento client-side e exportação de resultados.

## 🎯 Funcionalidades

### Upload e Processamento
- ✅ Upload de 2 arquivos Excel (Vendas + Devoluções)
- ✅ Validação automática de formato
- ✅ Botão "Carregar Exemplo" com dados pré-carregados
- ✅ Processamento 100% client-side (sem servidor)

### Análise de Dados
- ✅ **Resumo Executivo**: KPIs principais e qualidade do arquivo
- ✅ **Janelas de Tempo**: Análise por períodos (30, 60, 90, 120, 150, 180 dias)
- ✅ **Matriz vs Full**: Comparação de canais
- ✅ **Frete**: Análise por forma de entrega (em desenvolvimento)
- ✅ **Motivos**: Distribuição de motivos de devolução (em desenvolvimento)
- ✅ **Ads**: Análise de vendas por publicidade (em desenvolvimento)
- ✅ **SKUs**: Ranking de SKUs por risco (em desenvolvimento)
- ✅ **Simulador**: Simulação de impacto com redução de taxa (em desenvolvimento)

### Métricas Calculadas
- Taxa de devolução
- Impacto financeiro
- Perda total e parcial
- Classificação (Saudável/Crítica/Neutra)
- Qualidade do arquivo
- Score de risco por SKU

### Export
- ✅ Exportar resultados em XLSX
- ✅ Múltiplas abas com dados consolidados
- ✅ Dados brutos para análise adicional

## 🚀 Como Usar

### Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
streamlit run app.py
```

Acesse: `http://localhost:8501`

### Deploy no Streamlit Cloud (Recomendado)

#### Passo 1: Acesse Streamlit Cloud
1. Vá para [share.streamlit.io](https://share.streamlit.io)
2. Faça login com sua conta GitHub

#### Passo 2: Criar novo app
1. Clique em "New app"
2. Selecione:
   - **Repository**: `vlima-creator/Dashboard-Devolu-o`
   - **Branch**: `main`
   - **Main file path**: `app.py`

#### Passo 3: Deploy
1. Clique em "Deploy"
2. Aguarde ~2-3 minutos
3. Seu app estará disponível em: `https://dashboard-devolu-o.streamlit.app`

## 📁 Estrutura do Projeto

```
Dashboard-Devolu-o/
├── app.py                    # Aplicação Streamlit principal
├── utils/
│   ├── __init__.py
│   ├── parser.py            # Parser de Excel
│   ├── metricas.py          # Cálculo de métricas
│   └── export.py            # Export XLSX
├── public/
│   └── examples/            # Arquivos de exemplo
│       ├── vendas_exemplo.xlsx
│       └── devolucoes_exemplo.xlsx
├── .streamlit/
│   └── config.toml          # Configuração Streamlit
├── requirements.txt         # Dependências Python
└── README.md
```

## 📊 Formato dos Arquivos

### Arquivo de Vendas
Aba: `Vendas BR`

Colunas obrigatórias:
- N.º de venda
- Data da venda
- SKU
- Receita por produtos (BRL)
- Receita por envio (BRL)
- Custo de envio com base nas medidas e peso declarados
- Tarifa de venda e impostos (BRL)
- Venda por publicidade

### Arquivo de Devoluções
Abas: `devoluções vendas matriz` e `devoluções vendas full`

Colunas obrigatórias:
- N.º de venda
- Cancelamentos e reembolsos (BRL)
- Tarifa de venda e impostos (BRL)
- Custo de envio com base nas medidas e peso declarados
- Estado
- Motivo do resultado
- Forma de entrega
- Canal

## 🛠️ Tecnologias

- **Python 3.11+**
- **Streamlit** - Framework web
- **Pandas** - Processamento de dados
- **Plotly** - Gráficos interativos
- **OpenPyXL** - Leitura/escrita de Excel

## 🔒 Privacidade

- ✅ Processamento 100% client-side
- ✅ Nenhum dado é enviado para servidor
- ✅ Nenhuma autenticação necessária
- ✅ Dados não são armazenados

## 📝 Licença

MIT

## 🤝 Contribuições

Contribuições são bem-vindas! Abra uma issue ou pull request.

---

**Desenvolvido com ❤️ para análise de Mercado Livre**
