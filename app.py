import os
import csv
from flask import Flask, jsonify, request
from flasgger import Swagger, swag_from
import pandas as pd
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Books Scraping - Desafio Tech API',
    'uiversion': 3,
    'doc_dir': './docs/' # Opcional: para organizar os arquivos .yml
}

jwt = JWTManager(app)
swagger = Swagger(app)

# Configurações JWT
app.config["JWT_SECRET_KEY"] = "super-secret-key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 2592000

# Pega o diretório onde o script (app.py) está sendo executado.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constrói o caminho relativo para o seu arquivo CSV.
CSV_FILENAME = 'tabela_unificada.csv'
FULL_CSV_PATH = os.path.join(BASE_DIR, 'exports', 'csv', CSV_FILENAME)

def load_books_from_csv():
    """
    Carrega todos os dados dos livros do arquivo CSV.
    Retorna uma lista de dicionários.
    """
    if not os.path.exists(FULL_CSV_PATH):
        print(f"ERROR: CSV file not found at {FULL_CSV_PATH}")
        return None

    books_data = []
    try:
        with open(FULL_CSV_PATH, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                book = {
                    "product_page_url": row.get("product_page_url"),
                    "universal_product_code": row.get("universal_product_code"),
                    "title": row.get("title"),
                    "price_including_tax": row.get("price_including_tax"),
                    "price_excluding_tax": row.get("price_excluding_tax"),
                    "number_available": row.get("number_available"),
                    "product_description": row.get("product_description"),
                    "category": row.get("category"),
                    "review_rating": row.get("review_rating"),
                    "image_url": row.get("image_url"),
                    "arquivo_origem": row.get("arquivo_origem", CSV_FILENAME)
                }
                books_data.append(book)
        return books_data
    except Exception as e:
        print(f"ERROR: Error reading CSV file: {e}")
        return None

# Carrega os dados do CSV uma única vez
ALL_BOOKS_DATA = load_books_from_csv()

if ALL_BOOKS_DATA is None:
    print("FATAL: Failed to load books data at startup.")

# Função auxiliar para aplicar paginação
def apply_pagination(data_list):
    limit = request.args.get('limit', type=int, default=10)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(1, limit)
    offset = max(0, offset)
    return data_list[offset:offset + limit]

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/api/v1/books', methods=['GET'])
def get_all_books():
    """
    Retorna uma lista paginada de todos os livros.
    ---
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
        description: O número de livros a serem retornados por página.
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: O ponto de partida para a paginação.
    responses:
      200:
        description: Uma lista de livros.
      500:
        description: Erro interno do servidor, dados dos livros não carregados.
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500
    
    paginated_books = apply_pagination(ALL_BOOKS_DATA)
    return jsonify(paginated_books)

@app.route('/api/v1/books/category/<string:category_name>', methods=['GET'])
def get_books_by_category(category_name):
    """
    Busca livros por uma categoria específica.
    ---
    parameters:
      - name: category_name
        in: path
        type: string
        required: true
        description: O nome da categoria a ser buscada.
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
        description: O número de livros a serem retornados por página.
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: O ponto de partida para a paginação.
    responses:
      200:
        description: Uma lista de livros da categoria especificada.
      404:
        description: Nenhum livro encontrado para a categoria especificada.
      500:
        description: Erro interno, dados dos livros não carregados.
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500

    filtered_by_category = [
        book for book in ALL_BOOKS_DATA 
        if book.get('category', '').lower() == category_name.lower()
    ]

    if not filtered_by_category:
        return jsonify({"message": f"No books found for category: {category_name}"}), 404

    paginated_books = apply_pagination(filtered_by_category)
    return jsonify(paginated_books)

@app.route('/api/v1/books/search', methods=['GET'])
def search_books():
    """
    Retorna livros que correspondem parcial ou totalmente ao título e/ou à categoria informada
    ---
    summary: Busca livros por título e/ou categoria
    description: Retorna livros que correspondem parcial ou totalmente ao título e/ou à categoria informada.
    parameters:
      - name: title
        in: query
        type: string
        required: false
        description: Parte do título do livro (busca case-insensitive).
      - name: category
        in: query
        type: string
        required: false
        description: Nome exato da categoria (busca case-insensitive).
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
        description: Número máximo de livros retornados.
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: Quantidade de livros a serem pulados (paginação).
    responses:
      200:
        description: Lista de livros que atendem aos critérios de busca.
      400:
        description: Nenhum parâmetro de busca ('title' ou 'category') foi fornecido.
      404:
        description: Nenhum livro encontrado com os critérios informados.
      500:
        description: Erro interno - os dados dos livros não foram carregados corretamente.
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500

    title_filter = request.args.get('title')
    category_filter = request.args.get('category')

    if not title_filter and not category_filter:
        return jsonify({"error": "At least 'title' or 'category' query parameter is required for search."}), 400

    filtered_books = []
    # Usando uma cópia para não modificar a lista original
    search_list = list(ALL_BOOKS_DATA)

    if title_filter:
        search_list = [book for book in search_list if title_filter.lower() in book.get('title', '').lower()]
    
    if category_filter:
        search_list = [book for book in search_list if book.get('category', '').lower() == category_filter.lower()]
    
    filtered_books = search_list

    if not filtered_books:
        return jsonify({"message": "No books found matching the specified criteria."}), 404
    
    paginated_books = apply_pagination(filtered_books)
    return jsonify(paginated_books)

@app.route('/api/v1/books/<string:universal_product_code>', methods=['GET'])
def get_book_by_id(universal_product_code):
    """
    Buscar livro por Universal Product Code (UPC)
    ---
    summary: Buscar livro por Universal Product Code (UPC)
    description: Retorna um único livro com base no código universal fornecido.
    parameters:
      - name: universal_product_code
        in: path
        type: string
        required: true
        description: Código UPC do livro a ser buscado.
    responses:
      200:
        description: Livro encontrado com sucesso.
        schema:
          type: object
          properties:
            product_page_url:
              type: string
            universal_product_code:
              type: string
            title:
              type: string
            price_including_tax:
              type: string
            price_excluding_tax:
              type: string
            number_available:
              type: string
            product_description:
              type: string
            category:
              type: string
            review_rating:
              type: string
            image_url:
              type: string
            arquivo_origem:
              type: string
      404:
        description: Livro não encontrado com o UPC fornecido.
      500:
        description: Erro interno, dados dos livros não carregados.
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500

    for book in ALL_BOOKS_DATA:
        if book.get('universal_product_code') == universal_product_code:
            return jsonify(book), 200
    
    return jsonify({"message": "Book not found with the provided Universal Product Code."}), 404

@app.route('/api/v1/categories', methods=['GET'])
def get_categories():
    """
    Retorna uma lista de todas as categorias de livros disponíveis.
    ---
    responses:
      200:
        description: Uma lista ordenada de nomes de categorias.
        schema:
          type: array
          items:
            type: string
      500:
        description: Erro interno, dados dos livros não carregados.
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500
    
    categories = set(book.get('category') for book in ALL_BOOKS_DATA if book.get('category'))
    
    return jsonify(sorted(list(categories)))

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    Verifica a saúde da API.
    Indica se a API está funcionando e se os dados dos livros foram carregados.
    ---
    responses:
      200:
        description: A API está saudável e os dados foram carregados.
      500:
        description: A API não está saudável, os dados não puderam ser carregados.
    """
    if ALL_BOOKS_DATA is not None:
        return jsonify({
            "status": "healthy",
            "message": "API está saudável!",
            "total_books_loaded": len(ALL_BOOKS_DATA)
        }), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "message": "API não está saudável! Falha ao carregar os dados."
        }), 500
    

    
