# Pipeline Macro & Mercado Brasil

> 🚧 Em construção — pipeline de engenharia de dados ponta a ponta que combina indicadores macroeconômicos do Banco Central com preços de ações da B3, publicado como um dashboard interativo e gratuito, atualizado automaticamente.

## O que este projeto faz

Extrai a taxa Selic, o IPCA e a cotação USD/BRL do Banco Central do Brasil, além de preços de ações da B3 (via yfinance, com fallback para brapi.dev), carrega tudo no DuckDB, transforma através de um pipeline dbt em camadas bronze → silver → gold com testes automatizados de qualidade de dados, e publica um relatório interativo no GitHub Pages — atualizado periodicamente via GitHub Actions.

Notas de construção e arquitetura completas serão adicionadas aqui conforme cada etapa for finalizada.

## Roadmap do portfólio

Este é o projeto 1 de 3 num portfólio de dados mais amplo, cada um combinando um tema diferente com uma stack diferente:

| # | Tema | Foco | Stack |
|---|------|------|-------|
| 1 | Macro & mercado brasileiro (este repo) | Engenharia de Dados | Python, DuckDB, dbt, GitHub Actions, GitHub Pages |
| 2 | Análise esportiva | Análise de Dados | Notebooks/Quarto, Plotly |
| 3 | E-commerce/varejo | Cloud + BI | AWS/GCP free tier |

## Licença

MIT — veja [LICENSE](LICENSE).
