from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Condition, Lock
import tkinter as tkt
import json


def broadcast_receive():
    broadcast_socket.send("BROADCAST")
    while True:
        try:
            msg = broadcast_socket.recv(BUFFER_SIZE).decode("utf8")
            window_frame.push_broadcast_message(msg)
        except ConnectionResetError:
            print("Closed the broadcast connection")


def receive_from_server():
    global game_loop
    """Function for handling messages from the server"""

    # Initial communication
    try:
        # Message telling the instructions
        instructions_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        window_frame.push_message(instructions_msg)
        # Welcome message
        welcome_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        window_frame.push_message(welcome_msg)
        received_message = read_message()
        role_msg = received_message[0]
        window_frame.set_role_label(json.loads(role_msg)["role"])
        window_frame.push_message(received_message[1])
    except OSError:
        print("Closed the connection")
        return

    with selection_cond_variable:
        game_loop = True

    # Game loop
    while True:
        try:
            # Retrieve the questions
            if len(received_message) == 3:
                questions = json.loads(received_message[2])
            else:
                questions = json.loads(read_message()[0])
            # Show the questions
            show_alternatives(questions)
            # Retrieve the selected question from the combo box
            with selection_cond_variable:
                selection_cond_variable.wait()
            selected_question = window_frame.peek_message()
            window_frame.reset_message()
            # Send the selected question to the server
            client_socket.send(bytes(questions[int(selected_question) - 1], "utf8"))
            response = read_message()
            question_response = json.loads(response[0])
            # A trick question has been selected
            if question_response["status"] == "LOST":
                print("You lost")
                # Push the broadcast message
                window_frame.push_message(read_message()[0])
                # Close the window
                window_frame.close_window()
                return
            # If a not-trick question has been chosen
            # Retrieve the choices
            choices = question_response["choices"]
            # Show the choices
            show_alternatives(choices)
            # Make the user type the selected choice
            with selection_cond_variable:
                selection_cond_variable.wait()
            # Retrieve the selected choice
            selected_choice = window_frame.peek_message()
            window_frame.reset_message()
            # Send the selected choice to the server
            client_socket.send(bytes(choices[int(selected_choice) - 1], "utf8"))
            response = read_message()
            # Read the broadcast message with the new score
            window_frame.push_message(response[0])
            # Write the new score
            window_frame.push_message(f"Current score: {json.loads(read_message()[0])['score']}")
        except OSError:
            print("Closed the connection")
            break


def show_alternatives(elems):
    for i in range(len(elems)):
        window_frame.push_message(f"{i + 1}. {elems[i]}")


def send_to_server(event=None):
    global game_loop
    """Function for sending messages to the server"""
    msg = window_frame.peek_message()
    if msg == "{quit}":
        client_socket.send(bytes(msg, "utf8"))
        client_socket.close()
        window_frame.close_window()
        return

    with selection_cond_variable:
        if game_loop:
            selection_cond_variable.notify(1)
        else:
            client_socket.send(bytes(msg, "utf8"))
            window_frame.reset_message()


def read_message():
    """Read a message from the server, then return a list of messages sent by the server"""
    message = client_socket.recv(BUFFER_SIZE).decode("utf8")
    return list(filter(None, message.split('\r\n\r\n')))

def build_scrollable_listbox(parent):
    scrollbar = tkt.Scrollbar(parent)
    listbox = tkt.Listbox(parent, yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
    listbox.pack(side=tkt.LEFT, expand=True, fill=tkt.BOTH)
    return listbox

class TkinterFrame:
    """Class for handling the main frame"""

    def __init__(self, button_send_action):
        """Initialize the window"""
        self.button_send_action = button_send_action
        self.window = tkt.Tk()
        self.window.geometry("400x400")
        self.window.title("Chat Project")
        grid_configuration(self.window, 2, 4)
        # Role label
        self.role_label = tkt.Label()
        self.role_label.grid(column=0, row=0, sticky="nsew")

        self.messages_frame = tkt.Frame(self.window)
        self.message_property = tkt.StringVar()
        # Message list
        self.msg_list = build_scrollable_listbox(self.messages_frame)
        self.messages_frame.grid(column=0, row=1, sticky="nsew")
        self.entry_field = tkt.Entry(self.window, textvariable=self.message_property)
        self.entry_field.bind("<Return>", button_send_action)
        self.entry_field.grid(column=0, row=2, sticky="nsew")
        self.send_button = tkt.Button(self.window, text="Send", command=button_send_action)
        self.send_button.grid(column=0, row=3, sticky="nsew")
        # Broadcast list
        self.broadcast_pane = tkt.Frame(self.window)
        self.broadcast_list = build_scrollable_listbox(self.broadcast_pane)
        self.broadcast_pane.grid(column=1, row=1, sticky="nsew")
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

    def push_broadcast_message(self, message):
        """Push a message into the broadcast list"""
        self.broadcast_list.insert(tkt.END, message)

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

# Sync objects
selection_cond_variable = Condition()

game_loop = False

window_frame = TkinterFrame(send_to_server)

BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDRESS)

broadcast_socket = socket(AF_INET, SOCK_STREAM)
broadcast_socket.connect(ADDRESS)

receive_thread = Thread(target=receive_from_server)
receive_thread.start()

broadcast_thread = Thread(target=broadcast_receive)
broadcast_thread.start()

# Start the app
tkt.mainloop()
