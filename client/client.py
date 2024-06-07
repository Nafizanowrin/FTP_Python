import socket
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import threading

# Define server address and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

# Global variable for client socket
client_socket = None

def upload_files():
    global client_socket
    if not client_socket:
        messagebox.showerror("Connection Error", "You are not connected to the server.")
        return

    filepaths = filedialog.askopenfilenames()
    if not filepaths:
        return

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        try:
            client_socket.send(f"UPLOAD{SEPARATOR}{filename}{SEPARATOR}{filesize}".encode())
            print(f"Sent UPLOAD command for {filename}")

            with open(filepath, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    client_socket.sendall(bytes_read)
                print(f"File {filename} uploaded successfully.")
                # Add a small delay to allow the server to process each file individually
                time.sleep(0.1)

        except Exception as e:
            print(f"Error uploading file {filename}: {e}")

    # Request the updated list of files after upload
    list_files()

    messagebox.showinfo("Success", "All files uploaded successfully.")

def download_file():
    global client_socket
    if not client_socket:
        messagebox.showerror("Connection Error", "You are not connected to the server.")
        return

    handle_file_selection()

def handle_file_selection():
    global client_socket
    print("Requesting list of available files...")
    client_socket.send("LIST_FILES".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()
    print("Received response from server:", response)  # Add this line to print the response
    files = response.split(SEPARATOR)

    # Filter out empty strings and remove SEPARATOR from filenames
    files = [file.strip(SEPARATOR) for file in files if file.strip()]

    if not files:
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
        selection = file_listbox.curselection()
        if selection:
            index = selection[0]
            filename = file_listbox.get(index)
            print("User selected file:", filename)
            threading.Thread(target=download_selected_file, args=(filename,)).start()
            file_selection_dialog.destroy()  # Close the file selection dialog
        else:
            messagebox.showerror("Selection Error", "Please select a file to download.")

    download_button = tk.Button(file_selection_dialog, text="Download", command=on_download)
    download_button.pack(pady=10)

def download_selected_file(filename):
    global client_socket
    try:
        client_socket.send(f"DOWNLOAD{SEPARATOR}{filename}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        print("Received response from server:", response)
        
        # Print the selected filename
        print("User selected file:", filename)
        
        if response.startswith("File not found"):
            messagebox.showerror("Error", response)
            return

        file_info = response.split(SEPARATOR)
        filenames_from_server = file_info[:-1]  # Exclude the last empty element
        print("Filenames received from server:", filenames_from_server)

        if filename not in filenames_from_server:
            messagebox.showerror("Error", f"Selected file '{filename}' not found on the server.")
            return

        # Extract file size
        filename_index = filenames_from_server.index(filename)
        filesize = int(file_info[filename_index + 1])

        # Download the file as before...
        downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded files')
        os.makedirs(downloaded_files_dir, exist_ok=True)

        filepath = os.path.join(downloaded_files_dir, filename)
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < filesize:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                bytes_received += len(bytes_read)
        messagebox.showinfo("Success", f"File '{filename}' downloaded successfully.")
    except Exception as e:
        print(f"Error: {e}")

def connect_to_server():
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        messagebox.showinfo("Success", "Connected to the server.")
    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "The server is not started yet. Please start the server first.")

def list_files():
    global client_socket
    print("Requesting list of available files...")
    client_socket.send("LIST_FILES".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()
    print("Received response from server:", response)

app = tk.Tk()
app.title("File Client")

connect_btn = tk.Button(app, text="Connect to Server", command=connect_to_server)
connect_btn.pack(pady=10)

upload_btn = tk.Button(app, text="Upload Files", command=upload_files)
upload_btn.pack(pady=10)

download_btn = tk.Button(app, text="Download File", command=download_file)
download_btn.pack(pady=10)

app.mainloop()
