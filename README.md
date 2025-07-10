
 🧠 Projeto de Pipeline de Machine Learning com API Flask

Este projeto demonstra a construção de um pipeline completo de Machine Learning, desde a coleta de dados com Web Scraping até o consumo de predições via API Flask.

---

## 📊 1. Diagrama de Pipeline

```
flowchart TD
    A[📥 Ingestão de Dados (Web Scraping)] --> B[🗂️ Armazenamento CSV]
    B --> C[🧹 Pré-processamento & Unificação (Pandas)]
    C --> D[🚀 API Flask]
    D --> E[🌐 Consumo por Frontend, Cientistas de Dados, Apps]
    C --> F[🤖 Modelo de ML (Treinamento/Predição)]
    F --> D
```
    
---

## 🧾 2. Descrição do Pipeline

### 📥 Ingestão  
- Dados coletados via Web Scraping de um site de livros.  
- Armazenamento em arquivos `.csv` no diretório `exports/csv/`.

### 🔄 Processamento  
- Unificação dos arquivos CSV e pré-processamento com Pandas.  
- Geração do arquivo `tabela_unificada.csv`.  
- Limpeza de dados, tratamento de tipos e codificação de variáveis categóricas.

### 🚀 API  
A API Flask expõe os seguintes endpoints RESTful:

- 🔍 **Consulta e busca**
- 📊 **Estatísticas**
- 🔐 **Autenticação (JWT)**
- 🤖 **Predição com modelo ML**

### 🤖 Machine Learning  
- Treinamento de um modelo **RandomForest** para prever o `rating` dos livros.  
- Exposição do modelo via endpoint: `/api/v1/ml/predictions`.

### 🌐 Consumo  
- Cientistas de dados, aplicações web/mobile e dashboards podem consumir a API para análises, visualizações ou automações.

---

## 🏗️ 3. Arquitetura para Escalabilidade

### 🧩 Separação de Responsabilidades  
- Módulos independentes: scraping, processamento, API, ML.  
- Fácil manutenção e escalabilidade.

### 🗃️ Persistência  
- Dados armazenados em CSVs, com possibilidade futura de migração para PostgreSQL ou MongoDB.  
- Modelos versionados em disco (futuramente para S3, MLflow, etc).

### ⚙️ API Stateless  
- Flask pode ser servido por Gunicorn ou UWSGI atrás de um Nginx.  
- Suporte a escalabilidade horizontal (Docker, Kubernetes).

### 🧠 ML como Serviço  
- Modelo ML exposto como microserviço (ex: FastAPI, BentoML).  
- Possibilita re-treinamento e versionamento independentes.

---

## 👨‍🔬 4. Cenário de Uso para Cientistas de Dados/ML

### 📂 Acesso aos Dados  
Endpoints:

- `/api/v1/ml/features`
- `/api/v1/ml/training-data`

Permitem acesso aos dados prontos para análise e modelagem local.

### 📈 Predição Online  
- Endpoint `/api/v1/ml/predictions`: permite envio de dados e retorno da predição em tempo real.

### 🔁 Atualização do Modelo  
- Re-treinamento automático a partir dos CSVs.  
- Futuro: CI/CD para automação do deploy de modelos.

---

## 🔌 5. Plano de Integração com Modelos de ML

### 🎯 Treinamento  
- Script `data_model.py` realiza o treinamento e salva o modelo.  
- Pode ser agendado com `cron`, `Airflow`, etc.

### 🧠 Predição  
- Modelo carregado na inicialização da API.  
- Predições via requisições REST.

### 📊 Monitoramento  
- Exposição de métricas de performance por endpoint.  
- Logs de predições armazenados para análise de *model drift*.

---

## 🚀 6. Futuras Evoluções

- 📦 Migrar dados para banco relacional (PostgreSQL) ou NoSQL (MongoDB)  
- 🛠️ Orquestrar scraping e processamento com Apache Airflow  
- 🤖 Servir modelo com FastAPI, BentoML ou Seldon  
- 🔐 Adicionar autenticação OAuth2, rate limiting e cache com Redis  
- ☁️ Deploy em nuvem (AWS, Azure, GCP) com integração CI/CD  

---

## 📌 Referências

- Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)  
- Scikit-learn: [https://scikit-learn.org/](https://scikit-learn.org/)  
- JWT: [https://jwt.io/](https://jwt.io/)

---
