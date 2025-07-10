import os
import csv
from flask import Flask, jsonify, request
from flasgger import Swagger, swag_from

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Books Scraping - Desafio Tech API',
    'uiversion': 3,
    'doc_dir': './docs/' # Opcional: para organizar os arquivos .yml
}

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
    Busca livros por título e/ou categoria.
    Pelo menos um dos parâmetros (title ou category) deve ser fornecido.
    ---
    parameters:
      - name: title
        in: query
        type: string
        required: false
        description: Parte do título do livro a ser buscado (case-insensitive).
      - name: category
        in: query
        type: string
        required: false
        description: Nome da categoria exata do livro (case-insensitive).
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
        description: Uma lista de livros que correspondem aos critérios de busca.
      400:
        description: Nenhum parâmetro de busca ('title' ou 'category') foi fornecido.
      404:
        description: Nenhum livro encontrado com os critérios especificados.
      500:
        description: Erro interno, dados dos livros não carregados.
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
    Obtém os detalhes de um livro específico pelo seu UPC.
    ---
    parameters:
      - name: universal_product_code
        in: path
        type: string
        required: true
        description: O Universal Product Code (UPC) único do livro.
    responses:
      200:
        description: Os detalhes do livro solicitado.
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