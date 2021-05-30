from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter as tkt
import json


def receive_from_server():
    """Function for handling messages from the server"""
    try:
        # Message telling the instructions
        instructions_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        window_frame.push_message(instructions_msg)
        # Welcome message
        welcome_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        window_frame.push_message(welcome_msg)
        received_message = client_socket.recv(BUFFER_SIZE).decode("utf8")
        # Split the message because two messages are sent
        splitted_message = received_message.split('\r\n\r\n')
        role_msg = splitted_message[0]
        window_frame.set_role_label(json.loads(role_msg)["role"])
        window_frame.push_message(splitted_message[1])
    except OSError:
        print("Closed the connection")
        return

    while True:
        try:
            """Listening for messages from the server"""
            msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
            """Push the message to the message list"""
            window_frame.push_message(msg)
        except OSError:
            print("Closed the connection")
            break


def send_to_server(event=None):
    """Function for sending data to the server"""
    msg = window_frame.peek_message()
    window_frame.reset_message()
    client_socket.send(bytes(msg, "utf8"))
    if msg == "{quit}":
        client_socket.close()
        window_frame.close_window()


class TkinterFrame:
    """Class for handling the main frame"""

    def __init__(self, button_send_action):
        """Initialize the window"""
        self.button_send_action = button_send_action
        self.window = tkt.Tk()
        self.window.title("Chat Project")
        grid_configuration(self.window, 1, 4)
        # Role label
        self.role_label = tkt.Label()
        self.role_label.grid(column=0, row=0, sticky="nsew")

        self.messages_frame = tkt.Frame(self.window)
        self.message_property = tkt.StringVar()
        scrollbar = tkt.Scrollbar(self.messages_frame)
        self.msg_list = tkt.Listbox(self.messages_frame, yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
        self.msg_list.pack(side=tkt.LEFT, expand=True, fill=tkt.BOTH)
        self.messages_frame.grid(column=0, row=1, sticky="nsew")
        self.entry_field = tkt.Entry(self.window, textvariable=self.message_property)
        self.entry_field.bind("<Return>", button_send_action)
        self.entry_field.grid(column=0, row=2, sticky="nsew")
        self.send_button = tkt.Button(self.window, text="Send", command=button_send_action)
        self.send_button.grid(column=0, row=3, sticky="nsew")
        self.window.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __on_closing(self):
        """Function invoked when the window is closed"""
        self.message_property.set("{quit}")
        self.button_send_action()

    def peek_message(self):
        """Peek the current message"""
        return self.message_property.get()

    def reset_message(self):
        """Reset the message field"""
        self.message_property.set("")

    def close_window(self):
        """Close the window"""
        self.window.quit()

    def push_message(self, message):
        """Push a message into the message list"""
        self.msg_list.insert(tkt.END, message)

    def set_role_label(self, role):
        self.role_label.config(text=role)


def grid_configuration(node, colnum, rownum):
    for i in range(colnum):
        node.grid_columnconfigure(i, weight=1)

    for i in range(rownum):
        node.grid_rowconfigure(i, weight=1)


DEFAULT_PORT = 53000
DEFAULT_HOST = 'localhost'

# ----Connection to the Server----
HOST = input('Write the Host server: ')
PORT = input(f'Write the Host server port(default is {DEFAULT_PORT}): ')
if not PORT:
    PORT = DEFAULT_PORT
else:
    PORT = int(PORT)

if not HOST:
    HOST = DEFAULT_HOST

window_frame = TkinterFrame(send_to_server)

BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDRESS)

receive_thread = Thread(target=receive_from_server)
receive_thread.start()
# Start the app
tkt.mainloop()
