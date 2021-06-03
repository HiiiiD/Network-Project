from threading import Thread
from typing import List, Tuple
from socket import socket, AF_INET, SOCK_STREAM


def create_socket_thread(address: Tuple[str, int], thread_func):
    """Create a socket that connects to the `address` and a thread that handles `thread_func`, then connect the socket

    Parameters
    ----------
    address : Tuple[str, int]
        address used for connecting the socket
    thread_func : Any
        function used as the target for the thread

    """
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)
    sock_thread = Thread(target=thread_func, daemon=True)
    return sock, sock_thread


def read_message(sock: socket, buf_size: int = 1024) -> List[str]:
    """Read a message from the server, then return a list of messages sent by the server

    Parameters
    ----------
    sock : socket
        socket used to read the message
    buf_size : int
        size of the buffer(in bytes) used by the socket to read the message (default is 1024)

    Returns
    -------
    list[str]
        a list of messages split by the sequence '\\r\\n\\r\\n'
    """
    message = sock.recv(buf_size).decode("utf8")
    return list(filter(None, message.split('\r\n\r\n')))
