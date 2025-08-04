import logging
import os
import pandas as pd
import psycopg2
import gspread
from config import DB_CONFIG

def aggregate_data():
    """Агрегирует данные из таблицы attempts и возвращает DataFrame"""
    try:
        import pandas as pd
        import psycopg2

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COUNT(*) as total_attempts,
                COUNT(CASE WHEN is_correct THEN 1 END) as correct_attempts,
                COUNT(CASE WHEN attempt_type = 'submit' THEN 1 END) as submits,
                COUNT(CASE WHEN attempt_type = 'run' THEN 1 END) as runs,
                COUNT(DISTINCT user_id) as unique_users,
                MIN(created_at) as first_attempt,
                MAX(created_at) as last_attempt
            FROM attempts;
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()

        # Формируем DataFrame
        data = [{
            'Метрика': 'Общее количество попыток',
            'Значение': result[0]
        }, {
            'Метрика': 'Количество успешных попыток',
            'Значение': result[1]
        }, {
            'Метрика': 'Количество submit',
            'Значение': result[2]
        }, {
            'Метрика': 'Количество run',
            'Значение': result[3]
        }, {
            'Метрика': 'Уникальные пользователи',
            'Значение': result[4]
        }, {
            'Метрика': 'Первая попытка',
            'Значение': result[5]
        }, {
            'Метрика': 'Последняя попытка',
            'Значение': result[6]
        }]

        df = pd.DataFrame(data)
        logging.info("=== Агрегированные метрики ===")
        for _, row in df.iterrows():
            logging.info(f"{row['Метрика']}: {row['Значение']}")

        return df

    except Exception as e:
        logging.error(f"Ошибка при агрегации данных: {e}")
        return None


def upload_to_google_sheets(metrics_df, credentials_path='credentials.json', spreadsheet_id=None):
    """
    Выгружает DataFrame в Google Sheets
    :param metrics_df: DataFrame с метриками
    :param credentials_path: путь к credentials.json
    :param spreadsheet_id: ID Google Таблицы
    """
    try:
        # gc = gspread.service_account(filename=credentials_path)
        # import gspread
        from google.oauth2 import service_account
        import requests
        from urllib3.util import create_urllib3_context

        # Проверка входных данных
        if not spreadsheet_id:
            logging.critical("❌ Не указан ID таблицы")
            return
        if metrics_df is None or metrics_df.empty:
            logging.critical("❌ Нет данных для выгрузки")
            return

        # Создаём учётные данные
        creds = service_account.Credentials.from_service_account_file(credentials_path)

        # Отключаем SSL-проверку
        http = create_urllib3_context()
        http.disable_ssl_certificate_verification = True

        # Создаём сессию requests с отключённой SSL-проверкой
        session = requests.Session()
        session.verify = False  # Критически важно

        # Создаём клиент gspread с кастомной сессией
        gc = gspread.Client(auth=creds)
        gc.session = session  # ← Передаём сессию с verify=False

        # Открываем таблицу
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)

        # Очищаем и обновляем
        worksheet.clear()
        worksheet.update([metrics_df.columns.values.tolist()] + metrics_df.values.tolist())

        logging.info(f"✅ Данные успешно загружены в Google Sheets: {sh.url}")

    except gspread.exceptions.SpreadsheetNotFound:
        logging.error("❌ Таблица не найдена. Проверьте ID и доступ (поделили ли с client_email?).")
    except Exception as e:
        logging.error(f"❌ Ошибка при выгрузке в Google Sheets: {e}")

        # Сохраняем локально
        local_path = "metrics_backup.csv"
        try:
            metrics_df.to_csv(local_path, index=False)
            logging.info(f"ℹ️ Данные сохранены локально в файл {os.path.abspath(local_path)}")
        except Exception as save_err:
            logging.error(f"❌ Ошибка при сохранении данных локально: {save_err}")
