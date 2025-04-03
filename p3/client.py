import socket
import sys
import os
import threading
import time

PEER_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'peer_settings.txt')
SERVED_FILES_DIR = "served_files/"
SERVED_FILES = os.listdir(SERVED_FILES_DIR)
CURRENT_PEER = os.path.basename(os.getcwd())

# Read peer settings from file
PEERS = {}
with open(PEER_SETTINGS_FILE, "r") as f:
    for line in f:
        peerID, ipAddr, port = line.strip().split()
        PEERS[peerID] = (ipAddr, int(port))

def FileAll(target_peer_id, ip, port):
    '''
    This function sends a #FILELIST request to the specified peer to get the list of files served by the peer

    Args:
        target_peer_id (str): The ID of the peer to send the request to
        ip (str): The IP address of the peer
        port (int): The port
    '''

    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((ip, port))
        print(f"Client ({target_peer_id}): #FILELIST")

        try:
            clientSocket.sendall(b"#FILELIST")
            response = clientSocket.recv(1024).decode()
            while not response:
                response_buffer = clientSocket.recv(1024)

                if len(response_buffer) == 0:
                    raise Exception(f"TCP connection to server ({target_peer_id}) failed")

                response += response_buffer.decode()
            


            if response:
                print(f"Server ({target_peer_id}): {response}")
        
        except Exception as e:
            print(f"TCP connection to server ({target_peer_id}) failed")
        
        finally:
            clientSocket.close()
    
    except Exception as e:
        print(f"TCP connection to server {target_peer_id} failed")
    
    finally:
        clientSocket.close()

def Upload(target_peer_id, ip, port, file_name):
    '''
    This function uploads files to the specified peer by sending an #UPLOAD request

    Args:
        target_peer_id (str): The ID of the peer to send the request to
        ip (str): The IP address of the peer
        port (int): The port
        file_name (str): The name of the file to upload
    '''

    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((ip, port))
        fileSize = os.path.getsize(SERVED_FILES_DIR + file_name)
        print(f"Client ({target_peer_id}): #UPLOAD {file_name} bytes " + str(int(fileSize)))

        try:     
            
            clientSocket.sendall(b"#UPLOAD " + file_name.encode())
            response = ""
            while not response:
                response_buffer = clientSocket.recv(1024)

                if len(response_buffer) == 0:
                    raise Exception(f"TCP connection to server ({target_peer_id}) failed")

                response += response_buffer.decode()
            
            if "250" in response:
                print(f"Server ({target_peer_id}): {response}")
                return
            
            elif "330" in response:
                print(f"Server ({target_peer_id}): {response}")
                fi = open(SERVED_FILES_DIR + file_name, "rb")
                data = fi.read(100)
                ctr = 0
                while data:
                    msg = f"#UPLOAD {file_name} chunk {ctr} "
                    print(f"Client ({target_peer_id}): {msg}")
                    clientSocket.sendall(msg.encode() + data)
                    response = ""
                    while not response:
                        response_buffer = clientSocket.recv(1024)

                        if len(response_buffer) == 0:
                            raise Exception(f"TCP connection to server ({target_peer_id}) failed")

                        response += response_buffer.decode()
                    
                    if "200" in response:
                        print(f"Server ({target_peer_id}): {response}")
                        data = fi.read(100)
                        ctr += 1
                    else:
                        print(f"Server ({target_peer_id}): {response}")
                        print(f"File {file_name} upload failed")
                        break
                fi.close()

                clientSocket.sendall(b"Transmission complete")

                response2 = ""
                while not response2:
                    response_buffer = clientSocket.recv(1024)

                    if len(response_buffer) == 0:
                        raise Exception(f"TCP connection to server ({target_peer_id}) failed")

                    response2 += response_buffer.decode()
                if response2 == f"200 File {file_name} received":
                    print(f"Server ({target_peer_id}): {response2}")
                    print(f"File {file_name} upload success")
                else:
                    print(f"Server ({target_peer_id}): {response2}")
                    print(f"File {file_name} upload failed")


        
        except Exception as e:
            print(f"TCP connection to server ({target_peer_id}) failed")
        
        finally:
            clientSocket.close()
    
    except Exception as e:
        print(f"TCP connection to server {target_peer_id} failed")




