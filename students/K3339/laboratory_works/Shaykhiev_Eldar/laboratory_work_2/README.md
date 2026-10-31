# Лабораторная работа 2. Научные конференции (вариант 5)

Сайт на Django 5.2 + PostgreSQL. Отчёт: `docs/lab2/report.md` в корне репозитория.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# PostgreSQL в контейнере: база conferences, postgres:postgres, порт 5432
docker compose up -d          # или: podman compose up -d
# Свою базу можно указать переменными DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

python manage.py migrate
python manage.py loaddata demo        # конференции, пользователи, заявки и отзывы
python manage.py runserver
```

Сайт: http://127.0.0.1:8000/, админ-панель: http://127.0.0.1:8000/admin/.

Пользователи из `demo`: администратор `admin` с паролем `admin` и участники `ivanov`, `petrov`,
`sidorova`, `kuznetsov`, `smirnova` с паролем `Conf-pass-2026`.
