from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
import argparse
from time import sleep
import threading
from json import loads
import ssl

class Client:
    #constructor for the client class 
    def __init__(self, ip, port, name):
        #change to netowrk ip and port and create a port for the listening on client
        self.ip = ip
        self.port = port
        self.name = name
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sEvent = threading.Event()
        self.otherClients = []
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    #this function establishes connection to the server
    def establishConnection(self):
        #creates the context for the ssl and loads the crts that it will trust from 
        self.context.load_verify_locations('CAKeys/rootCA.crt')

        #wraps the socket with ssl and then connects and retrieves the cert for the server
        self.sock = self.context.wrap_socket(self.sock, server_hostname="network server")
        self.sock.connect((self.ip, self.port))
        cert = self.sock.getpeercert()

        self.send("establish connection", "recieved establish connection request")
        self.sock.send(self.name.encode())
        retMsg = self.sock.recv(1024).decode()
        match retMsg:
            case "connection successful":
                print(f"- Connected with name {self.name}")
                return retMsg
            case "need to register":
                self.register()
                #attempts to connect again after registering
                self.send("establish connection", "recieved establish connection request")
                self.send(self.name, "connection successful")
            case _:
                return "error with connecting to server"

    #this function sends the stuff nessisary to register itself with the server
    def register(self):
        self.send("register client", "recieved register client request")
        self.send(self.name, f"registered {self.name} with server")
        print(f"- Registered with name {self.name}")

    #this function requests all clients connected to the server 
    def fetchClients(self):
        self.send("fetch clients", "recieved request to fetch clients")
        clts = loads(self.sock.recv(2048).decode())
        self.otherClients = []
        for i in clts:
            if i[0] != self.name:
                self.otherClients.append(i)
    
    #this function sends a message to the server and raises an error if it does not reciece the expected return message
    def send(self, msg, expectedRetMsg):
        self.sock.send(msg.encode())
        retMsg = self.sock.recv(1024).decode()
        if retMsg != expectedRetMsg:
            raise Exception(f"error sending msg: {msg} to client: {self.ip} with retMsg: {retMsg}")            
    
    #this function starts the two timers for the two expected behaviors in two different threads
    def startTimedBehavior(self):
        self.t1 = threading.Thread(target = self.tenSecTimer)
        self.t1.start()
        self.t2 = threading.Thread(target = self.fifteenSecTimer)
        self.t2.start()

    def tenSecTimer(self):
        sec = 0
        while not self.sEvent.is_set():
            if sec >= 10:
                self.fetchClients()
                print("- Found client(s):")
                for i in self.otherClients:
                    print(f"\t* {i[0]}")
                sec = 0
            sleep(1)
            sec += 1

    def fifteenSecTimer(self):
        sec = 0
        while not self.sEvent.is_set():
            if sec >= 15:
                for i in self.otherClients:
                    sSock = socket(AF_INET, SOCK_STREAM)
                    sSock.connect((i[1], 8888))
                    sSock.send(b"PING")
                    print(f"> {i[0]}: PING")
                    received = sSock.recv(1024).decode()
                    print(f'< {i[0]}: {received}')
                    sSock.close()
                sec = 0
            sleep(1)
            sec += 1
        
    def listen(self):
        cSock = socket(AF_INET, SOCK_STREAM)
        # change to start running on a random port and also pass in with registering client
        cSock.bind(('0.0.0.0', 8888))
        cSock.listen(10)
        try:
            while True:
                (clientSock, clientAddr) = cSock.accept()
                message = clientSock.recv(1024).decode()
                if message == "PING":
                    clientSock.send(b'PONG')

        except KeyboardInterrupt:
            print("Shutting down client.......")
            self.sEvent.set()
            self.t1.join()
            self.t2.join()

            self.send("close connection", "recieved request to close connection")
            self.sock.send(self.name.encode())
            return


    #deconstructor for the client class sends message to the server to mark as inactive 
    def __del__(self):
        self.sock.shutdown(SHUT_RDWR)
        self.sock.close()

if __name__ == '__main__':
    #handles the flags for running the program 
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", required=True, help="enter the ip address for the network you want to connect to")
    parser.add_argument("--name", required=True, help="enter the name for the client", )
    args = parser.parse_args()
    network = args.network
    name = args.name

    #creates the client and then establishes connection
    client = Client(network, 9999, name)
    client.establishConnection()
    client.startTimedBehavior()
    client.listen()
    exit(1)


