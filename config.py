import os
from dotenv import load_dotenv

# Установите False в продакшене!
SSL_VERIFY = os.getenv('SSL_VERIFY', 'False').lower() == 'true'  # По умолчанию False для корпоративной сети

# Загружаем переменные из .env
load_dotenv()

# Настройки API
API_URL = "https://b2b.itresume.ru/api/statistics"
CLIENT = "Skillfactory"
CLIENT_KEY = "M2MGWS"

# Настройки PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Читаем даты из .env
START_PARSE = os.getenv("START_PARSE")
END_PARSE = os.getenv("END_PARSE")