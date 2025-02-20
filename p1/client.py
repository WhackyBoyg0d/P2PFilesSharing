import socket
import sys
import os
import threading

PEER_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'peer_settings.txt')
SERVED_FILES_DIR = "served_files/"
CURRENT_PEER = os.path.expanduser("~").split("/")[-1]

# Read peer settings from file
PEERS = {}
with open(PEER_SETTINGS_FILE, "r") as f:
    for line in f:
        peerID, ipAddr, port = line.strip().split()
        PEERS[peerID] = (ipAddr, int(port))

def FileAll(target_peer_id, ip, port):
    '''
    This function sends a FILELIST request to the specified peer

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
                    raise Exception(f"TCP connection to Server ({target_peer_id}) failed")

                response += response_buffer.decode()
            


            if response:
                print(f"Server ({target_peer_id}): {response}")
        
        except Exception as e:
            print(f"TCP connection to Server ({target_peer_id}) failed")
        
        finally:
            clientSocket.close()
    
    except Exception as e:
        print(f"TCP connection to Server {target_peer_id} failed")
    
    finally:
        clientSocket.close()

def Upload(target_peer_id, ip, port, file_name):
    '''
    This function uploads files to the specified peer

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
            if not os.path.exists(SERVED_FILES_DIR + file_name):
                print(f"Peer {CURRENT_PEER} does not serve file {file_name}")
                return
            
            clientSocket.sendall(b"#UPLOAD " + file_name.encode())
            response = ""
            while not response:
                response_buffer = clientSocket.recv(1024)

                if len(response_buffer) == 0:
                    raise Exception(f"TCP connection to Server ({target_peer_id}) failed")

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
                            raise Exception(f"TCP connection to Server ({target_peer_id}) failed")

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
                        raise Exception(f"TCP connection to Server ({target_peer_id}) failed")

                    response2 += response_buffer.decode()
                if response2 == f"200 File {file_name} received":
                    print(f"Server ({target_peer_id}): {response2}")
                    print(f"File {file_name} upload success")
                else:
                    print(f"Server ({target_peer_id}): {response2}")
                    print(f"File {file_name} upload failed")


        
        except Exception as e:
            print(f"TCP connection to Server ({target_peer_id}) failed")
        
        finally:
            clientSocket.close()
    
    except Exception as e:
        print(f"TCP connection to Server {target_peer_id} failed")


class ClientMain:
    '''
    This class is used to send commands to the server
    '''
    
    def __init__(self, command, target_peer_ids, file_name=None):
        self.target_peer_ids = target_peer_ids
        self.command = command
        self.file_name = file_name
    
    def executeCommand(self):
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
                        print(f"350: {e}")

                else:
                    print(f"Peer {target_peer_id} not found in peer settings")
                
        for t in threads:
            t.join()

        

def main():

    while True:
        command = input("Input your command: ").split()
        request = command[0]
        if request == "#FILELIST":
            client = ClientMain(request, command[1:])
            client.executeCommand()
        elif request == "#UPLOAD" or request == "#DOWNLOAD":
            client = ClientMain(request, command[2:], command[1])
            client.executeCommand()
        else:
            print("Invalid command")

if __name__ == "__main__":
    main()






