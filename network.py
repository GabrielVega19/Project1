from Crypto.PublicKey import RSA
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SHUT_RDWR
import threading
from json import loads, dumps
from time import sleep
import ssl

class Server:
    #constructor for the server, sets up the ip, port and active and registered clients
    def __init__(self, port):
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        
        self.ip = s.getsockname()[0]
        self.port = port
        self.activeClients = []
        self.registeredClients = []
    
    #makes the server start listening for clients
    def start(self):
        #sets up ssl context for socket
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="ServerKeys/server.crt", keyfile="ServerKeys/server.key")

        #creates and binds the socket
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(("0.0.0.0", self.port))
        #prints out which ip address the server is running on 
        print(f"Network started at address {self.ip}")
        #start listening and creates a new thread to handle each connection
        sock.listen(10)

        while True:
            (clientSock, clientAddr) = sock.accept()
            secSock = context.wrap_socket(clientSock, server_side=True)
            t1 = threading.Thread(target = self.serviceClient, args=(secSock, clientAddr)).start()

    #This is the function that handles each connected client
    def serviceClient(self, sock, addr):
        while True:
            print(self.activeClients)
            #this listens for a message to be sent from the client and then switches over the message to detect which operation the client is requesting
            op = sock.recv(1024).decode()
            print(f"Client {addr}: {op}")
            match op:
                #this is hit when the client attempts to connect to the server
                case "establish connection":
                    sock.send(b"recieved establish connection request")
                    name = sock.recv(1024).decode()
                    if name in map(lambda x: x[0], self.registeredClients):
                        if name not in self.activeClients:
                            self.activeClients.append(name)
                            sock.send(b"connection successful")
                        else:
                            sock.send(f"Client with the name {name} is already connected".encode())
                            sock.shutdown(SHUT_RDWR)
                            sock.close()
                            exit()
                    else:
                        sock.send(b"need to register")
                        self.registerClient(sock, addr)
                #this is hit when the client requests all other connected clients
                case "fetch clients":
                    sock.send(b"recieved request to fetch clients")
                    data = []
                    for i in self.activeClients:
                        for j in self.registeredClients:
                            if i == j[0]:
                                data.append(j)
                                break
                    jsonSend = dumps(data).encode()
                    sleep(.5)
                    sock.send(jsonSend)
                #this gets hit when the client requests to close the connection
                case "close connection":
                    sock.send(b"recieved request to close connection")
                    rem = sock.recv(1024).decode()
                    self.activeClients.remove(rem)
                    sock.shutdown(SHUT_RDWR)
                    sock.close()
                    exit()
                case _:
                    print("server recieved an invalid request")
                    sock.shutdown(SHUT_RDWR)
                    sock.close()
                    exit()
    
    #this function preforms the logic for registering a client
    def registerClient(self, sock, addr):
        op = sock.recv(1024).decode()
        if op == "register client":
            sock.send(b"recieved register client request")
            name = sock.recv(1024).decode()
            self.registeredClients.append((name, addr[0]))
            sock.send(f"registered {name} with server".encode())
        else:
            sock.send("failed to register closing connection")
            sock.shutdown(SHUT_RDWR)
            sock.close()
            exit()

if __name__ == "__main__":
    server = Server(9999)
    server.start()