class ClientMain:
    '''
    This class is used to send commands to the server
    '''
    
    def __init__(self, command, target_peer_ids, file_name=None):
        self.target_peer_ids = target_peer_ids
        self.command = command
        self.file_name = file_name
        self.serving_peers = []
    
    def executeCommand(self):
        '''
        This method executes #FILELIST and #UPLOAD commands
        '''
        threads = []
        target_peer_ids = self.target_peer_ids
        for target_peer_id in target_peer_ids:
                if target_peer_id in PEERS:
                    ip, port = PEERS[target_peer_id]
                    try :
                        if self.command == "#FILELIST":
                            t = threading.Thread(target=FileAll, args=(target_peer_id, ip, port))
                            t.start()
                            threads.append(t)
                        elif self.command == "#UPLOAD":
                            t = threading.Thread(target=Upload, args=(target_peer_id, ip, port, self.file_name))
                            t.start()
                            threads.append(t)
                        else:
                            print("Invalid command")
                    except Exception as e:
                        print(f"TCP connection to server {target_peer_id} failed")

                else:
                    print(f"Peer {target_peer_id} not found in peer settings")
                
        for t in threads:
            t.join()
    
    def excexuteDownload(self):
        '''
        This method executes the #DOWNLOAD command
        '''
        threads = []
        target_peer_ids = self.target_peer_ids
        self.serving_peers = []
        self.inactive_peers = []
        self.file_size = 0
        self.faliure = False
        self.failed_peer = None

        if self.file_name in SERVED_FILES:
            print(f"File {self.file_name} already exists in peer {CURRENT_PEER}")
            return

        for target_peer_id in target_peer_ids:
            if target_peer_id in PEERS:
                t = threading.Thread(target=self.checkAvailibity, args=(target_peer_id, self.file_name))
                t.start()
                threads.append(t)

            else:
                print(f"Peer {target_peer_id} not found in peer settings")
        for t in threads:
            t.join()

        if len(self.inactive_peers) == len(target_peer_ids):
            print(f"File {self.file_name} download failed, all peers are inactive")
            return

        if not self.serving_peers:
            print(f"File {self.file_name} download failed, peers {" ".join(target_peer_ids)} are not serving the file")
            return
        
        self.chunks = {}
        
        chunk = 0
        try:
            while chunk * 100 < self.file_size:
                t = threading.Thread(target=self.downloadChunk, args=(self.file_name, chunk))
                t.start()
                threads.append(t)
                if self.faliure:
                    print(f"TCP connection to server {self.failed_peer} failed")
                    print(f"File {self.file_name} download failed")
                    return
                chunk += 1
        except Exception as e:
            return

        for t in threads:
            t.join()


        if self.faliure or len(self.chunks) != chunk:
            print(f"File {self.file_name} download failed")
            return
        
        file_path = os.path.join(SERVED_FILES_DIR, self.file_name)
        
        try:
            with open(file_path, "w") as f:
                for i in range(chunk):
                    data = self.chunks.get(i, "")
                    if not data:
                        print(f"File {self.file_name} download failed")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return
                    f.write(data)
            SERVED_FILES.append(self.file_name)
            print(f"File {self.file_name} downloaded successfully.")
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            if self.file_name in SERVED_FILES:
                SERVED_FILES.remove(self.file_name)
            print(f"Error writing file {self.file_name}: {e}")

    def checkAvailibity(self, target_peer_id, file_name):
        '''
        This method checks if the file is available at the specified peer

        Args:
            target_peer_id (str): The ID of the peer to check
            file_name (str): The name of the file to check
        '''

        try:
            ip, port = PEERS[target_peer_id]
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect((ip, port))
            print(f"Client ({target_peer_id}): #DOWNLOAD {file_name}")

            try:
                clientSocket.sendall(b"#DOWNLOAD " + file_name.encode())
                response = ""
                while not response:
                    response_buffer = clientSocket.recv(1024)

                    if len(response_buffer) == 0:
                        raise Exception(f"TCP connection to server ({target_peer_id}) failed")

                    response += response_buffer.decode()
                
                if response:
                    print(f"Server ({target_peer_id}): {response}")
                    if "330" in response:
                        self.file_size = int(response.split()[-1])
                        self.serving_peers.append(target_peer_id)
            
            except Exception as e:
                print(f"TCP connection to server ({target_peer_id}) failed")
            
            finally:
                clientSocket.close()
        
        except Exception as e:
            self.inactive_peers.append(target_peer_id)
            print(f"TCP connection to server {target_peer_id} failed")
            return False
        
        finally:
            clientSocket.close()
    
    def downloadChunk(self, file_name, chunk):
        '''
        This method downloads a chunk of the file from the server
        '''

        while True:

            peerIdx = chunk % len(self.serving_peers)
            peerID = self.serving_peers[peerIdx]
            ip, port = PEERS[peerID]

            try:
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect((ip, port))
                print(f"Client ({peerID}): #DOWNLOAD {file_name} chunk {chunk}")
                req = f"#DOWNLOAD {file_name} chunk {chunk}"
                
                clientSocket.sendall(req.encode())

                response = ""
                while not response:
                    response_buffer = clientSocket.recv(1024)

                    if len(response_buffer) == 0:
                        self.faliure = True
                        self.failed_peer = peerID
                        raise Exception(f"TCP connection to server {peerID} failed")

                    response += response_buffer.decode()
                
                clientSocket.close()

                if "200" in response:
                    parts = response.split(" ", 5)
                    print(f"Server ({peerID}): {" ".join(parts[:5])}")
                    data = parts[5]
                    self.chunks[chunk] = data
                    return True
                
                else:
                    print(f"Server ({peerID}): {response}")
                    self.faliure = True
                    self.failed_peer = peerID
                    break
            
            except Exception as e:

                self.faliure = True
                self.failed_peer = peerID
                return False
            
            finally:
                clientSocket.close()

def main():

    while True:
        command = input("Input your command: ").split()
        request = command[0]
        if request == "#FILELIST":
            client = ClientMain(request, command[1:])
            client.executeCommand()
        elif request == "#UPLOAD":
            file_name = command[1]
            if file_name not in SERVED_FILES:
                print(f"Peer {CURRENT_PEER} does not serve file {file_name}")
                continue
            print(f"Uploading file {command[1]}")
            client = ClientMain(request, command[2:], command[1])
            client.executeCommand()
        elif request == "#DOWNLOAD":
            print(f"Downloading file {command[1]}")
            client = ClientMain(request, command[2:], command[1])
            client.excexuteDownload()
        else:
            print("Invalid command")

if __name__ == "__main__":
    main()