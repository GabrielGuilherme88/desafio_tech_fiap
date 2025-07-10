# data_model.py

import pandas as pd
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import joblib

# --- Configuração de Caminhos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_da_pasta_csv = os.path.join(BASE_DIR, 'exports', 'csv')
nome_arquivo_csv = 'tabela_unificada.csv'
caminho_completo_csv = os.path.join(caminho_da_pasta_csv, nome_arquivo_csv)

# Definir o caminho para salvar/carregar o modelo
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_FILENAME = 'book_rating_random_forest_model.pkl'
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILENAME)

# Variáveis globais
df_books = pd.DataFrame()
ml_model = None
features_columns_after_ohe = []
model_performance_metrics = {}

def load_data_and_train_model():
    """
    Carrega o arquivo CSV, pré-processa os dados, e treina/carrega o modelo de ML.
    Armazena o DataFrame processado, o modelo treinado e as métricas em variáveis globais.
    """
    global df_books, ml_model, features_columns_after_ohe, model_performance_metrics
    
    # Tenta carregar o modelo existente primeiro
    if os.path.exists(MODEL_PATH):
        try:
            ml_model = joblib.load(MODEL_PATH)
            print(f"Modelo de ML carregado de '{MODEL_PATH}'")
            
            # Carrega o CSV para as rotas da API e para obter features_columns_after_ohe
            try:
                df_books = pd.read_csv(caminho_completo_csv)
                df_books['price_including_tax'] = pd.to_numeric(df_books['price_including_tax'], errors='coerce')
                df_books['number_available'] = pd.to_numeric(df_books['number_available'], errors='coerce')
                df_books['review_rating'] = pd.to_numeric(df_books['review_rating'], errors='coerce')
                
                df_books[['price_including_tax', 'number_available', 'review_rating']] = \
                    df_books[['price_including_tax', 'number_available', 'review_rating']].fillna(0)
                df_books['category'].fillna('Unknown', inplace=True)
                
                # Re-obter as features_columns_after_ohe do df_books carregado
                temp_X = df_books[['price_including_tax', 'number_available', 'category']].copy()
                temp_X = pd.get_dummies(temp_X, columns=['category'], drop_first=True)
                features_columns_after_ohe = temp_X.columns.tolist()

                print("Dados carregados e pré-processados para ML (após carregamento do modelo).")
                
            except FileNotFoundError:
                print(f"Aviso: CSV '{caminho_completo_csv}' não encontrado, mas modelo foi carregado.")
                df_books = pd.DataFrame()
            except Exception as e:
                print(f"Aviso: Erro ao carregar CSV após carregar modelo: {e}")
                df_books = pd.DataFrame()
                
            return # Sai da função se o modelo foi carregado com sucesso

        except Exception as e:
            print(f"Erro ao carregar o modelo de ML de '{MODEL_PATH}': {e}. Tentando treinar um novo modelo.")
            ml_model = None

    # Se o modelo não existe ou falhou ao carregar, carrega os dados e treina um novo modelo
    try:
        df_books = pd.read_csv(caminho_completo_csv)
        
        df_books['price_including_tax'] = pd.to_numeric(df_books['price_including_tax'], errors='coerce')
        df_books['number_available'] = pd.to_numeric(df_books['number_available'], errors='coerce')
        df_books['review_rating'] = pd.to_numeric(df_books['review_rating'], errors='coerce')
        
        df_books[['price_including_tax', 'number_available', 'review_rating']] = \
            df_books[['price_including_tax', 'number_available', 'review_rating']].fillna(0)
        df_books['category'].fillna('Unknown', inplace=True)

        print("Dados carregados e pré-processados para ML (para novo treinamento).")

        # Preparação de Dados para Treinamento
        X = df_books[['price_including_tax', 'number_available', 'category']].copy()
        y = df_books['review_rating'].copy()

        X = pd.get_dummies(X, columns=['category'], drop_first=True)
        features_columns_after_ohe = X.columns.tolist()

        # Divisão em Treino e Teste
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        print(f"Dados divididos: {len(X_train)} para treino, {len(X_test)} para teste.")

        # Treinamento do Modelo ML
        ml_model = RandomForestRegressor(n_estimators=100, random_state=42)
        ml_model.fit(X_train, y_train)

        print("Modelo de Machine Learning treinado com sucesso!")

        # Salvar o Modelo
        joblib.dump(ml_model, MODEL_PATH)
        print(f"Modelo salvo como '{MODEL_PATH}'")

        # Cálculo de Métricas de Performance
        y_pred = ml_model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)

        model_performance_metrics = {
            "MAE": round(mae, 4),
            "MSE": round(mse, 4),
            "RMSE": round(rmse, 4),
            "R2_Score": round(r2, 4)
        }
        print(f"Métricas de Performance do Modelo: {model_performance_metrics}")
        
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_completo_csv}' não foi encontrado. Não foi possível treinar o modelo.")
        df_books = pd.DataFrame()
        ml_model = None
        model_performance_metrics = {"error": "CSV not found"}
    except Exception as e:
        print(f"Erro ao carregar, processar CSV ou treinar o modelo ML: {e}")
        df_books = pd.DataFrame()
        ml_model = None
        model_performance_metrics = {"error": str(e)}

# Chame a função de carregamento e treinamento uma vez quando o módulo é importado
load_data_and_train_model()

# --- Funções para Features e Training Data ---
def get_features_df_for_ml():
    return df_books[['price_including_tax', 'number_available', 'category']].copy()

def get_training_data_df_for_ml():
    return df_books[['price_including_tax', 'number_available', 'category', 'review_rating']].copy()

# --- NOVA FUNÇÃO DE PREDIÇÃO ---
def predict_book_rating(price_including_tax, number_available, category):
    """
    Recebe os dados de um livro, pré-processa-os e retorna a previsão do review_rating.
    
    Args:
        price_including_tax (float): Preço do livro.
        number_available (int): Número de cópias disponíveis.
        category (str): Categoria do livro.
        
    Returns:
        tuple: Um tupla contendo o rating previsto (arredondado) e a predição bruta.
               Retorna (None, None) se o modelo não estiver disponível.
    """
    if ml_model is None or not features_columns_after_ohe:
        print("Erro: Modelo de ML ou colunas de features não disponíveis para predição.")
        return None, None

    try:
        # Cria um DataFrame a partir dos dados de entrada
        input_data = {
            'price_including_tax': price_including_tax,
            'number_available': number_available,
            'category': category
        }
        input_df = pd.DataFrame([input_data])
        
        # Aplica o mesmo One-Hot Encoding da categoria
        input_df_processed = pd.get_dummies(input_df, columns=['category'], drop_first=True)

        # Alinha as colunas do input_df_processed com as colunas usadas no treinamento do modelo
        final_input_features = pd.DataFrame(0, index=input_df_processed.index, columns=features_columns_after_ohe)
        
        for col in input_df_processed.columns:
            if col in final_input_features.columns:
                final_input_features[col] = input_df_processed[col]

        # Realiza a predição
        prediction = ml_model.predict(final_input_features)[0]
        
        # Arredonda e garante o intervalo de 1 a 5
        predicted_rating = max(1, min(5, round(prediction)))

        return predicted_rating, prediction

    except Exception as e:
        print(f"Erro durante a predição no data_model: {e}")
        return None, None