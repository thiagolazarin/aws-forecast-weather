# 🌤️ Previsão de Temperatura com Machine Learning e AWS

Este projeto automatiza a previsão de temperatura para diferentes cidades, utilizando dados da API Open-Meteo, machine learning com Python e infraestrutura em nuvem da AWS. O resultado é visualizado em tempo real no Power BI através do Amazon Athena.

---

## 🚀 Tecnologias Utilizadas

- **Python + Jupyter Notebook** (pré-processamento e modelagem)
- **AWS S3** (armazenamento de dados e modelos)
- **AWS Lambda** (execução automatizada de previsões e gatilhos)
- **AWS Glue Crawler** (catálogo automático de dados)
- **Amazon Athena** (consulta SQL sobre dados particionados)
- **Power BI** (visualização dos resultados)
- **Open-Meteo API** (dados de clima abertos)

---

## 🧠 Funcionalidade do Projeto

1. **Extração de Dados**
   - Usa Jupyter para coletar dados históricos da Open-Meteo

2. **Modelagem**
   - Treina um modelo de machine learning (SVR) com features temporais
   - Salva o modelo e o scaler em um bucket S3

3. **Agendamento**
   - Um agendador do Windows executa a previsão semanalmente via script Python

4. **Execução da Previsão**
   - Um Lambda executa o modelo, gera previsões para 7 dias e salva no S3 em formato particionado (`data=` e `cidade=`)

5. **Atualização automática**
   - Outro Lambda escuta o S3 e dispara o Glue Crawler para atualizar o catálogo

6. **Consulta e Visualização**
   - Dados são consultados via Athena e visualizados no Power BI via ODBC

---

## 🗂️ Estrutura de Pastas
```
EXTRACT-DATA-FORECAST/
├── aws_lambda/              # Código da Lambda que gera previsões
│   ├── __init__.py
│   ├── predict_lambda.py
│   └── requirements.txt
├── events/
│   └── event.json           # Exemplo de evento de teste para a Lambda
├── load-data/
│   └── data-extract.ipynb   # Notebook para extrair dados históricos do Open-Meteo
├── ml/
│   ├── forecast_weather.ipynb
│   ├── scaler.pkl           # Scaler do modelo
│   └── svr_model.pkl        # Modelo treinado (SVR)
├── tests/
│   └── __init__.py
├── .gitignore
├── samconfig.toml           # Configuração SAM CLI
├── README.md                # Este arquivo
└── .aws-sam/                # Ignorado (build temporário do SAM)
```

## ⚙️ Fluxo de Execução

1. **load-data**: coleta dados históricos com Jupyter + Open-Meteo
2. **ml**: treina modelo SVR com features de hora e mês (seno/cosseno)
3. **aws_lambda**: Lambda gera previsão dos próximos 7 dias e salva JSON particionado no S3
4. **Crawler**: é acionado automaticamente por outra Lambda quando um novo arquivo é salvo no bucket
5. **Athena**: consulta os dados no formato `data=YYYY-MM-DD`, `cidade=sao_paulo`, etc.
6. **Power BI**: conexão via ODBC com Athena para visualização