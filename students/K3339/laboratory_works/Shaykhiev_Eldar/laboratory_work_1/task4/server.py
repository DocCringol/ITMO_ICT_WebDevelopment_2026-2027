import socket
import threading

HOST = 'localhost'
PORT = 8083
# Сколько подключений ОС держит в очереди, пока сервер не вызвал accept()
BACKLOG = 5

clients = {}  # сокет клиента -> имя пользователя
clients_lock = threading.Lock()


def broadcast(message, sender=None):
    # Рассылаем всем подключённым, кроме отправителя.
    # TCP - поток байт без границ сообщений: два сообщения подряд могут прийти
    # одним recv, поэтому каждое заканчиваем переводом строки
    with clients_lock:
        for client in clients:
            if client is not sender:
                try:
                    client.sendall(f'{message}\n'.encode())
                except OSError:
                    pass  # клиент уже отключился, его уберёт свой поток


def handle_client(connection, address):
    # Клиент заканчивает каждое сообщение переводом строки, поэтому сокет читаем
    # как текстовый файл: readline() отдаёт ровно одно сообщение
    reader = connection.makefile('r', encoding='utf-8')
    # finally выполнится при любом выходе: /exit, отключение клиента или неожиданная ошибка,
    # поэтому клиент не останется в списке «призраком»
    try:
        # Первая строка от клиента - его имя
        name = reader.readline().strip()

        with clients_lock:
            online = ', '.join(clients.values()) or 'никого'
            clients[connection] = name
        connection.sendall(f'Добро пожаловать, {name}! Сейчас в чате: {online}\n'.encode())
        print(f'Пользователь {name} подключился с адреса {address}')
        broadcast(f'* Пользователь {name} вошёл в чат', connection)

        while True:
            try:
                line = reader.readline()
            except ConnectionResetError:
                break
            # readline() вернул пустую строку: клиент закрыл соединение
            if not line:
                break
            message = line.strip()
            if message == '/exit':
                break
            print(f'{name}: {message}')
            broadcast(f'{name}: {message}', connection)
    finally:
        with clients_lock:
            # Клиента может не быть в списке, если ошибка случилась ещё до ввода имени
            name = clients.pop(connection, None)
        # Сокет закроется по-настоящему, только когда закрыт и файл-обёртка
        reader.close()
        connection.close()
        if name is not None:
            print(f'Пользователь {name} отключился')
            broadcast(f'* Пользователь {name} вышел из чата')


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(BACKLOG)
print(f'Сервер чата запущен на {HOST}:{PORT}...')

while True:
    connection, address = server_socket.accept()
    # Каждого клиента обслуживает свой поток, главный сразу ждёт следующего
    threading.Thread(target=handle_client, args=(connection, address), daemon=True).start()
