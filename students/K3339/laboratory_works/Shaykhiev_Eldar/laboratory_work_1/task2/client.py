import socket

HOST = 'localhost'
PORT = 8081
# Сколько байт забираем за один вызов recv, а не размер сообщения
BUFFER_SIZE = 1024

print('Площадь трапеции S = (a + b) / 2 * h')
a = input('Основание a: ')
b = input('Основание b: ')
h = input('Высота h: ')

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

client_socket.sendall(f'{a} {b} {h}'.encode())

response = client_socket.recv(BUFFER_SIZE).decode()
print(response)

client_socket.close()
