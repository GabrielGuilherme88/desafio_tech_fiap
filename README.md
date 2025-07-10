🧠 Projeto de Pipeline de Machine Learning com API Flask
📊 1. Diagrama de Pipeline
mermaid
Copiar
Editar
flowchart TD
    A[📥 Ingestão de Dados (Web Scraping)] --> B[🗂️ Armazenamento CSV]
    B --> C[🧹 Pré-processamento & Unificação (Pandas)]
    C --> D[🚀 API Flask]
    D --> E[🌐 Consumo por Frontend, Cientistas de Dados, Apps]
    C --> F[🤖 Modelo de ML (Treinamento/Predição)]
    F --> D
🧾 2. Descrição do Pipeline
📥 Ingestão
Web scraping coleta dados de livros e salva arquivos .csv em exports/csv/.

🔄 Processamento
Script unifica e pré-processa os CSVs, gerando tabela_unificada.csv.

Trata tipos, valores ausentes e faz encoding de variáveis categóricas.

🚀 API
A API Flask serve endpoints RESTful para:

🔍 Consulta e busca

📊 Estatísticas

🔐 Autenticação (JWT)

🤖 Predição com modelo ML

🤖 Machine Learning
Modelo RandomForest é treinado para prever o rating dos livros.

Exposto via endpoint: /api/v1/ml/predictions.

🌐 Consumo
Cientistas de dados, aplicações web/mobile e dashboards podem consumir a API para análises, visualizações ou automações.

🏗️ 3. Arquitetura para Escalabilidade
🧩 Separação de responsabilidades
Módulos independentes: scraping, processamento, API, ML.

Fácil de escalar e manter.

🗃️ Persistência
CSVs como intermediários (com possibilidade de migração para PostgreSQL/MongoDB).

Modelos versionados em disco (pode migrar para S3, MLflow, etc).

⚙️ API Stateless
Flask pode ser servido por Gunicorn/UWSGI atrás de um Nginx.

Escalável horizontalmente (Docker, Kubernetes).

🧠 ML como Serviço
Modelo ML pode ser exposto como microserviço (FastAPI, BentoML).

Permite re-treinamento/versionamento independente.

👨‍🔬 4. Cenário de Uso para Cientistas de Dados/ML
📂 Acesso aos Dados
Endpoints:

/api/v1/ml/features

/api/v1/ml/training-data

Dados prontos para análise/modelagem local.

📈 Predição Online
/api/v1/ml/predictions: permite enviar novos dados e receber predições em tempo real.

🔁 Atualização do Modelo
Re-treinamento automático com atualização do CSV.

Futuro: integração CI/CD para automação do deploy de modelos.

🔌 5. Plano de Integração com Modelos de ML
🎯 Treinamento
Script data_model.py treina e salva o modelo.

Pode ser agendado (cron, Airflow).

🧠 Predição
Modelo carregado na inicialização da API.

Predições servidas via REST.

📊 Monitoramento
Métricas de performance expostas via endpoint.

Logs de predição armazenados para análise de drift.

🚀 6. Futuras Evoluções
📦 Migrar dados para banco relacional (PostgreSQL) ou NoSQL (MongoDB)

🛠️ Orquestrar scraping/processamento com Airflow

🤖 Servir modelo com FastAPI, BentoML ou Seldon

🔐 Adicionar autenticação OAuth2, rate limiting, cache com Redis

☁️ Deploy em nuvem (AWS, Azure, GCP) com CI/CD
