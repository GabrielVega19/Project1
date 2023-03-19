from socket import socket, AF_INET, SOCK_STREAM
import argparse
from time import sleep
import threading

class Client:
    #constructor for the client class 
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.name = name
        self.sock = socket(AF_INET, SOCK_STREAM)

    #this function establishes connection to the server
    def establishConnection(self):
        self.sock.connect((self.ip, self.port))
        self.send("establish connection", "recieved establish connection request")
        self.sock.send(self.name.encode())
        retMsg = self.sock.recv(1024).decode()
        match retMsg:
            case "connection successful":
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

    #this function requests all clients connected to the server 
    def fetchClients(self):
        self.send("fetch clients", "recieved request to fetch clients")
        clients = self.sock.recv(2048).decode()
    
    #this function sends a message to the server and raises an error if it does not reciece the expected return message
    def send(self, msg, expectedRetMsg):
        self.sock.send(msg.encode())
        retMsg = self.sock.recv(1024).decode()
        if retMsg != expectedRetMsg:
            raise Exception(f"error sending msg: {msg} to client: {self.ip} with retMsg: {retMsg}")
    
    #this function starts the two timers for the two expected behaviors in two different threads
    def startTimedBehavior(self):
        t1 = threading.Thread(target = self.tenSecTimer).start()
        t2 = threading.Thread(target = self.fifteenSecTimer).start()

    def tenSecTimer(self):
        while True:
            print("ten seconds")
            sleep(10)

    def fifteenSecTimer(self):
        while True:
            print("fifteen seconds")
            sleep(15)

    def listen(self):
        while True:
            print("listening")
            sleep(1)

    #deconstructor for the client class sends message to the server to mark as inactive 
    def __del__(self):
        self.send("close connection", "recieved request to close connection")
        self.sock.send(self.name.encode())
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