# Criando as estatísticas de overview
# Carregar os dados uma vez ao iniciar a aplicação (ou em um serviço de dados)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_da_pasta_csv = os.path.join(BASE_DIR, 'exports', 'csv')
nome_arquivo_csv = 'tabela_unificada.csv'
caminho_completo_csv = os.path.join(caminho_da_pasta_csv, nome_arquivo_csv)

df = pd.DataFrame() # Inicializa o DataFrame vazio

try:
    df = pd.read_csv(caminho_completo_csv)
    # Garante que a coluna de preço seja numérica, tratando erros.
    df['price_including_tax'] = pd.to_numeric(df['price_including_tax'], errors='coerce')
    df.dropna(subset=['price_including_tax'], inplace=True)
except FileNotFoundError:
    print(f"Erro: O arquivo '{caminho_completo_csv}' não foi encontrado.")
except Exception as e:
    print(f"Erro ao carregar ou processar o CSV: {e}")

@app.route('/api/v1/stats/overview', methods=['GET'])
def get_stats_overview():
    """
    Retorna estatísticas gerais dos livros.
    ---
    responses:
      200:
        description: Estatísticas calculadas com sucesso.
        schema:
          type: object
          properties:
            total_livros:
              type: integer
              description: Número total de livros no dataset.
            preco_medio_geral:
              type: number
              format: float
              description: Preço médio incluindo impostos de todos os livros.
            distribuicao_ratings:
              type: object
              additionalProperties:
                type: integer
              description: Frequência de cada nota de avaliação.
            preco_medio_por_categoria:
              type: object
              additionalProperties:
                type: number
                format: float
              description: Preço médio por categoria.
      500:
        description: Dados não disponíveis.
    """
    if df.empty:
        return jsonify({"error": "Dados não disponíveis. Verifique o arquivo CSV e o caminho."}), 500

    total_livros = len(df)
    
    # Preço médio geral
    preco_medio_geral = df['price_including_tax'].mean()
    if preco_medio_geral is not None:
        preco_medio_geral = round(preco_medio_geral, 2)

    distribuicao_ratings = df['review_rating'].value_counts().sort_index().to_dict()

    # Calcular o preço médio por categoria
    # Agrupa por 'category', seleciona 'price_including_tax' e calcula a média
    preco_medio_por_categoria = df.groupby('category')['price_including_tax'].mean().round(2).to_dict()

    stats = {
        "total_livros": total_livros,
        "preco_medio_geral": preco_medio_geral,
        "distribuicao_ratings": distribuicao_ratings,
        "preco_medio_por_categoria": preco_medio_por_categoria
    }
    return jsonify(stats)


