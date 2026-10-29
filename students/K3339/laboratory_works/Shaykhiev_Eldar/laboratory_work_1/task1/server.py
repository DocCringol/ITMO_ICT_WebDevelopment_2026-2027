import socket

HOST = 'localhost'
PORT = 8080
# Сколько байт забираем за один вызов recv, а не размер сообщения
BUFFER_SIZE = 1024

# SOCK_DGRAM = UDP: соединение не устанавливается, listen/accept не нужны
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))
print(f'UDP-сервер запущен на {HOST}:{PORT}...')

while True:
    # recvfrom возвращает и данные, и адрес отправителя, по нему отвечаем
    data, client_address = server_socket.recvfrom(BUFFER_SIZE)
    print(f'Сообщение от {client_address}: {data.decode()}')

    server_socket.sendto('Hello, client'.encode(), client_address)
