from socket import socket, AF_INET, SOCK_STREAM

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
        while True:
            self.sock.send(b"fetch clients")        
    
    #this function sends a message to the server and raises an error if it does not reciece the expected return message
    def send(self, msg, expectedRetMsg):
        self.sock.send(msg.encode())
        retMsg = self.sock.recv(1024).decode()
        if retMsg != expectedRetMsg:
            raise Exception(f"error sending msg: {msg} to client: {self.ip} with retMsg: {retMsg}")
    
    #deconstructor for the client class sends message to the server to mark as inactive 
    def __del__(self):
        self.send("close connection", "recieved request to close connection")
        self.sock.send(self.name.encode())
        self.sock.close()

if __name__ == '__main__':
    client = Client('10.0.0.182', 9999, "test")
    client.establishConnection()

