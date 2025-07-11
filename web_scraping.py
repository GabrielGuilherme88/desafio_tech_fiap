import csv
import json
import os
import re
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm, trange
import pandas as pd
import argparse

class BookScraper:
    def __init__(self):
        self.root_url = "http://books.toscrape.com/"
        self.root_response = requests.get(self.root_url)
        self.root_soup = BeautifulSoup(self.root_response.text, 'html.parser')

        self.books = {}
        self.categories = self.setup_categories()

        self.exports_dir = "exports/"
        self.csv_dir = f"{self.exports_dir}csv/"
        self.json_dir = f"{self.exports_dir}json/"
        self.covers_dir = f"{self.exports_dir}covers/"

    def start_scraper(self, config):
        """
        Create 'exports' directory,
        Test connection,
        Parse config options and start scraping process,
        Return error for failed connection,
        @param config: dict of config args
        """
        try:
            os.mkdir(self.exports_dir)
        except FileExistsError:
            pass

        if self.root_response.status_code == 200:

            if config["categories"] is not None:
                cat_conf = config["categories"]
                for i, category in enumerate(cat_conf):
                    # if param is url, remove "index.html" or "page-x.html" suffix
                    cat_conf[i] = category.rsplit("/", 1)[0]
                self.categories = [(n, u) for n, u in self.categories if n in cat_conf or u in cat_conf]
                if not self.categories:
                    print("Invalid categories, please retry.")
                    exit()

            self.get_book_urls()

            if config["json"]:
                self.export_json(config["one_file"])
            if config["csv"]:
                self.export_csv(config["one_file"])
            if not config["ignore_covers"]:
                self.download_images()

        else:
            self.connection_error(self.root_response)

    def setup_categories(self):
        """
        Get all categories names and urls.
        @return: list of categories tuples (name, url)
        """
        if self.root_response.status_code == 200:
            categories = []
            categories_urls = [
                self.root_url + line["href"].rsplit("/", 1)[0]
                for line in self.root_soup.select("ul > li > ul > li > a")
            ]
            category_names = self.root_soup.find("ul", class_="nav nav-list").find("ul").find_all("li")
            for i, url in enumerate(categories_urls):
                categories.append((category_names[i].text.strip().lower(), url))
            return categories

        else:
            self.connection_error(self.root_response)

    def get_book_urls(self):
        """
        For each category, get all books urls,
        Check for extra pages (more than 20 books),
        Clean urls and extract data.
        """
        for category in tqdm(self.categories, desc="Extracting data", ncols=80):
            self.books[category[0]] = []
            response = requests.get(category[1])
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books_total = int(soup.select_one("form > strong").text)
                if books_total > 20:
                    page_total = int(soup.find("li", {"class": "current"}).text.replace("Page 1 of", ""))
                else:
                    page_total = 1

                book_urls = []
                for i in range(page_total):
                    if page_total == 1:
                        response = requests.get(category[1])
                    else:
                        response = requests.get(category[1] + f"/page-{i + 1}.html")
                    soup = BeautifulSoup(response.text, "html.parser")
                    book_raw_urls = [line["href"] for line in soup.select("ol > li > article > h3 > a")]
                    for url in book_raw_urls:
                        book_urls.append(url.replace("../../../", f"{self.root_url}catalogue/"))

                for book_url in tqdm(book_urls, desc=category[0].title(), ncols=80, leave=False):
                    self.book_data(category[0], book_url)

            else:
                self.connection_error(response)

    def book_data(self, category, book_url):
        """
        Scrape and clean book data and add data to books instance.
        @param category: current book category name
        @param book_url: current book url
        """
        response = requests.get(book_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            product_info = soup.find_all('td')
            description = soup.select_one("article > p").text.replace(' ...more', '')
            if description.isspace():
                description = 'n/a'
            img = soup.find("div", {"class": "item active"}).find("img")
            img_url = img["src"].replace("../../", f"{self.root_url}")
            book_data = {
                'product_page_url': book_url,
                'universal_product_code': product_info[0].text,
                'title': str(soup.find('h1').text),
                'price_including_tax': product_info[3].text,
                'price_excluding_tax': product_info[2].text,
                'number_available': re.sub(r"\D", "", product_info[5].text),
                'product_description': description,
                'category': category,
                'review_rating':
                    f"{self.review_rating(soup.select_one('.star-rating').attrs['class'][1])} star(s)",
                'image_url': img_url
            }
            self.books[category].append(book_data)

        else:
            self.connection_error(response)

    @staticmethod
    def review_rating(rating):
        """
        Compare star rating string to possible ratings list elements,
        Convert rating into integer.
        @param rating: star rating string
        @return: rating type int
        """
        for i, mark in enumerate(['One', 'Two', 'Three', 'Four', 'Five']):
            if rating == mark:
                return i + 1

    def export_csv(self, one_file: bool):
        """
        Export book data to csv files in exports directory.
        @param one_file: one file export if True
        """
        if not os.path.isdir(f"{self.csv_dir}"):
            os.mkdir(f"{self.csv_dir}")

        headers = [
            'product_page_url',
            'universal_product_code',
            'title',
            'price_including_tax',
            'price_excluding_tax',
            'number_available',
            'product_description',
            'category',
            'review_rating',
            'image_url'
        ]

        if one_file:
            csv_fullpath = f"./{self.csv_dir}books.csv"
            with open(csv_fullpath, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                for category in tqdm(self.categories, desc="Exporting to csv", ncols=80):
                    writer.writerows(self.books[category[0]])

        else:
            for category in tqdm(self.categories, desc="Exporting to csv", ncols=80):
                csv_filename = category[0].lower().replace(' ', '_') + ".csv"
                csv_fullpath = f"./{self.csv_dir}{csv_filename}"
                with open(csv_fullpath, 'w', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(self.books[category[0]])

    def export_json(self, one_file: bool):
        """
        Export book data to json files in exports directory.
        @param one_file: one file export if True
        """
        if not os.path.isdir(f"{self.json_dir}"):
            os.mkdir(f"{self.json_dir}")

        if one_file:
            for _ in trange(1, desc="Exporting to json", ncols=80):
                json_fullpath = f"./{self.json_dir}books.json"
                json_data = json.dumps(self.books, indent=2)
                with open(json_fullpath, "w") as json_file:
                    json_file.write(json_data)

        else:
            for category in tqdm(self.categories, desc="Exporting to json", ncols=80):
                json_filename = category[0].lower().replace(' ', '_') + ".json"
                json_fullpath = f"./{self.json_dir}{json_filename}"
                json_data = json.dumps(self.books[category[0]], indent=4)
                with open(json_fullpath, "w") as json_file:
                    json_file.write(json_data)

    def download_images(self):
        """
        Create category dirs within covers directory,
        Set names for image files as "upc + book title",
        Download cover images.
        """
        if not os.path.isdir(f"{self.covers_dir}"):
            os.mkdir(f"{self.covers_dir}")

        for category in tqdm(self.categories, desc="Downloading cover images", ncols=80):
            img_category_dir = f"{self.covers_dir}{category[0]}/"
            if not os.path.isdir(img_category_dir):
                os.mkdir(img_category_dir)

            for book in self.books[category[0]]:
                image = requests.get(book["image_url"])
                img_name = f"{book['universal_product_code']}.jpg"
                output_path = os.path.join(img_category_dir, img_name)
                with open(output_path, "wb") as f:
                    f.write(image.content)

    @staticmethod
    def connection_error(response):
        """Display error message"""
        print("Connection failed, please refer to details below:")
        print(response.raise_for_status())
        exit()




def unificar_csvs(caminho_pasta):
    """
    Lê todos os arquivos .csv de uma pasta, limpa os dados de preço,
    adiciona uma coluna com o nome do arquivo de origem,
    e salva uma tabela unificada na mesma pasta.
    Se nenhum CSV for encontrado, cria um arquivo vazio tabela_unificada.csv.
    """
    arquivos_csv = [f for f in os.listdir(caminho_pasta) if f.endswith('.csv') and f != 'tabela_unificada.csv']
    
    caminho_saida = os.path.join(caminho_pasta, "tabela_unificada.csv")

    if not arquivos_csv:
        print("Nenhum arquivo CSV para unificar encontrado na pasta especificada.")
        
        # Cria DataFrame vazio e salva como CSV
        pd.DataFrame().to_csv(caminho_saida, index=False)
        print(f"📄 Arquivo vazio criado em: {caminho_saida}")
        return

    dataframes = []
    print(f"Arquivos encontrados para unificação: {arquivos_csv}")

    for arquivo in arquivos_csv:
        caminho_arquivo = os.path.join(caminho_pasta, arquivo)
        try:
            df = pd.read_csv(caminho_arquivo)

            for col in ['price_including_tax', 'price_excluding_tax']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('£', '', regex=False).astype(float)

            df['arquivo_origem'] = arquivo
            dataframes.append(df)
        except Exception as e:
            print(f"Erro ao processar o arquivo {arquivo}: {e}")

    if not dataframes:
        print("Nenhum dataframe foi criado a partir dos arquivos CSV. Verifique o conteúdo dos arquivos.")
        pd.DataFrame().to_csv(caminho_saida, index=False)
        print(f"📄 Arquivo vazio criado em: {caminho_saida}")
        return

    tabela_unificada = pd.concat(dataframes, ignore_index=True)
    tabela_unificada.to_csv(caminho_saida, index=False)

    print(f"✅ Tabela unificada com {len(tabela_unificada)} linhas salva em: {caminho_saida}")


def timer(start):
    """Calculate and print scraping process time."""
    end_time = int(time.time()) - start
    print(f"\n\nAll done! Books exported in {end_time // 60} mins {end_time % 60} secs.")


def main_scraping():
    """Init arg parser, and start scraper with config vars."""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-c", "--csv", action="store_true", help="Export to csv files")
    parser.add_argument("-j", "--json", action="store_true", help="Export to json files")
    parser.add_argument("--one-file", action="store_true", help="Export data to one csv file")
    parser.add_argument("--ignore-covers", action="store_true", help="Skip cover downloads")
    parser.add_argument("--categories", type=str, nargs="+", default=None,
                        help="Scrape specific categories (name or full url)")
    args = parser.parse_args()
    config = vars(args)
    if not config["json"] and not config["csv"]:
        config["csv"] = True

    start = int(time.time())
    scraper = BookScraper()
    print("-" * 30)
    print(" Scraping Books.ToScrape.com")
    print("-" * 30)
    scraper.start_scraper(config)
    timer(start)

#Inicio da unificação dos csvs
print("Dando inicio a unificação dos csvs da pasta export...")

# Define o diretório base do script.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_da_pasta_csv = os.path.join(BASE_DIR, 'exports', 'csv')

if __name__ == "__main__":
    main_scraping()
    unificar_csvs(caminho_da_pasta_csv)
    

