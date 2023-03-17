from socket import socket, AF_INET, SOCK_STREAM

class TCPClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def send(self, message):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((self.server, self.port))

        received = sock.recv(1024)
        print(received)
        sock.send(message)

        sock.close()


if __name__ == '__main__':
    client = TCPClient('10.0.0.182', 9999)
    client.send(b'Hello Server.')
