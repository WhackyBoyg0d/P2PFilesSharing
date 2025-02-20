import socket
import threading
import os
import sys

PEER_ID = sys.argv[1]  # Pass peer ID as command-line argument
PORT = None
PEER_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'peer_settings.txt')
SERVED_FILES_DIR = "served_files/"
SERVED_FILES = os.listdir(SERVED_FILES_DIR)

# Read peer settings from file
PEERS = {}
with open(PEER_SETTINGS_FILE, "r") as f:
    for line in f:
        peerID, ipAddr, port = line.strip().split()
        PEERS[peerID] = (ipAddr, int(port))
        if peerID == PEER_ID:
            PORT = int(port)

os.makedirs(SERVED_FILES_DIR, exist_ok=True)

class ServerThread(threading.Thread):
    '''
    This class handles the client requests in a separate thread
    '''
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
    
    def sendFileList(self):
        '''
        This method sends the list of files served by the server
        '''
        response = "200 Files served: " + " ".join(SERVED_FILES)
        self.client.sendall(response.encode())
     
    def recvUpload(self, fileName):
        '''
        This method receives the file uploaded by the client
        '''
        if fileName in SERVED_FILES:
            self.client.sendall(f"250 Already serving file {fileName}".encode())
            return
        
        try:
            self.client.sendall(f"330 Ready to receive file {fileName}".encode())
            f = open(os.path.join(SERVED_FILES_DIR, fileName), "w")
            while True:
                response = ""
                while not response:
                    response_buffer = self.client.recv(1024)
                    if len(response_buffer) == 0:
                        raise Exception(f"TCP connection to Server failed")
                    print(f"Received data before decode: {response_buffer}")
                    response += response_buffer.decode()
                print(f"Received data: {response}")
                
                if response == "Transmission complete":
                    break

                parts = response.split(" ", 4)
                chunk = parts[3]
                data = parts[4]
                print(f"Writing data: {data}")
                f.write(data)
                self.client.sendall(f"200 File {fileName} chunk {chunk} received".encode())
            f.close()
            


            
            SERVED_FILES.append(fileName)
            self.client.sendall(f"200 File {fileName} received".encode())
        
        except Exception as e:
            print(e)
            if os.path.exists(os.path.join(SERVED_FILES_DIR, fileName)):
                os.remove(os.path.join(SERVED_FILES_DIR, fileName))
                if fileName in SERVED_FILES:
                    SERVED_FILES.remove(fileName)
            self.client.sendall(f"250 Error uploading file {fileName}".encode())
        

               
    
    def run(self):
        '''
        This method is called when the thread is started
        '''
        try:
            request = self.client.recv(1024).decode().split()
            if request[0] == "#FILELIST":
                self.sendFileList()
            elif request[0] == "#UPLOAD":
                fileName = request[1]
                print(f"Server: Received upload request for file {fileName}")
                self.recvUpload(fileName)
        
        except Exception as e:
            print(f"250 Error in handling client request: {e}")
        
        finally:
            self.client.close()
    




class ServerMain:
    '''
    This class starts the server for the peer
    '''
    def __init__(self):
        self.peer_name = PEER_ID
        self.peer_ip = PEERS[self.peer_name][0]
        self.peer_port = PEERS[self.peer_name][1]

    def server_run(self):
        '''
        This method starts the server for the peer
        '''

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(("localhost", PORT))
        serverSocket.listen(5)

        print(f"Server started for {self.peer_name} with ip {self.peer_ip} on port {PORT}")
        while True:
            client, addr = serverSocket.accept()
            print("Connection from peer at", addr)
            ServerThread(client).start()

if __name__ == "__main__":
    server = ServerMain()
    server.server_run()