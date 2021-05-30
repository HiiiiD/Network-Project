from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import json


def accept_incoming_connections():
    """Handle incoming connections to the server"""
    while True:
        client, client_address = SERVER.accept()
        print(f"{client}:{client_address} joined.")
        client.send(bytes("Write your name, then press Return or click the Send button to join!", "utf8"))
        addresses[client] = client_address
        # A thread for each client
        Thread(target=client_handler, args=(client,)).start()


def client_handler(client):
    """Handles a single client"""
    name = client.recv(BUFFER_SIZE).decode("utf8")

    if name == "{quit}":
        # Here the client closes the application before writing its name
        return

    # Welcomes the new user
    welcome_message = f"Welcome {name}! If you want to quit, write {{quit}}."
    client.send(bytes(welcome_message, "utf8"))
    role = {
        "role": "Master"
    }
    client.send(bytes(json.dumps(role), "utf8"))
    msg = f"{name} joined the chat with the role {role['role']}!"
    # Broadcast to all the users that a new user just joined the chat
    broadcast(bytes(msg, "utf8"))
    # Updates the client dictionary
    clients[client] = name

    # Listening for new messages from the chat
    while True:
        try:
            msg = client.recv(BUFFER_SIZE)
            if msg != bytes("{quit}", "utf8"):
                broadcast(msg, name + ": ")
            else:
                client.send(bytes("{quit}", "utf8"))
                client.close()
                del clients[client]
                del addresses[client]
                broadcast(bytes(f"{name} quit.", "utf8"))
                print(f'{client} disconnected from the chat')
                break
        except ConnectionResetError:
            # Here the client already closed its socket
            # so this Error is raised because socket.close() cannot be performed
            del clients[client]
            del addresses[client]
            broadcast(bytes(f"{name} quit.", "utf8"))
            print(f'{name} disconnected from the chat')
            break


def broadcast(message, prefix=""):
    """Broadcast a message to all the clients"""
    for user in clients:
        user.send(bytes(prefix, "utf8") + message)


clients = {}
addresses = {}

HOST = 'localhost'
PORT = 53000
BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDRESS)

if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connections...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
