# 📚 BookScraper API - Projeto FIAP

Este projeto tem como objetivo aplicar técnicas de **Web Scraping** e **APIs RESTful com Flask**, com foco na extração e disponibilização de informações sobre livros em um site de e-commerce fictício.

---

## 🚀 Objetivos do Projeto

- Coletar dados de livros via Web Scraping (usando `requests`, `BeautifulSoup`, etc.)
- Organizar os dados extraídos em arquivos `.csv` com características como:
  - Título
  - Preço com e sem imposto
  - Categoria
  - Disponibilidade
  - Avaliação
- Unificar os arquivos CSV automaticamente
- Criar uma API com Flask que permita:
  - 📥 Inserir, editar e deletar livros (CRUD)
  - 📊 Consultar estatísticas gerais (ex: preço médio, categorias mais comuns)
  - 🔍 Filtrar livros via query parameters (ex: por categoria ou faixa de preço)

---

## 🧰 Tecnologias Utilizadas

- Python 3.10+
- Flask
- BeautifulSoup
- Pandas
- SQLAlchemy
- SQLite
- Flasgger (Swagger UI para documentação da API)
- VSCode + Postman (para testes)

---

## 🗂 Estrutura do Projeto

Exemplos de Endpoints
GET /livros → Retorna todos os livros

GET /livros?categoria=Ficcao → Filtra por categoria

GET /estatisticas → Estatísticas dos preços e categorias

POST /livros → Adiciona novo livro

PUT /livros/<id> → Edita um livro existente

DELETE /livros/<id> → Remove um livro

📌 Observações
O projeto é 100% acadêmico, desenvolvido como desafio da FIAP.

A fonte dos dados é um site de livros fictício usado para aprendizado de scraping.

Boas práticas de desenvolvimento de APIs estão sendo aplicadas ao longo do projeto.

👨‍💻 Autor
Gabriel Guilherme
FIAP - Engenharia de Dados
LinkedIn (adicione o link real aqui)
