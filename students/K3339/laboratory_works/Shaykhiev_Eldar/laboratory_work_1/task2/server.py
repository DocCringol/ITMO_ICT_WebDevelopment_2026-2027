import socket

HOST = 'localhost'
PORT = 8081
# Сколько байт забираем за один вызов recv, а не размер сообщения
BUFFER_SIZE = 1024
# Сколько подключений ОС держит в очереди, пока сервер не вызвал accept()
BACKLOG = 1


def parse_params(request):
    # Запрос приходит строкой вида "a b h"; текст ValueError уходит клиенту
    try:
        a, b, h = map(float, request.split())
    except ValueError:
        raise ValueError('нужно передать три числа: a, b и h') from None
    if a <= 0 or b <= 0 or h <= 0:
        raise ValueError('основания и высота должны быть положительными')
    return a, b, h


def trapezoid_area(a, b, h):
    return (a + b) / 2 * h


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(BACKLOG)
print(f'TCP-сервер запущен на {HOST}:{PORT}...')

while True:
    client_connection, client_address = server_socket.accept()
    try:
        print(f'Подключение от {client_address}')

        request = client_connection.recv(BUFFER_SIZE).decode()
        print(f'Параметры: {request}')

        try:
            response = f'Площадь трапеции: {trapezoid_area(*parse_params(request))}'
        except ValueError as error:
            response = f'Ошибка: {error}'
        print(response)
        client_connection.sendall(response.encode())
    except Exception as error:
        # Неожиданная ошибка в одном запросе не должна останавливать весь сервер
        print(f'Ошибка при обработке запроса от {client_address}: {error!r}')
    finally:
        # Соединение закрывается, даже если при обработке запроса случилась ошибка
        client_connection.close()
