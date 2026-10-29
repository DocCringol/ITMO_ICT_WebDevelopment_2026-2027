import socket

HOST = 'localhost'
PORT = 8080
# Сколько байт забираем за один вызов recv, а не размер сообщения
BUFFER_SIZE = 1024

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Без connect: адрес получателя указывается в каждом sendto
client_socket.sendto('Hello, server'.encode(), (HOST, PORT))

data, server_address = client_socket.recvfrom(BUFFER_SIZE)
print(f'Ответ от сервера {server_address}: {data.decode()}')

client_socket.close()
