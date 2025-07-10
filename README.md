# Desafio Tech FIAP - Books Scraping & ML API

Este projeto realiza scraping de dados de livros, unificação e processamento dos dados, expõe uma API RESTful com autenticação JWT, e integra um modelo de Machine Learning para predição de ratings.

---

## Tecnologias Utilizadas

- **Python 3.8+**
- **Flask** — Framework web para a API REST.
- **Flasgger** — Documentação Swagger/OpenAPI automática.
- **Flask-JWT-Extended** — Autenticação JWT.
- **Pandas** — Manipulação e processamento de dados.
- **Scikit-learn** — Treinamento e uso do modelo de Machine Learning (RandomForest).
- **Joblib** — Serialização do modelo ML.
- **NumPy** — Operações numéricas.
- **argparse** — CLI para scraping.
- **os, time** — Utilitários do sistema.
- **csv** — Leitura e escrita de arquivos CSV.

---

## Estrutura do Projeto

desafio_tech_fiap/ │ ├── app.py # API Flask principal ├── data_model.py # Pipeline de ML: processamento, treino e predição ├── web_scraping.py # Scraper de livros e utilitários de unificação ├── exports/ │ └── csv/ # CSVs exportados e unificados ├── models/ # Modelos ML serializados (.pkl) ├── requirements.txt # Dependências do projeto └── README.md

--

## Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone <url-do-repo>
cd desafio_tech_fiap
```

2. Crie e ative um ambiente virtual
```
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências
```
pip install -r requirements.txt
```

4. Execute o Web Scraping (opcional, se já houver CSV)
```
python main.py --csv --one-file
```

Isso irá baixar os dados dos livros e gerar os arquivos CSV em exports/csv/.

5. Treine o modelo de Machine Learning (opcional)
O modelo é treinado automaticamente ao rodar a API, caso não exista um modelo salvo em models/.

6. Inicie a API Flask
```
python main.py
```

Principais Endpoints
/api/v1/books — Lista de livros (paginação)
/api/v1/books/category/<categoria>
/api/v1/books/search
/api/v1/books/<universal_product_code>
/api/v1/categories
/api/v1/stats/overview
/api/v1/ml/features — Dados de features para ML
/api/v1/ml/training-data — Dados de treino para ML
/api/v1/ml/predictions — Predição de rating via modelo ML (POST)
/api/v1/auth/login — Autenticação JWT


Observações
O arquivo unificado tabela_unificada.csv deve estar em exports/csv/.
O modelo ML é salvo/carregado automaticamente de models/book_rating_random_forest_model.pkl.
Para re-treinar o modelo, basta remover o arquivo .pkl e reiniciar a API.
O scraping pode ser executado via CLI para atualizar os dados.
