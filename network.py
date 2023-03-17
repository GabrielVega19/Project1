from Crypto.PublicKey import RSA
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
import threading

class Server:
    def __init__(self, port):
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        
        self.ip = s.getsockname()[0]
        self.port = port
        self.clients = []
    
    def start(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(("0.0.0.0", self.port))
        sock.listen(10)

        while True:
            (clientSock, clientAddr) = sock.accept()
            t1 = threading.Thread(target = self.serviceClient, args=(clientSock, clientAddr)).start()

    def serviceClient(self, sock, addr):
        sock.send(b"connection successful")
        msg = sock.recv(1024) 
        print(msg.decode())

if __name__ == "__main__":
    server = Server(9999)
    server.start()