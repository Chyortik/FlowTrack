# FlowTrack: API Data ETL with Logs & Alerts

**Этот проект реализует ETL-пайплайн для сбора данных об активности студентов из корпоративного API, их загрузки в локальную базу данных PostgreSQL и последующей агрегации с отправкой отчёта в Google Sheets и на email.**

## 0. Структура проекта

FlowTrack
| состав | Назначение |
|-------------|-------------|
| main.py                  |   Основной скрипт: API → PostgreSQL
| aggregate_to_sheets.py   |   Скрипт агрегации и выгрузки в Google Sheets
| email_sender.py          |   Отправка email-отчётов
| config.py                |   Конфигурация
| database.py              |   Работа с PostgreSQL
| analytics.py             |   Агрегация данных
| .env                     |   Переменные окружения (пароли, ключи)
| requirements.txt         |   Зависимости
| logs/                    |   Логи скриптов (автоматически)
| venv/                    |   Виртуальное окружение
| credentials.json         |   Ключ для Google Sheets (создаётся отдельно)
| README.md                |   Описание


## 1. Установка PostgreSQL (или PostgreSQL Portable)

* Вариант A: PostgreSQL Portable (рекомендуется для Windows)
1. Скачайте PostgreSQL-Portable.zip с официального сайта .
2. Распакуйте в папку, например: C:\PostgreSQL-Portable.
3. Запустите PostgreSQL-Start.bat.
4. Сервер запустится на localhost:5432.
* Вариант B: Установка PostgreSQL
1. Скачайте с postgresql.org
2. Установите, запомните:
Пароль администратора (postgres)
Порт (по умолчанию 5432)

## 2. Настройка pgAdmin 4

1. Установите pgAdmin 4 .
2. Откройте pgAdmin.
3. Подключитесь к серверу:
* Name: Local PostgreSQL
* Host: localhost
* Port: 5432
* Username: postgres
* Password: ваш пароль
4. Создайте базу данных:
5. Правой кнопкой → Create → Database
* Name: grade_analytics

## 3. Настройка переменных окружения (.env)
* Создайте файл .env в папке проекта:
 ```
 # Настройки PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grade_analytics
DB_USER=postgres
DB_PASSWORD=ваш_пароль_от_postgres

# Настройки API
CLIENT=Skillfactory
CLIENT_KEY=M2MGWS
API_URL=https://b2b.itresume.ru/api/statistics

# Период для парсинга (формат: YYYY-MM-DD HH:MM:SS.ffffff)
START_PARSE=2023-05-31 00:00:00.000000
END_PARSE=2023-05-31 23:59:59.999999

# Настройки SSL (False для корпоративных сетей)
SSL_VERIFY=False

# Настройки Google Sheets
SPREADSHEET_ID=1aBcD...Yz  # ID вашей Google Таблицы

# Настройки email
SMTP_SERVER=smtp.mail.ru
SMTP_PORT=465
SENDER_EMAIL=example@mail.ru
SENDER_PASSWORD=ваш_пароль_приложения
RECIPIENT_EMAIL=boss_example@mail.ru
``` 
## 4. Настройка Python и виртуального окружения
```
# Перейдите в папку проекта
cd C:\Users\...\Documents\project

# Создайте виртуальное окружение
python -m venv venv

# Активируйте его
venv\Scripts\activate

# Установите зависимости (с доверием к PyPI — для корпоративной сети)
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org requests psycopg2-binary python-dotenv pandas gspread

# (Опционально) Создайте requirements.txt
pip freeze > requirements.txt
```

## 5. Получение credentials.json для Google Sheets
1. Перейдите в Google Cloud Console .
2. Создайте проект: grade-analytics-report.
3. Включите API:
* Google Sheets API
* Google Drive API
4. Перейдите в IAM & Admin → Service Accounts → Create Service Account.
5. Назовите: gspread-bot.
6. На вкладке Keys → Add Key → Create new key → JSON.
7. Скачайте файл → переименуйте в credentials.json → положите в папку проекта.

