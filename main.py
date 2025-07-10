import argparse
import time
import os
from web_scraping import BookScraper, unificar_csvs
from app import app, ALL_BOOKS_DATA, FULL_CSV_PATH

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
    if ALL_BOOKS_DATA is None: #Executa as rotas do app.py
        print("\nFATAL ERROR: Application cannot start without valid CSV data.")
        print(f"Please check if '{FULL_CSV_PATH}' exists and is readable.")
    else:
        print(f"Loaded {len(ALL_BOOKS_DATA)} books from CSV. Starting Flask app...")
        app.run(debug=True)