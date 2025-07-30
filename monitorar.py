import time
import uuid
import traceback
import logging
import csv
import os
from functools import wraps
from flask import request

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Caminho relativo à raiz do projeto (usando __file__ do próprio arquivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
LOG_FILE_PATH = os.path.join(EXPORTS_DIR, 'logs_monitoramento.csv')

# Garante que a pasta 'exports/' exista
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Escreve o cabeçalho no arquivo CSV se ainda não existir
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "request_id", "endpoint", "method", "client_ip", "status_code", "duration_ms"
        ])
        writer.writeheader()

def monitor_api_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())

        path = request.path
        method = request.method
        client_ip = request.remote_addr
        status_code = 500

        try:
            response = func(*args, **kwargs)

            if hasattr(response, 'status_code'):
                status_code = response.status_code
            else:
                status_code = 200

            return response

        except Exception as e:
            error_message = str(e)
            logger.error(f"[ERRO] Rota {path}: {error_message}", extra={
                'extra_data': {
                    "request_id": request_id,
                    "endpoint": path,
                    "method": method,
                    "client_ip": client_ip,
                    "status_code": status_code,
                    "error_details": error_message,
                    "traceback": traceback.format_exc()
                }
            })
            raise

        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            log_data = {
                "request_id": request_id,
                "endpoint": path,
                "method": method,
                "client_ip": client_ip,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2)
            }

            # Salva em CSV
            try:
                with open(LOG_FILE_PATH, mode='a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=log_data.keys())
                    writer.writerow(log_data)
            except Exception as csv_err:
                logger.error(f"[ERRO] Falha ao salvar log em CSV: {csv_err}")

            # Log no terminal (opcional)
            if status_code >= 400:
                logger.warning(f"[AVISO] Chamada com erro: {path}", extra={'extra_data': log_data})
            else:
                logger.info(f"[INFO] Chamada bem-sucedida: {path}", extra={'extra_data': log_data})

    return wrapper
