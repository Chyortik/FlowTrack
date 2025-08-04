"""
Скрипт для агрегации данных из PostgreSQL и выгрузки в Google Sheets.
Запускайте ТОЛЬКО после успешной загрузки данных через main.py.
"""
import os
import logging
from database import create_table  # Проверим, что таблица есть
from analytics import aggregate_data, upload_to_google_sheets
from email_sender import send_email_report
from config import DB_CONFIG
import psycopg2
from datetime import datetime


def has_data_in_table():
    """Проверяет, есть ли записи в таблице attempts"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM attempts LIMIT 1;")
        has_data = cur.fetchone() is not None
        cur.close()
        conn.close()
        return has_data
    except Exception as e:
        logging.error(f"Ошибка при проверке данных: {e}")
        return False

def main():
    os.makedirs("logs", exist_ok=True)
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f"logs/aggregate_{datetime.now().strftime('%Y-%m-%d')}.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.info("=== Запуск скрипта: агрегация и выгрузка в Google Sheets ===")

    # 0. Проверка есть ли данные в таблице?
    if not has_data_in_table():
        logging.critical("❌ В таблице attempts нет данных. Сначала запустите main.py")
        return

    # 1. Проверка: пользователь выполнил обновление?
    print("\n" + "="*60)
    print("ВАЖНО: Этот скрипт работает ТОЛЬКО после загрузки данных через main.py")
    print("-" * 60)
    response = input("Вы уже запустили main.py и обновили данные в PostgreSQL? (да/нет): ").strip().lower()

    if response not in ['да', 'yes', 'y', 'д']:
        logging.critical("❌ Операция отменена. Сначала запустите main.py для обновления данных.")
        print("Совет: Запустите сначала: python main.py")
        return

    # 2. Проверка подключения к БД
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        logging.info("✅ Подключение к PostgreSQL успешно")
    except Exception as e:
        logging.critical(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return

    # 3. Агрегация данных
    logging.info("=== Агрегация данных ===")
    metrics_df = aggregate_data()
    if metrics_df is None:
        logging.critical("Не удалось агрегировать данные")
        return

        # Проверим, что df не пуст
    if metrics_df.empty:
        logging.critical("❌ DataFrame пустой — нет данных для выгрузки")
        return

    # 4. Выгрузка в Google Sheets
    logging.info("=== Выгрузка в Google Sheets ===")

    # Передаём metrics_df в функцию
    success = upload_to_google_sheets(
        metrics_df=metrics_df,
        credentials_path='credentials.json',
        spreadsheet_id='1KRFPLEfDkP-BbMv6fEj6nrEKogKGQR80QnZPPdHg85U'
    )

    # 5. Отправка email-отчёта
    logging.info("=== Отправка email-отчёта ===")

    if success:
        send_email_report(success=True, spreadsheet_url="https://docs.google.com/spreadsheets/d/1KRFPLEfDkP-BbMv6fEj6nrEKogKGQR80QnZPPdHg85U")
    else:
        send_email_report(success=False, local_file_path="metrics_backup.csv")

    # Финальное сообщение
    if success:
        logging.info("=== Скрипт агрегации завершён успешно ===")
        print("✅ Данные успешно агрегированы и выгружены в Google Sheets!")
    else:
        logging.critical("=== Скрипт агрегации завершён с частичным успехом ===")
        print("⚠️ Данные агрегированы, но выгрузка в Google Sheets не удалась. Сохранены локально.")


if __name__ == "__main__":
    main()
