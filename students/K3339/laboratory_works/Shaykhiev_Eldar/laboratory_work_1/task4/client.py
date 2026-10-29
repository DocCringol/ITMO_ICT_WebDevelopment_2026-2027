import socket
import threading

HOST = 'localhost'
PORT = 8083


def receive_messages(reader):
    # Отдельный поток: печатает входящие сообщения, пока главный ждёт ввода
    while True:
        try:
            line = reader.readline()
        except (OSError, ValueError):
            break
        if not line:
            print('Соединение с сервером закрыто')
            break
        # Сообщения уже заканчиваются переводом строки
        print(line, end='')


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
# Как и на сервере, сокет читаем как текстовый файл: readline() отдаёт сообщение целиком,
# даже если буква UTF-8 пришла разрезанной между двумя порциями байт
reader = client_socket.makefile('r', encoding='utf-8')

name = input('Ваше имя: ')
client_socket.sendall(f'{name}\n'.encode())
# Приветствие выводим до запуска потока приёма, чтобы оно шло первым
print(reader.readline(), end='')
print('Для выхода из чата введите /exit')

threading.Thread(target=receive_messages, args=(reader,), daemon=True).start()

try:
    while True:
        message = input()
        client_socket.sendall(f'{message}\n'.encode())
        if message == '/exit':
            break
except (KeyboardInterrupt, EOFError):
    # Ctrl+C или Ctrl+D: выходим так же, как по /exit, без трассировки ошибки
    try:
        client_socket.sendall('/exit\n'.encode())
    except OSError:
        pass  # сервер уже недоступен
finally:
    reader.close()
    client_socket.close()
