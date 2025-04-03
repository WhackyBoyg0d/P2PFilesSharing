# Peer-to-Peer File Sharing System

This project implements a simple peer-to-peer (P2P) file sharing system using Python's socket programming and multithreading. The system allows peers to share, upload, download, and list files across a network.

## Features

- **File Listing**: Retrieve a list of files served by a peer.
- **File Upload**: Upload files from a peer's local `served_files` directory to another peer.
- **File Download**: Download files from peers in 100-byte chunks.
- **Concurrency**: Uses threading to handle multiple simultaneous file transfers.
- **Chunked Data Transfer**: Files are transferred in fixed-size chunks to ensure reliable delivery.

## File Structure

```
├── client.py          # Client-side application for sending commands to peers
├── server.py          # Server-side application for handling peer requests
├── served_files/      # Directory containing files available for sharing
└── peer_settings.txt  # Configuration file (located in the parent directory) with peer IDs, IP addresses, and ports
```

## Setup

1. **Python Version**  
   Ensure you have Python 3.x installed.

2. **Directory Structure**  
   - Place `client.py` and `server.py` in your working directory.
   - Create a `served_files/` directory in the same directory to store files for sharing.
   - Create a `peer_settings.txt` file in the parent directory. This file should contain entries in the following format:
     ```
     peerID ipAddress port
     ```
     For example:
     ```
     peer1 127.0.0.1 5000
     peer2 127.0.0.1 5001
     ```

3. **Running the Server**  
   - Open a terminal and navigate to the directory containing `server.py`.
   - Start the server by running:
     ```
     python server.py <peerID>
     ```
     Replace `<peerID>` with the appropriate identifier as defined in your `peer_settings.txt`.

4. **Running the Client**  
   - Open another terminal in the same directory as `client.py`.
   - Start the client by running:
     ```
     python client.py
     ```
   - Follow the on-screen prompts to enter commands.

## Usage

When running the client, you can use the following commands:

- **File List**:  
  Retrieve the list of files from one or more peers:
  ```
  #FILELIST <target_peer_id(s)>
  ```

- **File Upload**:  
  Upload a file from your `served_files/` directory to one or more peers:
  ```
  #UPLOAD <file_name> <target_peer_id(s)>
  ```
  The file must exist in the local `served_files/` directory.

- **File Download**:  
  Download a file from one or more peers:
  ```
  #DOWNLOAD <file_name> <target_peer_id(s)>
  ```
  The file will be downloaded in 100-byte chunks.

## Technical Details

- **Networking**:  
  Utilizes TCP sockets for peer communication. The client initiates connections to send commands, and the server listens for incoming connections to handle requests.

- **Multithreading**:  
  Both the client and server use Python's `threading` module to manage concurrent operations, ensuring that multiple file transfers and requests can be processed simultaneously.

- **File Transfer Protocol**:  
  - **Upload**: The client sends a file in chunks. The server assembles these chunks and writes the file to the `served_files/` directory.
  - **Download**: The client requests file chunks sequentially. The server sends each chunk until the complete file is transferred.
  
- **Error Handling**:  
  The system checks for connection issues and prints error messages if transfers fail or if the file is already being uploaded.

## Notes

- **Peer Settings**:  
  The `peer_settings.txt` file is critical for defining the network topology. Ensure the file is correctly formatted with valid peer IDs, IP addresses, and ports.

- **Served Files**:  
  Place any files you wish to share in the `served_files/` directory.

- **Enhancements**:  
  This implementation is designed for learning and testing purposes. Additional features, security measures, and robustness improvements can be added for production use.

## License

This project is licensed under the MIT License.
