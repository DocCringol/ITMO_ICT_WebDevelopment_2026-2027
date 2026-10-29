import html
import socket
from urllib.parse import parse_qs

HOST = 'localhost'
PORT = 8084
# Сколько байт забираем за один вызов recv, а не размер сообщения
BUFFER_SIZE = 1024
# Сколько подключений ОС держит в очереди, пока сервер не вызвал accept()
BACKLOG = 5

# Журнал: дисциплина -> список оценок по ней
grades = {}


def read_request(connection):
    # Читаем, пока не дошли до пустой строки, отделяющей заголовки от тела
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = connection.recv(BUFFER_SIZE)
        if not chunk:
            return None
        data += chunk

    head, _, body = data.partition(b'\r\n\r\n')
    lines = head.decode().split('\r\n')
    method, path, _ = lines[0].split(' ')

    headers = {}
    for line in lines[1:]:
        key, _, value = line.partition(':')
        headers[key.strip().lower()] = value.strip()

    # Тело может прийти не целиком, дочитываем до Content-Length байт
    length = int(headers.get('content-length', 0))
    while len(body) < length:
        chunk = connection.recv(BUFFER_SIZE)
        if not chunk:
            return None
        body += chunk

    return method, path, body.decode()


def send_response(connection, status, body='', extra_headers=''):
    body = body.encode()
    response = (
        f'HTTP/1.1 {status}\r\n'
        'Content-Type: text/html; charset=utf-8\r\n'
        f'Content-Length: {len(body)}\r\n'
        f'{extra_headers}'
        'Connection: close\r\n'
        '\r\n'
    )
    connection.sendall(response.encode() + body)


def grades_page():
    if grades:
        rows = ''
        for discipline, marks in grades.items():
            rows += (f'<tr><td>{html.escape(discipline)}</td>'
                     f'<td>{html.escape(", ".join(marks))}</td></tr>\n')
        table = f'<table border="1">\n<tr><th>Дисциплина</th><th>Оценки</th></tr>\n{rows}</table>'
    else:
        table = '<p>Оценок пока нет.</p>'

    return f'''<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>Журнал оценок</title></head>
<body>
<h1>Журнал оценок</h1>
{table}
<h2>Добавить оценку</h2>
<form method="post" action="/">
    <input name="discipline" placeholder="Дисциплина" required>
    <input name="grade" placeholder="Оценка" required>
    <button type="submit">Сохранить</button>
</form>
</body>
</html>'''


def add_grade(connection, body):
    # Тело формы: discipline=...&grade=... (application/x-www-form-urlencoded)
    form = parse_qs(body)
    discipline = form.get('discipline', [''])[0].strip()
    grade = form.get('grade', [''])[0].strip()

    if discipline and grade:
        grades.setdefault(discipline, []).append(grade)
        print(f'Сохранено: {discipline}: {grade}')
        # После POST отправляем браузер обратно на страницу журнала
        send_response(connection, '303 See Other', extra_headers='Location: /\r\n')
    else:
        send_response(connection, '400 Bad Request',
                      '<h1>400</h1><p>Нужно указать дисциплину и оценку.</p>')


def handle_request(connection, address):
    # Один запрос: прочитать, разобрать и ответить. Ошибки, которых здесь не ждём,
    # ловит главный цикл, чтобы сервер работал дальше
    try:
        request = read_request(connection)
    except ValueError:
        # Первая строка не из трёх частей, Content-Length не число или байты не в UTF-8
        # (UnicodeDecodeError - подкласс ValueError)
        send_response(connection, '400 Bad Request', '<h1>400</h1><p>Некорректный запрос.</p>')
        return

    # Клиент закрыл соединение, так и не прислав запрос целиком
    if request is None:
        return

    method, path, body = request
    print(f'{address}: {method} {path}')

    if method == 'GET' and path == '/':
        send_response(connection, '200 OK', grades_page())
    elif method == 'POST' and path == '/':
        add_grade(connection, body)
    else:
        send_response(connection, '404 Not Found', '<h1>404</h1><p>Страница не найдена.</p>')


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(BACKLOG)
print(f'Веб-сервер запущен на http://{HOST}:{PORT}/')

while True:
    client_connection, client_address = server_socket.accept()
    try:
        handle_request(client_connection, client_address)
    except Exception as error:
        # Неожиданная ошибка в одном запросе не должна останавливать весь сервер
        print(f'Ошибка при обработке запроса от {client_address}: {error!r}')
    finally:
        # Соединение закрывается, даже если при обработке запроса случилась ошибка
        client_connection.close()
