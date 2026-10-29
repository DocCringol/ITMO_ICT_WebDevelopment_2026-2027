import socket
from pathlib import Path

HOST = 'localhost'
PORT = 8082
# Сколько байт забираем за один вызов recv, а не размер сообщения
BUFFER_SIZE = 1024
# Сколько подключений ОС держит в очереди, пока сервер не вызвал accept()
BACKLOG = 5

# index.html лежит рядом со скриптом, откуда бы его ни запускали
INDEX_PATH = Path(__file__).with_name('index.html')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(BACKLOG)
print(f'HTTP-сервер запущен на http://{HOST}:{PORT}/')

while True:
    client_connection, client_address = server_socket.accept()
    try:
        request = client_connection.recv(BUFFER_SIZE).decode()
        # Первая строка запроса: метод, путь, версия протокола
        request_line = request.split('\r\n')[0]
        print(f'{client_address}: {request_line}')

        body = INDEX_PATH.read_text(encoding='utf-8').encode()

        # Content-Length - длина тела в байтах, поэтому считаем после encode()
        headers = (
            'HTTP/1.1 200 OK\r\n'
            'Content-Type: text/html; charset=utf-8\r\n'
            f'Content-Length: {len(body)}\r\n'
            'Connection: close\r\n'
            '\r\n'
        )
        client_connection.sendall(headers.encode() + body)
    except Exception as error:
        # Неожиданная ошибка в одном запросе не должна останавливать весь сервер
        print(f'Ошибка при обработке запроса от {client_address}: {error!r}')
    finally:
        # Соединение закрывается, даже если при обработке запроса случилась ошибка
        client_connection.close()
