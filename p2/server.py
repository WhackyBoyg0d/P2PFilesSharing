import socket
import threading
import os
import sys
import time

PEER_ID = sys.argv[1]  # Pass peer ID as command-line argument
PORT = None
PEER_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'peer_settings.txt')
SERVED_FILES_DIR = "served_files/"
SERVED_FILES = os.listdir(SERVED_FILES_DIR)

# Global set and lock for tracking active upload
active_uploads = set()
active_lock = threading.Lock()

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
        """
        Receives a file uploaded by the client.
        Rejects the upload if the same file is currently being uploaded.
        Sleeps 0.5 seconds after processing each chunk.
        """
        self.recvChunks = {}

        # Check if file is already being uploaded
        with active_lock:
            if fileName in active_uploads:
                self.client.sendall(f"250 Currently receiving file {fileName}".encode())
                return
            active_uploads.add(fileName)

        # Check if file is already served
        if fileName in SERVED_FILES:
            self.client.sendall(f"250 Already serving file {fileName}".encode())
            with active_lock:
                active_uploads.remove(fileName)
            return
        
        try:
            self.client.sendall(f"330 Ready to receive file {fileName}".encode())
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

                # Expected header format: "#UPLOAD filename chunk i xxxxxx"
                parts = response.split(" ", 4)
                if len(parts) < 5:
                    print("Invalid message format")
                    continue
                
                chunk = parts[3]
                data = parts[4]
                self.recvChunks[chunk] = data
                self.client.sendall(f"200 File {fileName} chunk {chunk} received".encode())
                time.sleep(0.5)
            
            self.client.sendall(f"200 File {fileName} received".encode())

            # Write received chunks to file
            with open(os.path.join(SERVED_FILES_DIR, fileName), "wb") as f:
                for chunk in sorted(self.recvChunks.keys(), key=int):
                    f.write(self.recvChunks[chunk].encode())
            f.close()

            # Add file to served files list
            SERVED_FILES.append(fileName)
            
        
        except Exception as e:
            print(e)
            if os.path.exists(os.path.join(SERVED_FILES_DIR, fileName)):
                os.remove(os.path.join(SERVED_FILES_DIR, fileName))
                if fileName in SERVED_FILES:
                    SERVED_FILES.remove(fileName)
            self.client.sendall(f"250 Error uploading file {fileName}".encode())
        
        finally:
            # Ensure file is removed even if upload fails
            with active_lock:
                active_uploads.remove(fileName)
    
    def sendAvailibity(self, fileName):
        """
        Sends availability info of the requested file.
        If file exists, returns file size; otherwise, indicates file not served.
        """
        if fileName in SERVED_FILES and fileName not in active_uploads:
            fileSize = os.path.getsize(os.path.join(SERVED_FILES_DIR, fileName))
            self.client.sendall(f"330 Ready to send file {fileName} bytes {fileSize}".encode())
        else:
            self.client.sendall(f"250 Not serving file {fileName}".encode())
    
    def sendChunk(self, fileName, chunk):
        """
        Sends a specific 100-byte chunk from the file.
        Response is sent in the format:
          "200 File filename chunk i <data>"
        or sends "Transmission complete" if no more data.
        Sleeps 0.5 seconds after sending the chunk.
        """
        try:
            file_path = os.path.join(SERVED_FILES_DIR, fileName)

            with open(file_path, "rb") as f:
                f.seek(chunk * 100)
                data = f.read(100)
                if not data:
                    self.client.sendall("Transmission complete".encode())
                    return
                header = f"200 File {fileName} chunk {chunk} ".encode()
                print(f"Sending chunk {chunk} of {fileName}")
                self.client.sendall(header + data)
                time.sleep(0.5)
        except Exception as e:
            print(e)
            self.client.sendall(f"250 Error sending chunk {chunk} of file {fileName}".encode())
        

               
    
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
            elif request[0] == "#DOWNLOAD":
                if len(request) == 2:
                    fileName = request[1]
                    print(f"Server: Received download availibility request for file {fileName}")
                    self.sendAvailibity(fileName)
                elif request[2] == "chunk":
                    fileName = request[1]
                    chunk = int(request[3])
                    print(f"Server: Received download chunk request for file {fileName} chunk {chunk}")
                    self.sendChunk(fileName, chunk)
        
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