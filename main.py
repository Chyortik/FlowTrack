import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import ast
from datetime import datetime, timedelta
import os

# Отключаем стандартное предупреждение, только если вы НЕ хотите его видеть
# Но лучше удалить эту строку, если используете своё логирование
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import API_URL, CLIENT, CLIENT_KEY, DB_CONFIG, START_PARSE, END_PARSE, SSL_VERIFY
from database import create_table, insert_data
from analytics import aggregate_data, upload_to_google_sheets

def setup_logger():
    """Настройка системы логирования
        - удаление логов старше 3 дней
        - настройка записей логов с именей по дате (YYYY-MM-DD.log) и вывод в консоль
        - формат: время | уровень | сообщение
    """
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Удаляем логи старше 3 дней
    now = datetime.now()
    cutoff = now - timedelta(days=3)
    for filename in os.listdir(logs_dir):
        filepath = os.path.join(logs_dir, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getctime(filepath))
            if file_time < cutoff:
                os.remove(filepath)
                logging.info(f"Удалён старый лог: {filename}")

    # Настройка логгера
    log_filename = now.strftime("%Y-%m-%d.log")
    log_filepath = os.path.join(logs_dir, log_filename)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_session_with_retries():
    """ Создаёт объект requests.Session с автоматическими повторными попытками
        при ошибках (например, 500, 502, таймаут).
        - полезно при нестабильном соединении.
        - повторяет запрос до 3 раз с экспоненциальной задержкой.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_data_from_api(start, end):
    """Получает данные из API
        - отправляет GET-запрос к API с указанным периодом
        - использует сессию с повторными попытками
        - отключает SSL-проверку, если SSL_VERIFY = False (для корпоративных сетей)
        - логирует предупреждение об отключённой SSL-проверке
        - Возвращает данные в формате JSON или пустой список при ошибке
    """
    logging.info(f"Запрос данных с {start} по {end}")

    if not SSL_VERIFY:
        logging.warning("SSL-проверка отключена. Убедитесь, что соединение безопасно.")

    try:
        # Создаём сессию с повторными попытками
        session = get_session_with_retries()

        params = {
            'client': CLIENT,
            'client_key': CLIENT_KEY,
            'start': start,
            'end': end
        }

        response = session.get(API_URL, params=params, timeout=60, verify=SSL_VERIFY)

        if response.status_code == 200:
            data = response.json()
            logging.info(f"Успешно получено {len(data)} записей из API")
            return data
        else:
            logging.error(f"Ошибка API: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        logging.error(f"Исключение при запросе к API: {e}")
        return []

def parse_passback_params(raw_params):
    """Парсинг passback_params
        - безопасно парсит строку passback_params в настоящий словарь с помощью ast.literal_eval
        - Извлекает oauth_consumer_key, lis_result_sourcedid, lis_outcome_service_url
        - При ошибке логирует проблему и возвращает None
    """
    try:
        parsed = ast.literal_eval(raw_params)
        return {
            'oauth_consumer_key': parsed.get('oauth_consumer_key'),
            'lis_result_sourcedid': parsed.get('lis_result_sourcedid'),
            'lis_outcome_service_url': parsed.get('lis_outcome_service_url')
        }
    except Exception as e:
        logging.warning(f"Не удалось распарсить passback_params: {raw_params} | Ошибка: {e}")
        return None

def process_data(raw_data):
    """Обрабатывает и валидирует данные
        - проверяет наличие обязательных полей.
        - убеждается, что attempt_type — это run или submit.
        - парсит passback_params.
        - преобразует is_correct в bool или None.
        - формирует список корректных записей для загрузки в БД.
        - все отклонённые записи логируются с указанием причины.
    """
    processed = []
    for i, record in enumerate(raw_data):
        try:
            # Проверка обязательных полей
            missing_fields = [key for key in ['lti_user_id', 'passback_params', 'attempt_type', 'created_at'] 
                            if not (key in record and record[key])]
            if missing_fields:
                logging.warning(f"Пропущена запись {i}: отсутствуют поля {missing_fields}. Запись: {record}")
                continue

            if record['attempt_type'] not in ['run', 'submit']:
                logging.warning(f"Пропущена запись {i}: некорректный attempt_type: {record['attempt_type']}. Запись: {record}")
                continue

            # Парсим passback_params
            passback = parse_passback_params(record['passback_params'])
            if not passback:
                logging.warning(f"Пропущена запись {i}: не удалось распарсить passback_params. Значение: {record['passback_params']}")
                continue

            # Приводим is_correct к bool или None
            is_correct = record['is_correct']
            if is_correct is not None:
                is_correct = bool(is_correct)

            # Передаём created_at как есть (PostgreSQL сам обработает микросекунды)
            created_at = record['created_at']

            processed_record = {
                'user_id': record['lti_user_id'],
                'oauth_consumer_key': passback['oauth_consumer_key'],
                'lis_result_sourcedid': passback['lis_result_sourcedid'],
                'lis_outcome_service_url': passback['lis_outcome_service_url'],
                'is_correct': is_correct,
                'attempt_type': record['attempt_type'],
                'created_at': created_at
            }
            processed.append(processed_record)

        except Exception as e:
            logging.error(f"Ошибка при обработке записи {i}: {e}. Запись: {record}")
    logging.info(f"Обработано {len(processed)} валидных записей из {len(raw_data)}")
    return processed

def main():
    setup_logger()
    logging.info("=== Запуск скрипта сбора данных ===")

    # Проверка подключения к БД
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        logging.info("✅ Подключение к PostgreSQL успешно")
    except Exception as e:
        logging.critical(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return

    # Создаём таблицу
    create_table()

    # Запрос данных
    raw_data = fetch_data_from_api(START_PARSE, END_PARSE)

    if not raw_data:
        logging.warning("Нет данных от API, завершаем работу")
        return

    # Обработка данных
    processed_data = process_data(raw_data)

    # Загрузка в БД
    insert_data(processed_data)

    logging.info("=== Скрипт завершён успешно ===")

if __name__ == "__main__":
    main()