@app.route('/api/v1/books/top-rated', methods=['GET'])
def get_top_rated_books():
    """
    Retorna os 20 livros com melhor avaliação.
    ---
    responses:
      200:
        description: Lista dos livros com as maiores avaliações.
        schema:
          type: array
          items:
            type: object
            properties:
              title:
                type: string
              review_rating:
                type: number
                format: float
              price_including_tax:
                type: number
                format: float
              product_page_url:
                type: string
      500:
        description: Dados não disponíveis.
    """
    if df.empty:
        return jsonify({"error": "Dados não disponíveis. Verifique o arquivo CSV e o caminho."}), 500

    # Ordena os livros por review_rating em ordem decrescente
    # Se houver empate no rating, a ordem original ou por índice será mantida
    top_books_df = df.sort_values(by='review_rating', ascending=False).head(20)

    # Seleciona as colunas desejadas e converte para uma lista de dicionários
    top_books_list = top_books_df[[
        'title', 
        'review_rating', 
        'price_including_tax', 
        'product_page_url'
    ]].to_dict(orient='records')

    return jsonify(top_books_list)

@app.route('/api/v1/books/price-range', methods=['GET'])
def get_books_by_price_range():
    """
    Filtrar livros por faixa de preço
    ---
    summary: Filtrar livros por faixa de preço 
    description: Retorna livros cujo preço (com imposto) esteja dentro de uma faixa especificada. ex api/v1/books/price-range?max=15
    parameters:
      - name: min
        in: query
        type: number
        format: float
        required: false
        description: Preço mínimo (inclusivo) para filtrar os livros.
      - name: max
        in: query
        type: number
        format: float
        required: false
        description: Preço máximo (inclusivo) para filtrar os livros.
    responses:
      200:
        description: Lista de livros dentro da faixa de preço especificada.
        schema:
          type: array
          items:
            type: object
            properties:
              title:
                type: string
              price_including_tax:
                type: number
                format: float
              category:
                type: string
              review_rating:
                type: number
                format: float
              product_page_url:
                type: string
      500:
        description: Erro interno, dados dos livros não carregados.
    """
    if df.empty:
        return jsonify({"error": "Dados não disponíveis. Verifique o arquivo CSV e o caminho."}), 500

    min_price = request.args.get('min', type=float)
    max_price = request.args.get('max', type=float)

    filtered_df = df.copy() # Cria uma cópia para evitar modificar o DataFrame global

    # Aplica os filtros
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['price_including_tax'] >= min_price]
    
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['price_including_tax'] <= max_price]

    # Formata a saída
    books_in_range = filtered_df[[
        'title', 
        'price_including_tax', 
        'category',
        'review_rating', 
        'product_page_url'
    ]].to_dict(orient='records')

    return jsonify(books_in_range)


