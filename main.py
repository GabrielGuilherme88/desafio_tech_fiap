from app import app, ALL_BOOKS_DATA, FULL_CSV_PATH


if __name__ == "__main__":
    if ALL_BOOKS_DATA is None: #Executa as rotas do app.py
        print("\nFATAL ERROR: Application cannot start without valid CSV data.")
        print(f"Please check if '{FULL_CSV_PATH}' exists and is readable.")
    else:
        print(f"Loaded {len(ALL_BOOKS_DATA)} books from CSV. Starting Flask app...")
        app.run(debug=True)