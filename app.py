import os
import csv
from flask import Flask, jsonify, request
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

# Define o caminho base para a pasta de exports
BASE_EXPORTS_PATH = '/home/gabrielguilherme/FIAP/desafio_tech_fiap/exports/csv'
CSV_FILENAME = 'tabela_unificada.csv' # Nome do seu arquivo CSV
FULL_CSV_PATH = os.path.join(BASE_EXPORTS_PATH, CSV_FILENAME)

def load_books_from_csv():
    """
    Carrega todos os dados dos livros do arquivo CSV.
    Retorna uma lista de dicionários.
    """
    if not os.path.exists(FULL_CSV_PATH):
        print(f"ERROR: CSV file not found at {FULL_CSV_PATH}")
        return None # Retorna None se o arquivo não for encontrado

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

# Carrega os dados do CSV uma única vez na inicialização da aplicação
# Para evitar ler o arquivo a cada requisição
ALL_BOOKS_DATA = load_books_from_csv()

if ALL_BOOKS_DATA is None:
    print("FATAL: Failed to load books data at startup. Exiting or handling gracefully.")
    # Você pode optar por sair aqui ou ter rotas que retornem 500
    # se os dados não estiverem disponíveis.
    # Ex: import sys; sys.exit(1)

# Função auxiliar para aplicar paginação
def apply_pagination(data_list):
    limit = request.args.get('limit', type=int, default=10)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(1, limit)
    offset = max(0, offset)
    return data_list[offset:offset + limit]

# Schema de resposta para Swagger (ajustado para ser reutilizável)
book_schema = {
    "type": "object",
    "properties": {
        "product_page_url": {"type": "string"},
        "universal_product_code": {"type": "string"},
        "title": {"type": "string"},
        "price_including_tax": {"type": "string"},
        "price_excluding_tax": {"type": "string"},
        "number_available": {"type": "string"},
        "product_description": {"type": "string"},
        "category": {"type": "string"},
        "review_rating": {"type": "string"},
        "image_url": {"type": "string"},
        "arquivo_origem": {"type": "string"}
    }
}

@app.route('/api/v1/books', methods=['GET'])
def get_all_books():
    """
    Retorna todos os dados de livros a partir do arquivo CSV com paginação.
    ---
    parameters:
      - name: limit
        in: query
        type: integer
        default: 10
        description: Número máximo de registros a serem retornados.
      - name: offset
        in: query
        type: integer
        default: 0
        description: Número de registros para pular no início.
    responses:
      200:
        description: Lista de todos os livros paginados.
        schema:
          type: array
          items:
            $ref: '#/definitions/Book'
      500:
        description: Erro ao carregar os dados dos livros.
    definitions:
      Book:
        schema: *book_schema
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500
    
    paginated_books = apply_pagination(ALL_BOOKS_DATA)
    return jsonify(paginated_books)

@app.route('/api/v1/books/category/<string:category_name>', methods=['GET'])
def get_books_by_category(category_name):
    """
    Retorna dados de livros filtrados por categoria com paginação.
    ---
    parameters:
      - name: category_name
        in: path
        type: string
        required: true
        description: Nome da categoria para filtrar (case-insensitive).
      - name: limit
        in: query
        type: integer
        default: 10
        description: Número máximo de registros a serem retornados.
      - name: offset
        in: query
        type: integer
        default: 0
        description: Número de registros para pular no início.
    responses:
      200:
        description: Lista de livros filtrados por categoria paginados.
        schema:
          type: array
          items:
            $ref: '#/definitions/Book'
      404:
        description: Categoria não encontrada.
      500:
        description: Erro ao carregar os dados dos livros.
    definitions:
      Book:
        schema: *book_schema
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
    Busca livros por título e/ou categoria com paginação.
    ---
    parameters:
      - name: title
        in: query
        type: string
        description: Parte do título para filtrar (case-insensitive).
      - name: category
        in: query
        type: string
        description: Categoria para filtrar (case-insensitive).
      - name: limit
        in: query
        type: integer
        default: 10
        description: Número máximo de registros a serem retornados.
      - name: offset
        in: query
        type: integer
        default: 0
        description: Número de registros para pular no início.
    responses:
      200:
        description: Lista de livros que correspondem aos critérios de busca.
        schema:
          type: array
          items:
            $ref: '#/definitions/Book'
      404:
        description: Nenhum livro encontrado com os critérios fornecidos.
      500:
        description: Erro ao carregar os dados dos livros.
    definitions:
      Book:
        schema: *book_schema
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500

    title_filter = request.args.get('title')
    category_filter = request.args.get('category')

    # Se nenhum filtro for fornecido, retornar 400 Bad Request ou lista vazia/todos os livros.
    # Aqui, optamos por retornar 400 se nenhum filtro for especificado.
    if not title_filter and not category_filter:
        return jsonify({"error": "At least 'title' or 'category' query parameter is required for search."}), 400

    filtered_books = []
    for book in ALL_BOOKS_DATA:
        match_title = True
        match_category = True

        if title_filter:
            if title_filter.lower() not in book.get('title', '').lower():
                match_title = False
        
        if category_filter:
            if book.get('category', '').lower() != category_filter.lower():
                match_category = False
        
        # Um livro corresponde se ambos os filtros (se fornecidos) corresponderem
        if match_title and match_category:
            filtered_books.append(book)

    if not filtered_books:
        return jsonify({"message": "No books found matching the specified criteria."}), 404
    
    paginated_books = apply_pagination(filtered_books)
    return jsonify(paginated_books)

@app.route('/api/v1/books/<string:universal_product_code>', methods=['GET'])
def get_book_by_id(universal_product_code):
    """
    Retorna detalhes completos de um livro específico pelo Universal Product Code (UPC).
    ---
    parameters:
      - name: universal_product_code
        in: path
        type: string
        required: true
        description: O Universal Product Code (UPC) do livro a ser buscado.
    responses:
      200:
        description: Detalhes do livro encontrado.
        schema:
          $ref: '#/definitions/Book'
      404:
        description: Livro não encontrado com o UPC fornecido.
      500:
        description: Erro ao carregar os dados dos livros.
    definitions:
      Book:
        schema: *book_schema
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
    Lista todas as categorias de livros disponíveis.
    ---
    responses:
      200:
        description: Lista de categorias únicas.
        schema:
          type: array
          items:
            type: string
      500:
        description: Erro ao carregar os dados dos livros.
    """
    if ALL_BOOKS_DATA is None:
        return jsonify({"error": "Book data not loaded. Check server logs."}), 500
    
    categories = set()
    for book in ALL_BOOKS_DATA:
        category = book.get('category')
        if category:
            categories.add(category)
    
    return jsonify(sorted(list(categories)))

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    Verifica o status da API e conectividade com os dados.
    ---
    responses:
      200:
        description: API está saudável e dados carregados.
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            total_books_loaded:
              type: integer
      500:
        description: API não está saudável ou dados não carregados.
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    if ALL_BOOKS_DATA is not None:
        return jsonify({
            "status": "healthy",
            "message": "API está saudavel mané!",
            "total_books_loaded": len(ALL_BOOKS_DATA)
        }), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "message": "API está muito legal não jovem!"
        }), 500