## 6. Настройка Google Таблицы
1. Создайте новую таблицу: https://sheets.google.com .
2. Назовите: Пример:"Отчёт по студентов".
3. Скопируйте ID из URL:
```
https://docs.google.com/spreadsheets/d/1aBcD...Yz/edit

ID: 1aBcD...Yz
```
## 7. Настройка email (mail.ru)
1. Создайте аккаунт: example@mail.ru
2. Перейдите в настройки почты
3. Включите POP3/IMAP/SMTP.
4. Создайте пароль приложения (не пароль от почты!).
5. Скопируйте его в .env как SENDER_PASSWORD.

## 8. Запуск скриптов
1. Запуск основного пайплайна (API → PostgreSQL)
```
# Активировать окружение
venv\Scripts\activate

# Запустить сбор данных
.\venv\Scripts\python.exe main.py
```
2. Запуск агрегации и выгрузки (PostgreSQL → Google Sheets + Email)
```
# Активировать окружение
venv\Scripts\activate

# Запустить агрегацию
.\venv\Scripts\python.exe aggregate_to_sheets.py
```

## 9. Как работает система
| Скрипт | Назначение |
|-------------|-------------|
| main.py                  |   Основной ETL: API → PostgreSQL
| aggregate_to_sheets.py   |   Агрегация и выгрузка в Google Sheets / резервное сохранение
| email_sender.py          |   Отправка отчёта на email

## 10. Особенности корпоративной сети
* SSL-ошибки (CERTIFICATE_VERIFY_FAILED) — нормальны в сетях с прокси.
* Для requests используется verify=False.
* Для gspread может не работать выгрузка — используется fallback в .csv.
* Email работает, так как smtplib часто обходит SSL-инспекцию.


## 11. Логирование

* Логи сохраняются в папке logs/.
* Имя файла: YYYY-MM-DD.log.
* Автоматически удаляются логи старше 3 дней.

## 12. Проверка успешности
* PostgreSQL: Откройте pgAdmin → проверьте таблицу attempts.
* Google Sheets: Проверьте, что таблица обновилась.
* Email: Убедитесь, что отчёт пришёл.
* Локальный бэкап: Проверьте metrics_backup.csv (если Google Sheets недоступен).

## 13. Создайте файл .gitignore
```
venv/
.env
__pycache__/
*.pyc
.DS_Store
Thumbs.db
credentials.json
metrics_backup.csv
```

## 14. Основные команды для запуска проекта
| Команда / Действие | Корпоративная сеть (с SSL-инспекцией) | Обычная сеть / Продакшен |
|--------------------|----------------------------------------|----------------------------|
| 1. Активация виртуального окружения | `venv\Scripts\activate` <br> (в cmd) | `venv\Scripts\activate` <br> (в cmd или PowerShell, если разрешено) |
| 2. Установка библиотек | `pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org requests psycopg2-binary python-dotenv` | `pip install requests psycopg2-binary python-dotenv` |
| 3. Запуск скрипта | `.\venv\Scripts\python.exe main.py` <br> (чтобы гарантировать запуск из venv) | `python main.py` <br> (если venv активирован и в приоритете) |
| 4. Запуск PostgreSQL | Дважды кликнуть `PostgreSQL-Start.bat` <br> или запустить: <br> `.\pgsql\bin\pg_ctl.exe -D data -l logfile.txt start` | То же самое, если используется Portable. <br> Или: <br> `sudo service postgresql start` (Linux) |
| 5. Остановка PostgreSQL | Закрыть окно сервера или: <br> `.\pgsql\bin\pg_ctl.exe -D data stop` | `sudo service postgresql stop` |
| 6. Проверка, какой Python используется | `where python` <br> → должен показать путь к `venv\Scripts\python.exe` | `which python` (Linux/Mac) <br> или `where python` (Windows) |
| 7. Проверка установленных пакетов | `.\venv\Scripts\pip.exe list` | `pip list` |
| 8. Обновление `requirements.txt` | `.\venv\Scripts\pip.exe freeze > requirements.txt` | `pip freeze > requirements.txt` |
| 9. Удаление всех данных из таблицы `attempts` | Через pgAdmin: <br> `DELETE FROM attempts;` <br> или <br> `TRUNCATE TABLE attempts RESTART IDENTITY;` | То же самое — через SQL в pgAdmin или скрипт |
| 10. Перезапуск с новыми датами | Изменить `START_PARSE` и `END_PARSE` в `.env`, затем перезапустить скрипт | То же самое |


