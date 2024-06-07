import socket  # Import the socket module to enable network communication
import os  # Import the os module to interact with the operating system
import tkinter as tk  # Import the tkinter module to create a GUI
from tkinter import filedialog, messagebox  # Import specific modules from tkinter
import time  # Import the time module to use time-related functions
import threading  # Import the threading module to handle multiple threads

# Define server address and port
SERVER_HOST = '127.0.0.1'  # Localhost (your computer)
SERVER_PORT = 5001  # Port number to connect to the server
BUFFER_SIZE = 4096  # Buffer size for data transfer
SEPARATOR = "<SEPARATOR>"  # Separator used to separate parts of a message

# Global variable for client socket
client_socket = None  # Initialize client socket as None

def connect_to_server(show_message=True):
    """Function to connect to the server"""
    global client_socket
    try:
        # Create a new socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        # Show a success message if show_message is True
        if show_message:
            messagebox.showinfo("Success", "Connected to the server.")
    except ConnectionRefusedError:
        # Show an error message if connection is refused
        messagebox.showerror("Connection Error", "The server is not started yet. Please start the server first.")

def upload_files():
    """Function to handle file uploads to the server"""
    global client_socket
    if not client_socket:
        # Show an error message if not connected to the server
        messagebox.showerror("Connection Error", "You are not connected to the server.")
        return

    # Open a file dialog to select multiple files
    filepaths = filedialog.askopenfilenames()
    if not filepaths:
        return

    for filepath in filepaths:
        filename = os.path.basename(filepath)  # Get the filename from the file path
        filesize = os.path.getsize(filepath)  # Get the file size
        try:
            # Send upload command to the server
            client_socket.send(f"UPLOAD{SEPARATOR}{filename}{SEPARATOR}{filesize}".encode())
            print(f"Sent UPLOAD command for {filename}")

            # Open the file in binary read mode
            with open(filepath, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)  # Read bytes from the file
                    if not bytes_read:  # If no more bytes are read
                        break  # Break the loop
                    client_socket.sendall(bytes_read)  # Send the bytes to the server
                print(f"File {filename} uploaded successfully.")
                # Add a small delay to allow the server to process each file individually
                time.sleep(0.1)

        except Exception as e:
            print(f"Error uploading file {filename}: {e}")  # Print any errors

    # Close the current socket connection
    client_socket.close()

    # Reconnect to the server without showing the connection message
    connect_to_server(show_message=False)

    # Request the updated list of files after upload
    list_files()

    # Show success message
    messagebox.showinfo("Success", "All files uploaded successfully.")

def download_file():
    """Function to handle file download request from the server"""
    global client_socket
    if not client_socket:
        # Show an error message if not connected to the server
        messagebox.showerror("Connection Error", "You are not connected to the server.")
        return

    # Call the function to handle file selection
    handle_file_selection()

def handle_file_selection():
    """Function to handle file selection for download"""
    global client_socket
    print("Requesting list of available files...")
    # Send list files command to the server
    client_socket.send("LIST_FILES".encode())
    # Receive response from the server
    response = client_socket.recv(BUFFER_SIZE).decode()
    print("Received response from server:", response)  # Print the response
    # Split the response to get file names
    files = response.split(SEPARATOR)

    # Filter out empty strings and remove SEPARATOR from filenames
    files = [file.strip(SEPARATOR) for file in files if file.strip()]

    if not files:
        # Show message if no files available
        messagebox.showinfo("No Files", "No files available for download.")
        return

    # Create a dialog window to display the list of files
    file_selection_dialog = tk.Toplevel()
    file_selection_dialog.title("Select File to Download")

    # Create a listbox to display the files
    file_listbox = tk.Listbox(file_selection_dialog, width=50)
    file_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Add files to the listbox
    for filename in files:
        file_listbox.insert(tk.END, filename)

    def on_download():
        """Function to handle download button click event"""
        selection = file_listbox.curselection()
        if selection:
            index = selection[0]
            filename = file_listbox.get(index)
            print("User selected file:", filename)
            # Start a new thread to download the selected file
            threading.Thread(target=download_selected_file, args=(filename,)).start()
            # Close the file selection dialog
            file_selection_dialog.destroy()
        else:
            # Show error if no file selected
            messagebox.showerror("Selection Error", "Please select a file to download.")

    # Create download button
    download_button = tk.Button(file_selection_dialog, text="Download", command=on_download)
    download_button.pack(pady=10)

def download_selected_file(filename):
    """Function to download the selected file from the server"""
    global client_socket
    try:
        # Send download command to the server
        client_socket.send(f"DOWNLOAD{SEPARATOR}{filename}".encode())
        # Receive response from the server
        response = client_socket.recv(BUFFER_SIZE).decode()
        print("Received response from server:", response)
        
        # Print the selected filename
        print("User selected file:", filename)
        
        if response.startswith("File not found"):
            # Show error if file not found
            messagebox.showerror("Error", response)
            return

        # Split the response to get file information
        file_info = response.split(SEPARATOR)
        filenames_from_server = file_info[:-1]  # Exclude the last empty element
        print("Filenames received from server:", filenames_from_server)

        if filename not in filenames_from_server:
            # Show error if file not found
            messagebox.showerror("Error", f"Selected file '{filename}' not found on the server.")
            return

        # Extract file size
        filename_index = filenames_from_server.index(filename)
        filesize = int(file_info[filename_index + 1])

        # Directory to save downloaded files
        downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded files')
        os.makedirs(downloaded_files_dir, exist_ok=True)

        # Create a file path for the downloaded file
        filepath = os.path.join(downloaded_files_dir, filename)
        # Open the file in binary write mode
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < filesize:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                bytes_received += len(bytes_read)
        # Show success message
        messagebox.showinfo("Success", f"File '{filename}' downloaded successfully.")
    except Exception as e:
        print(f"Error: {e}")

def list_files():
    """Function to request the list of available files from the server"""
    global client_socket
    print("Requesting list of available files...")
    # Send list files command to the server
    client_socket.send("LIST_FILES".encode())
    # Receive response from the server
    response = client_socket.recv(BUFFER_SIZE).decode()
    print("Received response from server:", response)

# Create the main application window
app = tk.Tk()
app.title("File Client")

# Create and place the Connect button
connect_btn = tk.Button(app, text="Connect to Server", command=connect_to_server)
connect_btn.pack(pady=10)

# Create and place the Upload button
upload_btn = tk.Button(app, text="Upload Files", command=upload_files)
upload_btn.pack(pady=10)

# Create and place the Download button
download_btn = tk.Button(app, text="Download File", command=download_file)
download_btn.pack(pady=10)

# Start the Tkinter event loop
app.mainloop()
