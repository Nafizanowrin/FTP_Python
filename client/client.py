import socket  # Import the socket module to enable network communication
import os  # Import the os module to interact with the operating system
import tkinter as tk  # Import the tkinter module to create a GUI
from tkinter import filedialog, messagebox  # Import specific modules from tkinter
import time  # Import the time module to use time-related functions
import threading  # Import the threading module to handle multiple threads
import re

BUFFER_SIZE = 4096  # Buffer size for data transfer
SEPARATOR = "<SEPARATOR>"  # Separator used to separate parts of a message

# Global variable for client socket
client_socket = None  # Initialize client socket as None

import socket
import re
from tkinter import messagebox

def is_valid_ip(ip):
    """Validate an IPv4 address."""
    # Pattern to match IPv4 addresses
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    # Check if the pattern matches and each segment is between 0 and 255
    return pattern.match(ip) is not None and all(0 <= int(num) <= 255 for num in ip.split('.'))

def is_valid_port(port):
    """Validate a port number."""
    try:
        # Convert port to an integer and check if it's in the valid range
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        # Return False if conversion to integer fails
        return False

def connect_to_server(show_message=True):
    """Function to connect to the server"""
    global client_socket
    # Get the server address and port from user input
    server_host = server_ip_entry.get()
    server_port = server_port_entry.get()
    
    # Validate server IP and port
    if not server_host or not server_port:
        # Show error if either IP or port is not provided
        messagebox.showerror("Input Error", "Server IP and Port must be provided.")
        return
    
    if not is_valid_ip(server_host):
        # Show error if IP address format is invalid
        messagebox.showerror("Input Error", "Invalid IP address format.")
        return
    
    if not is_valid_port(server_port):
        # Show error if port number is out of valid range
        messagebox.showerror("Input Error", "Port number must be between 1 and 65535.")
        return

    try:
        # Convert port to an integer
        server_port = int(server_port)
        
        # Create a new socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        client_socket.connect((server_host, server_port))
        
        # Show a success message if show_message is True
        if show_message:
            messagebox.showinfo("Success", "Connected to the server.")

        # Enable the logout button and disable the connect button
        connect_btn.config(state=tk.DISABLED)
        logout_btn.config(state=tk.NORMAL)
        
    except ConnectionRefusedError:
        # Show an error message if connection is refused
        messagebox.showerror("Connection Error", "The server is not started yet. Please start the server first.")
    except socket.gaierror:
        # Show an error message for invalid address
        messagebox.showerror("Connection Error", "The server address is invalid.")
    except socket.error as e:
        # Show an error message for any other socket errors
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

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

    # Create a frame to hold the listbox and scrollbar
    frame = tk.Frame(file_selection_dialog)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Create a listbox to display the files
    file_listbox = tk.Listbox(frame, width=50)
    file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a scrollbar
    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=file_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the listbox to use the scrollbar
    file_listbox.config(yscrollcommand=scrollbar.set)

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

    finally:
        # Reconnect to the server without showing the connection message
        client_socket.close()
        connect_to_server(show_message=False)

def list_files():
    """Function to request the list of available files from the server"""
    global client_socket
    print("Requesting list of available files...")
    # Send list files command to the server
    client_socket.send("LIST_FILES".encode())
    # Receive response from the server
    response = client_socket.recv(BUFFER_SIZE).decode()
    print("Received response from server:", response)

def show_local_files():
    """List and display files in the downloaded files directory."""
    downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded files')

    # Create the directory if it doesn't exist
    os.makedirs(downloaded_files_dir, exist_ok=True)

    # List files in the directory
    local_files = os.listdir(downloaded_files_dir)

    # Create a new window to display the files
    file_window = tk.Toplevel(app)
    file_window.title("Local Files")

    # Create a Listbox to show the files
    file_listbox = tk.Listbox(file_window, width=50, selectmode=tk.SINGLE)
    file_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Add files to the Listbox
    for file in local_files:
        file_listbox.insert(tk.END, file)

    # Add a button to delete the selected file
    delete_button = tk.Button(file_window, text="Delete Selected File",
                              command=lambda: delete_local_file(file_listbox))
    delete_button.pack(padx=10, pady=10)

def delete_local_file(file_listbox):
    """Delete the selected file from the downloaded files directory and update the list."""
    downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded files')
    selected_files = file_listbox.curselection()

    if not selected_files:
        messagebox.showwarning("Selection Error", "Please select a file to delete.")
        return

    try:
        # Get the selected file name
        file_to_delete = file_listbox.get(selected_files[0])
        file_path = os.path.join(downloaded_files_dir, file_to_delete)

        # Delete the file
        os.remove(file_path)

        # Remove the file from the Listbox
        file_listbox.delete(selected_files[0])
        messagebox.showinfo("Success", "File deleted successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while deleting the file: {str(e)}")

def logout():
    """Function to disconnect from the server"""
    global client_socket
    if client_socket:
        try:
            client_socket.close()  # Close the socket connection
            client_socket = None
            messagebox.showinfo("Success", "Disconnected from the server.")
        except socket.error as e:
            messagebox.showerror("Error", f"An error occurred while disconnecting: {str(e)}")

        # Enable the connect button and disable the logout button
        connect_btn.config(state=tk.NORMAL)
        logout_btn.config(state=tk.DISABLED)


# Create the main application window
app = tk.Tk()
app.title("File Client")

# Set the width of the window
app.geometry("400x400")

# Create and place the input fields for server IP and port
tk.Label(app, text="Server IP:").pack()
server_ip_entry = tk.Entry(app)
server_ip_entry.pack()
tk.Label(app, text="Server Port:").pack()
server_port_entry = tk.Entry(app)
server_port_entry.pack()

# Create and place the Connect button
connect_btn = tk.Button(app, text="Connect to Server", command=connect_to_server)
connect_btn.pack(pady=10)

# Create and place the Upload button
upload_btn = tk.Button(app, text="Upload Files", command=upload_files)
upload_btn.pack(pady=10)

# Create and place the Download button
download_btn = tk.Button(app, text="Download File", command=download_file)
download_btn.pack(pady=10)

# create and place the "Show Available File" button
show_files_button = tk.Button(app, text="Show Available Files", command=show_local_files)
show_files_button.pack(pady=10)

# create and place the logout button
logout_btn = tk.Button(app, text="Logout", command=logout)
logout_btn.pack(pady=10)

# Run the main event loop
app.mainloop()