# aqui inicia a parte com JWT

# Criação dos tokens com roles
@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    """
    Login que retorna access token e refresh token.
    ---
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: "123"
    responses:
      200:
        description: Login bem-sucedido. Retorna access token e refresh token.
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
      401:
        description: Nome de usuário ou senha inválidos.
    """
    username = request.json.get("username")
    password = request.json.get("password")

    if username != "admin" or password != "123":
        return jsonify({"msg": "Nome de usuário ou senha inválidos"}), 401

    additional_claims = {
        "roles": ["admin", "user"] if username == "admin" else ["user"]
    }

    access_token = create_access_token(identity=username, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=username)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route("/api/v1/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Gera um novo access token a partir de um refresh token válido.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Novo access token gerado com sucesso.
        schema:
          type: object
          properties:
            access_token:
              type: string
      401:
        description: Token de refresh inválido ou expirado.
    """
    current_user = get_jwt_identity()
    claims = get_jwt()
    access_token = create_access_token(identity=current_user, additional_claims={"roles": claims["roles"]})
    return jsonify(access_token=access_token)


@app.route("/api/v1/scraping/trigger", methods=["POST"])
@jwt_required()
def trigger_scraping():
    """
    Exemplo de endpoint protegido para acionar scraping.
    Requer autenticação JWT válida e role de admin.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Scraping acionado com sucesso.
        schema:
          type: object
          properties:
            msg:
              type: string
            status:
              type: string
      403:
        description: Acesso não autorizado. Requer privilégios de administrador.
      401:
        description: Token de acesso inválido ou expirado.
    """
    current_user_identity = get_jwt_identity()
    claims = get_jwt()

    if "admin" not in claims.get("roles", []):
        return jsonify({"msg": "Acesso não autorizado. Requer privilégios de administrador."}), 403

    return jsonify(
        msg=f"Scraping acionado com sucesso pelo usuário: {current_user_identity}. Roles: {claims.get('roles')}",
        status="triggered"
    )

#inicio das rotas de ML 

@app.route('/api/v1/ml/features', methods=['GET'])
def get_ml_features():
    """
    Retorna os dados dos livros formatados como features para um modelo de Machine Learning.
    ---
    responses:
      200:
        description: Lista de features para cada livro, incluindo preço, quantidade disponível e categorias em one-hot encoding.
        schema:
          type: array
          items:
            type: object
            properties:
              price_including_tax:
                type: number
                format: float
                description: Preço do livro com imposto.
              number_available:
                type: integer
                description: Quantidade disponível do livro.
              # As propriedades das categorias one-hot aparecerão dinamicamente, mas podem ser descritas genericamente
              category_<nome>:
                type: integer
                description: Valor binário da categoria one-hot encoded.
      500:
        description: Dados não disponíveis. Problema ao carregar o arquivo CSV.
    """
    if df.empty:
        return jsonify({"error": "Dados não disponíveis. Verifique o arquivo CSV e o caminho."}), 500

    features_df = df[['price_including_tax', 'number_available', 'category']].copy()
    features_df = pd.get_dummies(features_df, columns=['category'], drop_first=True)
    return jsonify(features_df.to_dict(orient='records'))


@app.route('/api/v1/ml/training-data', methods=['GET'])
def get_ml_training_data():
    """
    Retorna o dataset completo para treinamento de um modelo de Machine Learning, incluindo features e variável alvo.
    ---
    responses:
      200:
        description: Dataset contendo features e target (review_rating).
        schema:
          type: array
          items:
            type: object
            properties:
              price_including_tax:
                type: number
                format: float
                description: Preço do livro com imposto.
              number_available:
                type: integer
                description: Quantidade disponível do livro.
              review_rating:
                type: number
                format: float
                description: Avaliação do livro (target).
              # As categorias one-hot encoded também aparecem aqui
              category_<nome>:
                type: integer
                description: Valor binário da categoria one-hot encoded.
      500:
        description: Dados não disponíveis. Problema ao carregar o arquivo CSV.
    """
    if df.empty:
        return jsonify({"error": "Dados não disponíveis. Verifique o arquivo CSV e o caminho."}), 500

    features_and_target_df = df[['price_including_tax', 'number_available', 'category', 'review_rating']].copy()
    features_and_target_df = pd.get_dummies(features_and_target_df, columns=['category'], drop_first=True)
    return jsonify(features_and_target_df.to_dict(orient='records'))


#predict
from data_model import (
    df_books, 
    ml_model, 
    features_columns_after_ohe, 
    get_features_df_for_ml, 
    get_training_data_df_for_ml, 
    model_performance_metrics,
    predict_book_rating
)

@app.route('/api/v1/ml/predictions', methods=['POST']) # Renomeado para predictions conforme sua solicitação
def make_prediction():
    
    """
    Recebe dados de um novo livro e retorna a previsão do review_rating.
    ---
    Espera um JSON com:
    
        "price_including_tax": float,
        "number_available": int,
        "category": "string"
    
    """
    # Verifica se o modelo foi carregado/treinado com sucesso
    if ml_model is None:
        return jsonify({"error": "Modelo de Machine Learning não treinado ou falhou ao carregar."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Corpo da requisição vazio ou inválido. Espera JSON."}), 400

    # Validação dos campos obrigatórios
    required_fields = ['price_including_tax', 'number_available', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo '{field}' ausente na requisição."}), 400
            
    # Validação de tipo de dados e tratamento de valores ausentes para input
    try:
        price = float(data.get('price_including_tax', 0))
        available = int(data.get('number_available', 0))
        category = str(data.get('category', 'Unknown')) # Use 'Unknown' como padrão para categoria ausente
    except ValueError as e:
        return jsonify({"error": f"Erro na conversão de tipo de dado: {str(e)}. Verifique 'price_including_tax' e 'number_available'."}), 400


    try:
        # Cria um DataFrame a partir dos dados de entrada
        input_df = pd.DataFrame([{
            'price_including_tax': price,
            'number_available': available,
            'category': category
        }])
        
        # Aplica o mesmo One-Hot Encoding da categoria
        input_df_processed = pd.get_dummies(input_df, columns=['category'], drop_first=True)

        # Alinha as colunas do input_df_processed com as colunas usadas no treinamento do modelo
        # Isso é CRÍTICO para a predição!
        final_input_features = pd.DataFrame(0, index=input_df_processed.index, columns=features_columns_after_ohe)
        
        # Copia os valores que existem do input para a estrutura final
        for col in input_df_processed.columns:
            if col in final_input_features.columns:
                final_input_features[col] = input_df_processed[col]

        # Realiza a predição
        prediction = ml_model.predict(final_input_features)[0]
        
        # Arredonda a predição para o número inteiro mais próximo, já que ratings são inteiros
        predicted_rating = round(prediction)
        # Garante que o rating esteja dentro dos limites esperados (1 a 5)
        predicted_rating = max(1, min(5, predicted_rating))

        return jsonify({
            "predicted_review_rating": predicted_rating,
            "raw_prediction": round(prediction, 4) # Opcional: mostrar a predição bruta
        })

    except Exception as e:
        # Captura erros gerais durante o processo de predição
        return jsonify({"error": f"Erro interno durante a predição: {str(e)}"}), 500