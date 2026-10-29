# Лабораторная работа 1. Работа с сокетами

Python 3, только стандартная библиотека. Сначала запускается сервер, затем клиент (в другом терминале):

| Задание | Запуск | Порт |
|---|---|---|
| 1. UDP: Hello, server / Hello, client | `python task1/server.py`, `python task1/client.py` | 8080 |
| 2. TCP: площадь трапеции (вариант 3) | `python task2/server.py`, `python task2/client.py` | 8081 |
| 3. Отдача `index.html` по HTTP | `python task3/server.py`, открыть http://localhost:8082/ | 8082 |
| 4. Многопользовательский чат (TCP + threading) | `python task4/server.py`, `python task4/client.py` в нескольких терминалах | 8083 |
| 5. Веб-сервер журнала оценок (GET/POST) | `python task5/server.py`, открыть http://localhost:8084/ | 8084 |

Отчёт: `docs/lab1/report.md` в корне репозитория.
