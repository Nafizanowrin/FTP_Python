import socket
import threading
import os
import tkinter as tk
from tkinter import messagebox

# Define server address and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

# Directory to store files if the user agrees to download
FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
os.makedirs(FILES_DIR, exist_ok=True)

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Server")
        
        self.start_btn = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_btn.pack(pady=5)
        
        self.stop_btn = tk.Button(root, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)
        
        self.file_listbox = tk.Listbox(root, width=50)
        self.file_listbox.pack(pady=20)
        self.file_listbox.bind('<Double-1>', self.on_file_select)
        
        self.files_received = []
        self.server_socket = None
        self.accept_thread = None

    def add_file(self, filename):
        self.file_listbox.insert(tk.END, filename + "\n")  # Add newline character
        self.files_received.append(filename)

    def on_file_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            filename = self.files_received[index]
            response = messagebox.askyesno("Download File", f"Do you want to download '{filename}'?")
            if response:
                self.download_file(filename)

    def download_file(self, filename):
        filepath = os.path.join(FILES_DIR, filename)
        
        with open(filepath, "rb") as f:
            while True:
                bytes_read = self.client_socket.recv(BUFFER_SIZE)
                if not bytes_read:    
                    break
                f.write(bytes_read)
        messagebox.showinfo("Success", f"File '{filename}' downloaded successfully.")
        self.client_socket.close()

    def handle_client(self, client_socket):
        self.client_socket = client_socket
        try:
            while True:
                command = client_socket.recv(BUFFER_SIZE).decode()
                if not command:
                    break

                if command.startswith("UPLOAD"):
                    _, filename, filesize = command.split(SEPARATOR)
                    filename = os.path.basename(filename)
                    filesize = int(filesize)

                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, "wb") as f:
                        bytes_received = 0
                        while bytes_received < filesize:
                            bytes_read = client_socket.recv(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                            bytes_received += len(bytes_read)
                    client_socket.send(f"{filename} upload complete".encode())
                    self.add_file(filename)
                    print(f"File {filename} uploaded successfully.")

                elif command == "LIST_FILES":
                    files = os.listdir(FILES_DIR)
                    if files:
                        response = SEPARATOR.join(files)
                    else:
                        response = "No files found"
                    client_socket.send(response.encode())

                elif command.startswith("DOWNLOAD"):
                    _, filename = command.split(SEPARATOR)
                    filepath = os.path.join(FILES_DIR, filename)
                    if os.path.exists(filepath):
                        filesize = os.path.getsize(filepath)
                        client_socket.send(f"{filename}{SEPARATOR}{filesize}".encode())

                        with open(filepath, "rb") as f:
                            while True:
                                bytes_read = f.read(BUFFER_SIZE)
                                if not bytes_read:
                                    break
                                client_socket.sendall(bytes_read)
                    else:
                        client_socket.send("File not found".encode())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def accept_connections(self):
        while self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Client {address} connected.")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
            except:
                break

    def start_server(self):
        if self.server_socket:
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

        self.accept_thread.join()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        print("Server stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ServerGUI(root)
    root.mainloop()
