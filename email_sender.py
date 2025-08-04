import smtplib
import ssl
from email.message import EmailMessage
import os
from config import DB_CONFIG, START_PARSE, END_PARSE

def send_email_report(success, local_file_path=None, spreadsheet_url=None):
    """
    Отправляет email с отчётом о выполнении скрипта.
    :param success: bool — успешно ли выгружено в Google Sheets
    :param local_file_path: путь к локальному файлу (если сохраняли)
    :param spreadsheet_url: ссылка на Google Sheets (если успешно)
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()

        # Загружаем данные из .env
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL")

        if not all([smtp_server, smtp_port, sender_email, sender_password, recipient_email]):
            print("❌ Не все переменные для email заданы в .env")
            return False

        # Формируем сообщение
        msg = EmailMessage()
        msg['From'] = sender_email
        msg['To'] = recipient_email

        if success and spreadsheet_url:
            msg['Subject'] = "✅ Отчёт по попыткам: успешно выгружен в Google Sheets"
            body = f"""
                Добрый день!

                Скрипт агрегации данных выполнен успешно.
                Данные за период {START_PARSE} — {END_PARSE} выгружены в Google Sheets.

                🔗 Ссылка на таблицу: {spreadsheet_url}

                С уважением,
                Система аналитики
                """
        else:
            msg['Subject'] = "⚠️ Отчёт по попыткам: выгрузка в Google Sheets не удалась"
            body = f"""
                Добрый день!

                Скрипт агрегации данных выполнен, но выгрузка в Google Sheets не удалась.
                Данные сохранены локально.

                📁 Файл: {os.path.abspath(local_file_path)} (если существует)

                Пожалуйста, проверьте подключение и повторите выгрузку.

                С уважением,
                Система аналитики
                """
        msg.set_content(body)

        # Добавляем файл, если он есть
        if local_file_path and os.path.isfile(local_file_path):
            with open(local_file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(local_file_path)
            msg.add_attachment(file_data, maintype='text', subtype='csv', filename=file_name)

        # Создаём защищённое соединение
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"✅ Письмо отправлено на {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при отправке email: {e}")
        return False
