import socket  # Import socket module to handle network connections
import threading  # Import threading module to handle multiple clients simultaneously
import os  # Import os module for file system operations
import tkinter as tk  # Import tkinter module for creating the graphical user interface (GUI)
from tkinter import messagebox, PhotoImage  # Import messagebox from tkinter for showing dialog boxes
from tkinter import Scrollbar  # Import Scrollbar from tkinter for creating scrollbars

# Define default server address and port
DEFAULT_SERVER_HOST = '127.0.0.1'  # Listen on all available network interfaces
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
        
        # Set the window icon
        icon_path = os.path.join(os.path.dirname(__file__), "logo.png")
        root.iconphoto(False, PhotoImage(file=icon_path))

        # Set the window title
        self.root.title("File Server")

        # Set the background color of the root window
        self.root.configure(bg="#ADD8E6")

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

        # Button to show available files
        self.show_files_btn = tk.Button(root, text="Show Available Files", command=self.show_available_files)
        # Pack the button with padding
        self.show_files_btn.pack(pady=5)

        # Listbox to display received files
        self.file_listbox = tk.Listbox(root, width=50)
        # Pack the listbox with padding
        self.file_listbox.pack(pady=20)

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

        try:
            # This line creates a new socket object using the socket module.
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # This line binds the socket to a specific IP address and port number.
            self.server_socket.bind((server_host, server_port))

            self.server_socket.listen(5)
            print(f"Server listening on {server_host}:{server_port}")

            self.accept_thread = threading.Thread(target=self.accept_connections)
            self.accept_thread.start()

            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

        except OSError as e:
            # Handle invalid IP address or port error
            if e.errno == 10049:  # Windows specific error code for invalid address context
                messagebox.showerror("Server Error", "The requested address is not valid in its context.")
            else:
                messagebox.showerror("Server Error", f"An error occurred: {str(e)}")
            self.server_socket = None  # Reset server socket if an error occurs

        except Exception as e:
            messagebox.showerror("Server Error", f"An unexpected error occurred: {str(e)}")
            self.server_socket = None  # Reset server socket if an error occurs

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

    def show_available_files(self):
        # Create a new window
        files_window = tk.Toplevel(self.root)
        files_window.title("Available Files")

        # Create a frame to hold the listbox and scrollbar
        frame = tk.Frame(files_window)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create a scrollbar
        scrollbar = Scrollbar(frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a listbox to display the files
        file_listbox = tk.Listbox(frame, width=50, yscrollcommand=scrollbar.set)
        file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure the scrollbar
        scrollbar.config(command=file_listbox.yview)

        # Get the list of files in the directory
        files = os.listdir(FILES_DIR)

        # Add files to the listbox
        for file in files:
            file_listbox.insert(tk.END, file)

        # Handle case when there are no files
        if not files:
            file_listbox.insert(tk.END, "No files available")

        # Create a delete button
        delete_button = tk.Button(files_window, text="Delete Selected File",
                                  command=lambda: self.delete_file(file_listbox))
        delete_button.pack(pady=10)

    def delete_file(self, file_listbox):
        # Get the selected item in the listbox
        selection = file_listbox.curselection()
        if selection:
            # Get the index of the selected item
            index = selection[0]
            # Get the filename from the list
            filename = file_listbox.get(index)
            # Get the full path of the file
            filepath = os.path.join(FILES_DIR, filename)
            # Confirm deletion
            response = messagebox.askyesno("Delete File", f"Do you want to delete '{filename}'?")
            if response:
                try:
                    # Delete the file
                    os.remove(filepath)
                    # Remove the file from the listbox
                    file_listbox.delete(index)

                    # Show success message
                    messagebox.showinfo("Success", f"File '{filename}' deleted successfully.")
                except Exception as e:
                    # Show error message if deletion fails
                    messagebox.showerror("Error", f"Could not delete file '{filename}'.\n{str(e)}")


if __name__ == "__main__":
    # Create the root window
    root = tk.Tk()
    # Create the server GUI
    gui = ServerGUI(root)
    # Run the main loop
    root.mainloop()
