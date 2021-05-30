from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import json


def accept_incoming_connections():
    """Handle incoming connections to the server"""
    while True:
        client, client_address = SERVER.accept()
        print(f"{client}:{client_address} joined.")
        socket_send(client, "Write your name, then press Return or click the Send button to join!")
        addresses[client] = client_address
        # A thread for each client
        Thread(target=client_handler, args=(client,)).start()


def client_handler(client: socket):
    """Handles a single client"""
    name = client.recv(BUFFER_SIZE).decode("utf8")

    if name == "{quit}":
        # Here the client closes the application before writing its name
        return

    # Welcomes the new user
    welcome_message = f"Welcome {name}! If you want to quit, write {{quit}}."
    socket_send(client, welcome_message)
    role = {
        "role": "Master"
    }
    socket_send(client, json.dumps(role))
    socket_send(client, f"Your role is: {role['role']}")
    msg = f"{name} joined the chat with the role {role['role']}!"
    # Broadcast to all the users that a new user just joined the chat
    broadcast(msg)
    # Updates the client dictionary
    clients[client] = name
    score[client] = 0

    # Game loop
    first_question = {
        "question": "What's your name?",
        "choices": [
            "Test1",
            "Test2",
            "Test3"
        ],
        "right_answer": "Test2"
    }
    second_question = {
        "question": "What's your surname?",
        "choices": [
            "Test1",
            "Test2",
            "Test3"
        ],
        "right_answer": "Test1"
    }
    third_question = {
        "question": "What's your full name?",
        "choices": [
            "Test1",
            "Test2",
            "Test3"
        ],
        "right_answer": "Test3"
    }

    all_questions = [first_question, second_question, third_question]

    trick_question = third_question
    questions = list(map(lambda q: q["question"], all_questions))
    while True:
        try:
            socket_send(client, json.dumps(questions))
            received_question = client.recv(BUFFER_SIZE).decode("utf8")
            if received_question == trick_question["question"]:
                socket_send(client, json.dumps({"status": "LOST"}))
                broadcast(f"{name} have been tricked")
                client.close()
                user_quit(client, name)
                return

            question_to_answer = next(q for q in all_questions if q["question"] == received_question)
            socket_send(client, json.dumps({"status": "NOT_LOST", "choices": question_to_answer["choices"]}))
            received_choice = client.recv(BUFFER_SIZE).decode("utf8")
            if received_choice == question_to_answer["right_answer"]:
                score[client] = score[client] + 1
            else:
                score[client] = score[client] - 1

            broadcast(f"{name} got a point, its current score is {score[client]}")
            socket_send(client, json.dumps({"score": score[client]}))
        except ConnectionResetError:
            # Here the client already closed its socket
            # so this Error is raised because socket.close() cannot be performed
            user_quit(client, name)
            break
        except Exception as err:
            print(f"Generic exception caused by {err}")
            user_quit(client, name)
            break


def broadcast(message: str, prefix=""):
    """Broadcast a message to all the clients"""
    for user in clients:
        socket_send(user, prefix + message)


def socket_send(sock: socket, message):
    """Send a message to the socket with utf8 encoding"""
    return sock.send(bytes(message + "\r\n\r\n", "utf8"))


def delete_client(client):
    del clients[client]
    del addresses[client]
    del score[client]


def user_quit(client, name):
    delete_client(client)
    broadcast(f"{name} quit.")
    print(f'{name} disconnected from the chat')


clients = {}
addresses = {}
score = {}

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
