from collections import OrderedDict, defaultdict
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Timer
import json
from random import sample, choice
from typing import Dict, Tuple, List
from traceback import print_exc


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
    # Get a random role
    role = {"role": choice(roles)}
    # Send the role
    socket_send(client, json.dumps(role))
    socket_send(client, f"Your role is: {role['role']}")
    msg = f"{name} joined the chat with the role {role['role']}!"
    # Broadcast to all the users that a new user just joined the chat
    broadcast(msg)
    # Updates the client dictionary
    clients[client] = name
    score[client] = 0
    broadcast_leaderboard()

    # Game loop
    while True:
        # Shuffle the questions
        shuffled_questions = sample(questions_obj["questions"], len(questions_obj["questions"]))
        # Get 3 of these shuffled questions
        all_questions = shuffled_questions[:3]
        # Map each question object to only the question name
        questions = list(map(lambda q: q["question"], all_questions))
        # Get the trick question
        trick_question = choice(all_questions)
        try:
            socket_send(client, json.dumps(questions))
            received_question = client.recv(BUFFER_SIZE).decode("utf8")
            # Check if there was a validation error
            if received_question == "VALIDATION ERROR":
                continue
            # Check if the client got the trick question
            if received_question == trick_question["question"]:
                socket_send(client, json.dumps({"status": "LOST"}))
                broadcast(f"{name} have been tricked")
                client.close()
                user_quit(client, name)
                return

            question_to_answer = next(q for q in all_questions if q["question"] == received_question)
            socket_send(client, json.dumps({"status": "NOT_LOST", "choices": question_to_answer["choices"]}))
            received_choice = client.recv(BUFFER_SIZE).decode("utf8")
            # Check for UI validation error
            if received_choice == "VALIDATION ERROR":
                continue

            won = False
            # Check if the right answer has been chosen
            if received_choice == question_to_answer["right_answer"]:
                won = True
                score[client] = score[client] + 1
            else:
                score[client] = score[client] - 1

            broadcast(f"{name} {'got' if won else 'lost'} a point, its current score is {score[client]}")
            broadcast_leaderboard()
            socket_send(client, json.dumps({"score": score[client]}))
        except (ConnectionResetError, ConnectionAbortedError):
            # Here the client already closed its socket
            # so this Error is raised because socket.close() cannot be performed
            print("Connection reset")
            user_quit(client, name)
            break
        except StopIteration:
            print(f"{name} quit the application when answering a question")
            user_quit(client, name)
            break
        except Exception:
            print_exc()
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

    if message == "TIMER ENDED":
        # If the broadcast message says TIMER ENDED then broadcast
        # To the leaderboard socket the winner
        ordered_leaderboard = order_leaderboard()
        # Group the leaderboard by value
        leaderboard_by_value = defaultdict(list)
        for key, val in sorted(ordered_leaderboard.items()):
            leaderboard_by_value[val].append(key)
        if len(leaderboard_by_value.keys()) == 0:
            return
        leaderboard_by_value = OrderedDict((k, v) for k, v in sorted(leaderboard_by_value.items(),
                                                                     key=lambda item: item[0],
                                                                     reverse=True))
        winner_score = next(iter(leaderboard_by_value))
        winner_list = leaderboard_by_value[winner_score]
        if len(winner_list) == 1:
            winner = {
                "winner_name": winner_list[0],
                "winner_score": winner_score
            }
        else:
            winner = list(map(lambda elem: {"winner_name": elem, "winner_score": winner_score}, winner_list))

        broadcast_leaderboard({"DECLARED_WINNER": winner})


def broadcast_leaderboard(winner_pair=None):
    """Broadcast the leaderboard"""
    # Broadcasting the winner
    if winner_pair is not None:
        message = json.dumps(winner_pair)
    else:
        # Broadcasting the entire leaderboard
        message = json.dumps(order_leaderboard())

    # Leaderboard sockets to delete
    leaderboard_to_delete: List[socket] = []
    for user in leaderboard_clients:
        try:
            socket_send(user, message)
        except ConnectionResetError:
            leaderboard_to_delete.append(user)
            print("A leaderboard disconnected")

    # Delete leaderboard sockets from the clients and from the addresses
    for user in leaderboard_to_delete:
        leaderboard_clients.remove(user)
        del addresses[user]


def order_leaderboard():
    """Order the leaderboard by value descending"""
    ordered_leaderboard = OrderedDict((clients[k], v) for (k, v) in sorted(score.items(),
                                                                           key=lambda item: item[1],
                                                                           reverse=True))
    return ordered_leaderboard


def socket_send(sock: socket, message):
    """Send a message to the socket with utf8 encoding"""
    return sock.send(bytes(message + "\r\n\r\n", "utf8"))


def delete_client(client):
    """Delete a client from all the dictionaries"""
    del clients[client]
    del addresses[client]
    del score[client]


def user_quit(client, name):
    """Function invoked whenever a user quit from the game"""
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

roles = [
    'Apprentice',
    'High',
    'Sage',
    'Demonlord',
    'High',
    'Magister',
    'Foreman',
    'Ranger',
    'Commander',
    'Spokesman',
    'Royal',
    'Saint',
    'Royal',
    'Mentor',
    'Warmaster'
]

# 5 Minutes timer
timer = Timer(2 * 60.0, broadcast, ['TIMER ENDED'])
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
