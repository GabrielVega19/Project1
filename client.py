from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
import argparse
from time import sleep
import threading
from json import loads, dumps
import ssl
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA3_512
from Crypto.Signature import PKCS1_v1_5

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

        #wraps the socket with ssl and then connects 
        self.sock = self.context.wrap_socket(self.sock, server_hostname="network server")
        self.sock.connect((self.ip, self.port))

        #sends the message that the client wants to esablish connection 
        self.send("establish connection", "recieved establish connection request")
        self.sock.send(self.name.encode())
        
        #gets a message back and switches over it to check if successful or needs to register or there was an error
        retMsg = self.sock.recv(1024).decode()
        match retMsg:
            #if successful then it opens the client keys to use for encryption 
            case "connection successful":
                print(f"- Connected with name {self.name}")
                with open("ClientKeys/client.key", "rb") as file:
                    self.privKey = RSA.import_key(file.read())
                with open("ClientKeys/client.pub", "rb") as file:
                    self.pubKey = RSA.import_key(file.read())
            
            #if if you need to register then it will generate the keys for the client first and then register itself and send them over to the server
            case "need to register":
                #generates and stores keys
                self.privKey = RSA.generate(2048)
                self.pubKey = self.privKey.public_key()
                with open("ClientKeys/client.pub", "wb") as file:
                    file.write(self.pubKey.export_key())
                with open("ClientKeys/client.key", "wb") as file:
                    file.write(self.privKey.export_key())

                #attempts to register itself
                self.register()

                #attempts to connect again after registering
                self.send("establish connection", "recieved establish connection request")
                self.send(self.name, "connection successful")
            case _:
                return "error with connecting to server"

    #this function sends the stuff nessisary to register itself with the server
    def register(self):
        #creates a dictionary object with the information to register yourself
        data = {"name": self.name, "pubKey": self.pubKey.export_key().hex()}

        #sends the message over that it wants to register itself and then sends over the data dumped to a json format
        self.send("register client", "recieved register client request")
        self.send(dumps(data), f"registered {self.name} with server")
        print(f"- Registered with name {self.name}")

    #this function requests all clients connected to the server 
    def fetchClients(self):
        self.send("fetch clients", "recieved request to fetch clients")
        clts = loads(self.sock.recv(2048).decode())
        self.otherClients = []
        for i in clts:
            # if i[0] != self.name:
            self.otherClients.append([i[0], i[1], bytes.fromhex(i[2])])
    
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
                    
                    #sends ping to the server
                    self.secureSend(sSock, "ping", i[0])
                    print(f"> {i[0]}: PING")
                    received, name = self.secureRecieve(sSock, 2048)
                    print(f'< {name}: {received}')

                    sSock.close()
                sec = 0
            sleep(1)
            sec += 1
        
    def listen(self):
        cSock = socket(AF_INET, SOCK_STREAM)
        # if have time change to start running on a random port and also pass in with registering client
        cSock.bind(('0.0.0.0', 8888))
        cSock.listen(10)
        try:
            while True:
                (clientSock, clientAddr) = cSock.accept()

                #waits to reviece the ping message and then returns pong
                message, name = self.secureRecieve(clientSock, 2048)
                if message == "PING":
                    self.secureSend(clientSock, "PONG", name)
                    clientSock.close()
                else: 
                    print("could not verify message from sender")

        except KeyboardInterrupt:
            print("Shutting down client.......")
            self.sEvent.set()
            self.t1.join()
            self.t2.join()

            self.send("close connection", "recieved request to close connection")
            self.sock.send(self.name.encode())
            return

    #securely sends a string between clients 
    def secureSend(self, sock, message, name):
        for i in self.otherClients:
            if i[0] == name:
                #creates the hash object for the message
                hash = SHA3_512.new(message.encode())
                #signes the hash
                sig = PKCS1_v1_5.new(self.privKey).sign(hash)
                #encodes the message
                ciphertext = PKCS1_OAEP.new(RSA.import_key(i[2])).encrypt(message.encode())
                #puts everything into a touple and then sends over
                data = dumps((self.name, sig.hex(), ciphertext.hex()))
                sock.send(data.encode())

    #secure recieve
    def secureRecieve(self, sock, numBytes):
        #recieves the initial message
        mes = loads(sock.recv(numBytes).decode())
        #parses it into a touple 
        data = (mes[0], bytes.fromhex(mes[1]), bytes.fromhex(mes[2]))
        #loops through the array of clients to find the information for the one who sent it
        for i in self.otherClients:
            if i[0] == data[0]:
                print(i)
                #decodes the message with the client priv key
                plaintext = PKCS1_OAEP.new(self.privKey).decrypt(data[2])
                #creates the hash for verification
                hash = SHA3_512.new(plaintext)
                #creates the verifyer object with the pubkey for the sender
                verifier = PKCS1_v1_5.new(RSA.import_key(i[2]))
                #if it can verify the signature then it returns the message and the senders name
                if verifier.verify(hash, data[1]):
                    return plaintext.decode(), data[0]
        print("weird error")
        return "error", "error"

                


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


