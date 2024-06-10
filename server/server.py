import socket  # Import socket module to handle network connections
import threading  # Import threading module to handle multiple clients simultaneously
import os  # Import os module for file system operations
import tkinter as tk  # Import tkinter module for creating the graphical user interface (GUI)
from tkinter import messagebox  # Import messagebox from tkinter for showing dialog boxes

# Define default server address and port
DEFAULT_SERVER_HOST = '0.0.0.0'  # Listen on all available network interfaces
DEFAULT_SERVER_PORT = 5001  # Default port to listen on
BUFFER_SIZE = 4096  # Size of the buffer for receiving data
SEPARATOR = "<SEPARATOR>"  # Separator used for splitting command strings

# Directory to store files if the user agrees to download
FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')  # Path to the 'files' directory
os.makedirs(FILES_DIR, exist_ok=True)  # Create the directory if it doesn't exist


class ServerGUI:
    def __init__(self, root):
        # Initialize the root window
        self.root = root
        # Set the window title
        self.root.title("File Server")

        # IP address label and entry
        self.ip_label = tk.Label(root, text="Server IP:")
        self.ip_label.pack(pady=5)
        self.ip_entry = tk.Entry(root)
        self.ip_entry.pack(pady=5)
        self.ip_entry.insert(tk.END, DEFAULT_SERVER_HOST)  # Default value

        # Port number label and entry
        self.port_label = tk.Label(root, text="Server Port:")
        self.port_label.pack(pady=5)
        self.port_entry = tk.Entry(root)
        self.port_entry.pack(pady=5)
        self.port_entry.insert(tk.END, str(DEFAULT_SERVER_PORT))  # Default value

        # Button to start the server
        self.start_btn = tk.Button(root, text="Start Server", command=self.start_server)
        # Pack the button with padding
        self.start_btn.pack(pady=5)

        # Button to stop the server, initially disabled
        self.stop_btn = tk.Button(root, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        # Pack the button with padding
        self.stop_btn.pack(pady=5)

        # Listbox to display received files
        self.file_listbox = tk.Listbox(root, width=50)
        # Pack the listbox with padding
        self.file_listbox.pack(pady=20)
        # Bind double-click event to file selection
        self.file_listbox.bind('<Double-1>', self.on_file_select)

        # List to keep track of received files
        self.files_received = []
        # Server socket, initially None
        self.server_socket = None
        # Thread for accepting connections, initially None
        self.accept_thread = None

    def add_file(self, filename):
        # Add the filename to the listbox
        self.file_listbox.insert(tk.END, filename + "\n")
        # Add the filename to the received files list
        self.files_received.append(filename)

    def on_file_select(self, event):
        # Get the selected item in the listbox
        selection = event.widget.curselection()
        if selection:
            # Get the index of the selected item
            index = selection[0]
            # Get the filename from the list
            filename = self.files_received[index]
            # Ask if the user wants to download the file
            response = messagebox.askyesno("Download File", f"Do you want to download '{filename}'?")
            if response:
                # If yes, download the file
                self.download_file(filename)

    def download_file(self, filename):
        # Get the full path of the file
        filepath = os.path.join(FILES_DIR, filename)

        # Open the file in binary read mode
        with open(filepath, "rb") as f:
            while True:
                # Receive bytes from the client
                bytes_read = self.client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    # If no more bytes are received, break the loop
                    break
                # Write the received bytes to the file
                f.write(bytes_read)
        # Show success message
        messagebox.showinfo("Success", f"File '{filename}' downloaded successfully.")
        # Close the client socket
        self.client_socket.close()

    def handle_client(self, client_socket):
        # Assign the client socket to an instance variable
        self.client_socket = client_socket
        try:
            while True:
                # Receive command from the client
                command = client_socket.recv(BUFFER_SIZE).decode()
                if not command:
                    # If no command is received, break the loop
                    break

                if command.startswith("UPLOAD"):
                    # Split the command into filename and filesize
                    _, filename, filesize = command.split(SEPARATOR)
                    # Get the basename of the file
                    filename = os.path.basename(filename)
                    # Convert filesize to integer
                    filesize = int(filesize)

                    # Get the full path of the file
                    filepath = os.path.join(FILES_DIR, filename)
                    # Open the file in binary write mode
                    with open(filepath, "wb") as f:
                        # Initialize bytes received counter
                        bytes_received = 0
                        # While the file is not completely received
                        while bytes_received < filesize:
                            # Receive bytes from the client
                            bytes_read = client_socket.recv(BUFFER_SIZE)
                            if not bytes_read:
                                # If no more bytes are received, break the loop
                                break
                            # Write the received bytes to the file
                            f.write(bytes_read)
                            # Update bytes received counter
                            bytes_received += len(bytes_read)
                    # Send upload complete message to the client
                    client_socket.send(f"{filename} upload complete".encode())
                    # Add the file to the listbox
                    self.add_file(filename)
                    # Print success message
                    print(f"File {filename} uploaded successfully.")

                elif command == "LIST_FILES":
                    # Get the list of files in the directory
                    files = os.listdir(FILES_DIR)
                    if files:
                        # Join the filenames with the separator
                        response = SEPARATOR.join(files)
                    else:
                        # If no files are found
                        response = "No files found"
                    # Send the response to the client
                    client_socket.send(response.encode())

                elif command.startswith("DOWNLOAD"):
                    # Split the command to get the filename
                    _, filename = command.split(SEPARATOR)
                    # Get the full path of the file
                    filepath = os.path.join(FILES_DIR, filename)
                    if os.path.exists(filepath):
                        # If the file exists, get the size of the file
                        filesize = os.path.getsize(filepath)
                        # Send the filename and filesize to the client
                        client_socket.send(f"{filename}{SEPARATOR}{filesize}".encode())

                        # Open the file in binary read mode
                        with open(filepath, "rb") as f:
                            while True:
                                # Read bytes from the file
                                bytes_read = f.read(BUFFER_SIZE)
                                if not bytes_read:
                                    # If no more bytes are read, break the loop
                                    break
                                # Send the bytes to the client
                                client_socket.sendall(bytes_read)
                    else:
                        # If the file is not found, send error message
                        client_socket.send("File not found".encode())
        except Exception as e:
            # Print any exceptions
            print(f"Error: {e}")
        finally:
            # Close the client socket
            client_socket.close()

    def accept_connections(self):
        while self.server_socket:
            try:
                # Accept a client connection
                client_socket, address = self.server_socket.accept()
                # Print client address
                print(f"Client {address} connected.")
                # Create a thread to handle the client
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                # Start the thread
                client_handler.start()
            except:
                # Break the loop if there is an exception
                break

    def start_server(self):
        if self.server_socket:
            # If the server is already running, return
            return

        # Get the IP address and port from the user inputs
        server_host = self.ip_entry.get() or DEFAULT_SERVER_HOST
        server_port = int(self.port_entry.get()) if self.port_entry.get() else DEFAULT_SERVER_PORT

        # Create a new socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the address and port
        self.server_socket.bind((server_host, server_port))
        # Start listening for connections
        self.server_socket.listen(5)
        # Print server status
        print(f"Server listening on {server_host}:{server_port}")

        # Create a thread to accept connections
        self.accept_thread = threading.Thread(target=self.accept_connections)
        # Start the thread
        self.accept_thread.start()

        # Disable the start button
        self.start_btn.config(state=tk.DISABLED)
        # Enable the stop button
        self.stop_btn.config(state=tk.NORMAL)

    def stop_server(self):
        if self.server_socket:
            # If the server is running, close the server socket
            self.server_socket.close()
            # Set the server socket to None
            self.server_socket = None

        # Wait for the accept thread to finish
        self.accept_thread.join()
        # Enable the start button
        self.start_btn.config(state=tk.NORMAL)
        # Disable the stop button
        self.stop_btn.config(state=tk.DISABLED)
        # Print server status
        print("Server stopped.")


if __name__ == "__main__":
    # Create the root window
    root = tk.Tk()
    # Create the server GUI
    gui = ServerGUI(root)
    # Run the main loop
    root.mainloop()
