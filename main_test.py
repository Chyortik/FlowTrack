import logging
from datetime import datetime, timedelta
import os

# Настройка логирования
def setup_logger():
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
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

# Подключаем конфиг и функции из других модулей
from config import DB_CONFIG
from database import create_table, insert_data

def test_connection():
    """Тест подключения к PostgreSQL"""
    import psycopg2
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("✅ Подключение к PostgreSQL успешно установлено")
        conn.close()
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False

def main():
    logging.info("=== Запуск скрипта сбора данных ===")

    # Проверяем подключение
    if not test_connection():
        logging.critical("Не удалось подключиться к базе данных. Работа скрипта остановлена.")
        return

    # Создаём таблицу (если ещё не создана)
    create_table()

    logging.info("=== Скрипт завершён успешно ===")

if __name__ == "__main__":
    setup_logger()
    main()