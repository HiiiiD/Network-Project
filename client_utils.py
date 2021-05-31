from typing import Callable, Tuple, List
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread


def create_socket_thread(address: Tuple[str, int], thread_func: Callable):
    """Create a socket that connects to the specified `address` and starts a thread with the `thread_func`

    Parameters
    ----------
    address : tuple[str, int]
        address used for connecting the socket
    thread_func
        function that is working on the thread
    """
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)
    sock_thread = Thread(target=thread_func)
    sock_thread.setDaemon(True)
    sock_thread.start()
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
