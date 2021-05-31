from threading import Condition
import tkinter as tkt
import json
from typing import Any

from GUI import TkinterApplication
from client_utils import create_socket_thread, read_message


def broadcast_receive():
    broadcast_socket.recv(BUFFER_SIZE).decode("utf8")
    broadcast_socket.send(bytes("BROADCAST", "utf8"))
    while True:
        try:
            msg = read_message(broadcast_socket)[0]
            if msg == 'TIMER ENDED':
                window.disable_inputs()
            window.push_broadcast_message(msg)
        except ConnectionResetError:
            print("Closed the broadcast connection")
            return


def leaderboard_receive():
    # Get the welcome message
    leaderboard_socket.recv(BUFFER_SIZE).decode("utf8")
    leaderboard_socket.send(bytes("LEADERBOARD", "utf8"))
    while True:
        try:
            msg = read_message(leaderboard_socket)[0]
            window.clear_leaderboard()
            parsed_msg = json.loads(msg)
            for (k, v) in parsed_msg.items():
                window.push_leaderboard_message(f"{k}:{v}")
        except ConnectionResetError:
            print("Closed the leaderboard connection")
            return


def client_receive():
    global game_loop
    """Function for handling messages from the server"""

    # Initial communication
    try:
        # Message telling the instructions
        instructions_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        window.push_client_message(instructions_msg)
        # Welcome message
        welcome_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        window.push_client_message(welcome_msg)
        received_message = read_message(client_socket)
        role_msg = received_message[0]
        window.set_role(json.loads(role_msg)["role"])
        window.push_client_message(received_message[1])
    except OSError:
        print("Closed the connection")
        return

    with selection_cond_variable:
        game_loop = True

    first_run = True

    # Game loop
    while True:
        try:
            # Retrieve the questions
            if len(received_message) == 3 and first_run:
                questions = json.loads(received_message[2])
                first_run = False
            else:
                questions = json.loads(read_message(client_socket)[0])

            question_response = manage_questions(questions)
            # If a not-trick question has been chosen
            # Retrieve the choices
            choices = question_response["choices"]
            manage_choices(choices)
        except OSError:
            print("Closed the connection")
            break


def manage_questions(questions: list[str]):
    """Manage the loading/selection of the question to answer

    Parameters
    ----------
    questions : list[str]
        list of strings containing the questions

    Returns
    -------
    Any
        question response that contains a status and the choices(list of strings)
    """
    # Show the questions message
    window.push_client_message("Questions")
    # Show the alternatives
    show_alternatives(questions)
    with selection_cond_variable:
        # Wait for the notification that a new message has been typed
        selection_cond_variable.wait()
    # Retrieve the selected question
    selected_question = window.peek_message()
    # Perform a check in order to have a valid question number
    if selected_question.isnumeric():
        numeric_selected_question = int(selected_question)
        if numeric_selected_question < 0 or numeric_selected_question >= len(questions):
            client_socket.send(bytes("VALIDATION ERROR", "utf8"))
            print("Invalid question number")
            restart_game()
            return
    else:
        client_socket.send(bytes("VALIDATION ERROR", "utf8"))
        print("Question number must be a number")
        restart_game()
        return
    # Reset the text field
    window.reset_field()
    # Send the selected question to the server
    client_socket.send(bytes(questions[int(selected_question) - 1], "utf8"))
    # Wait for a response that contains a status
    response = read_message(client_socket)
    # Parse the first argument of the response that is a json that indicates the status
    question_response = json.loads(response[0])
    # LOST status means that a TRICK question has been chosen
    if question_response["status"] == "LOST":
        print("You got a trick question")
        # Close the window
        window.quit()
        return

    # If the user didn't pick a trick question, return the question response
    return question_response


def manage_choices(choices: list[str]):
    # Show the choices message
    window.push_client_message("Choices")
    # Show the alternatives
    show_alternatives(choices)
    with selection_cond_variable:
        # Wait for the notification that a new message has been typed
        selection_cond_variable.wait()
    # Retrieve the selected choice
    selected_choice = window.peek_message()
    # Perform a check in order to have a valid choice number
    if selected_choice.isnumeric():
        numeric_selected_choice = int(selected_choice)
        if numeric_selected_choice < 0 or numeric_selected_choice >= len(choices):
            client_socket.send(bytes("VALIDATION ERROR", "utf8"))
            print("Invalid choice number")
            restart_game()
            return
    else:
        client_socket.send(bytes("VALIDATION ERROR", "utf8"))
        print("Choice number must be a number")
        restart_game()
        return
    # Reset the text field
    window.reset_message()
    # Send the selected choice to the server
    client_socket.send(bytes(choices[int(selected_choice) - 1], "utf8"))
    # Wait for a response that contains the new score
    response = read_message(client_socket)
    new_score = int(json.loads(response[0])['score'])
    # Write the new score
    window.set_score(new_score)
    window.clear_quiz_listbox()


def restart_game():
    window.clear_quiz_listbox()
    window.reset_field()


def show_alternatives(elems: list[Any]):
    """Show all the elements, one by one, in the client listbox"""
    for i in range(len(elems)):
        window.push_client_message(f"{i + 1}. {elems[i]}")


def send_to_server(event=None):
    global game_loop
    """Function for sending messages to the server"""
    msg = window.peek_message()
    if msg == "{quit}":
        client_socket.send(bytes(msg, "utf8"))
        client_socket.close()
        window.close_window()
        return

    with selection_cond_variable:
        if game_loop:
            selection_cond_variable.notify(1)
        else:
            client_socket.send(bytes(msg, "utf8"))
            window.reset_message()


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

window = TkinterApplication(send_to_server)

BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

client_socket, client_thread = create_socket_thread(ADDRESS, client_receive)
broadcast_socket, broadcast_thread = create_socket_thread(ADDRESS, broadcast_receive)
leaderboard_socket, leaderboard_thread = create_socket_thread(ADDRESS, leaderboard_receive)

# Start the app
tkt.mainloop()
