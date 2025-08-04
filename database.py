import psycopg2
from config import DB_CONFIG
import logging

def create_table():
    """Создаёт таблицу attempts, если её нет"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attempts (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100),
                oauth_consumer_key TEXT,
                lis_result_sourcedid TEXT,
                lis_outcome_service_url TEXT,
                is_correct BOOLEAN,
                attempt_type VARCHAR(10),
                created_at TIMESTAMP
            )
        ''')
        conn.commit()
        logging.info("Таблица attempts проверена/создана")
        cur.close()
    except Exception as e:
        logging.error(f"Ошибка при создании таблицы: {e}")
    finally:
        if conn:
            conn.close()

def insert_data(data):
    """Вставляет список записей в таблицу attempts"""
    if not data:
        logging.info("Нет данных для вставки")
        return

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = '''
            INSERT INTO attempts 
            (user_id, oauth_consumer_key, lis_result_sourcedid, lis_outcome_service_url, is_correct, attempt_type, created_at)
            VALUES (%(user_id)s, %(oauth_consumer_key)s, %(lis_result_sourcedid)s, %(lis_outcome_service_url)s, %(is_correct)s, %(attempt_type)s, %(created_at)s)
        '''
        cur.executemany(query, data)
        conn.commit()
        logging.info(f"Успешно вставлено {len(data)} записей")
    except Exception as e:
        logging.error(f"Ошибка при вставке данных: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
