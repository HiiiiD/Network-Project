from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Timer
import json
from random import shuffle, choice
from typing import Dict, Tuple, List


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
    if name == "BROADCAST":
        broadcast_clients.append(client)
        return

    if name == "LEADERBOARD":
        leaderboard_clients.append(client)
        broadcast_leaderboard()
        return

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
    while True:
        shuffle(questions_obj["questions"])
        all_questions = questions_obj["questions"][:3]
        questions = list(map(lambda q: q["question"], all_questions))
        trick_question = choice(all_questions)
        try:
            socket_send(client, json.dumps(questions))
            received_question = client.recv(BUFFER_SIZE).decode("utf8")
            if received_question == "VALIDATION ERROR":
                continue
            if received_question == trick_question["question"]:
                socket_send(client, json.dumps({"status": "LOST"}))
                broadcast(f"{name} have been tricked")
                client.close()
                user_quit(client, name)
                return

            question_to_answer = next(q for q in all_questions if q["question"] == received_question)
            socket_send(client, json.dumps({"status": "NOT_LOST", "choices": question_to_answer["choices"]}))
            received_choice = client.recv(BUFFER_SIZE).decode("utf8")
            if received_choice == "VALIDATION ERROR":
                continue

            won = False
            if received_choice == question_to_answer["right_answer"]:
                won = True
                score[client] = score[client] + 1
            else:
                score[client] = score[client] - 1

            broadcast(f"{name} {'got' if won else 'lost'} a point, its current score is {score[client]}")
            broadcast_leaderboard()
            socket_send(client, json.dumps({"score": score[client]}))
        except ConnectionResetError:
            # Here the client already closed its socket
            # so this Error is raised because socket.close() cannot be performed
            user_quit(client, name)
            break
        except Exception as err:
            print("Generic exception:", err)
            user_quit(client, name)
            break


def broadcast(message: str, prefix=""):
    """Broadcast a message to all the clients"""
    broadcast_to_delete = []
    for user in broadcast_clients:
        try:
            socket_send(user, prefix + message)
        except ConnectionResetError:
            broadcast_to_delete.append(user)
            print("A broadcast disconnected")

    for user in broadcast_to_delete:
        broadcast_clients.remove(user)
        del addresses[user]


def broadcast_leaderboard():
    ordered_leaderboard = dict((clients[k], v) for (k, v) in sorted(score.items(),
                                                                    key=lambda item: item[1],
                                                                    reverse=True))
    leaderboard_to_delete: List[socket] = []
    for user in leaderboard_clients:
        try:
            socket_send(user, json.dumps(ordered_leaderboard))
        except ConnectionResetError:
            leaderboard_to_delete.append(user)
            print("A leaderboard disconnected")

    for user in leaderboard_to_delete:
        leaderboard_clients.remove(user)
        del addresses[user]


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
    broadcast_leaderboard()


clients: Dict[socket, str] = {}
addresses: Dict[socket, Tuple[str, int]] = {}
score: Dict[socket, int] = {}
broadcast_clients: List[socket] = []
leaderboard_clients: List[socket] = []

HOST = 'localhost'
PORT = 53000
BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDRESS)

# 5 Minutes timer
timer = Timer(5 * 60.0, broadcast, ['TIMER ENDED'])
timer.start()

with open("questions.json", "r") as questions_file:
    questions_obj = json.load(questions_file)

if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connections...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
