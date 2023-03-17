from Crypto.PublicKey import RSA
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM

class Server:
    def __init__(self, port):
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        
        self.ip = s.getsockname()[0]
        self.port = port
    
    def start(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(("0.0.0.0", self.port))
        sock.listen(10)

        while True:
            (clientSock, clientAddr) = sock.accept()

            clientSock.send(b"connection successful")
            msg = clientSock.recv(1024) 
            print(msg, clientAddr)

if __name__ == "__main__":
    server = Server(9999)
    server.start()